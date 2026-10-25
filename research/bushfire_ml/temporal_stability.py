"""Development-only date slices and nested forward-window diagnostics."""

import json

import numpy as np
import pandas as pd

from .data import LOCAL_ROOT, ROOT, load_development, model_matrix, sha256, verify_seal
from .evaluation import evaluate
from .models import fit_logistic, fit_xgboost, fit_xgboost_fixed
from .temporal_reporting import write_temporal_report

CONFIG_PATH = ROOT / "config" / "temporal_stability_v1.json"
KEYS = ["grid_id", "feature_date", "target_date", "fire_positive", "fire_today"]
FEATURES = {"16": "conditions_core", "17": "core_plus_fire_today"}
NAMES = {"prevalence": "Past prevalence", "logistic_16": "Logistic 16", "logistic_17": "Logistic 17",
         "xgboost_16": "XGBoost 16", "xgboost_17": "XGBoost 17", "persistence": "Persistence"}


def window_rows(frame, start, end):
    return frame.loc[frame.feature_date.between(str(start)[:10], str(end)[:10])].copy()


def require_complete_days(frame, start, end):
    expected = set(pd.date_range(start, end).strftime("%Y-%m-%d"))
    if set(frame.feature_date) != expected or frame.duplicated(["grid_id", "feature_date"]).any():
        raise ValueError("Every requested date must be represented without duplicate cell-days")
    grids = set(frame.grid_id)
    if any(set(group.grid_id) != grids for _, group in frame.groupby("feature_date")):
        raise ValueError("Keep the same complete grid population on every represented date")


def forward_parts(development, window, config):
    """All cells stay together; both temporal gaps are defined by calendar days."""
    start = pd.Timestamp(window["start"])
    gap = config["gap_days"]
    if gap < 7 or config["stopping_days"] < 1:
        raise ValueError("Forward checks require at least seven gap days and a stopping window")
    refit_end = start - pd.Timedelta(days=gap+1)
    stop_start = refit_end - pd.Timedelta(days=config["stopping_days"]-1)
    inner_end = stop_start - pd.Timedelta(days=gap+1)
    past = development.loc[development.feature_date.gt(config["warmup_end_inclusive"])]
    refit = past.loc[past.feature_date.le(str(refit_end.date()))].copy()
    inner = past.loc[past.feature_date.le(str(inner_end.date()))].copy()
    stop = window_rows(past, stop_start, refit_end)
    outer = window_rows(past, window["start"], window["end"])
    require_complete_days(stop, stop_start, refit_end)
    require_complete_days(outer, window["start"], window["end"])
    for earlier, later in [(inner, stop), (refit, outer)]:
        if earlier.empty or not pd.to_datetime(earlier.target_date).max() < pd.to_datetime(later.feature_date).min():
            raise ValueError("Fitting outcomes must precede the next window's feature dates")
    if set(refit.grid_id) != set(outer.grid_id) or set(inner.grid_id) != set(outer.grid_id):
        raise ValueError("Forward windows must preserve the fitting grid population")
    return inner, stop, refit, outer


def describe(frame):
    return {"feature_start": str(frame.feature_date.min()), "feature_end": str(frame.feature_date.max()),
            "target_start": str(frame.target_date.min()), "target_end": str(frame.target_date.max()),
            "rows": len(frame), "days": int(frame.feature_date.nunique()),
            "positives": int(frame.fire_positive.sum()), "positive_rate": float(frame.fire_positive.mean())}


def score_window(frame, scores, threshold):
    days = int(frame.feature_date.nunique())
    subset = frame.fire_today.eq(0).to_numpy()
    metrics, subset_metrics = {}, {}
    for key, values in scores.items():
        metrics[key] = evaluate(frame.fire_positive, values, threshold, days, key == "persistence")
        if subset.any():
            # Use represented subset dates for per-day alert burden, not the full window length.
            subset_metrics[key] = evaluate(frame.fire_positive.to_numpy()[subset], np.asarray(values)[subset],
                                           threshold, int(frame.loc[subset, "feature_date"].nunique()), key == "persistence")
    return {**describe(frame), "metrics": metrics, "no_current_detection": subset_metrics}


