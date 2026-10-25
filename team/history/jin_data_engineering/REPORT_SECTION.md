> Historical pre-integration record. Numerical claims and roles describe the legacy version; see the current team index.

# Data methods contribution

Owner: Jin. The opening text summarises the merged data notes and requires the owner's final source/processing review before report use.

The native ERA5-Land 0.1-degree grid provides the common spatial unit. The NPWS estate boundary defines Blue Mountains National Park and supplies the fraction of each weather cell within the park. ERA5-Land hourly temperature, dew point, precipitation and wind components are aggregated into feature-day weather and rainfall summaries. Park-clipped SRTM terrain supplies elevation, slope and aspect features.

FIRMS detections are cleaned, deduplicated and assigned to grid cells. Detections overlapping dated prescribed-burn polygons from NPWS Fire History are retained for audit but excluded from eligible labels. The prediction target is eligible detection in the same park cell on the following UTC day. Feature-day labels supply the recent-fire predictors. This target includes continuing fire and is not a confirmed ignition record.

The extended panel contains 18,980 cell-days and 39 columns. Filtering cells to at least 10% park overlap retains 43 cells, 15,695 rows and 566 positive targets. The source weather describes the full weather cell; terrain and fire labels describe its park portion. The data contribution supplies the prepared panel and provenance; the ML implementation defines its own evaluation partitions rather than fitting to the CSV's original split.

## Processing and attribution details to complete

| Detail | Evidence and final wording |
| --- | --- |
| Official datasets, versions, access dates and licences | To be completed from the source register and official records |
| FIRMS sensor, confidence/type selection and duplicate rules | To be completed from processing scripts and source definitions |
| Prescribed-burn spatial/date matching | To be completed; distinguish partial coverage from complete removal |
| CRS, area fractions, clipping and terrain summaries | To be completed with actual method details |
| Weather units, humidity/wind derivation and precipitation timing | To be completed with actual aggregation rules |
| Missingness, grid/date uniqueness and reconstruction checks | Link actual audit and reconstruction records |

## Limits to retain

The panel covers one season. Satellite no-detection is not proof of no fire. Prescribed-burn exclusion is limited to the supplied dated polygons. Early rainfall history is incomplete, coarse cells aggregate varied terrain and direct fuel measurements are absent. Source availability and omitted raw files must match the current provenance record.

Review this contribution with Kian, then hand the checked wording and citations to Chris. Record the version and review in [CONTRIBUTIONS.md](https://github.com/nedavaskachristopher-jpg/Group-3-2112/blob/legacy-ml-2026-10-25/team/CONTRIBUTIONS.md).
