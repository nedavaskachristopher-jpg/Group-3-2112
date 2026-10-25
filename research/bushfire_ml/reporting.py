"""Compact aggregate comparison reports, separate from model fitting."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import precision_recall_curve

from .data import ROOT


def metric_table(metrics: dict, names: dict) -> list[str]:
    lines = ["| Model | AP | Precision | Recall | TP | FP | FN | Brier |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for key, row in metrics.items():
        lines.append(f"| {names[key]} | {row['average_precision']:.4f} | {row['precision']:.2%} | {row['recall']:.2%} | {row['true_positives']} | {row['false_positives']} | {row['false_negatives']} | {row['brier_score']:.4f} |")
    return lines


def write_xgboost_report(report: dict, validation, scores: dict, names: dict) -> None:
    metrics, subsets = report["validation_metrics"], report["fire_today_zero_subset_metrics"]
    subset = validation.fire_today.eq(0).to_numpy()
    colors = ["#9CA3AF", "#60A5FA", "#16A34A", "#7C3AED", "#D97706"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout="constrained")
    for axis, mask, table, title in [
        (axes[0], np.ones(len(validation), dtype=bool), metrics, f"All {len(validation)} validation cell-days"),
        (axes[1], subset, subsets, f"{int(subset.sum())} cell-days without current detections"),
    ]:
        for color, (key, prediction) in zip(colors, scores.items()):
            precision, recall, _ = precision_recall_curve(validation.fire_positive.to_numpy()[mask], prediction[mask])
            style = "--" if key.startswith("logistic") else "-"
            axis.step(recall, precision, where="post", color=color, linestyle=style,
                      label=f"{names[key]} (AP {table[key]['average_precision']:.3f})")
        axis.set(xlabel="Recall", ylabel="Precision", title=title, xlim=(0, 1.02), ylim=(0, 1.02))
        axis.grid(alpha=0.15)
        axis.legend(loc="lower left" if axis is axes[0] else "upper right", fontsize=7.5)
    fig.suptitle("Matched inputs: logistic regression and XGBoost | validation only", fontsize=13)
    output = ROOT / "reports"
    fig.savefig(output / "xgboost_comparison.png", dpi=160)
    plt.close(fig)
    lines = ["# XGBoost development comparison", "", "Validation only; the final temporal test remains sealed.", "",
             f"Training rows: {report['training_rows']:,}. Validation rows: {len(validation)} over {report['validation_days']} UTC feature dates.", "",
             "## Fixed diagnostic threshold: 0.5", "", *metric_table(metrics, names), "",
             "## No current detection subset", "", *metric_table(subsets, names), "",
             "![Matched-input ranking comparison](xgboost_comparison.png)", "",
             "## Boosting length chosen on validation", "",
             "| Input set | Trees retained | Rounds evaluated | Best validation AP | Training AP at retained model |",
             "| --- | ---: | ---: | ---: | ---: |"]
    for key, fit in report["fits"].items():
        lines.append(f"| {names[key]} | {fit['trees_retained']} | {fit['rounds_evaluated']} | {fit['best_validation_ap']:.4f} | {fit['training_ap']:.4f} |")
    lines += ["", "## Interpretation and limits", "", *[f"- {note}" for note in report["notes"]], "",
              "## Reproduce", "", "```powershell", ".\\.venv\\Scripts\\python.exe -m bushfire_ml.xgboost_experiment", "```", ""]
    (output / "xgboost_comparison.md").write_text("\n".join(lines), encoding="utf-8")
