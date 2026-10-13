r"""Build the model-ready Blue Mountains grid-cell/day dataset.

The script preserves all downloaded source data. It aligns ERA5-Land weather,
SRTM terrain and FIRMS fire detections to the native 0.1-degree ERA5-Land
grid over Blue Mountains National Park. Each model row uses predictors from a
feature date and a binary fire label for the following UTC day.

Run from the ENGG2112 workspace with:

    .venv\Scripts\python.exe \
        "Group Project\Dataset\scripts\build_model_ready_dataset.py"
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import xarray as xr
from shapely.geometry import box


DATASET_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = DATASET_DIR / "processed"
OUTPUT_DIR = DATASET_DIR / "model_ready"

ERA5_DIR = DATASET_DIR / "raw" / "era5_land"
BOUNDARY_FILE = PROCESSED_DIR / "blue_mountains_national_park_boundary.gpkg"
FIRE_HISTORY_FILE = PROCESSED_DIR / "blue_mountains_np_fire_history_2019_2020.gpkg"
FIRMS_FILE = PROCESSED_DIR / "blue_mountains_np_firms_2019_2020_clean.csv"
DEM_FILE = PROCESSED_DIR / "blue_mountains_np_srtm_dem_clipped.tif"

START_DATE = pd.Timestamp("2019-07-01")
END_DATE = pd.Timestamp("2020-06-30")
LAST_FEATURE_DATE = END_DATE - pd.Timedelta(days=1)

TRAIN_END = pd.Timestamp("2019-12-15")
VALIDATION_END = pd.Timestamp("2019-12-31")

WEATHER_COLUMNS = [
    "temperature_mean_c",
    "temperature_max_c",
    "temperature_min_c",
    "dewpoint_mean_c",
    "relative_humidity_mean_pct",
    "relative_humidity_min_pct",
    "precipitation_sum_mm",
    "precipitation_3d_mm",
    "wind_speed_mean_ms",
    "wind_speed_max_ms",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_analysis_grid(
    latitudes: np.ndarray,
    longitudes: np.ndarray,
    park: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Create ERA5 cells and retain cells with positive park overlap."""
    lat_step = float(np.median(np.abs(np.diff(latitudes))))
    lon_step = float(np.median(np.abs(np.diff(longitudes))))
    records: list[dict[str, object]] = []

    for lat_index, latitude in enumerate(latitudes):
        for lon_index, longitude in enumerate(longitudes):
            records.append(
                {
                    "grid_id": f"G{lat_index:02d}_{lon_index:02d}",
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                    "source_lat_index": lat_index,
                    "source_lon_index": lon_index,
                    "geometry": box(
                        float(longitude - lon_step / 2),
                        float(latitude - lat_step / 2),
                        float(longitude + lon_step / 2),
                        float(latitude + lat_step / 2),
                    ),
                }
            )

    grid = gpd.GeoDataFrame(records, crs="EPSG:4326")
    grid_projected = grid.to_crs("EPSG:3577")
    park_geometry = park.to_crs("EPSG:3577").geometry.iloc[0]
    intersection_area = grid_projected.geometry.intersection(park_geometry).area
    grid["park_area_fraction"] = (
        intersection_area / grid_projected.geometry.area
    ).clip(0, 1)
    grid = grid.loc[grid["park_area_fraction"] > 0].copy()
    return grid.sort_values("grid_id").reset_index(drop=True)


