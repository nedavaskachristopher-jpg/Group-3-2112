"""Create the model-ready FIRMS fire-detection table for 2019-20.

The official FIRMS archive remains unchanged. This script removes records that
are outside the study period, outside Blue Mountains National Park, or marked
low confidence, then writes a flat CSV for modelling.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd


DATASET_DIR = Path(__file__).resolve().parents[1]
SOURCE = (
    DATASET_DIR
    / "DL_FIRE_SV-C2_818385"
    / "fire_archive_SV-C2_818385.csv"
)
BOUNDARY = DATASET_DIR / "processed" / "blue_mountains_national_park_boundary.gpkg"
OUTPUT = DATASET_DIR / "processed" / "blue_mountains_np_firms_2019_2020_clean.csv"

START_DATE = pd.Timestamp("2019-07-01")
END_DATE = pd.Timestamp("2020-06-30")
RETAINED_CONFIDENCE = {"n", "h"}
REQUIRED_COLUMNS = {
    "latitude",
    "longitude",
    "acq_date",
    "acq_time",
    "satellite",
    "instrument",
    "confidence",
    "frp",
}


def main() -> None:
    detections = pd.read_csv(SOURCE)
    missing_columns = REQUIRED_COLUMNS.difference(detections.columns)
    if missing_columns:
        raise ValueError(f"Missing FIRMS columns: {sorted(missing_columns)}")

    if detections[list(REQUIRED_COLUMNS)].isna().any().any():
        raise ValueError("Required FIRMS fields contain missing values")
    if not detections["latitude"].between(-90, 90).all():
        raise ValueError("Invalid latitude values")
    if not detections["longitude"].between(-180, 180).all():
        raise ValueError("Invalid longitude values")

    detections["acq_date"] = pd.to_datetime(detections["acq_date"], errors="raise")
    period_mask = detections["acq_date"].between(START_DATE, END_DATE, inclusive="both")
    confidence_mask = detections["confidence"].isin(RETAINED_CONFIDENCE)

    park = gpd.read_file(BOUNDARY).to_crs("EPSG:4326")
    if len(park) != 1 or not park.geometry.is_valid.all():
        raise ValueError("Study boundary is missing or invalid")

    points = gpd.GeoSeries(
        gpd.points_from_xy(detections["longitude"], detections["latitude"]),
        crs="EPSG:4326",
    )
    park_mask = points.intersects(park.geometry.iloc[0])

    clean = detections.loc[period_mask & confidence_mask & park_mask].copy()
    clean["acq_date"] = clean["acq_date"].dt.strftime("%Y-%m-%d")
    clean = clean.drop_duplicates().sort_values(
        ["acq_date", "acq_time", "latitude", "longitude"],
        kind="stable",
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(OUTPUT, index=False, lineterminator="\n")

    print(f"Source rows: {len(detections)}")
    print(f"Removed outside study period: {(~period_mask).sum()}")
    print(f"Removed low-confidence records in study period: {(period_mask & ~confidence_mask).sum()}")
    print(
        "Removed outside park after date/confidence filters: "
        f"{(period_mask & confidence_mask & ~park_mask).sum()}"
    )
    print(f"Model-ready rows: {len(clean)}")
    print(f"Output: {OUTPUT}")


if __name__ == "__main__":
    main()