def fit_forward_window(development, window, config, logistic_config, xgb_config):
    inner, stop, refit, outer = forward_parts(development, window, config)
    scores = {"prevalence": np.full(len(outer), refit.fire_positive.mean()),
              "persistence": outer.fire_today.to_numpy(dtype=float)}
    fits = {}
    for size, feature_set in FEATURES.items():
        logistic = fit_logistic(refit, dict(logistic_config, feature_set=feature_set))
        scores[f"logistic_{size}"] = logistic.predict_proba(model_matrix(outer, feature_set))[:, 1]
        key = f"xgboost_{size}"
        if set(inner.fire_positive.unique()) != {0, 1} or set(stop.fire_positive.unique()) != {0, 1}:
            fits[key] = {"status": "unavailable", "reason": "Both classes required in past inner fitting and stopping data"}
            continue
        selection_model = fit_xgboost(inner, stop, xgb_config, feature_set)
        trees = int(selection_model.get_booster().num_boosted_rounds())
        model = fit_xgboost_fixed(refit, xgb_config, feature_set, trees)
        scores[key] = model.predict_proba(model_matrix(outer, feature_set))[:, 1]
        fits[key] = {"status": "fitted", "trees_selected_on_past": trees,
                     "refit_scale_pos_weight": float(model.get_params()["scale_pos_weight"])}
    result = {"name": window["name"], "inner_training": describe(inner), "inner_stopping": describe(stop),
              "refitting": describe(refit), "fits": fits,
              **score_window(outer, scores, config["diagnostic_threshold"])}
    predictions = outer[KEYS].copy()
    predictions["window"] = window["name"]
    for key, values in scores.items():
        predictions[key+"_score"] = values
    return result, predictions


def load_preserved_scores(validation, reference_report):
    path = LOCAL_ROOT / reference_report["experiment"] / "validation_predictions.csv"
    predicted = pd.read_csv(path)
    if len(predicted) != len(validation):
        raise ValueError("Saved predictions do not cover the validation population")
    aligned = validation[KEYS].merge(predicted, on=KEYS, validate="one_to_one", how="left", indicator=True)
    if not aligned["_merge"].eq("both").all():
        raise ValueError("Saved predictions do not match validation keys and labels")
    scores = {key: aligned[key+"_uncalibrated_score"].to_numpy() for key in NAMES if key != "prevalence"}
    return scores, path


def slice_results(validation, scores, windows, threshold):
    results = []
    for window in windows:
        mask = validation.feature_date.between(window["start"], window["end"]).to_numpy()
        part = validation.loc[mask]
        require_complete_days(part, window["start"], window["end"])
        results.append({"name": window["name"], **score_window(part, {k: v[mask] for k, v in scores.items()}, threshold)})
    return results


