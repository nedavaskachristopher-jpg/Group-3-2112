"""Export the ML handover from committed aggregates without loading raw data."""

import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "final": "research/reports/final_holdout.json", "freeze": "research/reports/final_freeze.json",
    "receipt": "research/reports/final_release.json", "partitions": "research/reports/partition_manifest.json",
    "audit": "research/reports/development_audit.json", "xgb": "research/reports/xgboost_comparison.json",
    "temporal": "research/reports/temporal_stability.json", "probability": "research/reports/probability_reliability.json",
    "logistic_config": "research/config/baseline_v1.json", "xgb_config": "research/config/xgboost_v1.json",
    "protocol": "research/config/protocol_v1.json",
}
MODEL_NAMES = {"training_prevalence": "Training prevalence", "persistence": "Persistence",
               "logistic_16": "Logistic 16", "logistic_17": "Logistic 17",
               "xgboost_16": "XGBoost 16", "xgboost_17": "XGBoost 17"}
POLICY_NAMES = {"recall_80_policy": "80% target", "recall_90_policy": "90% target", "persistence": "Persistence"}
REFERENCES = [
    {"key": "mlChen2016", "title": "XGBoost A Scalable Tree Boosting System", "author": "Tianqi Chen and Carlos Guestrin", "year": "2016", "url": "https://arxiv.org/abs/1603.02754"},
    {"key": "mlAveragePrecision", "title": "Average precision score", "author": "{scikit-learn developers}", "year": "2026", "url": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html"},
    {"key": "mlTemporalEvaluation", "title": "Cross validation of time series data", "author": "{scikit-learn developers}", "year": "2026", "url": "https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-of-time-series-data"},
    {"key": "mlCalibration", "title": "Probability calibration", "author": "{scikit-learn developers}", "year": "2026", "url": "https://scikit-learn.org/stable/modules/calibration.html"},
    {"key": "mlJois2026", "title": "Australian Bushfire Intelligence with AI Driven Environmental Analytics", "author": "Tanvi Jois and Hussain Ahmad and Fatima Noor and Faheem Ullah", "year": "2026", "url": "https://arxiv.org/abs/2601.06105"},
    {"key": "mlERA5Land", "title": "ERA5 Land hourly data from 1950 to present", "author": "{Copernicus Climate Change Service}", "year": "2026", "url": "https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview"},
    {"key": "mlFinalEvidence", "title": "Blue Mountains frozen final temporal evaluation", "author": "{ENGG2112 project team}", "year": "2026", "url": "https://github.com/kianluo024/ENGG2112-Blue-Mountain-Bushfire-prediction-ML-/blob/main/research/reports/final_holdout.md"},
]


def digest(path, text=False):
    content = path.read_text(encoding="utf-8").encode("utf-8") if text else path.read_bytes()
    return hashlib.sha256(content).hexdigest()


def read_evidence(root=ROOT):
    evidence = {name: json.loads((root / relative).read_text(encoding="utf-8")) for name, relative in SOURCES.items()}
    receipt, final = evidence["receipt"], evidence["final"]
    if receipt["status"] != "completed" or digest(root / SOURCES["final"]) != receipt["aggregate_sha256"]:
        raise ValueError("The completed final aggregate must match its release receipt")
    if final["fitting_performed"] or final["thresholds_adjusted_after_release"] or final["calibration"] is not None:
        raise ValueError("Packaging cannot replace the frozen no-refitting decision")
    if final["frozen_policies"] != evidence["freeze"]["policies"]:
        raise ValueError("Final policies differ from the freeze")
    return evidence


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True)+"\n", encoding="utf-8")


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"]*len(headers)) + " |",
                      *["| " + " | ".join(str(x) for x in row) + " |" for row in rows]])


def percent(value):
    return "N/A" if value is None else f"{value:.1%}"


