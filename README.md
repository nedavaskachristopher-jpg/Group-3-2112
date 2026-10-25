# ENGG2112 Group 3: Blue Mountains Bushfire Prediction

Research into next-day eligible satellite fire detections in Blue Mountains
National Park. The revised ML workflow is integrated; its final results do not
establish reliable warnings or calibrated fire probabilities.

## Start here

| Need | Entry point |
| --- | --- |
| Read the current code and settings | [Research workspace](research/README.md) |
| Read exact final evidence | [Final evaluation](research/reports/final_holdout.md) |
| Read the integrated group-report draft | [Report package](report/README.md) |
| Review methods and inputs | [Model card](docs/MODEL_CARD.md), [data notes](docs/DATA_NOTES.md) |
| Coordinate member review | [Workflow](WORKFLOW.md), [team workspaces](team/README.md), [task board](team/TASK_BOARD.md) |
| Understand what changed | [Integration record](docs/integration/README.md) |

## Public review

Python 3.12 is the recorded runtime. Results and public verification use only
the standard library, without private models or raw-data parsing.

```powershell
python review.py results
python review.py verify
python -m tools.check_repository
python -m tools.check_integration
```

For all synthetic/unit tests:

```powershell
python -m pip install -r requirements.txt
python review.py test
```

On Windows, use `.\.venv\Scripts\python.exe` for an existing environment.
The [runbook](docs/technical/runbook.md) covers export regeneration, the
[cached review notebook](notebooks/README.md) and optional private hash checks.

## Current result

The one-time frozen evaluation contains 7,783 cell-days and 49 positive next-day
targets. The 80% development-target policy detected 16, missed 33 and made 39
false alerts. The 90% policy detected 34, missed 15 and made 2,434 false alerts.
These names are development recall targets, not achieved final recall. Raw
scores are not validated probabilities, and the target includes continuing fire.
The prespecified logistic comparison ranked better than the selected XGBoost.

## Layout

```text
research/       Frozen evaluated code, configurations, original evidence and tests
report/         Integrated draft, English ML sections, LaTeX, figures and tables
docs/           Methods, provenance, lessons, integration and verification records
applications/   Guarded private-model inference and cache-only mapping
notebooks/      Executed cached-result review, without training or prediction
inputs/         Existing source data and provenance, preserved from the group baseline
team/           Current roles, handoffs, actual contributions and historical records
tools/, tests/  Delivery utilities and public/synthetic checks
review.py       One public entry point: results, verify, test
```

`src/` contains two compatibility commands; `output/` explains the retired old
location. The complete old code, models, predictions, notebook and SHAP/map
evidence remain at tag `legacy-ml-2026-10-25`. There is one active revised study.

The old and revised studies use the same source-table hash and overlapping
2019-20 dates; this is not an independent-season replication. The source ML
repository/commit and original freeze remain recorded in the integration files.
Private revised models and row predictions are not uploaded. Optional inference
requires the exact frozen model privately and rejects the released final dates.

Engineering acceptance is recorded separately from member review. The report
is an integration draft: author details, data licences/geometry, literature
interpretation, real contributions and final submission readiness still need
the group's confirmation. AI assistance is disclosed in the report package.
