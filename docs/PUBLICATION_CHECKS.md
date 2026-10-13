# Repository preparation checks

Checks performed on 14 October 2026 in a fresh local Python 3.12.14 environment with the versions pinned in `requirements.txt`:

| Check | Result |
| --- | --- |
| Python source syntax | All retained scripts parsed successfully |
| Notebook structure | Valid notebook; nine code cells have execution counts and outputs; no stored error outputs |
| Data audit | 18,980 rows, 39 columns; 43 retained cells, 15,695 retained rows and 566 positives |
| Extended feature reconstruction | All 39 columns reproduced within the original numerical tolerances |
| Independent metric verification | 126 metric rows and 226,228 prediction rows checked |
| Outer test coverage | All 15,695 retained rows covered once by the outer full-XGBoost test folds |
| Temporal partition checks | Whole-date grouping, nested one-/three-day purging and strict forward separation passed |
| Saved-model verification | 41,280 model/test-row comparisons passed; portable XGBoost scores and alerts match stored evaluations |
| Prepared inference example | 86 predictions reproduce the original scores and alerts |
| Missing-feature handling | Invalid input is rejected |
| Source preservation | SHA-256 equality for all 39 retained input/model files and the original predictions, metrics and run manifest |
| Public content check | Known student identifier, absolute user-directory paths and common embedded credential patterns absent from retained text |

The original notebook, model weights, predictions and training run manifest were retained. Model training and the full raw GIS pipeline were not rerun during these publication checks. The recorded notebook outputs are from the original execution. Report-generation code has a small privacy edit and handles an omitted university logo; packaging code was adapted to the public repository contents.

GitHub Actions runs the saved-result and feature-reconstruction checks on pushes and pull requests. Local validation above does not by itself establish the outcome of a remote workflow run.

## Group repository integration

The contribution is published to `nedavaskachristopher-jpg/Group-3-2112`. Its dataset directory is named `blue_mountains_2019_2020`. Documentation and code comments are in English, the notebook's stored text is English, and artifact paths are ASCII. `src/check_english.py` scans tracked/untracked non-ignored text for Chinese characters and checks file names; it is also included in GitHub Actions. Numerical inputs and saved model files are preserved from the original delivery.
