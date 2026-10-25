# Evaluated research workspace

This folder contains the completed ML study, separated from report exports and
delivery tooling. The evaluated source remains unchanged after relocation.

## Read the code in this order

| Order | Responsibility | Entry point |
| --- | --- | --- |
| 1 | Allowed inputs and chronological boundaries | [data.py](bushfire_ml/data.py) |
| 2 | Training-only preprocessing and model fitting | [models.py](bushfire_ml/models.py) |
| 3 | Shared metrics and score reliability | [evaluation.py](bushfire_ml/evaluation.py) |
| 4 | Matched model comparisons | [baselines.py](bushfire_ml/baselines.py), [xgboost_experiment.py](bushfire_ml/xgboost_experiment.py) |
| 5 | Past-only time checks | [temporal_stability.py](bushfire_ml/temporal_stability.py) |
| 6 | Calibration assessment and threshold selection | [probability_experiment.py](bushfire_ml/probability_experiment.py), [calibration.py](bushfire_ml/calibration.py) |
| 7 | Frozen artifacts and one-time evaluation | [freeze_final.py](bushfire_ml/freeze_final.py), [final_release.py](bushfire_ml/final_release.py) |

The [full code index](bushfire_ml/README.md) covers data preparation, independent
auditing, error analysis and presentation modules. The
[source map](../docs/technical/source_map.md) connects functions to settings,
results and tests. Avoid reading reporting/plotting modules first when reviewing
model behaviour.

## Supporting folders

- [config/](config/README.md): the original protocol and versioned experiment settings.
- [reports/](reports/README.md): original chronological evidence, final freeze and receipt.
- [tests/](tests/README.md): the original 48 synthetic checks retained with the study.
- [requirements.txt](requirements.txt): recorded ML dependency versions.

Use `python review.py results`, `python review.py verify` and `python review.py test`
from the repository root for current review. Historical experiment runners and
their command examples are retained for audit, not as a request to repeat fitting
or reopen the exposed final test. Reproduction of an original experiment needs
its historical Git checkout and matching private data workspace.

Original paths inside frozen manifests are relative to this folder. Private
artifacts remain outside Git in the original root `.local_data/`; the public
verifier understands that location. No compatibility copies or duplicate model
implementations were added.