def build_pages(evidence):
    final, frozen = evidence["final"], evidence["freeze"]
    population = final["all_rows"]["population"]
    models, policies = final["all_rows"]["models"], final["all_rows"]["policies"]
    recent = evidence["probability"]["scenarios"][-1]
    fit = recent["base_refitting"]
    params = evidence["xgb_config"]["xgboost"]
    gap_rows = evidence["protocol"]["gap_days"]*len(frozen["grid_ids"])
    p = lambda text: {"type": "paragraph", "text": text}
    h = lambda text: {"type": "heading", "text": text}
    table = lambda headers, rows, widths: {"type": "table", "headers": headers, "rows": rows, "widths": widths}
    first = [
        p("We built a research prototype for next-day eligible satellite fire detection in Blue Mountains National Park. The frozen model and its two development-selected recall policies did not establish reliable warning performance. The deliverable is an auditable ML comparison, not a deployed warning system or a validated ignition-probability map."),
        h("Prediction unit and evidence"),
        p("Each row is one retained ERA5-Land grid cell and one UTC feature day; the target is at least one eligible VIIRS detection on the following UTC day. Continuing fire counts as positive. Non-detection is not proof of no physical fire. Weather is aggregated over the grid cell, while terrain and labels concern its park portion; the group data owner must retain source and geometry documentation. ERA5-Land is retrospective reanalysis [6]."),
        h("Temporal separation"),
        table(["Partition", "UTC feature dates", "Rows"], [
            ["Training", "1 July to 8 December 2019", str(evidence["partitions"]["partitions"]["train"]["rows"])],
            ["Gap", "9 to 15 December 2019", str(gap_rows)],
            ["Validation", "16 to 24 December 2019", str(evidence["partitions"]["partitions"]["validation"]["rows"])],
            ["Gap", "25 to 31 December 2019", str(gap_rows)],
            ["Final holdout", "1 January to 29 June 2020", f"{population['rows']:,}"],
        ], [0.23, 0.61, 0.16]),
        p(f"All cells from a date stayed together. The supplier's future-test boundary was preserved, with seven-day gaps rather than interleaved weeks [3]. At least 10% park overlap retained {population['grid_cells']} cells. Rainfall warm-up excluded the first two feature days from fitting, leaving {fit['rows']:,} training rows and {fit['positives']} positive targets. Gaps reduce adjacency, not dependence between long-running fires."),
        h("Reviewed inputs"),
        p("The core has sixteen weather/terrain variables; the second version adds only the audited same-day fire_today flag. Target-day counts, labels, dates, grid identifiers and coordinates are excluded as predictors. Long rainfall/dry-history and other current-fire candidates were not enabled because their warm-up or semantics needed further treatment. Fuel-moisture imagery and NDVI were not implemented."),
    ]
    second = [
        h("Matched models and stopping"),
        p("Training prevalence and persistence were explicit references. Logistic regression and XGBoost were each compared with sixteen and seventeen inputs on matched fitting/evaluation rows. Logistic scaling and balanced weights used training rows only. Tree fitting used training negatives divided by positives for class emphasis; calibration did not rebalance labels. XGBoost tests nonlinear thresholds/interactions [1], rather than guaranteeing better performance."),
        table(["XGBoost setting", "Recorded value"], [["Maximum depth", str(params["max_depth"])],
              ["Learning rate", str(params["learning_rate"])], ["L2 leaf penalty", str(params["reg_lambda"])],
              ["Row and feature subsampling", f"{params['subsample']} and {params['colsample_bytree']}"],
              ["Early stopping", f"{evidence['xgb_config']['early_stopping']['rounds']} rounds without AP improvement"],
              ["Final 16 and 17 input tree counts", f"{frozen['models']['xgboost_16']['trees']} and {frozen['models']['xgboost_17']['trees']}"],
        ], [0.57, 0.43]),
        p("Average precision (AP) was computed from raw scores using sklearn, and explicitly maximised for stopping [2]. The initial validation selected tree length and was development evidence. Later forward checks selected length on past inner data and refitted that fixed count before checking later dates. Missing-class windows remained visible; the dependent windows were not treated as independent replication."),
        h("Probability and reminder decisions"),
        p("A nondecreasing regularised sigmoid was fitted on base-model-excluded calibration rows, then checked on later dates, with seven-day gaps and no post-calibration base refit. The week-long design worsened later probability quality; the improving recent design had only one calibration and one assessment day. Calibration was therefore not adopted [4]. The highest calibration-only cutoff meeting each requested recall constraint was retained, with ties together."),
        table(["Development target", "Exact raw cutoff", "Comparison"],
              [[percent(row["recall_target"]), repr(row["threshold"]), row["comparison"]] for row in frozen["policies"]], [0.31, 0.49, 0.20]),
        p(f"The complete source, features, artifacts, thresholds and reporting rules were committed in freeze {final['freeze_commit'][:7]} before one final release [7]. No final fitting, calibration or threshold search occurred. AP was primary; confusion counts, probability quality and alert burden were reported overall, without current detections, and for every calendar month."),
    ]
    policy_rows = [[POLICY_NAMES[key], str(row["true_positives"]), f"{row['false_positives']:,}", str(row["false_negatives"]), percent(row["recall"]), percent(row["precision"])]
                   for key, row in policies.items()]
    model_rows = [[MODEL_NAMES[key], f"{row['average_precision']:.4f}", percent(row["recall"]), f"{row['brier_score']:.4f}"] for key, row in models.items()]
    subset_policies = final["no_current_detection"]["policies"]
    third = [
        p(f"The final period has {population['rows']:,} cell-days, {population['days']} dates and {population['positives']} positive next-day targets ({population['positive_rate']:.2%}); these are not independent fires. Both frozen development recall targets failed to transfer [7]."),
        table(["Frozen policy", "TP", "FP", "FN", "Recall", "Precision"], policy_rows, [0.28, 0.10, 0.16, 0.10, 0.18, 0.18]),
        table(["Model at diagnostic 0.5", "AP", "Recall", "Brier"], model_rows, [0.45, 0.18, 0.19, 0.18]),
        {"type": "figure", "path": "figures/final_policy_tradeoff.png", "height": 154,
         "caption": "Figure 1  Frozen-policy trade-off. Counts are cell-days, not incidents or staffing requirements. The development target is not a promise of final recall."},
        p(f"The prespecified logistic 17 comparison ranked better than XGBoost 17; this did not trigger a replacement or retuning. Without current detections, the higher cutoff found {subset_policies['recall_80_policy']['true_positives']} of {final['no_current_detection']['population']['positives']} positives; the lower found {subset_policies['recall_90_policy']['true_positives']} with {subset_policies['recall_90_policy']['false_positives']:,} false alerts. All months were retained, including zero-positive months with undefined AP/recall. A no-alert reference scored {models['training_prevalence']['accuracy']:.2%} accuracy while missing every positive."),
    ]
    fourth = [
        {"type": "figure", "path": "figures/raw_score_reliability.png", "height": 156,
         "caption": "Figure 2  Fixed-bin reliability for the frozen raw score. Bin sizes and observed frequencies do not establish independent-event precision or calibrated percentages."},
        p("The raw scores overstate observed next-day detection frequencies. The small AP advantage over persistence does not establish practical warning benefit, and Brier/log loss measure overall probability quality rather than calibration alone. We did not fit a correction using final outcomes [4,7]."),
        h("Interpretation and recommendations"),
        p("The evidence supports a research prototype, not operational dispatch or public risk percentages. False alerts could waste review capacity and erode trust; missed detections could create false reassurance. A future interface should retain human review, label score meaning, provenance and timing, and distinguish satellite non-detection from physical safety. Response capacity and the costs of false versus missed alerts require stakeholder agreement, not invented financial assumptions."),
        p("Transfer is limited by sparse early positives, changing prevalence, one supplied season, dependent cells/events, imperfect detection coverage and coarse spatial aggregation. Retrospective publication latency was not simulated. The related Australian multi-source study motivates environmental modelling, but its task, data and headline accuracy are not a like-for-like benchmark for our next-day AP evaluation [5]."),
        p("Further work needs independent seasons/events, checked observation coverage, suitable fuel information and forecast-time data availability before calibration and response-policy validation. This exposed test must not become a tuning set. The ML contribution completes the auditable comparison; the group must still verify source/licence/map details, domain interpretation, citations, authorship and AI-use records before submission."),
    ]
    return [
        {"title": "Study design and inputs", "fragment": "ml_methods.tex", "blocks": first},
        {"title": "Models and evaluation procedure", "fragment": "ml_methods.tex", "blocks": second},
        {"title": "Final findings", "fragment": "ml_findings.tex", "blocks": third},
        {"title": "Reliability and implications", "fragment": "ml_recommendations.tex", "blocks": fourth},
    ]


