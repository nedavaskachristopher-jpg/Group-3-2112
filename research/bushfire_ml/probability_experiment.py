"""Chronological probability diagnostics and provisional recall-target policies."""

import json

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier

from .calibration import apply_sigmoid, fit_sigmoid, select_recall_threshold
from .data import LOCAL_ROOT, ROOT, load_development, model_matrix, sha256, verify_seal
from .evaluation import evaluate, reliability_bins
from .models import fit_logistic, fit_xgboost, fit_xgboost_fixed
from .probability_reporting import write_probability_report
from .temporal_stability import FEATURES, KEYS, describe, forward_parts, require_complete_days, window_rows

CONFIG_PATH = ROOT / "config/probability_v1.json"
NAMES = {"logistic_16": "Logistic 16 raw", "logistic_17": "Logistic 17 raw",
         "xgboost_16": "XGBoost 16 raw", "xgboost_17": "XGBoost 17 raw",
         "sigmoid_xgboost_17": "XGBoost 17 sigmoid candidate",
         "calibration_prevalence": "Past calibration prevalence", "persistence": "Persistence"}


def probability_metrics(frame, scores, config, hard_rule=False, calibrated=False):
    metrics = evaluate(frame.fire_positive, scores, config["diagnostic_threshold"], int(frame.feature_date.nunique()), hard_rule)
    bins = reliability_bins(frame.fire_positive, scores, config["reliability_bins"])
    metrics["reliability_bins"] = bins
    metrics["observed_rate"] = float(frame.fire_positive.mean())
    metrics["absolute_mean_gap"] = abs(metrics["score_mean"]-metrics["observed_rate"])
    metrics["binned_absolute_gap"] = sum(b["rows"]*abs(b["mean_probability"]-b["observed_rate"]) for b in bins)/len(frame)
    if calibrated:
        metrics["interpretation"] = "Sigmoid-recalibrated candidate estimate; reliability not established"
    return metrics


def partition_metrics(frame, scores, config):
    all_rows, no_current = {}, {}
    subset = frame.fire_today.eq(0).to_numpy()
    for key, prediction in scores.items():
        all_rows[key] = probability_metrics(frame, prediction, config, key == "persistence", key == "sigmoid_xgboost_17")
        if subset.any():
            no_current[key] = probability_metrics(frame.loc[subset], np.asarray(prediction)[subset], config,
                                                   key == "persistence", key == "sigmoid_xgboost_17")
    return {"all_rows": all_rows, "no_current_detection": no_current}


def assess_threshold(frame, scores, threshold):
    metrics = evaluate(frame.fire_positive, scores, threshold, int(frame.feature_date.nunique()))
    mask = frame.fire_today.eq(0).to_numpy()
    subset = evaluate(frame.fire_positive.to_numpy()[mask], np.asarray(scores)[mask], threshold,
                      int(frame.loc[mask, "feature_date"].nunique())) if mask.any() else None
    return {"all_rows": metrics, "no_current_detection": subset}


