# Frozen-artifact applications

These utilities do not train models, choose thresholds or evaluate the final
test. Public review needs no private artifacts: use `python review.py results`.

## Optional prepared-row inference

```powershell
python -m applications.predict --input examples/synthetic_features.csv --model PATH_TO_PRIVATE_FROZEN_MODEL --output .local_data/synthetic_scores.csv
```

Supply the exact original `xgboost_17.ubj` privately; its hash, input order and
eight-tree count must match the freeze. The utility never exports, repairs or
replaces model files. Existing output files are not overwritten. The example
contains synthetic unlabelled development-period rows, not new validation data.
Both unchanged policies appear as `alert_80` and `alert_90`. Percentages are
uncalibrated scores, and alerts use the unrounded raw values.

The input must contain `grid_id`, `feature_date`, `target_date` and all ordered
inputs in the [contract](../docs/technical/model_contract.json).
`park_area_fraction` is optional but checked if supplied. Labels and other
columns are rejected. Final-period rows are rejected: use the existing score
cache instead of predicting those dates again. The interface does not download
weather, build raw GIS inputs or support a new location or multi-day horizon.

## Cached illustrative map

```powershell
python -m applications.cached_map --cache PATH_TO_PRIVATE_FINAL_PREDICTIONS
```

The cache must match the original completed receipt byte hash. The map uses only
grid/date/score fields and supplied static geometry, with the first frozen
feature date selected before looking at outcomes. No new prediction or metric
calculation is involved. The published PNG and provenance JSON are under
`report/figures/`; no row-level scores or labels are published. Grid cells extend
outside the park and the colours are not validated probabilities.

Legacy inference, SHAP and maps remain identifiable at the preserved
`legacy-ml-2026-10-25` tag; they do not describe the revised model.
