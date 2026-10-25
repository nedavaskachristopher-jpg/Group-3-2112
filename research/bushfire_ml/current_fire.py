"""Lesson 4: add one same-day input, holding the logistic setup fixed."""

from __future__ import annotations

import json

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve

from .baselines import CONFIG_PATH as BASELINE_CONFIG
from .data import LOCAL_ROOT, ROOT, load_development, model_matrix, read_protocol, sha256, verify_seal
from .evaluation import evaluate, reliability_bins
from .models import fit_logistic

CONFIG_PATH = ROOT / "config" / "current_fire_v1.json"


def check_comparison_settings(candidate: dict, baseline: dict) -> None:
    for key in ["training_warmup_end_inclusive", "logistic_regression", "diagnostic_threshold", "calibration_bins"]:
        if candidate[key] != baseline[key]:
            raise ValueError(f"The one-input experiment also changed {key}")
    if candidate["added_predictors"] != ["fire_today"] or candidate["feature_set"] != "core_plus_fire_today":
        raise ValueError("This comparison permits only the reviewed current-fire flag")


def make_figure(validation, all_scores, metrics, subsets) -> None:
    labels = {"core_16": "Logistic: 16 conditions inputs", "core_plus_fire_17": "Logistic: 16 inputs + current fire", "persistence": "Fire persistence"}
    colors = {"core_16": "#6B7280", "core_plus_fire_17": "#2563EB", "persistence": "#D97706"}
    new_subset = validation.fire_today.eq(0).to_numpy()
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), layout="constrained")
    for axis, mask, title in [(axes[0], np.ones(len(validation), dtype=bool), "All 387 validation cell-days"),
                              (axes[1], new_subset, "232 cell-days without a current detection")]:
        table = metrics if axis is axes[0] else subsets
        for name, values in all_scores.items():
            precision, recall, _ = precision_recall_curve(validation.fire_positive.to_numpy()[mask], values[mask])
            if name == "persistence" and axis is axes[1]:
                axis.axhline(validation.fire_positive.to_numpy()[mask].mean(), color=colors[name], linestyle="--",
                             label=f"Persistence: constant zero (AP {table[name]['average_precision']:.3f})")
            else:
                axis.step(recall, precision, where="post", color=colors[name],
                          label=f"{labels[name]} (AP {table[name]['average_precision']:.3f})")
        axis.set(xlabel="Recall", ylabel="Precision", title=title, xlim=(0, 1.02), ylim=(0, 1.02))
        axis.grid(alpha=0.15)
        axis.legend(loc="lower left" if axis is axes[0] else "upper left", fontsize=8)
    fig.suptitle("One added input | same algorithm, rows and settings | validation only", fontsize=13)
    fig.savefig(ROOT / "reports" / "current_fire_comparison.png", dpi=160)
    plt.close(fig)


