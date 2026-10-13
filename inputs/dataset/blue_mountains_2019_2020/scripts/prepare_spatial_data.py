r"""Prepare the Blue Mountains study boundary, fire-history subset and DEM.

Run from the ENGG2112 workspace with:

    .venv\Scripts\python.exe "Group Project\Dataset\scripts\prepare_spatial_data.py"
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.mask import mask
from rasterio.merge import merge


DATASET_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = DATASET_DIR / "raw"
PROCESSED_DIR = DATASET_DIR / "processed"

BOUNDARY_SOURCE = (
    RAW_DIR / "boundary" / "tenure_npws_estate" / "NPWS_Estate.shp"
)
FIRE_HISTORY_SOURCE = (
    RAW_DIR
    / "fire_history"
    / "fire_npwsfirehistory"
    / "NPWSFireHistory.shp"
)

PARK_NAME = "Blue Mountains National Park"
START_DATE = "2019-07-01"
END_DATE = "2020-06-30"


def prepare_boundary() -> gpd.GeoDataFrame:
    estate = gpd.read_file(BOUNDARY_SOURCE)
    park = estate.loc[estate["NAME"].eq(PARK_NAME)].copy()
    if len(park) != 1:
        raise RuntimeError(f"Expected one {PARK_NAME!r} record, found {len(park)}")

    park = park.to_crs("EPSG:4326")
    park.geometry = park.geometry.make_valid()
    park.to_file(
        PROCESSED_DIR / "blue_mountains_national_park_boundary.geojson",
        driver="GeoJSON",
    )
    park.to_file(
        PROCESSED_DIR / "blue_mountains_national_park_boundary.gpkg",
        layer="study_boundary",
        driver="GPKG",
    )
    return park


def prepare_fire_history(park: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    history = gpd.read_file(FIRE_HISTORY_SOURCE, bbox=tuple(park.total_bounds))
    history = history.to_crs(park.crs)
    history["StartDate"] = pd.to_datetime(history["StartDate"], errors="coerce")
    history["EndDate"] = pd.to_datetime(history["EndDate"], errors="coerce")
    history = history.loc[
        history["StartDate"].between(START_DATE, END_DATE, inclusive="both")
    ].copy()
    history.geometry = history.geometry.make_valid()
    history = history.loc[history.geometry.intersects(park.geometry.iloc[0])].copy()
    history["fire_type"] = "unknown"
    history.loc[
        history["Label"].str.contains("Wildfire", case=False, na=False), "fire_type"
    ] = "wildfire"
    history.loc[
        history["Label"].str.contains("Prescribed", case=False, na=False),
        "fire_type",
    ] = "prescribed_burn"

    clipped = gpd.clip(history, park.geometry.iloc[0])
    clipped.to_file(
        PROCESSED_DIR / "blue_mountains_np_fire_history_2019_2020.gpkg",
        layer="fire_history",
        driver="GPKG",
    )
    return clipped


def prepare_dem(park: gpd.GeoDataFrame) -> Path:
    tile_paths = sorted((RAW_DIR / "dem").glob("blue_mountains_np_srtm_1sec_*.tif"))
    if len(tile_paths) != 4:
        raise RuntimeError(f"Expected four DEM tiles, found {len(tile_paths)}")

    sources = [rasterio.open(path) for path in tile_paths]
    try:
        mosaic, transform = merge(sources, resampling=rasterio.enums.Resampling.bilinear)
        profile = sources[0].profile.copy()
        profile.update(
            height=mosaic.shape[1],
            width=mosaic.shape[2],
            transform=transform,
            compress="deflate",
            predictor=3,
        )

        mosaic_path = PROCESSED_DIR / "blue_mountains_np_srtm_dem_mosaic.tif"
        with rasterio.open(mosaic_path, "w", **profile) as dst:
            dst.write(mosaic)

        with rasterio.open(mosaic_path) as src:
            clipped, clipped_transform = mask(
                src,
                park.geometry,
                crop=True,
                nodata=-9999.0,
                filled=True,
            )
            clipped_profile = src.profile.copy()
            clipped_profile.update(
                height=clipped.shape[1],
                width=clipped.shape[2],
                transform=clipped_transform,
                nodata=-9999.0,
                compress="deflate",
                predictor=3,
            )

        clipped_path = PROCESSED_DIR / "blue_mountains_np_srtm_dem_clipped.tif"
        with rasterio.open(clipped_path, "w", **clipped_profile) as dst:
            dst.write(clipped)
        # The full rectangular mosaic is only an intermediate used for masking.
        # Retain the clipped study-area raster and remove the reproducible temp file.
        mosaic_path.unlink(missing_ok=True)
        return clipped_path
    finally:
        for source in sources:
            source.close()


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    park = prepare_boundary()
    history = prepare_fire_history(park)
    dem_path = prepare_dem(park)
    print(f"Boundary: {tuple(round(value, 6) for value in park.total_bounds)}")
    print(f"Fire-history features: {len(history)}")
    print(f"DEM: {dem_path}")


if __name__ == "__main__":
    main()
