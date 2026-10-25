"""Lesson 2: prespecified baseline comparisons on validation data only."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import precision_recall_curve

from .data import LOCAL_ROOT, PROTOCOL_PATH, ROOT, load_development, model_matrix, read_protocol, sha256, verify_seal
from .evaluation import evaluate, reliability_bins
from .models import fit_logistic

CONFIG_PATH = ROOT / "config" / "baseline_v1.json"
MODEL_NAMES = {
    "training_prevalence": "Training prevalence",
    "persistence": "Fire persistence",
    "logistic_core": "Balanced logistic regression",
}


def make_figure(validation, scores, metrics, calibration, output: Path) -> None:
    colors = {"training_prevalence": "#6B7280", "persistence": "#D97706", "logistic_core": "#2563EB"}
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout="constrained")
    for name, prediction in scores.items():
        precision, recall, _ = precision_recall_curve(validation.fire_positive, prediction)
        if name == "training_prevalence":
            axes[0].axhline(validation.fire_positive.mean(), color=colors[name], linestyle="--",
                            label=f"Constant-score reference (AP {metrics[name]['average_precision']:.3f})")
        else:
            axes[0].step(recall, precision, where="post", color=colors[name],
                         label=f"{MODEL_NAMES[name]} (AP {metrics[name]['average_precision']:.3f})")
    axes[0].set(xlabel="Recall", ylabel="Precision", xlim=(0, 1.02), ylim=(0, 1.02),
                title="Validation ranking: precision and recall")
    axes[0].legend(loc="lower left", fontsize=8)
    axes[1].plot([0, 1], [0, 1], color="#6B7280", linestyle="--", label="Perfect reliability reference")
    for name in ["training_prevalence", "logistic_core"]:
        bins = calibration[name]
        axes[1].plot([item["mean_probability"] for item in bins], [item["observed_rate"] for item in bins],
                     marker="o", color=colors[name], label=MODEL_NAMES[name])
        if name == "logistic_core":
            for item in bins:
                axes[1].annotate(f"n={item['rows']}", (item["mean_probability"], item["observed_rate"]),
                                 xytext=(4, 5), textcoords="offset points", fontsize=8)
    axes[1].set(xlabel="Mean predicted probability", ylabel="Observed positive fraction",
                xlim=(0, 1.02), ylim=(0, 1.02), title="Validation reliability: no calibration fitted")
    axes[1].legend(loc="upper left", fontsize=8)
    for axis in axes:
        axis.grid(alpha=0.15)
    figure.suptitle("Lesson 2 baselines | 9 validation days | final test remains sealed", fontsize=13)
    figure.savefig(output, dpi=160)
    plt.close(figure)


def main() -> None:
    seal_before = verify_seal()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    protocol = read_protocol()
    training_source = load_development("train")
    validation = load_development("validation")
    training = training_source.loc[training_source.feature_date.gt(config["training_warmup_end_inclusive"])].copy()
    if not pd.to_datetime(training.target_date).max() < pd.to_datetime(validation.feature_date).min():
        raise ValueError("Training outcomes overlap the validation feature period")
    model = fit_logistic(training, config)
    validation_inputs = model_matrix(validation, config["feature_set"])
    training_prevalence = float(training.fire_positive.mean())
    scores = {
        "training_prevalence": np.full(len(validation), training_prevalence),
        "persistence": validation.fire_today.to_numpy(dtype=float),
        "logistic_core": model.predict_proba(validation_inputs)[:, 1],
    }
    days = int(validation.feature_date.nunique())
    metrics = {name: evaluate(validation.fire_positive, values, config["diagnostic_threshold"], days,
                              hard_rule=name == "persistence") for name, values in scores.items()}
    subset = validation.fire_today.eq(0).to_numpy()
    new_detection = {name: evaluate(validation.fire_positive.to_numpy()[subset], values[subset],
                                   config["diagnostic_threshold"], days, hard_rule=name == "persistence")
                     for name, values in scores.items()}
    calibration = {name: reliability_bins(validation.fire_positive, scores[name], config["calibration_bins"])
                   for name in ["training_prevalence", "logistic_core"]}
    scaler = model.named_steps["scaler"]
    # Confirm validation prediction did not fit or update preprocessing.
    np.testing.assert_allclose(scaler.mean_, model_matrix(training).mean().to_numpy(), atol=1e-10)
    if int(scaler.n_samples_seen_) != len(training):
        raise RuntimeError("The scaler saw data other than the training rows")
    if verify_seal() != seal_before:
        raise RuntimeError("A sealed data file changed during the baseline run")

    report_dir = ROOT / "reports"
    local_output = LOCAL_ROOT / config["experiment"]
    local_output.mkdir(exist_ok=True)
    joblib.dump(model, local_output / "logistic_core.joblib")
    predictions = validation[["grid_id", "feature_date", "target_date", "fire_positive", "fire_today"]].copy()
    for name, values in scores.items():
        predictions[name+"_score"] = values
    predictions["logistic_uncalibrated_percent"] = 100*scores["logistic_core"]
    predictions.to_csv(local_output / "validation_predictions.csv", index=False, lineterminator="\n")
    figure_path = report_dir / "baseline_validation.png"
    make_figure(validation, scores, metrics, calibration, figure_path)
    report = {
        "experiment": config["experiment"], "evaluation_partition": "validation",
        "protocol_sha256": sha256(PROTOCOL_PATH), "baseline_config_sha256": sha256(CONFIG_PATH),
        "data_hashes": seal_before["file_sha256"],
        "software": {"scikit_learn": sklearn.__version__, "numpy": np.__version__, "pandas": pd.__version__},
        "training_rows_before_warmup": len(training_source), "training_rows_fitted": len(training),
        "warmup_rows_removed": len(training_source)-len(training),
        "training_positive_cell_days": int(training.fire_positive.sum()),
        "training_prevalence": training_prevalence, "training_feature_count": validation_inputs.shape[1],
        "validation_days": days, "validation_rows": len(validation),
        "scaler_training_rows_seen": int(scaler.n_samples_seen_),
        "logistic_iterations": int(model.named_steps["classifier"].n_iter_[0]),
        "diagnostic_threshold": config["diagnostic_threshold"], "validation_metrics": metrics,
        "fire_today_zero_subset_metrics": new_detection, "reliability_bins": calibration,
        "notes": [
            "The 0.5 threshold is a fixed diagnostic reference, not an optimised warning rule.",
            "Balanced class weights are calculated from training labels only. They change the loss, not the number of data rows.",
            "Class weighting and the train-validation base-rate change mean logistic outputs are not established real-world probabilities.",
            "The persistence rule has access to current fire, while the conditions-only logistic model does not. This is a practical benchmark, not a controlled feature-matched comparison.",
            "The constant-score AP equals validation prevalence, although its predicted probability comes from training prevalence.",
            "The fire_today=0 subset retains negatives and positives. A next-day new detection is not proof of a new ignition.",
            "One short, dependent fire interval provides limited evidence; do not claim independent-season performance.",
            "No hyperparameter search, threshold optimisation, calibration fit or final-test evaluation was performed."
        ],
        "holdout_evaluated": False,
    }
    (report_dir / "baseline_validation.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    lines = ["# Lesson 2 baseline results", "", "Validation results only. The final test remains sealed.", "",
             f"Training used {len(training):,} rows after removing {len(training_source)-len(training)} warm-up rows, with 16 core inputs.",
             f"Training prevalence: {training_prevalence:.4%}. Validation: {len(validation)} rows across {days} UTC feature dates.", "",
             "## Fixed diagnostic threshold: 0.5", "",
             "| Method | AP | Precision | Recall | TP | FP | FN | TN | Brier | Alerts/day |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for name, result in metrics.items():
        lines.append(f"| {MODEL_NAMES[name]} | {result['average_precision']:.4f} | {result['precision']:.2%} | {result['recall']:.2%} | {result['true_positives']} | {result['false_positives']} | {result['false_negatives']} | {result['true_negatives']} | {result['brier_score']:.4f} | {result['alerts_per_day']:.2f} |")
    lines += ["", "Brier for persistence is the squared-error reference of its hard 0/1 outputs; these are not calibrated probability forecasts.", "",
              "![Validation precision-recall and reliability diagnostics](baseline_validation.png)", "",
              "## Interpretation limits", "", *[f"- {note}" for note in report["notes"]], "",
              "## Reproduce", "", "```powershell", ".\\.venv\\Scripts\\python.exe -m bushfire_ml.baselines", "```", "",
              "Row-level validation predictions and the fitted pipeline remain under the ignored local data directory.", ""]
    (report_dir / "baseline_validation.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"training_rows_fitted": len(training), "validation_metrics": metrics,
                      "fire_today_zero_subset_metrics": new_detection, "holdout_evaluated": False}, indent=2))


if __name__ == "__main__":
    main()
