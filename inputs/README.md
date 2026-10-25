# Preserved group source inputs

The dataset tree retains its original data/provenance bytes. It includes a wider
39-column extended table, source metadata, spatial files, preparation scripts
and a limited raw subset. Not all available columns are active predictors.

Current modelling uses [16/17 approved inputs](../docs/technical/feature_catalog.md).
Original quality/provenance records describe the supplied table and earlier
processing/model context. They must not override the active frozen contract.
See [data notes](../docs/DATA_NOTES.md) and the current data-owner handoff.

Acquisition/GIS scripts are historical source-processing utilities requiring
additional upstream inputs, dependencies and credentials; default review/CI
does not run them. No complete raw GIS rerun or new dataset licence is claimed.