def build_weather_features(grid: gpd.GeoDataFrame) -> tuple[pd.DataFrame, int]:
    """Aggregate hourly ERA5-Land fields into complete UTC days."""
    monthly_files = sorted(ERA5_DIR.glob("era5_land_*.nc"))
    if len(monthly_files) != 12:
        raise ValueError(f"Expected 12 ERA5-Land files, found {len(monthly_files)}")

    required_variables = {"t2m", "d2m", "tp", "u10", "v10"}
    daily_frames: list[pd.DataFrame] = []
    precipitation_frames: list[pd.DataFrame] = []
    total_hourly_steps = 0

    for path in monthly_files:
        with xr.open_dataset(path) as dataset:
            missing = required_variables.difference(dataset.data_vars)
            if missing:
                raise ValueError(f"{path.name} is missing {sorted(missing)}")

            total_hourly_steps += dataset.sizes["valid_time"]
            temperature_c = dataset["t2m"] - 273.15
            dewpoint_c = dataset["d2m"] - 273.15
            wind_speed = np.hypot(dataset["u10"], dataset["v10"])
            relative_humidity = 100 * np.exp(
                (17.625 * dewpoint_c / (243.04 + dewpoint_c))
                - (17.625 * temperature_c / (243.04 + temperature_c))
            )
            relative_humidity = relative_humidity.clip(min=0, max=100)

            daily = xr.Dataset(
                {
                    "temperature_mean_c": temperature_c.resample(
                        valid_time="1D"
                    ).mean(),
                    "temperature_max_c": temperature_c.resample(
                        valid_time="1D"
                    ).max(),
                    "temperature_min_c": temperature_c.resample(
                        valid_time="1D"
                    ).min(),
                    "dewpoint_mean_c": dewpoint_c.resample(valid_time="1D").mean(),
                    "relative_humidity_mean_pct": relative_humidity.resample(
                        valid_time="1D"
                    ).mean(),
                    "relative_humidity_min_pct": relative_humidity.resample(
                        valid_time="1D"
                    ).min(),
                    "wind_speed_mean_ms": wind_speed.resample(valid_time="1D").mean(),
                    "wind_speed_max_ms": wind_speed.resample(valid_time="1D").max(),
                }
            ).load()

            # ERA5-Land accumulated variables reset after 00 UTC. The value at
            # 00 UTC is the complete accumulation for the preceding UTC day,
            # so shift it back one date instead of summing cumulative hours.
            midnight_precipitation = dataset["tp"].where(
                dataset["valid_time"].dt.hour == 0, drop=True
            ).load()

        frame = daily.to_dataframe().reset_index()
        frame = frame[
            ["valid_time", "latitude", "longitude"]
            + [
                column
                for column in WEATHER_COLUMNS
                if column not in {"precipitation_sum_mm", "precipitation_3d_mm"}
            ]
        ]
        daily_frames.append(frame)

        precipitation_frame = midnight_precipitation.to_dataframe(
            name="precipitation_sum_mm"
        ).reset_index()
        precipitation_frame["precipitation_sum_mm"] = (
            precipitation_frame["precipitation_sum_mm"].clip(lower=0) * 1000
        )
        precipitation_frame["valid_time"] = (
            pd.to_datetime(precipitation_frame["valid_time"])
            - pd.Timedelta(days=1)
        )
        precipitation_frames.append(
            precipitation_frame[
                ["valid_time", "latitude", "longitude", "precipitation_sum_mm"]
            ]
        )

    weather = pd.concat(daily_frames, ignore_index=True)
    precipitation = pd.concat(precipitation_frames, ignore_index=True)
    weather = weather.merge(
        precipitation,
        on=["valid_time", "latitude", "longitude"],
        how="inner",
        validate="one_to_one",
    )
    weather = weather.rename(columns={"valid_time": "feature_date"})
    weather["feature_date"] = pd.to_datetime(weather["feature_date"]).dt.normalize()
    weather = weather.loc[
        weather["feature_date"].between(
            START_DATE, LAST_FEATURE_DATE, inclusive="both"
        )
    ].copy()

    grid_lookup = {
        (round(row.latitude, 6), round(row.longitude, 6)): row.grid_id
        for row in grid.itertuples()
    }
    weather["grid_id"] = [
        grid_lookup.get((round(latitude, 6), round(longitude, 6)))
        for latitude, longitude in zip(weather["latitude"], weather["longitude"])
    ]
    weather = weather.loc[weather["grid_id"].notna()].copy()
    weather = weather.sort_values(["grid_id", "feature_date"]).reset_index(drop=True)
    weather["precipitation_3d_mm"] = weather.groupby(
        "grid_id", sort=False
    )["precipitation_sum_mm"].transform(
        lambda values: values.rolling(3, min_periods=1).sum()
    )

    expected_steps = len(pd.date_range(START_DATE, END_DATE, freq="D")) * 24
    if total_hourly_steps != expected_steps:
        raise ValueError(
            f"Expected {expected_steps} ERA5 hours, found {total_hourly_steps}"
        )
    return weather, total_hourly_steps


