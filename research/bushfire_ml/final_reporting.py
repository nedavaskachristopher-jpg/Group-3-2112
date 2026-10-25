"""Render the already-computed frozen evaluation; no models or data are fitted."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .data import ROOT
from .final_metrics import NAMES, POLICY_NAMES
from .temporal_reporting import number


def model_table(group):
    lines = ["| Model (diagnostic cutoff 0.5) | AP | Precision | Recall | TP | FP | FN | Accuracy | Brier | Log loss |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for key, row in group["models"].items():
        lines.append(f"| {NAMES[key]} | {number(row['average_precision'])} | {number(row['precision'], True)} | {number(row['recall'], True)} | {row['true_positives']} | {row['false_positives']} | {row['false_negatives']} | {number(row['accuracy'], True)} | {number(row['brier_score'])} | {number(row['log_loss'])} |")
    return lines


def policy_table(group):
    lines = ["| Frozen policy | Exact cutoff | Precision | Recall | TP | FP | FN | Alerts/day | False alerts/day |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for key, row in group["policies"].items():
        lines.append(f"| {POLICY_NAMES[key]} | {row['threshold']!r} | {number(row['precision'], True)} | {number(row['recall'], True)} | {row['true_positives']} | {row['false_positives']} | {row['false_negatives']} | {row['alerts_per_day']:.2f} | {row['false_alerts_per_day']:.2f} |")
    return lines


def write_final_report(result):
    all_rows, subset, monthly = result["all_rows"], result["no_current_detection"], result["monthly"]
    config = result["configuration"]
    population = all_rows["population"]
    primary = all_rows["models"][config["primary_model"]]
    persistence = all_rows["models"]["persistence"]
    difference = None if primary["average_precision"] is None else primary["average_precision"]-persistence["average_precision"]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8.5), layout="constrained")
    for key, curve in result["pr_curves"].items():
        if key != "training_prevalence":
            axes[0, 0].step(curve["recall"], curve["precision"], where="post",
                            label=f"{NAMES[key]} (AP {number(all_rows['models'][key]['average_precision'])})")
    axes[0, 0].axhline(population["positive_rate"], color="#64748B", linestyle=":", label="Constant-score AP reference")
    axes[0, 0].set(title="Prespecified model ranking comparison", xlabel="Recall", ylabel="Precision", xlim=(0, 1), ylim=(0, 1))
    axes[0, 0].legend(fontsize=7.5, loc="upper right")
    bins = primary["reliability_bins"]
    axes[0, 1].plot([0, 1], [0, 1], linestyle="--", color="#9CA3AF")
    axes[0, 1].plot([b["mean_probability"] for b in bins], [b["observed_rate"] for b in bins], marker="o", color="#D97706")
    for row in bins:
        axes[0, 1].annotate(f"n={row['rows']}", (row["mean_probability"], row["observed_rate"]), xytext=(4, 6), textcoords="offset points", fontsize=8)
    axes[0, 1].set(title="Frozen XGBoost 17 reliability", xlabel="Mean raw score in bin", ylabel="Observed detection rate", xlim=(0, 1), ylim=(0, 1))
    for key, color in zip(POLICY_NAMES, ["#D97706", "#7C3AED", "#334155"]):
        rows = [month["all_rows"]["policies"][key] for month in monthly]
        axes[1, 0].plot(range(len(monthly)), [r["false_alerts_per_day"] for r in rows], marker="o", color=color, label=POLICY_NAMES[key])
        axes[1, 1].plot(range(len(monthly)), [np.nan if r["recall"] is None else r["recall"] for r in rows], marker="o", color=color)
    for axis, title, ylabel in [(axes[1, 0], "Monthly false-alert burden", "False positive cell-days / represented day"),
                                (axes[1, 1], "Monthly recall (undefined with no positives)", "Recall")]:
        axis.set_xticks(range(len(monthly)), [row["month"] for row in monthly], rotation=20)
        axis.set(title=title, ylabel=ylabel, xlabel="UTC feature month")
    axes[1, 0].legend(fontsize=8)
    axes[1, 1].set_ylim(0, 1.02)
    for axis in axes.flat:
        axis.grid(alpha=0.15)
    fig.suptitle(f"Single frozen temporal evaluation | {population['rows']:,} cell-days | no fitting or threshold changes", fontsize=12)
    output = ROOT / "reports"
    fig.savefig(output / "final_holdout.png", dpi=160)
    plt.close(fig)
    lines = ["# Frozen final temporal evaluation", "",
             "One authorised release of the protected retrospective temporal holdout. All models, both cutoffs and the evaluation rules were frozen and committed before outcomes were parsed. No fitting or threshold adjustment occurred.", "",
             f"Freeze commit: `{result['freeze_commit']}`. Freeze manifest SHA256: `{result['freeze_manifest_sha256']}`.", "",
             f"UTC feature dates: {population['first_feature_date']} to {population['last_feature_date']}; targets: {population['first_target_date']} to {population['last_target_date']}.",
             f"Population: {population['rows']:,} cell-days, {population['days']} dates, {population['grid_cells']} cells; {population['positives']} positive cell-days ({population['positive_rate']:.2%}).", "",
             "## Both frozen reminder policies", "", *policy_table(all_rows), "",
             "Policy names refer to recall constraints on development selection rows. They do not guarantee final recall. Counts are cell-days, not independent fires, dispatches or staffing requirements. Cutoffs operate on uncalibrated scores and use inclusive comparisons.", "",
             "## Prespecified model comparison", "", *model_table(all_rows), "",
             f"Frozen XGBoost 17 minus persistence AP difference: {number(difference)}. This descriptive difference is not a statistical superiority claim. Accuracy is secondary and can be dominated by negative rows.", ""]
    if subset:
        pop = subset["population"]
        lines += ["## Cells without current detections", "",
                  f"{pop['rows']:,} cell-days with {pop['positives']} positive targets ({pop['positive_rate']:.2%}); both target classes are retained where present.", "",
                  *policy_table(subset), "", *model_table(subset), "",
                  "A detection in a previously unflagged cell is not a confirmed new ignition.", ""]
    lines += ["## Every prespecified calendar month", "",
              "| Feature month | Rows | Positives | Rate | XGB 17 AP | Persistence AP |",
              "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for month in monthly:
        pop, metrics = month["all_rows"]["population"], month["all_rows"]["models"]
        lines.append(f"| {month['month']} | {pop['rows']} | {pop['positives']} | {pop['positive_rate']:.2%} | {number(metrics['xgboost_17']['average_precision'])} | {number(metrics['persistence']['average_precision'])} |")
    lines += ["", "| Feature month | Policy | Recall | TP | FP | FN | False alerts/day |",
              "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for month in monthly:
        for key, row in month["all_rows"]["policies"].items():
            lines.append(f"| {month['month']} | {POLICY_NAMES[key]} | {number(row['recall'], True)} | {row['true_positives']} | {row['false_positives']} | {row['false_negatives']} | {row['false_alerts_per_day']:.2f} |")
    lines += ["", "N/A AP/recall means there are no positive outcomes; these dates and their false alerts remain included. AP comparisons across months also reflect changing prevalence.", "",
              "## Raw-score reliability", "",
              "| Score bin | Rows | Mean raw score | Observed detection rate |",
              "| --- | ---: | ---: | ---: |"]
    for row in bins:
        lines.append(f"| {row['lower']:.1f}-{row['upper']:.1f} | {row['rows']} | {row['mean_probability']:.2%} | {row['observed_rate']:.2%} |")
    lines += ["", f"XGBoost 17 Brier: {primary['brier_score']:.4f}; log loss: {primary['log_loss']:.4f}. These assess overall probability quality, not calibration alone. No calibration is fitted on these outcomes.", "",
              "![Frozen evaluation](final_holdout.png)", "", "## Integrity and limitations", "",
              "- Every final row and every prespecified month is retained. No labels, cutoffs, features, scaler values or tree parameters were altered.",
              "- Both research policies remain reported. A more favourable final metric is not used to choose a new production cutoff.",
              "- All four model artifacts are byte-identical copies of reviewed development fits; the primary model has eight trees and seventeen approved inputs. Original baseline reports remain unchanged.",
              "- The initial seal is a historical preparation record. The final-release receipt records the change in evaluation status; it does not rewrite the original seal.",
              f"- {result['prior_information']}", f"- {result['availability_assumption']}",
              "- The target is next-day eligible satellite detection, including ongoing fire, not ignition, fire spread or severity. Non-detection is not proof of no fire.",
              "- Dates and cells are dependent and may represent continuing fires. This is not independent-event or independent-season validation, and no such confidence interval is claimed.",
              "- Raw percentages remain unvalidated probability estimates. Frozen threshold performance does not establish operational safety, staffing benefit or real-time availability.",
              "- Later commands can return this cached result without reopening the holdout. Future tuning must be assessed on new independent data and cannot be called another blind result on this test.",
              "- Displayed PR curves use at most the prespecified number of points; AP is computed from all raw scores.", "",
              "## Audit artifacts", "", "- [Committed freeze manifest](final_freeze.json)",
              "- [One-time release receipt](final_release.json)", "- [Complete aggregate results](final_holdout.json)", "",
              "Local row-level predictions remain ignored. The implementation and report were AI-assisted; retain prompts, outputs and team verification for the course appendix.", ""]
    (output / "final_holdout.md").write_text("\n".join(lines), encoding="utf-8")
