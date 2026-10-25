"""Audit development data and source derivations without profiling final-test labels."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import netCDF4
import numpy as np
import pandas as pd

from .data import LOCAL_ROOT, ROOT, load_development, read_protocol, sha256, verify_seal


def read_before(path: Path, date_column: str, cutoff: str) -> pd.DataFrame:
    """Filter dates before numeric conversion or any outcome analysis."""
    with path.open(encoding="utf-8-sig", newline="") as stream:
        frame = pd.DataFrame(row for row in csv.DictReader(stream) if row[date_column] < cutoff)
    text_columns = {"grid_id", "feature_date", "target_date", "split"}
    for column in frame.columns.difference(list(text_columns)):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    return frame


def compare_numeric(observed, expected, tolerance: float = 1e-4) -> dict:
    actual = np.asarray(observed, dtype=float)
    expected = np.asarray(expected, dtype=float)
    if actual.shape != expected.shape or not np.isfinite(actual).all() or not np.isfinite(expected).all():
        raise ValueError("Non-finite values or incompatible shapes in a derivation check")
    delta = np.abs(actual - expected)
    return {"mismatches": int((delta > tolerance).sum()),
            "max_absolute_error": float(delta.max(initial=0)), "tolerance": tolerance}


def audit_weather(source_root: Path, frame: pd.DataFrame, cutoff: str) -> tuple[dict, dict]:
    """Independently recalculate source weather in development months only.

    Memory-backed NetCDF avoids the native library's Unicode-path limitation on
    Windows. The original files are read, never rewritten or executed.
    """
    centres = frame.drop_duplicates("grid_id").set_index("grid_id")
    daily_parts = []
    rain_parts = []
    for path in sorted((source_root / "raw" / "era5_land").glob("era5_land_*.nc")):
        month = path.stem.removeprefix("era5_land_").replace("_", "-") + "-01"
        if month >= cutoff:
            continue
        with netCDF4.Dataset("development_weather", memory=path.read_bytes()) as dataset:
            latitudes = np.asarray(dataset.variables["latitude"][:])
            longitudes = np.asarray(dataset.variables["longitude"][:])
            time = dataset.variables["valid_time"]
            times = pd.DatetimeIndex([pd.Timestamp(t.isoformat()) for t in netCDF4.num2date(time[:], time.units)])
            if len(times) != len(times.unique()) or not (times[1:] - times[:-1] == pd.Timedelta(hours=1)).all():
                raise ValueError("Raw weather timestamps are duplicated or not hourly")
            arrays = {name: np.asarray(dataset.variables[name][:], dtype=float)
                      for name in ["t2m", "d2m", "u10", "v10", "tp"]}
            for grid, cell in centres.iterrows():
                i = int(np.abs(latitudes-cell.latitude).argmin())
                j = int(np.abs(longitudes-cell.longitude).argmin())
                temperature = arrays["t2m"][:, i, j] - 273.15
                dewpoint = arrays["d2m"][:, i, j] - 273.15
                wind = np.hypot(arrays["u10"][:, i, j], arrays["v10"][:, i, j])
                humidity = np.clip(100*np.exp(17.625*dewpoint/(243.04+dewpoint)
                                              -17.625*temperature/(243.04+temperature)), 0, 100)
                hourly = pd.DataFrame({"feature_date": times.normalize(), "temperature": temperature,
                                       "dewpoint": dewpoint, "wind": wind, "humidity": humidity})
                if not hourly.groupby("feature_date").size().eq(24).all():
                    raise ValueError("A source weather day is incomplete")
                daily = hourly.groupby("feature_date", as_index=False).agg(
                    temperature_mean_c=("temperature", "mean"), temperature_max_c=("temperature", "max"),
                    temperature_min_c=("temperature", "min"), dewpoint_mean_c=("dewpoint", "mean"),
                    relative_humidity_mean_pct=("humidity", "mean"), relative_humidity_min_pct=("humidity", "min"),
                    wind_speed_mean_ms=("wind", "mean"), wind_speed_max_ms=("wind", "max"))
                daily["grid_id"] = grid
                daily_parts.append(daily)
                midnight = times.hour == 0
                rain_parts.append(pd.DataFrame({
                    "grid_id": grid, "feature_date": times[midnight].normalize()-pd.Timedelta(days=1),
                    "precipitation_sum_mm": np.maximum(arrays["tp"][midnight, i, j], 0)*1000}))

    expected = pd.concat(daily_parts, ignore_index=True)
    expected["feature_date"] = expected.feature_date.dt.strftime("%Y-%m-%d")
    merged = frame.merge(expected, on=["grid_id", "feature_date"], suffixes=("", "_raw"), validate="one_to_one")
    if len(merged) != len(frame):
        raise ValueError("Some development weather rows were not checked")
    checks = {column: compare_numeric(merged[column], merged[column+"_raw"], tolerance=5e-4)
              for column in expected.columns if column not in {"grid_id", "feature_date"}}
    rain = pd.concat(rain_parts, ignore_index=True)
    rain["feature_date"] = rain.feature_date.dt.strftime("%Y-%m-%d")
    checked_rain = frame.merge(rain, on=["grid_id", "feature_date"], suffixes=("", "_raw"), validate="one_to_one")
    checks["precipitation_sum_mm"] = compare_numeric(checked_rain.precipitation_sum_mm,
                                                     checked_rain.precipitation_sum_mm_raw)
    checks["precipitation_source_rows_checked"] = len(checked_rain)
    checks["precipitation_last_day_not_checked"] = "2019-12-31: next-month midnight was intentionally not opened"
    prefix = rain.loc[rain.feature_date.eq("2019-06-30")].set_index("grid_id").precipitation_sum_mm.to_dict()
    return checks, prefix


def main() -> None:
    manifest = verify_seal()
    protocol = read_protocol()
    location = json.loads((LOCAL_ROOT / "source_location.json").read_text(encoding="utf-8"))
    source_root = Path(location["dataset_root"])
    source = source_root / "model_ready" / protocol["source_table"]
    if sha256(source) != manifest["source_table_sha256"]:
        raise RuntimeError("The supplied source table changed after sealing")
    # Validate source hashes without examining final-test values or outcomes.
    inventory = json.loads((LOCAL_ROOT / "source_inventory.json").read_text(encoding="utf-8"))
    for entry in inventory:
        if sha256(source_root / entry["path"]) != entry["sha256"]:
            raise RuntimeError("A supplied file changed after sealing")
    cutoff = (pd.Timestamp(protocol["original_validation_end"])+pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    frame = read_before(source, "feature_date", cutoff).sort_values(["grid_id", "feature_date"])
    base = read_before(source_root / "model_ready" / "blue_mountains_model_table_2019_2020.csv", "feature_date", cutoff)
    labels = read_before(source_root / "model_ready" / "daily_fire_labels_2019_2020.csv", "target_date", cutoff)
    current = labels.rename(columns={"target_date": "feature_date", "fire_positive": "expected_fire_today"})
    frame = frame.merge(current[["grid_id", "feature_date", "expected_fire_today"]],
                        on=["grid_id", "feature_date"], validate="one_to_one").sort_values(["grid_id", "feature_date"])
    checks = {
        "unique_grid_date_keys": not bool(frame.duplicated(["grid_id", "feature_date"]).any()),
        "no_missing_development_values": not bool(frame.isna().any().any()),
        "binary_development_target": bool(frame.fire_positive.isin([0, 1]).all()),
        "next_day_target": bool((pd.to_datetime(frame.target_date)-pd.to_datetime(frame.feature_date)).eq(pd.Timedelta(days=1)).all()),
        "label_matches_eligible_target_count": bool(frame.fire_positive.eq(frame.eligible_fire_detection_count.gt(0)).all()),
        "target_count_accounting": bool(frame.fire_detection_count_raw.eq(frame.eligible_fire_detection_count+frame.prescribed_burn_detection_count).all()),
        "fire_today_matches_same_day_label": bool(frame.fire_today.eq(frame.expected_fire_today).all()),
        "humidity_in_range": bool(frame.relative_humidity_mean_pct.between(0, 100).all() and frame.relative_humidity_min_pct.between(0, 100).all()),
        "temperature_order": bool((frame.temperature_min_c <= frame.temperature_mean_c).all() and (frame.temperature_mean_c <= frame.temperature_max_c).all()),
        "nonnegative_weather": bool((frame[["precipitation_sum_mm", "wind_speed_mean_ms", "wind_speed_max_ms"]] >= 0).all().all()),
        "terrain_static_per_grid": bool(frame.groupby("grid_id")[["elevation_mean_m", "slope_mean_deg", "aspect_sin", "aspect_cos"]].nunique().le(1).all().all()),
    }
    shared = base.set_index(["grid_id", "feature_date"]).sort_index()
    extended = frame.set_index(["grid_id", "feature_date"]).sort_index()
    checks["base_extended_shared_fields_agree"] = all(
        bool(np.allclose(shared[column], extended[column], atol=1e-6))
        if pd.api.types.is_numeric_dtype(shared[column])
        else bool(shared[column].eq(extended[column]).all()) for column in shared.columns)
    weather_checks, prefix = audit_weather(source_root, frame, cutoff)
    checks["daily_weather_recomputed_from_raw"] = all(
        result["mismatches"] == 0 for result in weather_checks.values() if isinstance(result, dict))
    for window in [3, 7, 30, 90]:
        errors = []
        for grid, part in frame.groupby("grid_id", sort=False):
            history = part.precipitation_sum_mm.reset_index(drop=True)
            if window != 3:
                history = pd.concat([pd.Series([prefix[grid]]), history], ignore_index=True)
            expected = history.rolling(window, min_periods=1).sum().to_numpy()
            if window != 3:
                expected = expected[1:]
            errors.extend(part[f"precipitation_{window}d_mm"].to_numpy()-expected)
        checks[f"precipitation_{window}d_causal_window"] = bool(np.abs(errors).max() < 1e-4)
    expected_last7 = frame.groupby("grid_id").expected_fire_today.transform(lambda s: s.rolling(7, min_periods=1).sum())
    checks["fire_last7_includes_today_only_and_past"] = bool(frame.fire_days_last_7.eq(expected_last7).all())
    checks["rain_history_length"] = bool(frame.rain_history_days.eq(
        (pd.to_datetime(frame.feature_date)-pd.Timestamp("2019-06-30")).dt.days+1).all())
    dry_matches = []
    unknown_dry_history_rows = 0
    for _, part in frame.groupby("grid_id"):
        counter = 120
        seen_wet_day = False
        expected = []
        for rain in part.precipitation_sum_mm:
            seen_wet_day |= rain >= 5
            counter = 0 if rain >= 5 else min(120, counter+1)
            expected.append(counter)
            unknown_dry_history_rows += int(not seen_wet_day)
        dry_matches.extend(part.days_since_rain_5mm.to_numpy() == expected)
    checks["dry_spell_initialisation_reproduced"] = bool(all(dry_matches))
    fire_panel = labels.pivot(index="target_date", columns="grid_id", values="fire_positive")
    centres = frame.drop_duplicates("grid_id").set_index("grid_id")[["latitude", "longitude"]]
    neighbour_mismatches = 0
    for grid, part in frame.groupby("grid_id"):
        distance = (centres-centres.loc[grid]).abs().max(axis=1)
        neighbours = centres.index[distance.gt(0) & distance.le(0.100001)]
        expected = fire_panel[neighbours].max(axis=1).reindex(part.feature_date).to_numpy()
        neighbour_mismatches += int(np.count_nonzero(part.fire_neighbour_today.to_numpy() != expected))
    checks["fire_neighbour_is_current_day_8_neighbour_flag"] = neighbour_mismatches == 0
    if not all(checks.values()):
        raise RuntimeError("Development audit failed: " + ", ".join(key for key, passed in checks.items() if not passed))

    summary = {}
    for partition in ["train", "validation"]:
        part = load_development(partition)
        summary[partition] = {"rows": len(part), "positive_cell_days": int(part.fire_positive.sum()),
                              "positive_rate": float(part.fire_positive.mean()),
                              "all_negative_accuracy": float(1-part.fire_positive.mean()),
                              "missing_primary_predictor_values": int(part[protocol["feature_sets"]["conditions_core"]].isna().sum().sum())}
    report = {
        "scope": "Development data only; final-test outcomes were not profiled or scored",
        "source_files_hashed": len(inventory), "supplier_provenance_files_verified": manifest["source_provenance_checks_passed"],
        "checks": checks, "raw_weather_checks": weather_checks, "development_partitions": summary,
        "dry_history_unknown_rows_before_first_observed_wet_day_all_development_cells": unknown_dry_history_rows,
        "limitations": [
            "The 39-column extended table has no supplied generation script or complete data dictionary; its shared fields and eight additions were independently checked on development data.",
            "The 7/30/90-day rainfall sums include a 30 June 2019 accumulation from the 1 July 00 UTC weather record. Early windows are partial, not full-duration histories.",
            "The dry-spell counter starts at 120 without 120 days of preceding observations. Treat these initial values as unknown; exclude or repair before using extended features.",
            "The first two development feature days have incomplete three-day rainfall history. Drop these warm-up rows before the first core-feature fit.",
            "Validation is a short high-fire interval with a much larger positive rate than training. Probability calibration and threshold stability need development-only checks.",
            "Seven-day gaps reduce adjacency but do not guarantee that long-lived fire events are independent across partitions.",
            "No independent-season or independent-location generalisation is demonstrated.",
            "Terrain extraction and raw point-to-polygon fire labelling were reviewed in the supplied scripts, not independently rerun with GIS software.",
            "Known prescribed burns are partially excluded using retrospective fire-history polygons. Satellite non-detection is not confirmed absence of fire.",
            "ERA5-Land reanalysis and full-day satellite archives do not reproduce real-time data publication latency."
        ],
        "holdout_evaluated": False,
    }
    (ROOT / "reports" / "development_audit.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    lines = ["# Development data audit", "", report["scope"]+".", "",
             f"Verified {len(inventory)} source-file hashes and all {manifest['source_provenance_checks_passed']} supplier provenance hashes.", "",
             "## Frozen partitions", "", "| Partition | Feature dates (UTC) | Rows |", "| --- | --- | ---: |"]
    for name in ["train", "validation", "final_test"]:
        part = manifest["partitions"][name]
        lines.append(f"| {name} | {part['first_feature_date']} to {part['last_feature_date']} | {part['rows']:,} |")
    lines += ["", "The two seven-day gaps contain 602 excluded rows. Whole feature dates are assigned together.", "",
              "## Development label balance", "", "| Partition | Positive cell-days | Positive rate | All-negative accuracy |",
              "| --- | ---: | ---: | ---: |"]
    for name, part in summary.items():
        lines.append(f"| {name} | {part['positive_cell_days']} | {part['positive_rate']:.2%} | {part['all_negative_accuracy']:.2%} |")
    lines += ["", "Final-test label counts, example outcomes and model scores are intentionally absent.", "",
              "## Checks", "", *[f"- PASS: {key.replace('_', ' ')}." for key in checks], "",
              "## Findings and limits", "", *[f"- {item}" for item in report["limitations"]], "",
              "## Next lesson", "", "Fit simple baselines on the training partition, using only the 16 approved core conditions features. Remove the first two warm-up days. Inspect validation results only. Keep the final test sealed. No estimator has been fitted in this stage.", ""]
    (ROOT / "reports" / "development_audit.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"checks_passed": len(checks), "development_partitions": summary,
                      "holdout_evaluated": False}, indent=2))


if __name__ == "__main__":
    main()