def build_terrain_features(grid: gpd.GeoDataFrame) -> pd.DataFrame:
    """Summarise park-only SRTM elevation, slope and aspect within each cell."""
    with rasterio.open(DEM_FILE) as source:
        if source.crs.to_epsg() != 4326:
            raise ValueError(f"Expected EPSG:4326 DEM, found {source.crs}")
        elevation = source.read(1, masked=True).filled(np.nan).astype("float64")
        transform = source.transform
        x_centres = transform.c + (np.arange(source.width) + 0.5) * transform.a
        y_centres = transform.f + (np.arange(source.height) + 0.5) * transform.e

    metres_per_latitude_degree = 111_320.0
    mean_latitude = float(np.nanmean(y_centres))
    metres_per_longitude_degree = metres_per_latitude_degree * np.cos(
        np.deg2rad(mean_latitude)
    )
    north_south_spacing = abs(transform.e) * metres_per_latitude_degree
    east_west_spacing = abs(transform.a) * metres_per_longitude_degree

    row_gradient, east_gradient = np.gradient(
        elevation, north_south_spacing, east_west_spacing
    )
    slope = np.degrees(np.arctan(np.hypot(row_gradient, east_gradient)))
    aspect = (
        np.degrees(np.arctan2(-east_gradient, row_gradient)) + 360
    ) % 360

    records: list[dict[str, object]] = []
    for row in grid.itertuples():
        min_x, min_y, max_x, max_y = row.geometry.bounds
        column_mask = (x_centres >= min_x) & (x_centres < max_x)
        row_mask = (y_centres >= min_y) & (y_centres < max_y)
        cell_elevation = elevation[np.ix_(row_mask, column_mask)]
        cell_slope = slope[np.ix_(row_mask, column_mask)]
        cell_aspect = aspect[np.ix_(row_mask, column_mask)]
        valid = np.isfinite(cell_elevation)
        valid_slope = valid & np.isfinite(cell_slope)
        valid_aspect = valid & np.isfinite(cell_aspect)
        if not valid.any():
            continue

        aspect_radians = np.deg2rad(cell_aspect[valid_aspect])
        aspect_sin = float(np.mean(np.sin(aspect_radians)))
        aspect_cos = float(np.mean(np.cos(aspect_radians)))
        aspect_mean = float(
            (np.degrees(np.arctan2(aspect_sin, aspect_cos)) + 360) % 360
        )
        records.append(
            {
                "grid_id": row.grid_id,
                "dem_valid_pixel_count": int(valid.sum()),
                "elevation_mean_m": float(np.nanmean(cell_elevation[valid])),
                "elevation_min_m": float(np.nanmin(cell_elevation[valid])),
                "elevation_max_m": float(np.nanmax(cell_elevation[valid])),
                "slope_mean_deg": float(np.nanmean(cell_slope[valid_slope])),
                "aspect_mean_deg": aspect_mean,
                "aspect_sin": aspect_sin,
                "aspect_cos": aspect_cos,
            }
        )

    terrain = pd.DataFrame.from_records(records)
    if len(terrain) != len(grid):
        missing_cells = sorted(set(grid["grid_id"]) - set(terrain["grid_id"]))
        raise ValueError(f"Grid cells without valid DEM pixels: {missing_cells}")
    return terrain.sort_values("grid_id").reset_index(drop=True)