def export_tables(evidence, root=ROOT):
    final, frozen = evidence["final"], evidence["freeze"]
    fields = ["average_precision", "precision", "recall", "accuracy", "brier_score", "log_loss",
              "true_positives", "false_positives", "false_negatives", "true_negatives", "alerts_per_day", "false_alerts_per_day"]
    folder = root / "report/tables"
    write_csv(folder / "final_models.csv", [{"model": key, **{field: row[field] for field in fields}}
              for key, row in final["all_rows"]["models"].items()])
    policy_rows = []
    for subset in ["all_rows", "no_current_detection"]:
        for key, row in final[subset]["policies"].items():
            policy_rows.append({"population": subset, "policy": key, "threshold": row["threshold"], **{field: row[field] for field in fields}})
    write_csv(folder / "final_policies.csv", policy_rows)
    write_csv(folder / "monthly_policies.csv", [{"feature_month": month["month"], "rows": month["all_rows"]["population"]["rows"],
              "positive_targets": month["all_rows"]["population"]["positives"], "policy": key, **{field: row[field] for field in fields}}
              for month in final["monthly"] for key, row in month["all_rows"]["policies"].items()])
    write_csv(folder / "reliability_bins.csv", final["all_rows"]["models"]["xgboost_17"]["reliability_bins"])
    partitions = evidence["partitions"]["partitions"]
    gap = evidence["protocol"]["gap_days"]
    rows = [{"partition": key, **partitions[key]} for key in ["train", "validation", "final_test"]]
    # Each gap is a full seven-day block over the same static retained cells.
    rows += [{"partition": "gap_before_validation", "rows": gap*len(frozen["grid_ids"]), "first_feature_date": "2019-12-09", "last_feature_date": "2019-12-15"},
             {"partition": "gap_before_final", "rows": gap*len(frozen["grid_ids"]), "first_feature_date": "2019-12-25", "last_feature_date": "2019-12-31"}]
    write_csv(folder / "partitions.csv", sorted(rows, key=lambda row: row["first_feature_date"]))
    write_csv(folder / "development_summary.csv", [{"evidence_scope": "development validation used for original tree selection", "model": key,
              **{field: row[field] for field in fields}} for key, row in evidence["xgb"]["validation_metrics"].items()])