def main() -> None:
    seal = verify_seal()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    baseline_config = json.loads(BASELINE_CONFIG.read_text(encoding="utf-8"))
    check_comparison_settings(config, baseline_config)
    if config["reference_baseline_config_sha256"] != sha256(BASELINE_CONFIG):
        raise RuntimeError("The reference baseline configuration changed")
    reference_path = ROOT / "reports" / "baseline_validation.json"
    reference_hash = sha256(reference_path)
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    if reference["data_hashes"] != seal["file_sha256"] or reference["baseline_config_sha256"] != sha256(BASELINE_CONFIG):
        raise RuntimeError("The reference run does not match the frozen data/settings")
    training = load_development("train")
    training = training.loc[training.feature_date.gt(config["training_warmup_end_inclusive"])].copy()
    validation = load_development("validation")
    if len(training) != reference["training_rows_fitted"]:
        raise RuntimeError("The training row population changed")
    if not pd.to_datetime(training.target_date).max() < pd.to_datetime(validation.feature_date).min():
        raise ValueError("Training outcomes overlap validation features")
    prediction_path = LOCAL_ROOT / reference["experiment"] / "validation_predictions.csv"
    previous_hash = sha256(prediction_path)
    previous = pd.read_csv(prediction_path)
    keys = ["grid_id", "feature_date", "target_date", "fire_positive", "fire_today"]
    # Align saved baseline predictions to the exact same validation rows.
    compared = validation[keys].merge(previous, on=keys, validate="one_to_one")
    if len(compared) != len(validation) or len(previous) != len(validation):
        raise ValueError("The reference validation rows changed")
    model = fit_logistic(training, config)
    inputs = model_matrix(validation, config["feature_set"])
    scores = model.predict_proba(inputs)[:, 1]
    scaler = model.named_steps["scaler"]
    np.testing.assert_allclose(scaler.mean_, model_matrix(training, config["feature_set"]).mean().to_numpy(), atol=1e-10)
    if int(scaler.n_samples_seen_) != len(training):
        raise RuntimeError("The scaler was fitted on a different population")
    days = int(validation.feature_date.nunique())
    candidate_metrics = evaluate(validation.fire_positive, scores, config["diagnostic_threshold"], days)
    new_subset = validation.fire_today.eq(0).to_numpy()
    candidate_new = evaluate(validation.fire_positive.to_numpy()[new_subset], scores[new_subset],
                             config["diagnostic_threshold"], days)
    metrics = {
        "core_16": reference["validation_metrics"]["logistic_core"],
        "core_plus_fire_17": candidate_metrics,
        "persistence": reference["validation_metrics"]["persistence"],
    }
    subsets = {
        "core_16": reference["fire_today_zero_subset_metrics"]["logistic_core"],
        "core_plus_fire_17": candidate_new,
        "persistence": reference["fire_today_zero_subset_metrics"]["persistence"],
    }
    # Reconcile comparison rows/scores to saved baseline metrics without refitting.
    for name, column in [("core_16", "logistic_core_score"), ("persistence", "persistence_score")]:
        result = evaluate(compared.fire_positive, compared[column], config["diagnostic_threshold"], days,
                          hard_rule=name == "persistence")
        for key in ["average_precision", "true_positives", "false_positives", "false_negatives", "true_negatives"]:
            if not np.isclose(result[key], metrics[name][key]):
                raise RuntimeError("The reference predictions no longer reproduce the baseline report")
    if sha256(reference_path) != reference_hash or sha256(prediction_path) != previous_hash or verify_seal() != seal:
        raise RuntimeError("A baseline or sealed data file changed during comparison")
    local_output = LOCAL_ROOT / config["experiment"]
    local_output.mkdir(exist_ok=True)
    joblib.dump(model, local_output / "logistic_core_plus_fire.joblib")
    output = validation[keys].copy()
    output["uncalibrated_score"] = scores
    output["uncalibrated_percent"] = 100*scores
    output.to_csv(local_output / "validation_predictions.csv", index=False, lineterminator="\n")
    report = {
        "experiment": config["experiment"], "comparison_config_sha256": sha256(CONFIG_PATH),
        "reference_report_sha256": reference_hash, "reference_predictions_sha256": previous_hash,
        "data_hashes": seal["file_sha256"], "feature_columns": list(inputs.columns),
        "training_rows": len(training), "validation_rows": len(validation), "validation_days": days,
        "settings_unchanged": config["logistic_regression"], "diagnostic_threshold": config["diagnostic_threshold"],
        "candidate_iterations": int(model.named_steps["classifier"].n_iter_[0]),
        "validation_metrics": metrics, "fire_today_zero_subset_metrics": subsets,
        "reliability_bins": reliability_bins(validation.fire_positive, scores, config["calibration_bins"]),
        "no_label_changes": True, "no_hyperparameter_search": True, "no_calibration_fitted": True,
        "holdout_evaluated": False,
    }
    (ROOT / "reports" / "current_fire_comparison.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    labels = {"core_16": "Logistic: 16 conditions inputs", "core_plus_fire_17": "Logistic: 16 inputs + current fire", "persistence": "Fire persistence"}
    all_scores = {"core_16": compared.logistic_core_score.to_numpy(), "core_plus_fire_17": scores,
                  "persistence": compared.persistence_score.to_numpy()}
    make_figure(validation, all_scores, metrics, subsets)
    lines = ["# Lesson 4: one added input", "", "The only design change is adding the audited same-day `fire_today` flag. The model is refitted, so all learned weights may change.", "",
             f"Both logistic fits use {len(training):,} training rows, the same 387 validation rows and identical classifier settings. The fixed diagnostic threshold remains 0.5. No final-test evaluation or calibration fit.", ""]
    for title, table in [("All validation rows", metrics), ("No current detection: 232 rows, 37 next-day positives", subsets)]:
        lines += [f"## {title}", "", "| Method | AP | Precision | Recall | TP | FP | FN | Brier | Alerts/day |",
                  "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
        for name, result in table.items():
            lines.append(f"| {labels[name]} | {result['average_precision']:.4f} | {result['precision']:.2%} | {result['recall']:.2%} | {result['true_positives']} | {result['false_positives']} | {result['false_negatives']} | {result['brier_score']:.4f} | {result['alerts_per_day']:.2f} |")
        lines.append("")
    lines += ["![Validation comparison](current_fire_comparison.png)", "", "## Interpretation limits", "",
              "- The validation set has already guided development. This is a development comparison, not a final independent performance estimate.",
              "- Check ranking and the fixed-threshold confusion counts separately. A higher AP does not guarantee fewer missed detections at threshold 0.5.",
              "- Gains can be dominated by continuing fire. Keep the no-current-detection subset visible; new detections are not confirmed new ignitions.",
              "- Current-day observations are assumed available after the UTC feature day ends. No following-day fire counts are inputs; archive publication latency remains a limitation.",
              "- The 22 December zero-detection issue and all other original labels remain unchanged.",
              "- Balanced class weights and temporal event-rate changes mean raw sigmoid percentages still require reliability assessment. No deployed warning threshold is chosen.",
              "- Persistence is a hard binary comparator; its Brier value is a squared-error reference rather than proof of calibrated 0/100% probabilities.", "",
              "## Reproduce", "", "```powershell", ".\\.venv\\Scripts\\python.exe -m bushfire_ml.current_fire", "```", ""]
    (ROOT / "reports" / "current_fire_comparison.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"validation_metrics": metrics, "fire_today_zero_subset_metrics": subsets,
                      "holdout_evaluated": False}, indent=2))


if __name__ == "__main__":
    main()
