# Code index

The evaluated Python source is frozen. Its original modules and hashes are
preserved inside this research workspace. Full claim-to-evidence links are in
the [source map](../../docs/technical/source_map.md).

| Responsibility | Modules | Main functions or entry points |
| --- | --- | --- |
| Data access and partitioning | [data.py](data.py), [prepare.py](prepare.py) | `load_development`, `model_matrix`, `verify_seal`, `prepare` |
| Independent development audit | [audit.py](audit.py) | Development-only reconstruction and consistency checks |
| Model fitting | [models.py](models.py) | `fit_logistic`, `fit_xgboost`, `fit_xgboost_fixed` |
| Shared metrics | [evaluation.py](evaluation.py) | `evaluate`, `reliability_bins` |
| Calibration and cutoffs | [calibration.py](calibration.py) | `fit_sigmoid`, `apply_sigmoid`, `select_recall_threshold` |
| Development experiments | [baselines.py](baselines.py), [current_fire.py](current_fire.py), [xgboost_experiment.py](xgboost_experiment.py) | Matched fitting and validation comparisons |
| Error and temporal checks | [error_analysis.py](error_analysis.py), [temporal_stability.py](temporal_stability.py) | Saved-error analysis and past-only forward windows |
| Probability experiment | [probability_experiment.py](probability_experiment.py) | `fit_scenario`, `calibration_decision` |
| Final freeze | [freeze_final.py](freeze_final.py) | `verify_freeze`, `main`; no holdout-outcome parsing |
| One-time final release | [final_release.py](final_release.py), [final_metrics.py](final_metrics.py) | Receipt-gated loading, `predict_frozen`, `final_results` |
| Presentation | [reporting.py](reporting.py), [temporal_reporting.py](temporal_reporting.py), [probability_reporting.py](probability_reporting.py), [final_reporting.py](final_reporting.py) | Tables/figures separated from model fitting |

Typical flow is: explicit inputs -> past-only fitting -> scores -> shared
metrics -> aggregate reporting. The final path replaces fitting with loading
fixed artifacts. Only its dedicated release runner may parse final outcomes,
and the completed release now returns cached results.
