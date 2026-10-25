# Synthetic inference inputs

[synthetic_features.csv](synthetic_features.csv) contains two deliberately
synthetic development-period rows with the revised input schema. It includes
no outcomes and is not a validation sample or evidence of model performance.

Use the [application instructions](../applications/README.md) with a privately
supplied exact frozen model. Result CSVs remain local. Public review and CI do
not require the model; `python review.py results` displays cached aggregates.