def fit_scenario(development, scenario, config, logistic_config, xgb_config):
    inner, stopping, refit, calibration = forward_parts(development, scenario["calibration"], config)
    assessment = window_rows(development, **scenario["assessment"])
    require_complete_days(assessment, **scenario["assessment"])
    distance = (pd.Timestamp(assessment.feature_date.min())-pd.Timestamp(calibration.feature_date.max())).days
    if distance < config["gap_days"]+1 or not pd.to_datetime(calibration.target_date).max() < pd.to_datetime(assessment.feature_date).min():
        raise ValueError("Calibration outcomes must precede assessment with the full calendar gap")
    if set(calibration.grid_id) != set(assessment.grid_id):
        raise ValueError("Calibration and assessment must preserve the same grid population")
    if set(calibration.fire_positive.unique()) != {0, 1}:
        raise ValueError("Calibration requires both classes; do not borrow future labels")
    frames = {"calibration": calibration, "assessment": assessment}
    scores = {part: {} for part in frames}
    fits, models = {}, {}
    for size, feature_set in FEATURES.items():
        logistic = fit_logistic(refit, dict(logistic_config, feature_set=feature_set))
        selection = fit_xgboost(inner, stopping, xgb_config, feature_set)
        tree_count = int(selection.get_booster().num_boosted_rounds())
        boosted = fit_xgboost_fixed(refit, xgb_config, feature_set, tree_count)
        fits[f"xgboost_{size}"] = {"trees": tree_count, "scale_pos_weight": float(boosted.get_params()["scale_pos_weight"])}
        for key, model in [(f"logistic_{size}", logistic), (f"xgboost_{size}", boosted)]:
            models[key] = model
            for part, frame in frames.items():
                scores[part][key] = model.predict_proba(model_matrix(frame, feature_set))[:, 1]
    sigmoid = fit_sigmoid(scores["calibration"]["xgboost_17"], calibration.fire_positive, config["sigmoid"])
    for part, frame in frames.items():
        scores[part]["sigmoid_xgboost_17"] = apply_sigmoid(scores[part]["xgboost_17"], sigmoid)
        scores[part]["calibration_prevalence"] = np.full(len(frame), calibration.fire_positive.mean())
        scores[part]["persistence"] = frame.fire_today.to_numpy(dtype=float)
    policies = []
    for key in ["xgboost_17", "sigmoid_xgboost_17"]:
        for target in config["recall_targets"]:
            selection = select_recall_threshold(scores["calibration"][key], calibration.fire_positive, target)
            policies.append({"score": key, **selection,
                             **{part: assess_threshold(frame, scores[part][key], selection["threshold"]) for part, frame in frames.items()}})
    # Include exact score transitions so a plot cannot interpolate impossible alert counts.
    observed_scores = np.unique(np.asarray(scores["assessment"]["xgboost_17"], dtype=float))
    sweep_cutoffs = set(config["threshold_sweep"]) | set(observed_scores)
    sweep_cutoffs.update(float(value) for value in np.nextafter(observed_scores, np.inf) if value <= 1)
    sweep_cutoffs.update(p["threshold"] for p in policies if p["score"] == "xgboost_17")
    sweep = [{"threshold": threshold, **assess_threshold(assessment, scores["assessment"]["xgboost_17"], threshold)}
             for threshold in sorted(sweep_cutoffs)]
    daily = []
    for date, frame in assessment.groupby("feature_date"):
        mask = assessment.feature_date.eq(date).to_numpy()
        day_scores = {key: values[mask] for key, values in scores["assessment"].items()}
        daily.append({"date": date, **partition_metrics(frame, day_scores, config)})
    fire_groups = {}
    for flag, frame in assessment.groupby("fire_today"):
        mask = assessment.fire_today.eq(flag).to_numpy()
        fire_groups[str(flag)] = {
            key: probability_metrics(frame, scores["assessment"][key][mask], config, calibrated=key == "sigmoid_xgboost_17")
            for key in ["xgboost_17", "sigmoid_xgboost_17"]}
    result = {"name": scenario["name"], "inner_training": describe(inner), "inner_stopping": describe(stopping),
              "base_refitting": describe(refit), "calibration_population": describe(calibration),
              "assessment_population": describe(assessment), "base_fits": fits, "sigmoid_fit": sigmoid,
              "calibration_metrics": partition_metrics(calibration, scores["calibration"], config),
              "assessment_metrics": partition_metrics(assessment, scores["assessment"], config),
              "policies": policies, "assessment_threshold_sweep": sweep,
              "daily_assessment": daily, "assessment_fire_today_groups": fire_groups}
    predictions = []
    for part, frame in frames.items():
        prediction = frame[KEYS].copy()
        prediction["scenario"], prediction["partition"] = scenario["name"], part
        for key, values in scores[part].items():
            # Keep float32 model scores exact when CSV and JSON cutoffs are replayed together.
            prediction[key+"_score"] = np.asarray(values, dtype=float)
        predictions.append(prediction)
    return result, pd.concat(predictions, ignore_index=True), models


def calibration_decision(results, gate):
    supported, improved = [], []
    for result in results:
        calibration, assessment = result["calibration_population"], result["assessment_population"]
        enough_days = calibration["days"] >= gate["minimum_calibration_days"] and assessment["days"] >= gate["minimum_assessment_days"]
        enough_classes = all(min(part["positives"], part["rows"]-part["positives"]) >= gate["minimum_class_count_per_partition"]
                             for part in [calibration, assessment])
        if not (enough_days and enough_classes):
            continue
        supported.append(result)
        metrics = result["assessment_metrics"]["all_rows"]
        if all(metrics["sigmoid_xgboost_17"][metric] < metrics[reference][metric]
               for metric in ["brier_score", "log_loss"] for reference in ["xgboost_17", "calibration_prevalence"]):
            improved.append(result)
    disjoint = []
    for result in sorted(improved, key=lambda r: r["assessment_population"]["feature_end"]):
        if not disjoint or result["assessment_population"]["feature_start"] > disjoint[-1]["assessment_population"]["feature_end"]:
            disjoint.append(result)
    adopted = len(disjoint) >= gate["minimum_disjoint_assessment_windows"]
    return {"sigmoid_adopted": adopted, "supported_windows": [r["name"] for r in supported],
            "improved_supported_windows": [r["name"] for r in improved],
            "disjoint_improved_windows": len(disjoint), "required_windows": gate["minimum_disjoint_assessment_windows"],
            "reliable_percentages_established": False,
            "conclusion": "Sigmoid meets project research comparison gate; this is not an operational probability guarantee" if adopted
                          else "Do not adopt sigmoid. Available temporal support and held-later improvements do not meet the project evidence gate. Retain raw research scores; trustworthy probability percentages remain unestablished."}


