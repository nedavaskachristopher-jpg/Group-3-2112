# Data provenance and reproducibility scope

The source delivery includes prepared grid-day tables, daily labels/weather, terrain summaries, a weather-grid GeoPackage, a park-boundary GeoJSON, July 2019 ERA5-Land NetCDF, processing scripts, a source register and checksums. These are retained with their original relative paths so the modelling code works after cloning.

The source register identifies NASA FIRMS VIIRS detections, Copernicus ERA5-Land, Geoscience Australia SRTM and NSW NPWS boundary/fire-history data. Authoritative links and source metadata are in `inputs/dataset/blue_mountains_2019_2020/metadata/data_register.csv` and `inputs/dataset/blue_mountains_2019_2020/model_ready/provenance.json`.

The dataset folder has an English name in this group repository. The original relative paths inside its provenance records are retained; file contents and the numerical modelling inputs are unchanged by the folder rename.

The original delivery is a modelling input subset. It omits the full FIRMS downloads, DEM raster, fire-history GIS files and eleven monthly weather files referenced by the original provenance. Retained historical provenance describes those original inputs; it is not a claim that every referenced file is present here. The acquisition/GIS scripts are preserved for provenance and require additional upstream inputs and dependencies to rerun.

The included data support checking the extended feature table, reproducing ML experiments and generating saved-model scores. The July NetCDF supports the initial rainfall-history audit. The complete raw GIS pipeline has not been rerun during repository preparation.

Upstream data retain their source attribution and applicable provider terms. A project code licence has not been assigned. No credentials are included; the ERA5 download script expects the user to configure their own CDS account locally.
