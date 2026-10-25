"""Aggregate probability reliability and alert trade-off reporting."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .data import ROOT
from .temporal_reporting import number


def metric_rows(metrics, names):
    lines = ["| Model | AP | Mean score | Observed rate | Brier | Log loss | Binned gap |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for key, name in names.items():
        row = metrics.get(key)
        if row:
            lines.append(f"| {name} | {number(row['average_precision'])} | {number(row['score_mean'], True)} | {number(row['observed_rate'], True)} | {number(row['brier_score'])} | {number(row['log_loss'])} | {number(row['binned_absolute_gap'])} |")
    return lines


def write_probability_report(report, names):
    results = report["scenarios"]
    fig, axes = plt.subplots(2, len(results), figsize=(12, 8.5), squeeze=False, layout="constrained")
    keys = ["xgboost_17", "sigmoid_xgboost_17", "calibration_prevalence"]
    colors = ["#D97706", "#16A34A", "#64748B"]
    for index, result in enumerate(results):
        population = result["assessment_population"]
        axis = axes[0, index]
        axis.plot([0, 1], [0, 1], color="#9CA3AF", linestyle="--", label="Ideal reliability")
        for key, color in zip(keys, colors):
            bins = result["assessment_metrics"]["all_rows"][key]["reliability_bins"]
            axis.plot([b["mean_probability"] for b in bins], [b["observed_rate"] for b in bins],
                      marker="o", color=color, label=names[key])
            for row in bins:
                axis.annotate(f"n={row['rows']}", (row["mean_probability"], row["observed_rate"]),
                              xytext=(4, 5), textcoords="offset points", fontsize=7, color=color)
        axis.set(title=f"Base fit through {result['base_refitting']['feature_end']}\nCheck {population['feature_start']} to {population['feature_end']}",
                 xlabel="Mean predicted score in bin", ylabel="Observed next-day detection rate", xlim=(0, 1), ylim=(0, 1))
        axis.legend(fontsize=7.5, loc="lower right")
        axis.grid(alpha=0.15)
        axis = axes[1, index]
        sweep = result["assessment_threshold_sweep"]
        axis.step([r["threshold"] for r in sweep], [r["all_rows"]["false_positives"] for r in sweep], where="post", color="#DC2626", label="False alerts")
        axis.step([r["threshold"] for r in sweep], [r["all_rows"]["false_negatives"] for r in sweep], where="post", color="#2563EB", label="Missed positives")
        annotations = []
        for row in result["policies"]:
            if row["score"] == "xgboost_17":
                axis.axvline(row["threshold"], color="#64748B", linestyle=":", alpha=0.7)
                annotations.append(f"{row['recall_target']:.0%} selection target: cutoff {row['threshold']:.4f}, later recall {row['assessment']['all_rows']['recall']:.1%}")
        axis.text(0.03, 0.96, "\n".join(annotations), transform=axis.transAxes, va="top", fontsize=8,
                  bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"})
        axis.set(title="Raw XGBoost 17: later-date trade-off", xlabel="Score cutoff (not a validated probability)",
                 ylabel="Cell-days", xlim=(0, 1), ylim=(0, population["rows"]*1.12))
        axis.grid(alpha=0.15)
        axis.legend(fontsize=8, loc="upper right", bbox_to_anchor=(1, 0.78))
    fig.suptitle("Probability checks | retrospective development only | thresholds selected on earlier calibration rows", fontsize=12)
    output = ROOT / "reports"
    fig.savefig(output / "probability_reliability.png", dpi=160)
    plt.close(fig)
    decision = report["calibration_decision"]
    lines = ["# Probability reliability and provisional research thresholds", "", decision["conclusion"], "",
             "The final holdout remains sealed. No reliable probability percentages or operational alert thresholds have been established.", "",
             "## Fixed chronological designs", "",
             "| Scenario | Base fit ends | Base positives | XGB 16 / 17 trees | Calibration feature dates | Calibration days / positives | Assessment feature dates | Assessment days / positives |",
             "| --- | --- | ---: | --- | --- | --- | --- | --- |"]
    for row in results:
        base, cal, check = (row[key] for key in ["base_refitting", "calibration_population", "assessment_population"])
        lines.append(f"| {row['name']} | {base['feature_end']} | {base['positives']} | {row['base_fits']['xgboost_16']['trees']} / {row['base_fits']['xgboost_17']['trees']} | {cal['feature_start']} to {cal['feature_end']} | {cal['days']} / {cal['positives']} | {check['feature_start']} to {check['feature_end']} | {check['days']} / {check['positives']} |")
    lines += ["", "Every target is the following UTC day. Seven calendar gap days separate fitting from calibration and calibration from assessment. Inner early stopping also uses past observations with its own gap. The base model is not refitted after calibration. The second assessment overlaps the first and is not independent replication.", "",
              "## Calibration decision", "", f"Supported comparison windows: {len(decision['supported_windows'])}. Supported windows improving both Brier and log loss over raw scores and past-calibration prevalence: {len(decision['improved_supported_windows'])}. Disjoint improved windows: {decision['disjoint_improved_windows']}; project gate requires {decision['required_windows']}.", "",
              "These support counts are project heuristics, not proof of calibration. The recent one-day split cannot support adoption. Full policy: [draft research policy](draft_probability_policy.json).", ""]
    for row in results:
        lines += [f"## {row['name']}", "", "### Held-later probability diagnostics", "",
                  *metric_rows(row["assessment_metrics"]["all_rows"], names), "",
                  "Lower Brier/log loss indicates better overall probability predictions; neither metric isolates calibration alone. Binned gap is a descriptive weighted absolute difference, sensitive to binning.", "",
                  "### Held-later rows without current detections", "",
                  *metric_rows(row["assessment_metrics"]["no_current_detection"], names), "",
                  "### Recall-target policies selected only on calibration rows", "",
                  "| Score | Selection recall target | Cutoff | Actual selection recall | Later recall | Later precision | Later TP | Later FP | Later FN | Later alerts/day |",
                  "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
        for policy in row["policies"]:
            check = policy["assessment"]["all_rows"]
            lines.append(f"| {names[policy['score']]} | {policy['recall_target']:.0%} | {policy['threshold']:.8f} | {policy['selection_recall']:.1%} | {number(check['recall'], True)} | {number(check['precision'], True)} | {check['true_positives']} | {check['false_positives']} | {check['false_negatives']} | {check['alerts_per_day']:.2f} |")
        persistence = row["assessment_metrics"]["all_rows"]["persistence"]
        lines += [f"| Persistence | N/A | 0.5 | N/A | {number(persistence['recall'], True)} | {number(persistence['precision'], True)} | {persistence['true_positives']} | {persistence['false_positives']} | {persistence['false_negatives']} | {persistence['alerts_per_day']:.2f} |", "",
                  "Targets apply only to selection rows, not later dates. Tied scores may force the two targets to select the same cutoff and many alerts. Use the full-precision JSON cutoff with `score >= cutoff`; the displayed decimal is rounded. No target was optimised on the later assessment.", "",
                  "### Same policies without current detections", "",
                  "| Score | Selection target | Later subset TP | FP | FN | Recall |",
                  "| --- | ---: | ---: | ---: | ---: | ---: |"]
        for policy in row["policies"]:
            subset = policy["assessment"]["no_current_detection"]
            if subset:
                lines.append(f"| {names[policy['score']]} | {policy['recall_target']:.0%} | {subset['true_positives']} | {subset['false_positives']} | {subset['false_negatives']} | {number(subset['recall'], True)} |")
        lines += ["", "### Reliability by current-detection group", "",
                  "| Current flag | Score | Rows | Mean score | Actual detection rate |",
                  "| --- | --- | ---: | ---: | ---: |"]
        for flag, scores in row["assessment_fire_today_groups"].items():
            for key, values in scores.items():
                lines.append(f"| {flag} | {names[key]} | {values['rows']} | {values['score_mean']:.1%} | {values['observed_rate']:.1%} |")
        lines += ["", "### Calibration-fit diagnostics (selection rows, not held-later evidence)", "",
                  *metric_rows(row["calibration_metrics"]["all_rows"], {key: names[key] for key in keys}), ""]
    lines += ["![Reliability and threshold trade-offs](probability_reliability.png)", "", "## Interpretation and limitations", "",
              *[f"- {note}" for note in report["notes"]], "", "## Reproduce", "", "```powershell",
              ".\\.venv\\Scripts\\python.exe -m bushfire_ml.probability_experiment", "```", "",
              "## Primary references", "",
              "- [scikit-learn: probability calibration and reliability diagrams](https://scikit-learn.org/stable/modules/calibration.html)",
              "- [scikit-learn: threshold selection and separate tuning data](https://scikit-learn.org/stable/modules/classification_threshold.html)", ""]
    (output / "probability_reliability.md").write_text("\n".join(lines), encoding="utf-8")
