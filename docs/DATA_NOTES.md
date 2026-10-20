# Data provenance and reproducibility scope

The source delivery includes prepared grid-day tables, daily labels/weather, terrain summaries, a weather-grid GeoPackage, a park-boundary GeoJSON, July 2019 ERA5-Land NetCDF, processing scripts, a source register and checksums. These are retained with their original relative paths so the modelling code works after cloning.

The source register identifies NASA FIRMS VIIRS detections, Copernicus ERA5-Land, Geoscience Australia SRTM and NSW NPWS boundary/fire-history data. Authoritative links and source metadata are in `inputs/dataset/blue_mountains_2019_2020/metadata/data_register.csv` and `inputs/dataset/blue_mountains_2019_2020/model_ready/provenance.json`.

## How the source datasets become model rows

The native ERA5-Land 0.1-degree grid is the common spatial unit. The NPWS estate boundary defines Blue Mountains National Park and supplies each cell's park-overlap fraction. ERA5-Land hourly temperature, dew point, precipitation and wind components are aggregated to feature-day weather and rainfall variables. Park-clipped SRTM pixels are summarised by cell to produce static elevation, slope and aspect features.

FIRMS detections are cleaned, deduplicated and assigned to the same grid. The NPWS Fire History layer is used to flag detections that overlap dated prescribed-burn polygons; those detections remain available for audit but are removed from the eligible label. For each feature date, the target is whether an eligible detection occurs in the same cell on the following UTC day. Feature-day detections also supply the three recent-fire predictors in the full model.

The resulting 39-column extended table has 18,980 rows for 52 cells and 365 feature dates. The modelling code then applies `park_area_fraction >= 0.1`, retaining 15,695 rows, 43 cells and 566 positive targets. It uses 23 predictors for the full model and 20 for the conditions-only comparison. Dates, identifiers, coordinates, detection-count audit fields, `park_area_fraction`, the target and the original `split` field are excluded from predictors. The ML code regenerates purged temporal partitions after filtering instead of using the CSV split column.

`inputs/dataset/blue_mountains_2019_2020/model_ready/quality_report.json` records the verified counts and checks. `output/feature_contract.json` records the exact predictor lists, and `inputs/dataset/blue_mountains_2019_2020/model_ready/provenance.json` records the source and derived-table lineage.

The dataset folder has an English name in this group repository. The original relative paths inside its provenance records are retained; file contents and the numerical modelling inputs are unchanged by the folder rename.

The original delivery is a modelling input subset. It omits the full FIRMS downloads, DEM raster, fire-history GIS files and eleven monthly weather files referenced by the original provenance. Retained historical provenance describes those original inputs; it is not a claim that every referenced file is present here. The acquisition/GIS scripts are preserved for provenance and require additional upstream inputs and dependencies to rerun.

The included data support checking the extended feature table, reproducing ML experiments and generating saved-model scores. The July NetCDF supports the initial rainfall-history audit. The complete raw GIS pipeline has not been rerun during repository preparation.

Upstream data retain their source attribution and applicable provider terms. A project code licence has not been assigned. No credentials are included; the ERA5 download script expects the user to configure their own CDS account locally.
