# Data methods contribution

Owner: Jin. The wording below was checked against the retained source data and the reproducible final audit on 25 October 2026.

The native ERA5-Land 0.1-degree grid provides the common spatial unit. The NPWS estate boundary defines Blue Mountains National Park and supplies the fraction of each weather cell within the park. ERA5-Land hourly temperature, dew point, precipitation and wind components are aggregated into feature-day weather and rainfall summaries. Park-clipped SRTM terrain supplies elevation, slope and aspect features.

FIRMS detections are cleaned, deduplicated and assigned to grid cells. Detections overlapping dated prescribed-burn polygons from NPWS Fire History are retained for audit but excluded from eligible labels. The prediction target is eligible detection in the same park cell on the following UTC day. Feature-day labels supply the recent-fire predictors. This target includes continuing fire and is not a confirmed ignition record.

The extended panel contains 18,980 cell-days and 39 columns. Filtering cells to at least 10% park overlap retains 43 cells, 15,695 rows and 566 positive targets. The source weather describes the full weather cell; terrain and fire labels describe its park portion. The data contribution supplies the prepared panel and provenance; the ML implementation defines its own evaluation partitions rather than fitting to the CSV's original split.

## Processing and attribution details

| Detail | Evidence and final wording |
| --- | --- |
| Official datasets, versions, access dates and licences | Sources accessed 7 October 2026: NSW NPWS Estate and NPWS Fire History (Creative Commons Attribution), GA SRTM-derived 1 Second DEM Version 1.0 through the official WCS (CC BY 4.0), NASA FIRMS S-NPP VIIRS Collection 2 archive (NASA open-data/citation terms), and ERA5-Land hourly data (CC-BY; DOI `10.24381/cds.e2161bac`). Links and local locations are in the [source register](../../inputs/dataset/blue_mountains_2019_2020/metadata/data_register.csv). |
| FIRMS sensor, confidence/type selection and duplicate rules | The S-NPP VIIRS 375 m archive was restricted to 2019-07-01 through 2020-06-30, normal (`n`) or high (`h`) confidence and points intersecting the park boundary. Required fields were checked, and identical whole rows were dropped before stable date/time/location sorting. The audit reproduced 17,290 clean records and found zero duplicates removed. |
| Prescribed-burn spatial/date matching | A detection was marked prescribed when its point intersected an NPWS polygon labelled prescribed burn and its UTC date fell inclusively between that polygon's start and end dates. One supplied polygon excluded 18 detections from eligible labels. This only covers the dated polygons present in the supplied NPWS layer and is not proof that every planned burn was removed. |
| CRS, area fractions, clipping and terrain summaries | Source vectors were transformed to EPSG:4326. ERA5 cells were projected to Australian Albers (EPSG:3577) for area intersection; 52 cells had positive park overlap and 43 met the main 10% filter. Four EPSG:4326 SRTM WCS tiles were mosaicked and clipped to the park. Elevation mean/minimum/maximum, mean slope and circular aspect components were calculated from valid park pixels within each cell. |
| Weather units, humidity/wind derivation and precipitation timing | Hourly ERA5-Land temperature/dew point were converted from K to degrees C. Relative humidity was derived from temperature and dew point; wind speed from `sqrt(u10^2 + v10^2)`. Daily UTC mean/extreme summaries were used. ERA5-Land total precipitation at 00 UTC represents the preceding day's completed accumulation, so it was shifted back one date, clipped at zero and converted from m to mm before causal rolling totals were constructed. |
| Missingness, grid/date uniqueness and reconstruction checks | The 12 monthly files contain 8,784 continuous hourly timestamps and no missing values in `t2m`, `d2m`, `tp`, `u10` or `v10`. Cell/date keys, daily completeness, label arithmetic, target shift, source hashes and the final training-input hash all pass the [final audit](FINAL_DATA_AUDIT.md). The cleaned FIRMS table and daily label panel were exactly reconstructed. |

## Limits to retain

The panel covers one season. Satellite no-detection is not proof of no fire or complete observation. Prescribed-burn exclusion is limited to the supplied dated polygons. Early rainfall history is incomplete, coarse cells aggregate varied terrain and direct fuel measurements are absent. Raw downloads are retained outside this Git repository; the repository contains the prepared panel, hashes and audit records.

Kian has confirmed that the data/ML interface matches the current implementation. Chris should integrate this wording while retaining the stated limitations and source attribution. The version and review are recorded in [CONTRIBUTIONS.md](../CONTRIBUTIONS.md).
