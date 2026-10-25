"""Audit the Data Engineer handoff without changing model or source data.

The repository checks cover the prepared cell-day panel.  When ``--source-root``
is supplied, this script also verifies the retained original downloads, rebuilds
the cleaned FIRMS subset, reconstructs the fire labels, and checks ERA5-Land
hourly coverage.  The output deliberately distinguishes a complete label panel
from independently verified satellite observation coverage: a FIRMS archive is
a detection archive, so an absent detection cannot prove that a fire-free
observation occurred.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "inputs" / "dataset" / "blue_mountains_2019_2020"
MODEL_READY = DATASET / "model_ready"
START_DATE = pd.Timestamp("2019-07-01")
END_DATE = pd.Timestamp("2020-06-30")
RETAINED_CONFIDENCE = {"n", "h"}
REQUIRED_ERA5 = {"t2m", "d2m", "tp", "u10", "v10"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dataframe_equal(left: pd.DataFrame, right: pd.DataFrame) -> tuple[bool, str]:
    """Compare ordered tables while tolerating only numeric CSV round-off."""
    if list(left.columns) != list(right.columns):
        return False, "column names/order differ"
    if len(left) != len(right):
        return False, f"row counts differ ({len(left)} versus {len(right)})"
    for column in left.columns:
        a = left[column].reset_index(drop=True)
        b = right[column].reset_index(drop=True)
        if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
            if not np.allclose(a.to_numpy(), b.to_numpy(), rtol=0, atol=1e-9, equal_nan=True):
                return False, f"numeric values differ in {column}"
        elif not a.astype(str).equals(b.astype(str)):
            return False, f"values differ in {column}"
    return True, "ordered rows and columns match"


class Audit:
    def __init__(self) -> None:
        self.checks: list[dict[str, object]] = []

    def add(self, name: str, passed: bool | None, evidence: object, critical: bool = True) -> None:
        status = "not_verifiable" if passed is None else "pass" if bool(passed) else "fail"
        self.checks.append(
            {"name": name, "status": status, "critical": critical, "evidence": evidence}
        )

    def require(self, name: str, passed: bool, evidence: object) -> None:
        self.add(name, passed, evidence, critical=True)
        if not passed:
            raise AssertionError(f"{name}: {evidence}")


def load_repository_tables(audit: Audit) -> dict[str, pd.DataFrame]:
    tables = {
        "base": pd.read_csv(
            MODEL_READY / "blue_mountains_model_table_2019_2020.csv",
            parse_dates=["feature_date", "target_date"],
        ),
        "extended": pd.read_csv(
            MODEL_READY / "blue_mountains_model_table_2019_2020_extended.csv",
            parse_dates=["feature_date", "target_date"],
        ),
        "labels": pd.read_csv(
            MODEL_READY / "daily_fire_labels_2019_2020.csv",
            parse_dates=["target_date"],
        ),
        "weather": pd.read_csv(
            MODEL_READY / "daily_weather_features_2019_2020.csv",
            parse_dates=["feature_date"],
        ),
        "terrain": pd.read_csv(MODEL_READY / "terrain_features.csv"),
    }
    base, extended, labels, weather, terrain = (tables[k] for k in tables)

    audit.require("base table dimensions", base.shape == (18_980, 31), list(base.shape))
    audit.require("extended table dimensions", extended.shape == (18_980, 39), list(extended.shape))
    audit.require("label panel dimensions", labels.shape[0] == 19_032, list(labels.shape))
    audit.require("weather panel dimensions", weather.shape[0] == 18_980, list(weather.shape))
    audit.require("terrain dimensions", terrain.shape[0] == 52, list(terrain.shape))
    audit.require(
        "unique model keys",
        not extended.duplicated(["grid_id", "feature_date"]).any(),
        "grid_id + feature_date",
    )
    audit.require(
        "complete finite extended table",
        extended.notna().all().all()
        and np.isfinite(extended.select_dtypes("number").to_numpy()).all(),
        {"missing_values": int(extended.isna().sum().sum())},
    )
    audit.require(
        "one-day target alignment",
        ((extended.target_date - extended.feature_date).dt.days == 1).all(),
        {
            "feature_range": [str(extended.feature_date.min().date()), str(extended.feature_date.max().date())],
            "target_range": [str(extended.target_date.min().date()), str(extended.target_date.max().date())],
        },
    )
    audit.require(
        "complete dates per extended grid cell",
        extended.groupby("grid_id").size().eq(365).all(),
        {"cells": int(extended.grid_id.nunique()), "feature_days_per_cell": 365},
    )
    audit.require(
        "complete dates per label grid cell",
        labels.groupby("grid_id").size().eq(366).all(),
        {"cells": int(labels.grid_id.nunique()), "target_days_per_cell": 366},
    )

    counts_consistent = (
        labels.eligible_fire_detection_count
        == labels.fire_detection_count_raw - labels.prescribed_burn_detection_count
    ).all()
    binary_consistent = (
        labels.fire_positive == (labels.eligible_fire_detection_count > 0).astype("int8")
    ).all()
    audit.require(
        "label arithmetic and binary rule",
        bool(counts_consistent and binary_consistent),
        "eligible = raw - prescribed; fire_positive = eligible > 0",
    )

    label_columns = [
        "grid_id",
        "target_date",
        "fire_detection_count_raw",
        "prescribed_burn_detection_count",
        "eligible_fire_detection_count",
        "fire_positive",
    ]
    joined = base[label_columns].merge(
        labels[label_columns],
        on=["grid_id", "target_date"],
        suffixes=("_base", "_label"),
        validate="one_to_one",
    )
    matches = all(
        np.array_equal(joined[f"{c}_base"], joined[f"{c}_label"])
        for c in label_columns[2:]
    )
    audit.require("base target fields reproduce label panel", matches, label_columns[2:])

    current = labels[["grid_id", "target_date", "fire_positive"]].rename(
        columns={"target_date": "feature_date", "fire_positive": "expected_fire_today"}
    )
    current_join = extended.merge(current, on=["grid_id", "feature_date"], validate="one_to_one")
    audit.require(
        "fire_today uses feature-day label",
        np.array_equal(current_join.fire_today, current_join.expected_fire_today),
        "fire_today is joined from the label panel on feature_date",
    )
    target_join = extended[["grid_id", "target_date", "fire_positive"]].merge(
        labels[["grid_id", "target_date", "fire_positive"]],
        on=["grid_id", "target_date"],
        suffixes=("_extended", "_label"),
        validate="one_to_one",
    )
    audit.require(
        "extended target reproduces label panel",
        np.array_equal(target_join.fire_positive_extended, target_join.fire_positive_label),
        "target joined on grid_id + target_date",
    )
    return tables


def verify_repository_provenance(audit: Audit) -> dict[str, object]:
    provenance = json.loads((MODEL_READY / "provenance.json").read_text(encoding="utf-8"))
    quality = json.loads((MODEL_READY / "quality_report.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "output" / "results" / "run_manifest.json").read_text(encoding="utf-8"))

    model_checks = []
    for record in provenance["model_ready_files"]:
        path = DATASET / record["file"]
        ok = path.is_file() and path.stat().st_size == record["bytes"] and sha256(path) == record["sha256"]
        model_checks.append({"file": record["file"], "verified": ok})
    audit.require(
        "model-ready provenance hashes",
        all(item["verified"] for item in model_checks),
        model_checks,
    )
    extended_hash = sha256(MODEL_READY / "blue_mountains_model_table_2019_2020_extended.csv")
    audit.require(
        "training input identity",
        extended_hash == manifest["input_sha256"],
        {"sha256": extended_hash, "run_manifest_sha256": manifest["input_sha256"]},
    )
    register = pd.read_csv(DATASET / "metadata" / "data_register.csv")
    audit.require(
        "source register covers five required datasets",
        set(register.dataset)
        == {
            "NPWS Estate boundary",
            "NPWS Fire History",
            "SRTM-derived DEM",
            "S-NPP VIIRS active fire",
            "ERA5-Land",
        },
        register.dataset.tolist(),
    )
    missing_governance = [
        column for column in ["access_date", "licence_or_terms"] if column not in register.columns
    ]
    blank_governance = {
        column: int(register[column].isna().sum()) if column in register.columns else len(register)
        for column in ["access_date", "licence_or_terms"]
    }
    audit.add(
        "source access dates and licences recorded",
        not missing_governance and not any(blank_governance.values()),
        {"missing_columns": missing_governance, "blank_values": blank_governance},
        critical=False,
    )
    return {"provenance": provenance, "quality": quality, "register": register.to_dict("records")}


def reproduce_clean_firms(audit: Audit, source_root: Path) -> dict[str, object]:
    raw_path = source_root / "DL_FIRE_SV-C2_818385" / "fire_archive_SV-C2_818385.csv"
    boundary_path = source_root / "processed" / "blue_mountains_national_park_boundary.gpkg"
    cleaned_path = source_root / "processed" / "blue_mountains_np_firms_2019_2020_clean.csv"
    raw = pd.read_csv(raw_path)
    required = {"latitude", "longitude", "acq_date", "acq_time", "satellite", "instrument", "confidence", "frp"}
    audit.require("raw FIRMS required fields", required <= set(raw.columns), sorted(required))
    dates = pd.to_datetime(raw.acq_date, errors="raise")
    period = dates.between(START_DATE, END_DATE, inclusive="both")
    confidence = raw.confidence.isin(RETAINED_CONFIDENCE)
    park = gpd.read_file(boundary_path).to_crs("EPSG:4326")
    points = gpd.GeoSeries(gpd.points_from_xy(raw.longitude, raw.latitude), crs="EPSG:4326")
    park_mask = points.intersects(park.geometry.iloc[0])
    rebuilt = raw.loc[period & confidence & park_mask].copy()
    rebuilt["acq_date"] = dates.loc[rebuilt.index].dt.strftime("%Y-%m-%d")
    before_dedup = len(rebuilt)
    rebuilt = rebuilt.drop_duplicates().sort_values(
        ["acq_date", "acq_time", "latitude", "longitude"], kind="stable"
    ).reset_index(drop=True)
    supplied = pd.read_csv(cleaned_path)
    equal, reason = dataframe_equal(rebuilt, supplied)
    audit.require("cleaned FIRMS table reproduced from raw archive", equal, reason)
    return {
        "raw_rows": int(len(raw)),
        "rows_in_period": int(period.sum()),
        "rows_with_retained_confidence_in_period": int((period & confidence).sum()),
        "rows_inside_park_after_date_confidence": int((period & confidence & park_mask).sum()),
        "duplicates_removed": int(before_dedup - len(rebuilt)),
        "cleaned_rows": int(len(rebuilt)),
        "confidence_counts": {str(k): int(v) for k, v in rebuilt.confidence.value_counts().items()},
        "first_detection_date": str(pd.to_datetime(rebuilt.acq_date).min().date()),
        "last_detection_date": str(pd.to_datetime(rebuilt.acq_date).max().date()),
    }


def reconstruct_labels(
    audit: Audit, source_root: Path, supplied_labels: pd.DataFrame
) -> dict[str, object]:
    firms = pd.read_csv(source_root / "processed" / "blue_mountains_np_firms_2019_2020_clean.csv")
    firms["target_date"] = pd.to_datetime(firms.acq_date, errors="raise")
    points = gpd.GeoDataFrame(
        firms,
        geometry=gpd.points_from_xy(firms.longitude, firms.latitude),
        crs="EPSG:4326",
    )
    history = gpd.read_file(
        source_root / "processed" / "blue_mountains_np_fire_history_2019_2020.gpkg"
    ).to_crs("EPSG:4326")
    prescribed = history.loc[history.fire_type.eq("prescribed_burn")].copy()
    prescribed["StartDate"] = pd.to_datetime(prescribed.StartDate)
    prescribed["EndDate"] = pd.to_datetime(prescribed.EndDate)
    prescribed_mask = pd.Series(False, index=points.index)
    for fire in prescribed.itertuples():
        prescribed_mask |= points.geometry.intersects(fire.geometry) & points.target_date.between(
            fire.StartDate, fire.EndDate
        )
    points["prescribed_burn_overlap"] = prescribed_mask.astype("int8")

    grid = gpd.read_file(MODEL_READY / "blue_mountains_era5_grid.gpkg").to_crs("EPSG:4326")
    latitudes = np.sort(grid.latitude.unique())
    longitudes = np.sort(grid.longitude.unique())
    lookup = {
        (round(row.latitude, 6), round(row.longitude, 6)): row.grid_id
        for row in grid.itertuples()
    }
    nearest_latitudes = [float(latitudes[np.abs(latitudes - value).argmin()]) for value in points.latitude]
    nearest_longitudes = [float(longitudes[np.abs(longitudes - value).argmin()]) for value in points.longitude]
    points["grid_id"] = [
        lookup.get((round(latitude, 6), round(longitude, 6)))
        for latitude, longitude in zip(nearest_latitudes, nearest_longitudes)
    ]
    audit.require(
        "all cleaned FIRMS points assigned to analysis grid",
        points.grid_id.notna().all(),
        {"unassigned": int(points.grid_id.isna().sum())},
    )
    counts = (
        points.groupby(["grid_id", "target_date"], as_index=False)
        .agg(
            fire_detection_count_raw=("grid_id", "size"),
            prescribed_burn_detection_count=("prescribed_burn_overlap", "sum"),
        )
    )
    counts["eligible_fire_detection_count"] = (
        counts.fire_detection_count_raw - counts.prescribed_burn_detection_count
    )
    full_index = pd.MultiIndex.from_product(
        [grid.grid_id.tolist(), pd.date_range(START_DATE, END_DATE, freq="D")],
        names=["grid_id", "target_date"],
    )
    rebuilt = counts.set_index(["grid_id", "target_date"]).reindex(full_index, fill_value=0).reset_index()
    count_columns = [
        "fire_detection_count_raw",
        "prescribed_burn_detection_count",
        "eligible_fire_detection_count",
    ]
    rebuilt[count_columns] = rebuilt[count_columns].astype("int32")
    rebuilt["fire_positive"] = (rebuilt.eligible_fire_detection_count > 0).astype("int8")
    supplied = supplied_labels.sort_values(["grid_id", "target_date"]).reset_index(drop=True)
    rebuilt = rebuilt[supplied.columns].sort_values(["grid_id", "target_date"]).reset_index(drop=True)
    equal, reason = dataframe_equal(rebuilt, supplied)
    audit.require("daily fire-label panel independently reconstructed", equal, reason)
    return {
        "cleaned_firms_records": int(len(points)),
        "prescribed_burn_records_excluded": int(prescribed_mask.sum()),
        "eligible_firms_records": int((~prescribed_mask).sum()),
        "positive_grid_cell_days": int(rebuilt.fire_positive.sum()),
        "prescribed_polygons_used": int(len(prescribed)),
    }


def audit_fire_history_window(audit: Audit, source_root: Path) -> dict[str, object]:
    park = gpd.read_file(
        source_root / "processed" / "blue_mountains_national_park_boundary.gpkg"
    ).to_crs("EPSG:4326")
    history = gpd.read_file(
        source_root / "raw" / "fire_history" / "fire_npwsfirehistory" / "NPWSFireHistory.shp",
        bbox=tuple(park.total_bounds),
    ).to_crs("EPSG:4326")
    history["StartDate"] = pd.to_datetime(history.StartDate, errors="coerce")
    history["EndDate"] = pd.to_datetime(history.EndDate, errors="coerce")
    intersects = history.geometry.intersects(park.geometry.iloc[0])
    current_rule = history.StartDate.between(START_DATE, END_DATE, inclusive="both") & intersects
    effective_end = history.EndDate.fillna(history.StartDate)
    overlap_rule = (
        history.StartDate.le(END_DATE) & effective_end.ge(START_DATE) & intersects
    )
    omitted = history.loc[overlap_rule & ~current_rule].copy()
    omitted_prescribed = omitted.Label.str.contains("Prescribed", case=False, na=False)
    audit.add(
        "fire-history interval overlap coverage",
        len(omitted) == 0,
        {
            "records_under_current_start_date_rule": int(current_rule.sum()),
            "records_overlapping_study_period": int(overlap_rule.sum()),
            "overlapping_records_omitted_by_current_rule": int(len(omitted)),
            "omitted_prescribed_burn_records": int(omitted_prescribed.sum()),
        },
        critical=False,
    )
    return {
        "records_under_current_start_date_rule": int(current_rule.sum()),
        "records_overlapping_study_period": int(overlap_rule.sum()),
        "overlapping_records_omitted_by_current_rule": int(len(omitted)),
        "omitted_prescribed_burn_records": int(omitted_prescribed.sum()),
    }


def verify_external_hashes_and_era5(
    audit: Audit, source_root: Path, provenance: dict[str, object]
) -> dict[str, object]:
    source_checks = []
    for record in provenance["sources"]:
        path = source_root / str(record["relative_path"]).replace("\\", "/")
        ok = path.is_file() and path.stat().st_size == record["bytes"] and sha256(path) == record["sha256"]
        source_checks.append({"relative_path": record["relative_path"], "verified": ok})
    audit.require(
        "base-build source hashes against retained source root",
        all(item["verified"] for item in source_checks),
        {"verified": sum(item["verified"] for item in source_checks), "expected": len(source_checks)},
    )

    manifest = pd.read_csv(DATASET / "metadata" / "sha256_manifest.csv")
    manifest_checks = []
    for row in manifest.itertuples():
        path = source_root / str(row.relative_path).replace("\\", "/")
        ok = path.is_file() and path.stat().st_size == row.size_bytes and sha256(path) == row.sha256
        manifest_checks.append({"relative_path": row.relative_path, "verified": bool(ok)})
    audit.require(
        "raw-download manifest hashes",
        all(item["verified"] for item in manifest_checks),
        {"verified": sum(item["verified"] for item in manifest_checks), "expected": len(manifest_checks)},
    )

    files = sorted((source_root / "raw" / "era5_land").glob("era5_land_*.nc"))
    expected_names = [
        f"era5_land_{month.year}_{month.month:02d}.nc"
        for month in pd.date_range("2019-07-01", "2020-06-01", freq="MS")
    ]
    audit.require("ERA5-Land monthly files", [p.name for p in files] == expected_names, [p.name for p in files])
    all_times = []
    coordinate_signature = None
    missing_values: dict[str, int] = {name: 0 for name in REQUIRED_ERA5}
    monthly_steps: dict[str, int] = {}
    for path in files:
        with xr.open_dataset(path) as dataset:
            audit.require(
                f"ERA5 variables {path.name}",
                REQUIRED_ERA5 <= set(dataset.data_vars),
                sorted(dataset.data_vars),
            )
            times = pd.DatetimeIndex(dataset.valid_time.values)
            all_times.extend(times.tolist())
            monthly_steps[path.stem.replace("era5_land_", "")] = int(len(times))
            signature = (
                tuple(np.asarray(dataset.latitude.values).round(8)),
                tuple(np.asarray(dataset.longitude.values).round(8)),
            )
            if coordinate_signature is None:
                coordinate_signature = signature
            audit.require(f"ERA5 coordinates {path.name}", signature == coordinate_signature, "common grid")
            for name in REQUIRED_ERA5:
                missing_values[name] += int(dataset[name].isnull().sum().item())
    expected_times = pd.date_range("2019-07-01 00:00", "2020-06-30 23:00", freq="h")
    actual_times = pd.DatetimeIndex(all_times)
    audit.require(
        "continuous ERA5 hourly coverage",
        actual_times.equals(expected_times),
        {
            "hourly_steps": int(len(actual_times)),
            "first": str(actual_times.min()),
            "last": str(actual_times.max()),
            "duplicates": int(actual_times.duplicated().sum()),
        },
    )
    audit.require("ERA5 required variables have no missing cells", sum(missing_values.values()) == 0, missing_values)
    return {
        "source_hashes_verified": len(source_checks),
        "raw_manifest_hashes_verified": len(manifest_checks),
        "monthly_hourly_steps": monthly_steps,
        "total_hourly_steps": int(len(actual_times)),
        "missing_values": missing_values,
    }


def monthly_coverage(labels: pd.DataFrame) -> list[dict[str, object]]:
    grouped = labels.assign(month=labels.target_date.dt.to_period("M")).groupby("month", observed=True)
    rows = []
    for month, frame in grouped:
        daily = frame.groupby("target_date", observed=True).agg(
            raw_detections=("fire_detection_count_raw", "sum"),
            prescribed_detections=("prescribed_burn_detection_count", "sum"),
            eligible_detections=("eligible_fire_detection_count", "sum"),
            positive_cells=("fire_positive", "sum"),
        )
        rows.append(
            {
                "month": str(month),
                "calendar_days": int(daily.shape[0]),
                "label_rows": int(len(frame)),
                "days_with_any_raw_detection": int((daily.raw_detections > 0).sum()),
                "days_with_any_positive_cell": int((daily.positive_cells > 0).sum()),
                "raw_detections": int(daily.raw_detections.sum()),
                "prescribed_detections": int(daily.prescribed_detections.sum()),
                "eligible_detections": int(daily.eligible_detections.sum()),
                "positive_cell_days": int(daily.positive_cells.sum()),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, help="Retained original Dataset directory")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "output" / "results" / "data_handoff_audit.json",
    )
    args = parser.parse_args()
    audit = Audit()
    tables = load_repository_tables(audit)
    repo_records = verify_repository_provenance(audit)
    external: dict[str, object] | None = None
    if args.source_root:
        source_root = args.source_root.resolve()
        external = {
            "provenance_and_era5": verify_external_hashes_and_era5(
                audit, source_root, repo_records["provenance"]
            ),
            "firms_cleaning": reproduce_clean_firms(audit, source_root),
            "label_reconstruction": reconstruct_labels(audit, source_root, tables["labels"]),
            "fire_history_window": audit_fire_history_window(audit, source_root),
        }
    else:
        audit.add(
            "external raw-source verification",
            None,
            "Run with --source-root pointing to the retained original Dataset directory.",
            critical=False,
        )

    retained = tables["extended"].loc[tables["extended"].park_area_fraction >= 0.1]
    months = monthly_coverage(tables["labels"])
    zero_months = [row["month"] for row in months if row["positive_cell_days"] == 0]
    audit.add(
        "satellite observation opportunities on zero-label dates",
        None,
        (
            "The supplied FIRMS archive lists detections, not every successful satellite overpass or clear-sky "
            "observation. Complete zero-filled label rows therefore do not independently verify observed negatives."
        ),
        critical=False,
    )
    audit.add(
        "independent fire-absence confirmation",
        None,
        "No independent incident or complete observation-availability panel is supplied for zero-label dates.",
        critical=False,
    )

    failed_critical = [c for c in audit.checks if c["critical"] and c["status"] == "fail"]
    failed_noncritical = [c for c in audit.checks if not c["critical"] and c["status"] == "fail"]
    unverifiable = [c for c in audit.checks if c["status"] == "not_verifiable"]
    status = "fail" if failed_critical else "pass_with_limitations" if failed_noncritical or unverifiable else "pass"
    result = {
        "generated_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "scope": "Data provenance, label construction, date alignment and observation coverage; no model retraining or test-set tuning.",
        "overall_status": status,
        "summary": {
            "original_panel_rows": int(len(tables["extended"])),
            "original_grid_cells": int(tables["extended"].grid_id.nunique()),
            "retained_modelling_rows": int(len(retained)),
            "retained_grid_cells": int(retained.grid_id.nunique()),
            "retained_positive_targets": int(retained.fire_positive.sum()),
            "feature_date_range": [
                str(tables["extended"].feature_date.min().date()),
                str(tables["extended"].feature_date.max().date()),
            ],
            "target_date_range": [
                str(tables["labels"].target_date.min().date()),
                str(tables["labels"].target_date.max().date()),
            ],
            "zero_positive_months": zero_months,
        },
        "monthly_detection_coverage": months,
        "checks": audit.checks,
        "external_source_audit": external,
        "conclusion": (
            "Prepared-table integrity, provenance identities, label arithmetic and the one-day target shift are "
            "verified. Zero labels mean no eligible FIRMS detection in the supplied archive; they are not "
            "independent confirmation that no fire occurred or that satellite observation was complete."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8", newline="\n")
    print(json.dumps({"overall_status": status, "checks": len(audit.checks), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