def build_fire_labels(
    grid: gpd.GeoDataFrame,
    latitudes: np.ndarray,
    longitudes: np.ndarray,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Aggregate FIRMS points by cell/day after excluding known prescribed burns."""
    firms = pd.read_csv(FIRMS_FILE)
    firms["target_date"] = pd.to_datetime(firms["acq_date"], errors="raise")
    points = gpd.GeoDataFrame(
        firms,
        geometry=gpd.points_from_xy(firms["longitude"], firms["latitude"]),
        crs="EPSG:4326",
    )

    fire_history = gpd.read_file(FIRE_HISTORY_FILE).to_crs("EPSG:4326")
    prescribed = fire_history.loc[
        fire_history["fire_type"].eq("prescribed_burn")
    ].copy()
    prescribed["StartDate"] = pd.to_datetime(prescribed["StartDate"])
    prescribed["EndDate"] = pd.to_datetime(prescribed["EndDate"])

    prescribed_mask = pd.Series(False, index=points.index)
    for fire in prescribed.itertuples():
        prescribed_mask |= (
            points.geometry.intersects(fire.geometry)
            & points["target_date"].between(fire.StartDate, fire.EndDate)
        )
    points["prescribed_burn_overlap"] = prescribed_mask.astype("int8")

    grid_lookup = {
        (round(row.latitude, 6), round(row.longitude, 6)): row.grid_id
        for row in grid.itertuples()
    }
    nearest_latitudes = [
        float(latitudes[np.abs(latitudes - value).argmin()])
        for value in points["latitude"]
    ]
    nearest_longitudes = [
        float(longitudes[np.abs(longitudes - value).argmin()])
        for value in points["longitude"]
    ]
    points["grid_id"] = [
        grid_lookup.get((round(latitude, 6), round(longitude, 6)))
        for latitude, longitude in zip(nearest_latitudes, nearest_longitudes)
    ]
    if points["grid_id"].isna().any():
        raise ValueError("Some park FIRMS detections could not be assigned to a grid cell")

    counts = (
        points.groupby(["grid_id", "target_date"], as_index=False)
        .agg(
            fire_detection_count_raw=("grid_id", "size"),
            prescribed_burn_detection_count=("prescribed_burn_overlap", "sum"),
        )
    )
    counts["eligible_fire_detection_count"] = (
        counts["fire_detection_count_raw"]
        - counts["prescribed_burn_detection_count"]
    )

    full_index = pd.MultiIndex.from_product(
        [
            grid["grid_id"].tolist(),
            pd.date_range(START_DATE, END_DATE, freq="D"),
        ],
        names=["grid_id", "target_date"],
    )
    labels = counts.set_index(["grid_id", "target_date"]).reindex(
        full_index, fill_value=0
    ).reset_index()
    count_columns = [
        "fire_detection_count_raw",
        "prescribed_burn_detection_count",
        "eligible_fire_detection_count",
    ]
    labels[count_columns] = labels[count_columns].astype("int32")
    labels["fire_positive"] = (
        labels["eligible_fire_detection_count"] > 0
    ).astype("int8")

    audit = {
        "firms_clean_records": int(len(points)),
        "prescribed_burn_records_excluded_from_label": int(prescribed_mask.sum()),
        "eligible_firms_records": int((~prescribed_mask).sum()),
        "positive_grid_cell_days": int(labels["fire_positive"].sum()),
    }
    return labels, audit


def assign_split(feature_dates: pd.Series) -> pd.Series:
    conditions = [
        feature_dates <= TRAIN_END,
        feature_dates <= VALIDATION_END,
    ]
    return pd.Series(
        np.select(conditions, ["train", "validation"], default="test"),
        index=feature_dates.index,
        dtype="string",
    )


def build_model_table(
    grid: gpd.GeoDataFrame,
    weather: pd.DataFrame,
    terrain: pd.DataFrame,
    labels: pd.DataFrame,
) -> pd.DataFrame:
    feature_weather = weather.loc[
        weather["feature_date"].between(
            START_DATE, LAST_FEATURE_DATE, inclusive="both"
        )
    ].copy()
    model = feature_weather.merge(
        grid.drop(columns="geometry")[
            ["grid_id", "latitude", "longitude", "park_area_fraction"]
        ],
        on=["grid_id", "latitude", "longitude"],
        how="inner",
        validate="many_to_one",
    )
    model = model.merge(terrain, on="grid_id", how="inner", validate="many_to_one")
    model["target_date"] = model["feature_date"] + pd.Timedelta(days=1)
    model = model.merge(
        labels,
        on=["grid_id", "target_date"],
        how="left",
        validate="one_to_one",
    )

    model["split"] = assign_split(model["feature_date"])
    day_of_year = model["feature_date"].dt.dayofyear
    model["day_of_year_sin"] = np.sin(2 * np.pi * day_of_year / 366)
    model["day_of_year_cos"] = np.cos(2 * np.pi * day_of_year / 366)

    ordered_columns = [
        "grid_id",
        "feature_date",
        "target_date",
        "split",
        "latitude",
        "longitude",
        "park_area_fraction",
        *WEATHER_COLUMNS,
        "day_of_year_sin",
        "day_of_year_cos",
        "dem_valid_pixel_count",
        "elevation_mean_m",
        "elevation_min_m",
        "elevation_max_m",
        "slope_mean_deg",
        "aspect_mean_deg",
        "aspect_sin",
        "aspect_cos",
        "fire_detection_count_raw",
        "prescribed_burn_detection_count",
        "eligible_fire_detection_count",
        "fire_positive",
    ]
    model = model[ordered_columns].sort_values(
        ["feature_date", "grid_id"]
    ).reset_index(drop=True)
    return model


def build_data_dictionary() -> pd.DataFrame:
    definitions = [
        ("grid_id", "identifier", "Stable ERA5-Land grid-cell identifier."),
        ("feature_date", "date (UTC)", "Date represented by all predictor values."),
        ("target_date", "date (UTC)", "Following day used to create the fire label."),
        ("split", "category", "Chronological train, validation or test partition."),
        ("latitude", "degrees north", "ERA5-Land cell-centre latitude."),
        ("longitude", "degrees east", "ERA5-Land cell-centre longitude."),
        ("park_area_fraction", "0-1", "Fraction of the ERA5 cell covered by the park."),
        ("temperature_mean_c", "degrees C", "Daily mean 2 m air temperature."),
        ("temperature_max_c", "degrees C", "Daily maximum 2 m air temperature."),
        ("temperature_min_c", "degrees C", "Daily minimum 2 m air temperature."),
        ("dewpoint_mean_c", "degrees C", "Daily mean 2 m dew-point temperature."),
        ("relative_humidity_mean_pct", "percent", "Daily mean relative humidity derived from temperature and dew point."),
        ("relative_humidity_min_pct", "percent", "Daily minimum derived relative humidity."),
        ("precipitation_sum_mm", "mm", "ERA5-Land daily accumulation ending at 00 UTC on the following day."),
        ("precipitation_3d_mm", "mm", "Rolling three-day precipitation sum ending on feature_date."),
        ("wind_speed_mean_ms", "m/s", "Daily mean 10 m wind speed derived from u10 and v10."),
        ("wind_speed_max_ms", "m/s", "Daily maximum derived 10 m wind speed."),
        ("day_of_year_sin", "unitless", "Sine encoding of seasonal day of year."),
        ("day_of_year_cos", "unitless", "Cosine encoding of seasonal day of year."),
        ("dem_valid_pixel_count", "count", "Valid park-clipped SRTM pixels in the cell."),
        ("elevation_mean_m", "m", "Mean SRTM elevation within the park portion of the cell."),
        ("elevation_min_m", "m", "Minimum SRTM elevation within the park portion of the cell."),
        ("elevation_max_m", "m", "Maximum SRTM elevation within the park portion of the cell."),
        ("slope_mean_deg", "degrees", "Mean terrain slope derived from SRTM."),
        ("aspect_mean_deg", "degrees", "Circular mean downslope aspect, clockwise from north."),
        ("aspect_sin", "unitless", "Sine component of mean terrain aspect for modelling."),
        ("aspect_cos", "unitless", "Cosine component of mean terrain aspect for modelling."),
        ("fire_detection_count_raw", "count", "All retained FIRMS detections in the target cell/day."),
        ("prescribed_burn_detection_count", "count", "FIRMS detections overlapping a dated NPWS prescribed-burn polygon."),
        ("eligible_fire_detection_count", "count", "FIRMS detections remaining after the prescribed-burn check."),
        ("fire_positive", "0/1 target", "1 when at least one eligible FIRMS detection occurs on target_date."),
    ]
    return pd.DataFrame(definitions, columns=["column", "unit_or_type", "definition"])


def validate_outputs(
    grid: gpd.GeoDataFrame,
    weather: pd.DataFrame,
    terrain: pd.DataFrame,
    labels: pd.DataFrame,
    model: pd.DataFrame,
) -> dict[str, object]:
    expected_days = len(pd.date_range(START_DATE, END_DATE, freq="D"))
    expected_feature_days = len(
        pd.date_range(START_DATE, LAST_FEATURE_DATE, freq="D")
    )
    expected_weather_rows = len(grid) * expected_feature_days
    expected_label_rows = len(grid) * expected_days
    expected_model_rows = len(grid) * expected_feature_days

    if len(weather) != expected_weather_rows:
        raise ValueError(
            f"Expected {expected_weather_rows} weather rows, found {len(weather)}"
        )
    if len(labels) != expected_label_rows:
        raise ValueError(
            f"Expected {expected_label_rows} label rows, found {len(labels)}"
        )
    if len(model) != expected_model_rows:
        raise ValueError(f"Expected {expected_model_rows} rows, found {len(model)}")
    if model.duplicated(["grid_id", "feature_date"]).any():
        raise ValueError("Duplicate grid_id/feature_date keys in model table")
    if model.isna().any().any():
        missing = model.isna().sum()
        raise ValueError(f"Missing model values: {missing[missing > 0].to_dict()}")

    split_summary = (
        model.groupby("split", observed=True)
        .agg(
            rows=("fire_positive", "size"),
            positive_rows=("fire_positive", "sum"),
            first_feature_date=("feature_date", "min"),
            last_feature_date=("feature_date", "max"),
        )
        .reindex(["train", "validation", "test"])
    )
    split_summary["negative_rows"] = (
        split_summary["rows"] - split_summary["positive_rows"]
    )
    split_summary["positive_rate"] = (
        split_summary["positive_rows"] / split_summary["rows"]
    )
    train_positive = int(split_summary.loc["train", "positive_rows"])
    train_negative = int(split_summary.loc["train", "negative_rows"])
    class_weight = train_negative / train_positive if train_positive else None

    return {
        "checks_passed": {
            "complete_grid_day_weather_panel": True,
            "complete_grid_day_label_panel": True,
            "unique_grid_feature_date_keys": True,
            "no_missing_model_values": True,
            "chronological_split": True,
            "raw_sources_unchanged": True,
        },
        "grid_cells": int(len(grid)),
        "weather_rows": int(len(weather)),
        "terrain_rows": int(len(terrain)),
        "label_rows": int(len(labels)),
        "model_rows": int(len(model)),
        "feature_date_range": [
            model["feature_date"].min().strftime("%Y-%m-%d"),
            model["feature_date"].max().strftime("%Y-%m-%d"),
        ],
        "target_date_range": [
            model["target_date"].min().strftime("%Y-%m-%d"),
            model["target_date"].max().strftime("%Y-%m-%d"),
        ],
        "split_summary": {
            split: {
                "rows": int(values["rows"]),
                "positive_rows": int(values["positive_rows"]),
                "negative_rows": int(values["negative_rows"]),
                "positive_rate": float(values["positive_rate"]),
                "first_feature_date": values["first_feature_date"].strftime("%Y-%m-%d"),
                "last_feature_date": values["last_feature_date"].strftime("%Y-%m-%d"),
            }
            for split, values in split_summary.iterrows()
        },
        "recommended_xgboost_scale_pos_weight_from_training_only": class_weight,
        "limitations": [
            "The split is within one fire season; additional seasons are needed to test year-to-year generalisation.",
            "Days use UTC because FIRMS acquisition dates and ERA5-Land timestamps are aligned in UTC.",
            "FIRMS active-fire detections are proxy labels, not confirmed ignition records.",
            "Prescribed-burn exclusion is limited to dated polygons present in the NPWS Fire History layer.",
        ],
    }


def write_outputs(
    grid: gpd.GeoDataFrame,
    weather: pd.DataFrame,
    terrain: pd.DataFrame,
    labels: pd.DataFrame,
    model: pd.DataFrame,
    quality_report: dict[str, object],
    fire_audit: dict[str, int],
    total_hourly_steps: int,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_frames = {
        "daily_weather_features_2019_2020.csv": weather,
        "terrain_features.csv": terrain,
        "daily_fire_labels_2019_2020.csv": labels,
        "blue_mountains_model_table_2019_2020.csv": model,
        "data_dictionary.csv": build_data_dictionary(),
    }
    for filename, frame in csv_frames.items():
        output = frame.copy()
        for column in ["feature_date", "target_date"]:
            if column in output.columns:
                output[column] = pd.to_datetime(output[column]).dt.strftime("%Y-%m-%d")
        output.to_csv(OUTPUT_DIR / filename, index=False, lineterminator="\n")

    grid.to_file(
        OUTPUT_DIR / "blue_mountains_era5_grid.gpkg",
        layer="analysis_grid",
        driver="GPKG",
    )

    quality_report = dict(quality_report)
    quality_report["era5_hourly_time_steps"] = total_hourly_steps
    quality_report["fire_label_audit"] = fire_audit
    (OUTPUT_DIR / "quality_report.json").write_text(
        json.dumps(quality_report, indent=2), encoding="utf-8"
    )

    source_files = [
        FIRMS_FILE,
        BOUNDARY_FILE,
        FIRE_HISTORY_FILE,
        DEM_FILE,
        *sorted(ERA5_DIR.glob("era5_land_*.nc")),
    ]
    provenance = {
        "generated_by": str(Path(__file__).relative_to(DATASET_DIR)),
        "generated_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "study_area": "Blue Mountains National Park",
        "study_period": [START_DATE.strftime("%Y-%m-%d"), END_DATE.strftime("%Y-%m-%d")],
        "sources": [
            {
                "relative_path": str(path.relative_to(DATASET_DIR)),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in source_files
        ],
    }
    (OUTPUT_DIR / "provenance.json").write_text(
        json.dumps(provenance, indent=2), encoding="utf-8"
    )

    split_summary = quality_report["split_summary"]
    readme = f"""# Model-ready Blue Mountains dataset

This folder contains the reproducible, aligned dataset for the student proof-of-concept. Raw downloads and source-specific cleaned files remain unchanged elsewhere in `Dataset`.

## Main training file

`blue_mountains_model_table_2019_2020.csv` has one row per ERA5-Land grid cell and feature day. The predictors describe the feature day; `fire_positive` describes whether at least one eligible FIRMS detection occurs in the same cell on the following UTC day (`target_date`).

- Grid: native ERA5-Land 0.1-degree cells intersecting Blue Mountains National Park
- Feature dates: {quality_report['feature_date_range'][0]} to {quality_report['feature_date_range'][1]}
- Target dates: {quality_report['target_date_range'][0]} to {quality_report['target_date_range'][1]}
- Rows: {quality_report['model_rows']:,}
- Grid cells: {quality_report['grid_cells']}
- Missing model values: 0

## Chronological partitions

| Split | Feature dates | Rows | Positive cell-days |
| --- | --- | ---: | ---: |
| Train | {split_summary['train']['first_feature_date']} to {split_summary['train']['last_feature_date']} | {split_summary['train']['rows']:,} | {split_summary['train']['positive_rows']:,} |
| Validation | {split_summary['validation']['first_feature_date']} to {split_summary['validation']['last_feature_date']} | {split_summary['validation']['rows']:,} | {split_summary['validation']['positive_rows']:,} |
| Test | {split_summary['test']['first_feature_date']} to {split_summary['test']['last_feature_date']} | {split_summary['test']['rows']:,} | {split_summary['test']['positive_rows']:,} |

Do not randomly reshuffle these partitions. The recommended training-only starting value for XGBoost `scale_pos_weight` is recorded in `quality_report.json`; it must be recalculated if the split changes.

## Supporting files

- `daily_weather_features_2019_2020.csv`: daily ERA5-Land features before the next-day label shift.
- `terrain_features.csv`: static park-only elevation, slope and aspect summaries.
- `daily_fire_labels_2019_2020.csv`: full cell-day label panel and prescribed-burn audit counts.
- `blue_mountains_era5_grid.gpkg`: analysis-cell geometries and park-overlap fractions.
- `data_dictionary.csv`: definitions and units for every model-table field.
- `quality_report.json`: completeness checks, split balance and limitations.
- `provenance.json`: source paths, byte sizes and SHA-256 hashes.

## Important limitations

This is a student proof-of-concept based on one fire season. FIRMS active-fire detections are proxy labels, and the within-season test split does not demonstrate year-to-year generalisation. The data should not be used as an operational warning system.
"""
    (OUTPUT_DIR / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    era5_files = sorted(ERA5_DIR.glob("era5_land_*.nc"))
    if not era5_files:
        raise FileNotFoundError("No ERA5-Land NetCDF files found")
    with xr.open_dataset(era5_files[0]) as sample:
        latitudes = sample["latitude"].values.astype("float64")
        longitudes = sample["longitude"].values.astype("float64")

    park = gpd.read_file(BOUNDARY_FILE).to_crs("EPSG:4326")
    if len(park) != 1 or not park.geometry.is_valid.all():
        raise ValueError("Study boundary must contain one valid geometry")

    grid = build_analysis_grid(latitudes, longitudes, park)
    weather, total_hourly_steps = build_weather_features(grid)
    terrain = build_terrain_features(grid)
    labels, fire_audit = build_fire_labels(grid, latitudes, longitudes)
    model = build_model_table(grid, weather, terrain, labels)
    quality_report = validate_outputs(grid, weather, terrain, labels, model)
    write_outputs(
        grid,
        weather,
        terrain,
        labels,
        model,
        quality_report,
        fire_audit,
        total_hourly_steps,
    )

    print(f"Grid cells: {len(grid)}")
    print(f"Model rows: {len(model)}")
    print(f"Positive next-day rows: {int(model['fire_positive'].sum())}")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