def export_claims(evidence, root=ROOT):
    claims = []

    def add(source, path, transform=None):
        value = evidence[source]
        for key in path:
            value = value[key]
        if transform == "length":
            value = len(value)
        claims.append({"source": SOURCES[source], "path": path, "transform": transform, "value": value})

    for key in evidence["final"]["all_rows"]["population"]:
        add("final", ["all_rows", "population", key])
    fields = ["average_precision", "precision", "recall", "accuracy", "brier_score", "log_loss", "true_positives", "false_positives", "false_negatives", "alerts_per_day"]
    for population in ["all_rows", "no_current_detection"]:
        for section in ["models", "policies"]:
            for key in evidence["final"][population][section]:
                for field in fields:
                    add("final", [population, section, key, field])
    for index, month in enumerate(evidence["final"]["monthly"]):
        add("final", ["monthly", index, "all_rows", "population", "positives"])
        for key in month["all_rows"]["policies"]:
            for field in ["recall", "true_positives", "false_positives", "false_negatives"]:
                add("final", ["monthly", index, "all_rows", "policies", key, field])
    for index, row in enumerate(evidence["final"]["all_rows"]["models"]["xgboost_17"]["reliability_bins"]):
        for key in row:
            add("final", ["all_rows", "models", "xgboost_17", "reliability_bins", index, key])
    for key, spec in evidence["freeze"]["models"].items():
        add("freeze", ["models", key, "columns"], "length")
        if "trees" in spec:
            add("freeze", ["models", key, "trees"])
    for index in range(len(evidence["freeze"]["policies"])):
        add("freeze", ["policies", index, "threshold"])
    write_json(root / "docs/evidence/claims.json", {"scope": "Aggregate claims only; values are not rounded", "claims": claims})


