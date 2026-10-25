# Final feature catalogue

Ordered inputs are copied from the frozen seventeen-input model. The sixteen-input comparison omits only `fire_today`. Units follow the audited variable definitions.

| Order | Column | Group | Unit | Availability |
| --- | --- | --- | --- | --- |
| 1 | temperature_mean_c | Weather | degrees C | Full feature day or earlier |
| 2 | temperature_max_c | Weather | degrees C | Full feature day or earlier |
| 3 | temperature_min_c | Weather | degrees C | Full feature day or earlier |
| 4 | dewpoint_mean_c | Weather | degrees C | Full feature day or earlier |
| 5 | relative_humidity_mean_pct | Weather | % | Full feature day or earlier |
| 6 | relative_humidity_min_pct | Weather | % | Full feature day or earlier |
| 7 | precipitation_sum_mm | Rainfall | mm | Full feature day or earlier |
| 8 | precipitation_3d_mm | Rainfall | mm | Full feature day or earlier |
| 9 | wind_speed_mean_ms | Weather | m/s | Full feature day or earlier |
| 10 | wind_speed_max_ms | Weather | m/s | Full feature day or earlier |
| 11 | elevation_mean_m | Terrain | m | Static park terrain |
| 12 | elevation_min_m | Terrain | m | Static park terrain |
| 13 | elevation_max_m | Terrain | m | Static park terrain |
| 14 | slope_mean_deg | Terrain | degrees | Static park terrain |
| 15 | aspect_sin | Terrain | unitless | Static park terrain |
| 16 | aspect_cos | Terrain | unitless | Static park terrain |
| 17 | fire_today | Current detection | 0/1 | Full feature day or earlier |

`precipitation_3d_mm` includes the feature day and two earlier days. `fire_today` is the eligible same-UTC-day detection flag, not tomorrow's answer. Full-day retrospective availability is assumed; publication latency is not reproduced. Weather covers the grid cell, whereas terrain/fire data concern its park portion.

Excluded predictors include the label, target-day detection counts, dates, coordinates, grid ID and partition fields. Longer rainfall/dry-spell histories and other current-fire candidates were not approved for this frozen model. No NDVI or fuel-moisture imagery is present. See [model_matrix](../../research/bushfire_ml/data.py), [audit](../../research/reports/development_audit.md) and [final manifest](../../research/reports/final_freeze.json).
