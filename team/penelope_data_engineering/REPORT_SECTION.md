# Data report contribution

The integrated draft's data section describes the supplied source lineage,
native grid/day unit, park filter, target proxy and missing raw inputs. Read
[the draft](../../report/group_report.md) and [data notes](../../docs/DATA_NOTES.md).

The native ERA5-Land 0.1-degree grid is the common spatial unit. The NPWS
estate boundary defines Blue Mountains National Park and supplies each cell's
park-overlap fraction. ERA5-Land hourly temperature, dew point, precipitation
and wind components are aggregated into completed-UTC-day weather features.
Park-clipped SRTM elevation supplies terrain summaries. FIRMS VIIRS detections
are restricted to the study period, retained confidence classes and park
boundary, then deduplicated and assigned to grid cells. Detections intersecting
dated prescribed-burn polygons remain in audit counts but are excluded from the
eligible label. The target is an eligible detection in the same cell on the
following UTC day, not a confirmed ignition.

The wider source table contains 39 columns. The frozen full model selects 17
inputs; the conditions-only comparison selects the same contract without
`fire_today` and therefore uses 16. Dates, identifiers, coordinates, target-day
counts and the label are excluded from predictors.

The [final audit](FINAL_DATA_AUDIT.md) checks these details against the prepared
tables and retained source folder. It also records access/licence fields, label
and geometry checks, the 17/16-input interface and observation-coverage limits.
The full upstream GIS pipeline was not rerun, and Kian/Chris review of the
migrated report wording remains pending.
