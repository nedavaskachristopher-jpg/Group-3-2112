"""Download monthly ERA5-Land files for the 2019-20 fire season.

Requires a free Copernicus Climate Data Store account, acceptance of the
ERA5-Land licence, and a valid ~/.cdsapirc API configuration.
"""

from __future__ import annotations

import calendar
from datetime import date
from pathlib import Path

import cdsapi


DATASET_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = DATASET_DIR / "raw" / "era5_land"

# CDS order: North, West, South, East. This is the National Park bounding box
# rounded outward to the ERA5-Land 0.1-degree grid.
AREA = [-33.3, 149.8, -34.4, 150.7]
START_MONTH = date(2019, 7, 1)
END_MONTH = date(2020, 6, 1)

VARIABLES = [
    "2m_temperature",
    "2m_dewpoint_temperature",
    "total_precipitation",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
]


def months_between(start: date, end: date):
    # Yield inclusive calendar months, rolling December into January of next year.
    current = start
    while current <= end:
        yield current.year, current.month
        current = date(
            current.year + (current.month == 12),
            1 if current.month == 12 else current.month + 1,
            1,
        )


def main() -> None:
    # Network stage: read credentials from the user's CDS setup, never source code.
    # This downloads raw monthly files; it does not prepare daily model features.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    client = cdsapi.Client()
    for year, month in months_between(START_MONTH, END_MONTH):
        target = OUTPUT_DIR / f"era5_land_{year}_{month:02d}.nc"
        # Nonempty-file skipping supports resuming, but is not a checksum or
        # completeness check. Downstream processing must validate downloaded data.
        if target.exists() and target.stat().st_size > 0:
            print(f"Skipping existing file: {target.name}")
            continue

        # Request every UTC hour, respecting each month's length and leap years.
        days = calendar.monthrange(year, month)[1]
        request = {
            "variable": VARIABLES,
            "year": [str(year)],
            "month": [f"{month:02d}"],
            "day": [f"{day:02d}" for day in range(1, days + 1)],
            "time": [f"{hour:02d}:00" for hour in range(24)],
            "data_format": "netcdf",
            "download_format": "unarchived",
            "area": AREA,
        }
        print(f"Requesting {year}-{month:02d}")
        client.retrieve("reanalysis-era5-land", request).download(str(target))


if __name__ == "__main__":
    main()
