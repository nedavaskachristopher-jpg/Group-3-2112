# ENGG2112 Group 3 Next Day Active Fire Detection

ENGG2112 Group 3 project repository. The current implementation contains Kian Luo's ML engineering contribution. It uses weather, rainfall, terrain and recent fire observations to predict whether a satellite will detect eligible active fire in a Blue Mountains National Park grid cell on the following UTC day.

The repository contains the training and evaluation code, executed notebook, saved models, individual predictions, metrics and figures. It is a retrospective research prototype using the 2019–20 season. The target includes continuing fires; it is not a verified ignition label.

## Results

| Evaluation of full XGBoost | Average precision (AP) | Recall | Precision | True positives | False positives | False negatives |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Within-season weekly holdout | 0.824 | 0.766 | 0.837 | 82 | 16 | 25 |
| Strictly forward test | 0.186 | 0.289 | 0.271 | 13 | 35 | 32 |

Five-fold within-season mean AP is 0.692, with sample standard deviation 0.093. AP measures ranking quality, not classification accuracy. In the forward test, none of the 32 positive cell-days with no detection on the feature day triggered an alert at the selected threshold.

The results support better within-season ranking than simple baselines, but do not establish reliable new-fire warnings. See [the model card](docs/MODEL_CARD.md) for evaluation assumptions and limitations.

## Repository contents

| Location | Contents |
| --- | --- |
| `src/train_evaluate.py` | Baselines, Logistic Regression and XGBoost; validation tuning, weekly, five-fold and forward evaluation |
| `src/predict.py` | Load a portable saved XGBoost model and score prepared feature rows |
| `src/score_display.py` and `src/update_score_display.py` | Add percentage presentation while retaining raw scores, labels and evaluation results |
| `src/audit_data.py`, `src/rebuild_extended.py` and `src/update_data_records.py` | Input checks, extended-table reconstruction and reproducible quality/provenance updates |
| `src/verify_results.py` | Independently recompute metrics and check saved-model predictions and temporal partitions |
| `src/make_figures.py` | Generate PR curves, confusion matrices, SHAP plots and an illustrative map |
| `output/Kian_ML_Analysis.ipynb` | Nine previously executed code cells with outputs |
| `output/models/` | Eight saved LR/XGBoost variants and their feature/threshold metadata; four portable XGBoost UBJ files |
| `output/results/predictions.csv` | 226,228 evaluation rows across models and experiments, including repeated evaluation of cell-days |
| `output/results/metrics.csv` | 126 metric rows, including all-cell and no-fire-today views |
| `output/example_features.csv` and `output/example_scores.csv` | Prepared inference example without outcome labels, and its saved scores |
| `inputs/dataset/` | Prepared research data, provenance, source-processing scripts and a limited raw input subset |
| `docs/` | Model card, data notes and AI assistance record |

The final report and group completion scaffold are maintained separately. Uploaded documentation, code comments, notebook text and file names use English. Personal student identifiers and original assignment/chat screenshots are excluded from this public code repository.

## Run the saved model

Use Python 3.12 and install the pinned environment. From the repository root on Windows PowerShell:

```powershell
git clone https://github.com/nedavaskachristopher-jpg/Group-3-2112.git
cd Group-3-2112
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src/predict.py --input output/example_features.csv --model output/models/chronological_xgb_full.json --output output/reproduced_example_scores.csv
```

On macOS/Linux, replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`.

The main display fields are `model_score_percent` and `threshold_percent`, on a 0-100 scale. For example, a raw score of 0.73 is displayed as 73%; this is an **uncalibrated model score**, not a claim of a 73% chance of fire. The raw `model_score` and `threshold` remain on the 0-1 scale, and the binary `alert` is computed from the unrounded raw values. Outputs also identify the one-day `forecast_horizon_days` and score interpretation.

The evaluation file `output/results/predictions.csv` similarly adds `score_percent` and `threshold_percent` beside its original raw scores, binary observations and alerts. Accuracy, precision, recall, AP and other metrics continue to use the original labels and score scale. Display conversion does not improve or reduce model performance.

Inputs must already contain the required 23 full-model features, or 20 conditions-only features. This interface does not fetch live weather or accept raw sensor readings.

## Human activity and forecast horizon

Deliberate or accidental ignition, recreation, land-management actions and suppression are not explicit inputs. Their effects can occur in historical labels, but the model cannot anticipate a particular unobserved action. A low score does not establish safety, and percentage formatting does not remove missing-information uncertainty.

The model predicts the next day only, including continuing fire. A detected fire today can inform tomorrow's score. Running the model again with newly observed conditions tomorrow gives an updated next-day prediction; it does not provide a two-/three-day forecast from today's inputs. See [forecast horizons and continuing fire](docs/FORECAST_HORIZONS.md) for the distinction and future development requirements.

## Verify and reproduce

Run the existing independent checks before changing or retraining models:

```powershell
.\.venv\Scripts\python.exe src/verify_results.py
.\.venv\Scripts\python.exe src/rebuild_extended.py
.\.venv\Scripts\python.exe src/check_english.py
```

To rerun the experiments and figures:

```powershell
.\.venv\Scripts\python.exe src/train_evaluate.py
.\.venv\Scripts\python.exe src/make_figures.py
```

These commands regenerate files under `output/`. Copy any results you want to retain before rerunning. Random seed is 2112; software versions and the original input hash are recorded in `output/results/run_manifest.json`. Historical run records describe the original execution; current publication checks are recorded in `docs/PUBLICATION_CHECKS.md`.

To regenerate and execute the notebook, run `python src/build_notebook.py` using the same environment. For interactive use, also install `ipykernel` and select the corresponding Python environment. Open the notebook from the repository root or `output/`.

## Data and attribution

The supplied panel has 18,980 rows and 39 columns. Filtering to cells with at least 10% park overlap retains 43 cells, 15,695 cell-days and 566 positives. It covers one season only. Sources include NASA FIRMS, Copernicus ERA5-Land, Geoscience Australia SRTM and NSW NPWS boundaries/fire history. Source inventory and checksums are retained in `inputs/dataset/blue_mountains_2019_2020/`.

See [data provenance and scope](docs/DATA_NOTES.md). The complete raw GIS acquisition pipeline cannot be reproduced from the limited original delivery alone. Upstream data retain their providers' terms; this repository does not grant an additional dataset licence. No open-source licence has been selected for the project code.

## AI assistance and report integration

Codex assisted with implementation, experimental checks, explanations and repository preparation. [The AI assistance record](docs/AI_ASSISTANCE.md) distinguishes completed automated checks from team review still to be documented. The final report should link to this public repository and follow the course's report and disclosure requirements.
