"""Inspect existing validation errors; never fit a model or open test labels."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .data import LOCAL_ROOT, ROOT, load_development, model_matrix, sha256, verify_seal


def main() -> None:
    seal = verify_seal()
    reference = json.loads((ROOT / "reports" / "baseline_validation.json").read_text())
    config_path = ROOT / "config" / "baseline_v1.json"
    config = json.loads(config_path.read_text())
    if reference["baseline_config_sha256"] != sha256(config_path) or reference["data_hashes"] != seal["file_sha256"]:
        raise RuntimeError("Baseline settings or data no longer match the recorded run")
    prediction_path = LOCAL_ROOT / reference["experiment"] / "validation_predictions.csv"
    predictions = pd.read_csv(prediction_path)
    validation = load_development("validation")
    keys = ["grid_id", "feature_date", "target_date"]
    joined = validation[keys+["fire_positive", "fire_today"]].merge(
        predictions, on=keys, validate="one_to_one", suffixes=("_source", ""))
    if len(joined) != len(validation) or len(predictions) != len(validation):
        raise ValueError("Validation prediction coverage changed")
    for column in ["fire_positive", "fire_today"]:
        if not joined[column].eq(joined[column+"_source"]).all():
            raise ValueError("Prediction outcomes do not match the sealed validation file")
    truth = predictions.fire_positive.eq(1)
    alert = predictions.logistic_core_score.ge(config["diagnostic_threshold"])
    predictions["TP"] = (alert & truth).astype(int)
    predictions["FP"] = (alert & ~truth).astype(int)
    predictions["FN"] = (~alert & truth).astype(int)
    predictions["TN"] = (~alert & ~truth).astype(int)
    counts = predictions.groupby("fire_today").agg(
        rows=("fire_positive", "size"), positives=("fire_positive", "sum"),
        TP=("TP", "sum"), FP=("FP", "sum"), FN=("FN", "sum"), TN=("TN", "sum"))
    daily = predictions.groupby(["feature_date", "target_date"]).agg(
        rows=("fire_positive", "size"), positives=("fire_positive", "sum"),
        TP=("TP", "sum"), FP=("FP", "sum"), FN=("FN", "sum"), TN=("TN", "sum")).reset_index()
    recorded = reference["validation_metrics"]["logistic_core"]
    for short, long in {"TP": "true_positives", "FP": "false_positives", "FN": "false_negatives", "TN": "true_negatives"}.items():
        if int(predictions[short].sum()) != recorded[long]:
            raise ValueError("Saved errors do not reconcile to the baseline report")
    training = load_development("train")
    training = training.loc[training.feature_date.gt(config["training_warmup_end_inclusive"])]
    train_x, validation_x = model_matrix(training), model_matrix(validation)
    mean_shift = (validation_x.mean()-train_x.mean())/train_x.std(ddof=0).replace(0, np.nan)
    drift = pd.DataFrame({"feature": train_x.columns,
                          "mean_shift_in_training_standard_deviations": mean_shift.to_numpy(),
                          "fraction_outside_training_range": (validation_x.lt(train_x.min()) | validation_x.gt(train_x.max())).mean().to_numpy()})
    drift = drift.assign(order=mean_shift.abs().to_numpy()).sort_values("order", ascending=False).drop(columns="order")

    location = json.loads((LOCAL_ROOT / "source_location.json").read_text(encoding="utf-8"))
    source_root = Path(location["dataset_root"])
    dates = pd.date_range(predictions.target_date.min(), predictions.target_date.max()).strftime("%Y-%m-%d")
    source_counts = pd.DataFrame({"target_date": dates})
    for name, path in [
        ("archive_detections", source_root / "DL_FIRE_SV-C2_818385" / "fire_archive_SV-C2_818385.csv"),
        ("clean_park_detections", source_root / "processed" / "blue_mountains_np_firms_2019_2020_clean.csv"),
    ]:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            frame = pd.DataFrame(row for row in csv.DictReader(stream) if dates.min() <= row["acq_date"] <= dates.max())
        observed = frame.groupby("acq_date").size()
        source_counts[name] = source_counts.target_date.map(observed).fillna(0).astype(int)
    daily = daily.merge(source_counts, on="target_date", validate="one_to_one")
    flagged = daily.loc[daily.positives.eq(0) & daily.FP.gt(0)]
    report = {
        "scope": "Existing validation predictions only; no model refit or test-label analysis",
        "prediction_file_sha256": sha256(prediction_path),
        "training_positive_rate": float(training.fire_positive.mean()),
        "validation_positive_rate": float(validation.fire_positive.mean()),
        "current_fire_groups": counts.reset_index().to_dict("records"),
        "daily_errors_and_source_trace": daily.to_dict("records"),
        "descriptive_input_shift": drift.to_dict("records"),
        "highest_logistic_score_bin": reference["reliability_bins"]["logistic_core"][-1],
        "flagged_zero_detection_days": flagged.to_dict("records"),
        "flag_interpretation": "A review flag, not proof of cloud, instrument outage, wrong labels or absence of fire. Keep the original outcomes and scores unchanged.",
        "holdout_evaluated": False,
    }
    (ROOT / "reports" / "baseline_error_analysis.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    lines = ["# Baseline error analysis", "", report["scope"]+".", "",
             "## Current fire versus no current detection", "",
             "| Fire detected on feature day | Rows | Next-day positives | TP | FP | FN | TN |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for current, row in counts.iterrows():
        lines.append(f"| {'Yes' if current else 'No'} | {int(row.rows)} | {int(row.positives)} | {int(row.TP)} | {int(row.FP)} | {int(row.FN)} | {int(row.TN)} |")
    lines += ["", "The conditions-only logistic model detected 7 of 37 positive outcomes among cells without a current detection, with 114 false alerts. New detections can be spread or previously missed fire, not necessarily new ignitions.", "",
              "## Daily error trace", "",
              "| Feature date | Target date | Positives | TP | FP | FN | Archive detections | Clean park detections |",
              "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in daily.itertuples():
        lines.append(f"| {row.feature_date} | {row.target_date} | {row.positives} | {row.TP} | {row.FP} | {row.FN} | {row.archive_detections} | {row.clean_park_detections} |")
    lines += ["", "## What these observations suggest", "",
              "- Current-fire persistence is a strong benchmark. The first logistic model omits this information, so the comparison does not isolate algorithm quality.",
              "- The fitted training positive rate is 2.09%, versus 41.34% in validation. Validation maximum temperature is about 1.69 training standard deviations higher on average; 20.67% of its maximum-temperature values exceed the observed training range. These are descriptive shifts, not proof of the cause of every error.",
              "- The highest logistic-score bin averages 88.07%, but only 31.58% of its 114 validation rows are positive. These outputs are not established event probabilities.",
              "- For target day 2019-12-22, the archive has 10 detections in its supplied region and the cleaned park file has zero. The baseline flagged all 43 model cells, contributing 43 of its 140 false positives against the detection labels. This is not an all-region instrument outage established by these files.",
              "- Zero park detections on that day do not establish that all fire stopped. Cloud, smoke, observation coverage or genuinely different activity remain unverified possibilities. The point archive contains no complete cloud/valid-observation mask.",
              "- Keep this day, its labels and its error contribution unchanged. Do not remove a difficult date or relabel it to improve the score. Additional observation-quality evidence must support any later data revision.", "",
              "## Next controlled experiment", "",
              "After reviewing label quality, add only `fire_today` to the 16 core features, with the same training rows, scaler policy, classifier settings and validation dates. This 17-feature logistic experiment would test the value of current-fire information while holding the algorithm fixed. Preserve the original 16-feature baseline. Continue to report the fire_today=0 subset separately.", "",
              "Only after interpreting that comparison should we test nonlinear models, then design calibration and alert thresholds on development data. Final-test labels remain sealed.", "",
              "## Official source context", "",
              "NASA explains that clouds and smoke can obscure detections; this general limitation does not establish the cause on our flagged date.", "",
              "- [NASA FIRMS alert notes](https://firms.modaps.eosdis.nasa.gov/alerts/notes.php)",
              "- [NASA Earthdata: active-fire caveats and missing observations](https://forum.earthdata.nasa.gov/viewtopic.php?t=5188)", "",
              "## Reproduce", "", "```powershell", ".\\.venv\\Scripts\\python.exe -m bushfire_ml.error_analysis", "```", ""]
    (ROOT / "reports" / "baseline_error_analysis.md").write_text("\n".join(lines), encoding="utf-8")
    verify_seal()
    print(json.dumps({"current_fire_groups": report["current_fire_groups"],
                      "flagged_zero_detection_days": report["flagged_zero_detection_days"],
                      "holdout_evaluated": False}, indent=2))


if __name__ == "__main__":
    main()
