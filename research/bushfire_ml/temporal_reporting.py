"""Aggregate temporal tables and figures, separate from fitting."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .data import ROOT


def number(value, percent=False):
    if value is None:
        return "N/A"
    return f"{value:.1%}" if percent else f"{value:.4f}"


def ranking_table(windows, names, subset=False):
    lines = ["| Feature-date window | Rows | Positives | Rate | " + " | ".join(names.values()) + " |",
             "| --- | ---: | ---: | ---: | " + " | ".join(["---:"]*len(names)) + " |"]
    for row in windows:
        metrics = row["no_current_detection"] if subset else row["metrics"]
        population = next(iter(metrics.values()), {})
        count, positives = population.get("rows", 0), population.get("positive_cell_days", 0)
        values = [number(metrics.get(key, {}).get("average_precision")) for key in names]
        lines.append(f"| {row['feature_start']} to {row['feature_end']} | {count} | {positives} | {number(positives/count if count else None, True)} | " + " | ".join(values) + " |")
    return lines


def decision_table(windows, names):
    lines = ["| Window | Model | TP | FP | FN | Precision | Recall | Brier |",
             "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in windows:
        for key, name in names.items():
            metrics = row["metrics"].get(key)
            if metrics is not None:
                lines.append(f"| {row['feature_start']} to {row['feature_end']} | {name} | {metrics['true_positives']} | {metrics['false_positives']} | {metrics['false_negatives']} | {number(metrics['precision'], True)} | {number(metrics['recall'], True)} | {number(metrics['brier_score'])} |")
    return lines


def write_temporal_report(report, names):
    blocks, daily, forward = (report[key] for key in ["existing_validation_blocks", "existing_validation_days", "forward_windows"])
    fig, axes = plt.subplots(2, 2, figsize=(12, 8.5), layout="constrained")
    colors = {"prevalence": "#9CA3AF", "logistic_16": "#60A5FA", "logistic_17": "#16A34A",
              "xgboost_16": "#7C3AED", "xgboost_17": "#D97706", "persistence": "#334155"}
    panels = [(blocks, "metrics", "Original models: three-day AP", "average_precision"),
              (blocks, "metrics", "Original models: false alerts at 0.5", "false_positives"),
              (forward, "metrics", "Past-only refits: AP", "average_precision"),
              (forward, "no_current_detection", "Past-only refits: AP without current detections", "average_precision")]
    for axis, (windows, population, title, metric) in zip(axes.flat, panels):
        for key, name in names.items():
            values = [row[population].get(key, {}).get(metric) for row in windows]
            values = [np.nan if value is None else value for value in values]
            axis.plot(range(len(windows)), values, marker="o", label=name, color=colors[key],
                      linestyle="--" if key in {"prevalence", "persistence"} else "-")
        labels = [f"{r['feature_start'][5:]}\nto {r['feature_end'][5:]}" for r in windows]
        axis.set_xticks(range(len(windows)), labels)
        axis.set(title=title, xlabel="UTC feature dates", ylabel="AP" if metric == "average_precision" else "False positive cell-days")
        if metric == "average_precision":
            axis.set_ylim(0, 1.02)
        axis.grid(alpha=0.15)
    axes[0, 0].legend(fontsize=8, loc="lower left", ncol=2)
    fig.suptitle("Temporal development diagnostics | missing XGBoost points = unavailable past stopping data", fontsize=12)
    output = ROOT / "reports"
    fig.savefig(output / "temporal_stability.png", dpi=160)
    plt.close(fig)
    comparable = [row for row in forward if "xgboost_17" in row["metrics"]]
    wins = sum(row["metrics"]["xgboost_17"]["average_precision"] > row["metrics"]["persistence"]["average_precision"] for row in comparable)
    deltas = [row["metrics"]["xgboost_17"]["average_precision"]-row["metrics"]["persistence"]["average_precision"] for row in blocks]
    matching = sum(all(row["metrics"]["xgboost_17"][key] == row["metrics"]["persistence"][key]
                       for key in ["true_positives", "false_positives", "false_negatives"]) for row in blocks)
    lines = ["# Temporal stability diagnostics", "", "Development only. Final holdout outcomes were not parsed or evaluated.", "",
             "## Main finding", "",
             "Temporal stability and a dependable improvement over persistence have not been established.", "",
             f"The original XGBoost 17 minus persistence AP difference is {min(deltas):.4f} to {max(deltas):.4f} across the {len(blocks)} fixed validation blocks. Both methods have the same TP/FP/FN counts in {matching} of {len(blocks)} blocks at 0.5.", "",
             f"Past-only XGBoost fits are available for {len(comparable)} of {len(forward)} outer windows, and XGBoost 17 exceeds persistence AP in {wins} of those {len(comparable)}. Missing-class stopping windows prevent the remaining fits. The available evidence does not support a reliable cross-period advantage.", "",
             "## Existing models: fixed validation slices", "",
             "AP is a ranking score, not accuracy or a calibrated percentage. Original XGBoost early stopping used these validation outcomes; slices are descriptive.", "",
             *ranking_table(blocks, names), "", "### Same slices without current detections", "",
             *ranking_table(blocks, names, subset=True), "", "### Daily XGBoost 17 and persistence decisions", "",
             "| Feature date | Target date | Positives | XGB AP | Persistence AP | XGB TP / FP / FN | Persistence TP / FP / FN |",
             "| --- | --- | ---: | ---: | ---: | --- | --- |"]
    for row in daily:
        xgb, persistence = row["metrics"]["xgboost_17"], row["metrics"]["persistence"]
        counts = lambda m: f"{m['true_positives']} / {m['false_positives']} / {m['false_negatives']}"
        lines.append(f"| {row['feature_start']} | {row['target_start']} | {row['positives']} | {number(xgb['average_precision'])} | {number(persistence['average_precision'])} | {counts(xgb)} | {counts(persistence)} |")
    lines += ["", "## Past-only forward windows", "",
              "Settings are inherited from the original model configurations. Select XGBoost length on past inner data, then refit with that fixed length on the same past rows as logistic. Outer outcomes never select trees. Windows were specified after development coverage and original scores were known, so this is retrospective development evidence.", "",
              "| Outer feature dates | Inner fitting end (positives) | Inner stopping dates (positives) | Refit end (positives) | XGB 16 / 17 selected trees |",
              "| --- | --- | --- | --- | --- |"]
    for row in forward:
        inner, stop, refit = (row[k] for k in ["inner_training", "inner_stopping", "refitting"])
        trees = " / ".join(str(row["fits"][key].get("trees_selected_on_past", "unavailable")) for key in ["xgboost_16", "xgboost_17"])
        lines.append(f"| {row['feature_start']} to {row['feature_end']} | {inner['feature_end']} ({inner['positives']}) | {stop['feature_start']} to {stop['feature_end']} ({stop['positives']}) | {refit['feature_end']} ({refit['positives']}) | {trees} |")
    lines += ["", "### Forward-window AP", "", *ranking_table(forward, names), "",
              "### Forward-window AP without current detections", "", *ranking_table(forward, names, subset=True), "",
              "N/A means a missing-class inner window prevented fitting, or AP is undefined because the evaluation subset has no positives. Consult JSON for the exact reason and counts. No unavailable window is silently discarded.", "",
              "### Diagnostic decisions at 0.5", "", *decision_table(forward, names), "",
              "![Temporal comparison](temporal_stability.png)", "", "## Interpretation constraints", "",
              *[f"- {note}" for note in report["notes"]], "", "## Reproduce", "", "```powershell",
              ".\\.venv\\Scripts\\python.exe -m bushfire_ml.temporal_stability", "```", "",
              "## Method references", "",
              "- [scikit-learn: time-series cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-of-time-series-data)",
              "- [XGBoost: early stopping](https://xgboost.readthedocs.io/en/stable/python/sklearn_estimator.html#early-stopping)", ""]
    (output / "temporal_stability.md").write_text("\n".join(lines), encoding="utf-8")