def main():
    seal = verify_seal()
    config = json.loads(CONFIG_PATH.read_text())
    logistic_path, xgb_path = ROOT / "config/baseline_v1.json", ROOT / "config/xgboost_v1.json"
    logistic_config, xgb_config = json.loads(logistic_path.read_text()), json.loads(xgb_path.read_text())
    reference_paths = [logistic_path, xgb_path, ROOT / "config/temporal_stability_v1.json",
                       *[ROOT / f"reports/{name}.json" for name in ["baseline_validation", "current_fire_comparison", "xgboost_comparison", "temporal_stability"]]]
    hashes = {str(path.relative_to(ROOT)): sha256(path) for path in reference_paths}
    baseline = json.loads((ROOT / "reports/baseline_validation.json").read_text())
    xgb_reference = json.loads((ROOT / "reports/xgboost_comparison.json").read_text())
    if sha256(logistic_path) != baseline["baseline_config_sha256"] or sha256(xgb_path) != xgb_reference["configuration_sha256"]:
        raise ValueError("Model settings must match the original comparisons")
    for path in reference_paths:
        if path.parent.name == "reports" and json.loads(path.read_text())["data_hashes"] != seal["file_sha256"]:
            raise ValueError("A reference used different sealed data")
    development = pd.concat([load_development("train"), load_development("validation")], ignore_index=True)
    if development.duplicated(["grid_id", "feature_date"]).any():
        raise ValueError("Development partitions overlap")
    results, predictions, artifact_hashes = [], [], {}
    local_output = LOCAL_ROOT / config["experiment"]
    local_output.mkdir(exist_ok=True)
    for scenario in config["scenarios"]:
        result, prediction, models = fit_scenario(development, scenario, config, logistic_config, xgb_config)
        folder = local_output / scenario["name"]
        folder.mkdir(exist_ok=True)
        for key, model in models.items():
            path = folder / (key+(".ubj" if key.startswith("xgboost") else ".joblib"))
            if key.startswith("xgboost"):
                model.save_model(path)
                restored = XGBClassifier()
                restored.load_model(path)
            else:
                joblib.dump(model, path)
                restored = joblib.load(path)
            feature_set = FEATURES[key.rsplit("_", 1)[1]]
            for part in ["calibration", "assessment"]:
                frame = window_rows(development, **scenario[part])
                replay = restored.predict_proba(model_matrix(frame, feature_set))[:, 1].astype(float)
                expected = prediction.loc[prediction.partition.eq(part), key+"_score"].to_numpy()
                if not np.array_equal(replay, expected):
                    raise RuntimeError("Saved model does not exactly reproduce the policy scores")
            artifact_hashes[str(path.relative_to(ROOT))] = sha256(path)
        (folder / "sigmoid.json").write_text(json.dumps(result["sigmoid_fit"], indent=2)+"\n", encoding="utf-8")
        artifact_hashes[str((folder / "sigmoid.json").relative_to(ROOT))] = sha256(folder / "sigmoid.json")
        results.append(result)
        predictions.append(prediction)
    prediction_path = local_output / "probability_predictions.csv"
    combined = pd.concat(predictions, ignore_index=True)
    combined.to_csv(prediction_path, index=False, lineterminator="\n", float_format="%.17g")
    replay = pd.read_csv(prediction_path, converters={column: float for column in combined if column.endswith("_score")})
    if not np.array_equal(combined.filter(like="_score").to_numpy(), replay.filter(like="_score").to_numpy()):
        raise RuntimeError("CSV round trip changed scores used by exact tied-score cutoffs")
    artifact_hashes[str(prediction_path.relative_to(ROOT))] = sha256(prediction_path)
    decision = calibration_decision(results, config["calibration_evidence_gate"])
    recent = results[-1]
    score_key = "sigmoid_xgboost_17" if decision["sigmoid_adopted"] else "xgboost_17"
    policy = {"status": "draft_research_policy_not_frozen", "model": "xgboost_17", "scenario": recent["name"],
              "trees": recent["base_fits"]["xgboost_17"]["trees"], "calibration": "sigmoid" if decision["sigmoid_adopted"] else None,
              "base_artifact": str((local_output / recent["name"] / "xgboost_17.ubj").relative_to(ROOT)),
              "base_fit_feature_end": recent["base_refitting"]["feature_end"], "score_scale": [0, 1],
              "score": score_key, "score_display_label": "Experimental model score", "display_as_validated_probability_percent": False,
              "cutoffs": [{k: row[k] for k in ["recall_target", "threshold", "comparison", "selection_recall", "selection_rows", "selection_scope"]}
                          for row in recent["policies"] if row["score"] == score_key],
              "selection_dates": recent["calibration_population"], "limitations": "Recall constraints describe calibration selection rows, not a promise for future dates. One calibration day is inadequate for a dependable operating threshold. No operational dispatch is authorised or modelled.",
              "artifact_hashes": artifact_hashes, "final_holdout_evaluated": False}
    report = {"experiment": config["experiment"], "configuration": config, "configuration_sha256": sha256(CONFIG_PATH),
              "data_hashes": seal["file_sha256"], "reference_hashes": hashes, "scenarios": results,
              "calibration_decision": decision, "draft_research_policy": policy,
              "notes": [
                  "The base model is fitted before calibration and then kept fixed. Calibration and threshold labels never enter base fitting or tree selection, and assessment labels enter none of these fitting steps.",
                  "Every date is a UTC feature date; the binary target is eligible satellite detection on the next day, including continuing fire, not confirmed ignition or fire severity.",
                  "Inputs are retrospective full-feature-day weather and satellite records. Their real publication latencies are not modelled; these are research reminders rather than a real-time service.",
                  "Both scenarios use identical rows for matched logistic/XGBoost feature sets. Scalers and class weights use base fitting rows only. The calibrator uses natural label prevalence without balanced weights.",
                  "One fixed nondecreasing sigmoid is compared with raw scores. This is an explicitly regularised logistic recalibration on score logits, not an assertion that it is identical to sklearn's implementation or will always preserve AP; zero slope or clipping can introduce ties.",
                  "Reliability bins show observed frequencies and sample sizes. Brier and log loss assess overall probability quality, including discrimination, and do not isolate calibration. Binned gaps depend on bin definitions and are descriptive, not certification.",
                  "Assessment rows are excluded from each scenario's fitting but were previously reviewed in development. The scenarios overlap in assessment dates and share ongoing events; they are not independent replications or a new-season test.",
                  "Project evidence-gate counts are transparent conservative heuristics, not universal minimum sample requirements. Calendar support alone cannot establish independent-fire-event support.",
                  "Calibration fits and threshold selection share calibration rows and are selection results. Only subsequent assessment metrics check transfer. Do not report calibration-fit reliability as held-later reliability.",
                  "Recall targets of 80% and 90% were requested for parallel research comparison. Cutoffs minimise selection-row alerts subject to that target, retain ties, and may miss the target later. No false-alarm price or missed-fire cost is invented.",
                  "The assessment sweep includes a fixed grid, observed score transitions and previously selected cutoffs to show exact stepwise trade-offs. No policy cutoff is reselected using assessment answers, including on the no-current-detection subset.",
                  "No dates or labels were changed, including the target-date 22 December zero-detection concern. All cell-day counts are distinct from independent incidents or staff requirements.",
                  "The recent one-day calibration/one-day assessment scenario is a small transfer check, not enough evidence for an adopted calibrator or operational warning policy.",
                  "Every local saved model is reloaded and required to reproduce its exact calibration/assessment scores. Score CSVs use float64 and 17-digit text with round-trip checks so tied-score threshold decisions are reproducible; rounded display cutoffs are not replay inputs.",
                  "The draft policy and local artifacts are concrete candidates for a later pipeline freeze. No final-test outputs were generated and no trustworthy percentage claim is made."
              ], "holdout_evaluated": False}
    if verify_seal() != seal or any(sha256(ROOT / path) != digest for path, digest in hashes.items()):
        raise RuntimeError("Frozen data or preserved model references changed")
    (ROOT / "reports/probability_reliability.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    (ROOT / "reports/draft_probability_policy.json").write_text(json.dumps(policy, indent=2)+"\n", encoding="utf-8")
    write_probability_report(report, NAMES)
    print(json.dumps({"calibration_decision": decision, "recent_cutoffs": policy["cutoffs"],
                      "scenario_metrics": [{"name": r["name"], "assessment": {k: {m: v[m] for m in ["brier_score", "log_loss", "score_mean", "observed_rate"]}
                          for k, v in r["assessment_metrics"]["all_rows"].items() if k in ["xgboost_17", "sigmoid_xgboost_17", "calibration_prevalence"]},
                          "policies": [{"score": p["score"], "target": p["recall_target"], "cutoff": p["threshold"],
                              "assessment": {m: p["assessment"]["all_rows"][m] for m in ["precision", "recall", "true_positives", "false_positives", "false_negatives"]}} for p in r["policies"]]}
                          for r in results], "holdout_evaluated": False}, indent=2))


if __name__ == "__main__":
    main()
