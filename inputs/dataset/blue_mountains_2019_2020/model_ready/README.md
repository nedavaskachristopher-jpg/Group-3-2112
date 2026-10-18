# Model-ready Blue Mountains dataset

This folder contains the aligned grid-day data used by the student proof-of-concept. The study area is Blue Mountains National Park and the study period is 1 July 2019 to 30 June 2020. These files support retrospective model development; they are not operational fire-warning data.

## Primary modelling table

The ML code uses `blue_mountains_model_table_2019_2020_extended.csv`. Each row represents one ERA5-Land grid cell on one feature day. `fire_positive` equals 1 when at least one eligible NASA FIRMS S-NPP VIIRS detection occurs in the same cell on the following UTC day. The target may represent a continuing fire and is not a confirmed new-ignition label.

| Item | Value |
| --- | ---: |
| Base table | 18,980 rows, 31 columns |
| Extended table | 18,980 rows, 39 columns |
| Full panel | 52 cells, 365 feature dates |
| Feature dates | 2019-07-01 to 2020-06-29 |
| Target dates | 2019-07-02 to 2020-06-30 |
| Missing extended-table values | 0 |

Before fitting, `park_area_fraction >= 0.10` is applied. The modelling subset contains 43 cells, 15,695 grid-cell-day rows and 566 positive targets.

## How the datasets are combined

| Source | Use in the pipeline |
| --- | --- |
| NASA FIRMS S-NPP VIIRS | Normal- and high-confidence active-fire detections are cleaned, deduplicated and assigned to grid cells. Eligible next-day detections form `fire_positive`; feature-day detections form recent-fire predictors. |
| NSW NPWS estate boundary | Defines the park, clips source data and supplies `park_area_fraction` for the 10% filter. |
| NSW NPWS Fire History | Flags detections that overlap dated prescribed-burn polygons. These detections remain in audit counts but are excluded from the eligible fire label. |
| ERA5-Land | Hourly temperature, dew point, precipitation and wind components are converted to daily weather summaries and causal rainfall-history features on the common 0.1-degree grid. |
| Geoscience Australia SRTM DEM | Park-clipped elevation pixels are summarised within each ERA5-Land cell to produce elevation, slope and aspect predictors. |

The sources are joined by ERA5-Land `grid_id` and UTC date. Static terrain values repeat across dates. Time-varying predictors use information available on or before `feature_date`; the label uses `target_date = feature_date + 1 day`.

## Feature and split contract

The full model uses 23 predictors: eight weather, six rainfall, six terrain and three recent-fire features. The conditions-only comparison uses the same 20 weather, rainfall and terrain features but omits `fire_today`, `fire_neighbour_today` and `fire_days_last_7`.

Identifiers, coordinates, dates, the original `split` field, `park_area_fraction`, target-day detection counts, audit fields and the target are excluded from the predictors. `output/feature_contract.json` records the exact lists.

`src/train_evaluate.py` regenerates purged temporal partitions after the park filter. It does not use the CSV's original `split` column for model fitting. The original split and its summary remain as data-engineering metadata only.

## Supporting records

- `blue_mountains_model_table_2019_2020.csv`: 31-column base table.
- `blue_mountains_model_table_2019_2020_extended.csv`: 39-column table used by the ML code.
- `daily_weather_features_2019_2020.csv`: daily ERA5-Land features.
- `terrain_features.csv`: static elevation, slope and aspect summaries.
- `daily_fire_labels_2019_2020.csv`: label panel and prescribed-burn audit counts.
- `blue_mountains_era5_grid.gpkg`: cell geometry and park-overlap fractions.
- `data_dictionary.csv`: definitions for the base table; extended-field definitions are in `output/feature_contract.json`.
- `quality_report.json`: base-pipeline checks, extended-table audit and modelling-subset checks.
- `provenance.json`: source hashes, derived-table lineage and repository-delivery scope.

## Limitations

- The panel covers one fire season and cannot establish year-to-year generalisation.
- FIRMS detections are satellite observations and proxy labels, not confirmed ignition records.
- Prescribed-burn exclusion is limited to dated polygons in the supplied NPWS layer.
- Early rainfall windows have partial pre-season history; `rain_history_days` records the available history.
- Recent-fire features can help identify continuing fires, so results should include the conditions-only comparison.
- The repository contains the prepared tables but only a documented subset of the original raw inputs. See `docs/DATA_NOTES.md` for the reproducibility boundary.
