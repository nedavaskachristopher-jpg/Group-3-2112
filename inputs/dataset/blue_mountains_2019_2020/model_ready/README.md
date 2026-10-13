# Model-ready Blue Mountains dataset

This folder contains the reproducible, aligned dataset for the student proof-of-concept. Raw downloads and source-specific cleaned files remain unchanged elsewhere in `Dataset`.

## Main training file

`blue_mountains_model_table_2019_2020.csv` has one row per ERA5-Land grid cell and feature day. The predictors describe the feature day; `fire_positive` describes whether at least one eligible FIRMS detection occurs in the same cell on the following UTC day (`target_date`).

- Grid: native ERA5-Land 0.1-degree cells intersecting Blue Mountains National Park
- Feature dates: 2019-07-01 to 2020-06-29
- Target dates: 2019-07-02 to 2020-06-30
- Rows: 18,980
- Grid cells: 52
- Missing model values: 0

## Chronological partitions

| Split | Feature dates | Rows | Positive cell-days |
| --- | --- | ---: | ---: |
| Train | 2019-07-01 to 2019-12-15 | 8,736 | 249 |
| Validation | 2019-12-16 to 2019-12-31 | 832 | 275 |
| Test | 2020-01-01 to 2020-06-29 | 9,412 | 54 |

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
