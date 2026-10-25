# Configuration index

These files are historical or frozen research settings, not current commands
to optimise a model on the exposed final test. The final manifest hashes all
of them. A new modelling iteration needs new independent evaluation data.

| File | Purpose |
| --- | --- |
| [protocol_v1.json](protocol_v1.json) | Original date/geography separation and input exclusions |
| [baseline_v1.json](baseline_v1.json) | Prespecified 16-input logistic baseline |
| [current_fire_v1.json](current_fire_v1.json) | Add only the reviewed same-day detection flag |
| [xgboost_v1.json](xgboost_v1.json) | Shallow-tree configuration and AP stopping definition |
| [temporal_stability_v1.json](temporal_stability_v1.json) | Daily/block descriptions and past-only forward windows |
| [probability_v1.json](probability_v1.json) | Separated calibration/assessment designs and both recall targets |
| [final_evaluation_v1.json](final_evaluation_v1.json) | Final population, comparisons, subsets, metrics and release rules |

The exact final fitted models, ordered inputs, no-calibration decision and
cutoffs are in [final_freeze.json](../reports/final_freeze.json). The original
protocol's initial primary feature set is historical; it was not overwritten
when the reviewed 17-input comparison became the selected final model.