def export_features(evidence, root=ROOT):
    columns = evidence["freeze"]["models"]["xgboost_17"]["columns"]
    rows = []
    for index, column in enumerate(columns, start=1):
        if column.endswith("_c"):
            unit, group = "degrees C", "Weather"
        elif column.endswith("_pct"):
            unit, group = "%", "Weather"
        elif column.startswith("precipitation"):
            unit, group = "mm", "Rainfall"
        elif column.endswith("_ms"):
            unit, group = "m/s", "Weather"
        elif column.startswith("elevation"):
            unit, group = "m", "Terrain"
        elif column.startswith("slope"):
            unit, group = "degrees", "Terrain"
        elif column.startswith("aspect"):
            unit, group = "unitless", "Terrain"
        else:
            unit, group = "0/1", "Current detection"
        rows.append([index, column, group, unit, "Full feature day or earlier" if group != "Terrain" else "Static park terrain"])
    text = "# Final feature catalogue\n\nOrdered inputs are copied from the frozen seventeen-input model. The sixteen-input comparison omits only `fire_today`. Units follow the audited variable definitions.\n\n"
    text += markdown_table(["Order", "Column", "Group", "Unit", "Availability"], rows)
    text += "\n\n`precipitation_3d_mm` includes the feature day and two earlier days. `fire_today` is the eligible same-UTC-day detection flag, not tomorrow's answer. Full-day retrospective availability is assumed; publication latency is not reproduced. Weather covers the grid cell, whereas terrain/fire data concern its park portion.\n\n"
    text += "Excluded predictors include the label, target-day detection counts, dates, coordinates, grid ID and partition fields. Longer rainfall/dry-spell histories and other current-fire candidates were not approved for this frozen model. No NDVI or fuel-moisture imagery is present. See [model_matrix](../../research/bushfire_ml/data.py), [audit](../../research/reports/development_audit.md) and [final manifest](../../research/reports/final_freeze.json).\n"
    (root / "docs/technical/feature_catalog.md").write_text(text, encoding="utf-8")
    write_json(root / "docs/technical/model_contract.json", {
        "purpose": "Research interface only; not an operational warning API", "target": evidence["freeze"]["target"],
        "ordered_inputs": columns, "metadata_not_predictors": ["grid_id", "feature_date", "target_date"],
        "output_score": {"range": [0, 1], "label": "Experimental raw model score", "validated_probability": False},
        "research_flags": evidence["freeze"]["policies"], "calibration": None,
        "model_artifact_sha256": evidence["freeze"]["models"]["xgboost_17"]["sha256"],
        "availability_assumption": evidence["freeze"]["availability_assumption"],
    })


def tex_text(text):
    escaped = "".join({"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}"}.get(char, char) for char in text)
    def citation(match):
        keys = [REFERENCES[int(index)-1]["key"] for index in match.group(1).split(",")]
        return r"\cite{"+",".join(keys)+"}"
    return re.sub(r"\[([1-7](?:,[1-7])*)\]", citation, escaped)


