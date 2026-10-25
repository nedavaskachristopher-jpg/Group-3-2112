# Original research checks

These seven modules contain the original 48 synthetic/unit tests. Their Python
contents are unchanged and remain covered by the original freeze manifest.

| Test module | Behaviour checked |
| --- | --- |
| [test_data_guards.py](test_data_guards.py) | Boundaries, excluded inputs and seal tampering |
| [test_baselines.py](test_baselines.py) | Metrics and training-only preprocessing |
| [test_current_fire.py](test_current_fire.py) | One extra audited input and matched settings |
| [test_xgboost.py](test_xgboost.py) | Training weights, AP stopping and model persistence |
| [test_temporal_stability.py](test_temporal_stability.py) | Calendar gaps and outer-answer isolation |
| [test_probability.py](test_probability.py) | Calibration, tied cutoffs and held-later answer isolation |
| [test_final_release.py](test_final_release.py) | One-time access, cache recovery and exact threshold replay |

Use `python review.py test` from the repository root to run these and the
[delivery tests](../../tests/README.md). Direct unittest discovery must run
with `research/` as its working directory so original imports resolve.
No private holdout rows are required.