def main():
    seal = verify_seal()
    config = json.loads(CONFIG_PATH.read_text())
    logistic_path, xgb_path = ROOT / "config/baseline_v1.json", ROOT / "config/xgboost_v1.json"
    logistic_config, xgb_config = json.loads(logistic_path.read_text()), json.loads(xgb_path.read_text())
    reference_path = ROOT / "reports/xgboost_comparison.json"
    reference = json.loads(reference_path.read_text())
    if reference["data_hashes"] != seal["file_sha256"]:
        raise ValueError("Original experiment used different sealed data")
    if sha256(xgb_path) != reference["configuration_sha256"]:
        raise ValueError("XGBoost settings changed since the original comparison")
    if any(sha256(ROOT / path) != digest for path, digest in reference["reference_file_hashes"].items()):
        raise ValueError("Preserved logistic references changed since the original comparison")
    baseline = json.loads((ROOT / "reports/baseline_validation.json").read_text())
    if sha256(logistic_path) != baseline["baseline_config_sha256"]:
        raise ValueError("Logistic settings changed since the original baseline")
    training, validation = load_development("train"), load_development("validation")
    scores, prediction_path = load_preserved_scores(validation, reference)
    original_training = training.loc[training.feature_date.gt(config["warmup_end_inclusive"])]
    scores["prevalence"] = np.full(len(validation), original_training.fire_positive.mean())
    reference_paths = [reference_path, prediction_path, *[ROOT / p for p in reference["reference_file_hashes"]]]
    hashes = {str(path.relative_to(ROOT)): sha256(path) for path in reference_paths}
    daily_windows = [{"name": date, "start": date, "end": date} for date in sorted(validation.feature_date.unique())]
    development = pd.concat([training, validation], ignore_index=True)
    if development.duplicated(["grid_id", "feature_date"]).any():
        raise ValueError("Development partitions overlap")
    forward, predictions = [], []
    for window in config["forward_windows"]:
        result, prediction = fit_forward_window(development, window, config, logistic_config, xgb_config)
        forward.append(result)
        predictions.append(prediction)
    local_output = LOCAL_ROOT / config["experiment"]
    local_output.mkdir(exist_ok=True)
    pd.concat(predictions, ignore_index=True).to_csv(local_output / "forward_predictions.csv", index=False, lineterminator="\n")
    report = {
        "experiment": config["experiment"], "configuration": config,
        "configuration_hashes": {str(p.relative_to(ROOT)): sha256(p) for p in [CONFIG_PATH, logistic_path, xgb_path]},
        "data_hashes": seal["file_sha256"], "reference_hashes": hashes,
        "original_training": describe(original_training),
        "existing_validation_blocks": slice_results(validation, scores, config["validation_blocks"], config["diagnostic_threshold"]),
        "existing_validation_days": slice_results(validation, scores, daily_windows, config["diagnostic_threshold"]),
        "forward_windows": forward,
        "notes": [
            "All dates in window headings are UTC feature dates. The target date is the following day.",
            "Existing-model daily and three-day slices reuse the original validation outcomes that selected XGBoost length. They describe variability; they are not additional independent tests.",
            "Forward checks select tree count on past inner stopping data, then refit that fixed count on all available past rows before the outer gap. Both algorithms use identical refitting rows and reviewed inputs. Each fold learns its own class weights and logistic scaling from those rows.",
            "Seven feature-date gap days precede both inner stopping and outer evaluation. Inner gaps may rejoin the later refitting population because they are past development observations. Frozen protocol embargo rows are never loaded.",
            "The first seven-day window ends on the last sparse-fire week; subsequent windows follow the calendar. Development label availability and original validation results were already reviewed. No claim of untouched model selection is made.",
            "Keep unavailable XGBoost folds and zero-positive dates visible. No positive outcomes means AP and recall are undefined, not zero; false alerts and Brier remain available.",
            "AP depends on prevalence. Compare models within the same window; raw AP changes across windows do not isolate model deterioration. Do not average only available XGBoost folds and call that a four-fold comparison.",
            "These are dependent cells and dates from one season, potentially the same ongoing fires. Ranges are descriptive, not confidence intervals or independent-event validation.",
            "The original target-date 22 December zero-detection concern is retained (feature date 21 December). No dates or labels are changed.",
            "All scores remain uncalibrated; the fixed 0.5 cutoff is diagnostic. Stability of ranking does not establish reliable percentages or a useful operational threshold.",
            "Only training and validation outcomes were parsed. Original model reports and frozen data remain unchanged; the final test remains sealed."
        ],
        "holdout_evaluated": False,
    }
    if verify_seal() != seal or any(sha256(ROOT / p) != digest for p, digest in hashes.items()):
        raise RuntimeError("Sealed data or preserved references changed during temporal checks")
    (ROOT / "reports/temporal_stability.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    write_temporal_report(report, NAMES)
    print(json.dumps({"forward_windows": [{"name": row["name"], "refit_positives": row["refitting"]["positives"],
                      "stopping_positives": row["inner_stopping"]["positives"], "fits": row["fits"],
                      "AP": {k: v["average_precision"] for k, v in row["metrics"].items()}}
                     for row in forward], "holdout_evaluated": False}, indent=2))


if __name__ == "__main__":
    main()