def export_report(pages, root=ROOT):
    folder = root / "report"
    markdown = ["# Machine Learning Report Contribution", "", "Blue Mountains Bushfire Prediction", "",
                "English ML contribution for integration into the group report. Numerical sources and the frozen procedure are linked in the handover; this is not the completed whole-group submission.", ""]
    fragments = {}
    for page in pages:
        markdown += ["## "+page["title"], ""]
        tex = [r"\subsection{"+tex_text(page["title"])+"}", ""]
        for block in page["blocks"]:
            if block["type"] == "paragraph":
                markdown += [block["text"], ""]
                tex += [tex_text(block["text"]), ""]
            elif block["type"] == "heading":
                markdown += ["### "+block["text"], ""]
                tex += [r"\subsubsection*{"+tex_text(block["text"])+"}", ""]
            elif block["type"] == "table":
                markdown += [markdown_table(block["headers"], block["rows"]), ""]
                widths = [f"p{{{width*0.86:.3f}\\linewidth}}" for width in block["widths"]]
                tex += [r"\begin{center}\small\setlength{\tabcolsep}{3pt}", r"\begin{tabular}{"+"".join(widths)+"}", r"\hline",
                        " & ".join(tex_text(str(x)) for x in block["headers"])+r" \\ \hline"]
                tex += [" & ".join(tex_text(str(x)) for x in row)+r" \\" for row in block["rows"]]
                tex += [r"\hline\end{tabular}\end{center}", ""]
            else:
                markdown += [f"![{block['caption']}]({block['path']})", "", block["caption"], ""]
                vector = "report/"+block["path"].replace(".png", ".pdf")
                tex += [r"\begin{figure}[htbp]\centering", r"\includegraphics[width=0.94\linewidth]{"+vector+"}",
                        r"\caption{"+tex_text(re.sub(r"^Figure \d+  ", "", block["caption"]))+"}", r"\end{figure}", ""]
        fragments.setdefault(page["fragment"], []).extend(tex)
    markdown += ["## References", ""]
    for index, reference in enumerate(REFERENCES, start=1):
        markdown.append(f"{index}. {reference['author'].replace('{', '').replace('}', '')}. {reference['title']}. {reference['year']}. [{reference['url']}]({reference['url']})")
    markdown += ["", "## Evidence", "", "[Final aggregate](../research/reports/final_holdout.json) | [Freeze](../research/reports/final_freeze.json) | [Release](../research/reports/final_release.json) | [Claim paths](../docs/evidence/claims.json)", ""]
    (folder / "ml_sections.md").write_text("\n".join(markdown), encoding="utf-8")
    for filename, lines in fragments.items():
        (folder / filename).write_text("% Generated from committed aggregates; insert inside the relevant report section.\n"+"\n".join(lines), encoding="utf-8")
    bib = []
    for reference in REFERENCES:
        bib += [f"@misc{{{reference['key']},", f"  author = {{{reference['author']}}},", f"  title = {{{reference['title']}}},",
                f"  year = {{{reference['year']}}},", f"  howpublished = {{\\url{{{reference['url']}}}}}", "}", ""]
    (folder / "ml_references.bib").write_text("\n".join(bib), encoding="utf-8")
    write_json(folder / "report_content.json", {"title": "Machine Learning Report Contribution", "project": "Blue Mountains Bushfire Prediction", "pages": pages, "references": REFERENCES})


def export_figures(evidence, root=ROOT):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    folder = root / "report/figures"
    policies = evidence["final"]["all_rows"]["policies"]
    labels = [POLICY_NAMES[key] for key in policies]
    detected = [row["true_positives"] for row in policies.values()]
    missed = [row["false_negatives"] for row in policies.values()]
    false = [row["false_positives"] for row in policies.values()]
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3), layout="constrained")
    axes[0].bar(labels, detected, label="Detected", color="#237A57")
    axes[0].bar(labels, missed, bottom=detected, label="Missed", color="#CBD5E1")
    for index, (tp, fn) in enumerate(zip(detected, missed)):
        axes[0].text(index, tp/2, str(tp), ha="center", va="center", color="white", fontsize=11)
        axes[0].text(index, tp+fn/2, str(fn), ha="center", va="center", fontsize=11)
    axes[0].set(title="Positive target cell-days", ylabel="Count")
    axes[0].legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, 1.02), ncol=2)
    axes[0].set_ylim(0, max(tp+fn for tp, fn in zip(detected, missed))*1.2)
    axes[1].bar(labels, false, color=["#D97706", "#7C3AED", "#475569"])
    for index, count in enumerate(false):
        axes[1].text(index, count+max(false)*0.025, f"{count:,}", ha="center", fontsize=11)
    axes[1].set(title="False-alert cell-days", ylabel="Count", ylim=(0, max(false)*1.15))
    for axis in axes:
        axis.grid(axis="y", alpha=0.15)
        axis.set_axisbelow(True)
    for suffix in ["png", "pdf"]:
        fig.savefig(folder / ("final_policy_tradeoff."+suffix), dpi=180)
    plt.close(fig)
    bins = evidence["final"]["all_rows"]["models"]["xgboost_17"]["reliability_bins"]
    fig, axis = plt.subplots(figsize=(7.5, 2.75), layout="constrained")
    axis.plot([0, 1], [0, 1], linestyle="--", color="#94A3B8", label="Ideal reliability")
    axis.plot([row["mean_probability"] for row in bins], [row["observed_rate"] for row in bins], marker="o", color="#D97706", label="Frozen raw score")
    for index, row in enumerate(bins):
        axis.annotate(f"n={row['rows']:,}", (row["mean_probability"], row["observed_rate"]),
                      xytext=(-10 if index == 0 else 8, 12 if index != 1 else 29), textcoords="offset points", fontsize=9)
    axis.set(xlabel="Mean raw model score", ylabel="Observed detection rate", xlim=(0, 1), ylim=(0, 1))
    axis.grid(alpha=0.15)
    axis.legend(fontsize=8, loc="upper left")
    for suffix in ["png", "pdf"]:
        fig.savefig(folder / ("raw_score_reliability."+suffix), dpi=180)
    plt.close(fig)


def refresh_manifest(root=ROOT):
    manifest_path = root / "docs/evidence/delivery_manifest.json"
    paths = [root / name for name in ["README.md", "AGENTS.md", ".gitignore", ".gitattributes", "review.py"]]
    for directory in ["report", "docs", "tools", "tests"]:
        paths += [path for path in (root / directory).rglob("*")
                  if path.is_file() and "__pycache__" not in path.parts and path != manifest_path]
    files = {}
    for path in sorted(paths):
        text = path.suffix.lower() not in {".png", ".pdf"}
        files[path.relative_to(root).as_posix()] = {"sha256": digest(path, text=text), "mode": "text_lf" if text else "bytes"}
    write_json(manifest_path, {"purpose": "Post-evaluation packaging only; no new prediction or fitting",
        "source_hash_mode": "Canonical UTF-8 LF text except binary assets",
        "research_root": "research",
        "sources": {relative: digest(root / relative, text=True) for relative in SOURCES.values()}, "files": files})


def main():
    evidence = read_evidence()
    for directory in ["report/tables", "docs/evidence", "docs/technical", "report/figures"]:
        (ROOT / directory).mkdir(parents=True, exist_ok=True)
    export_tables(evidence)
    export_claims(evidence)
    export_features(evidence)
    export_report(build_pages(evidence))
    export_figures(evidence)
    refresh_manifest()
    print(json.dumps({"aggregate_only_exports": True, "raw_data_read": False, "model_fitting": False,
                      "pdf_next_step": "python tools/render_handover_pdf.py"}, indent=2))


if __name__ == "__main__":
    main()
