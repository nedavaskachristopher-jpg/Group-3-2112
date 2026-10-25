# ENGG2112 Group 3: Blue Mountains Bushfire Prediction

ENGG2112 ML research for next-day eligible VIIRS detections in Blue Mountains
National Park. The modelling and evaluation workflow is complete. Final results
did not establish reliable warning performance or calibrated fire probabilities.

## Choose one starting point

| What you want | Where to start |
| --- | --- |
| Read the code | [Research workspace](research/README.md) |
| Read the final result | [Final evaluation](research/reports/final_holdout.md) |
| Use the English ML report | [Report package](report/README.md) |
| Understand decisions and methods | [Documentation](docs/README.md) |

## Review from the repository root

Python 3.12 is the recorded runtime. Viewing results and verifying the public
files use only the Python standard library; no private data is required.

```powershell
python review.py results
python review.py verify
```

To run all synthetic/unit tests, install the recorded ML dependencies first:

```powershell
python -m pip install -r research/requirements.txt
python review.py test
```

Use the existing virtual environment's Python on Windows if needed:
`.\.venv\Scripts\python.exe review.py verify`. Commands also work when invoked
using an absolute path from another directory. See the [runbook](docs/technical/runbook.md)
for export regeneration and optional private hash checks.

## Folder responsibilities

```text
research/   Evaluated code, settings, original evidence and original tests
report/     English ML sections, LaTeX, reading PDF, figures and summary tables
docs/       Methods, lessons, evidence indexes and verification records
tools/      Aggregate-only export and verification scripts
tests/      Delivery and review-entry-point tests
review.py   One entry point: results, verify, test
```

The research workspace is a relocated snapshot: frozen Python, configurations,
tests, aggregate values and release records retain their original content.
Its historical paths are relative to `research/`; the [relocation record](docs/technical/repository_layout.md)
explains this boundary. Private data, predictions and fitted models remain ignored.

There was one final evaluation. The two policy names refer to development recall
targets, not achieved final recall. Scores are not validated probabilities; the
target includes continuing detections, not just new ignitions. Further improvement
requires a new research cycle and independent evaluation data.

The ML contribution is ready for group integration. Whole-report assembly,
verified data/map provenance, authorship and member review remain with the group;
see the [integration guide](report/integration_guide.md) and
[AI-use record](report/ai_use_appendix.md).

## Group integration

[Team workspaces](team/README.md) and [workflow](WORKFLOW.md) retain historical
contribution context. Current group text is being reconciled on the integration
branch. See [integration records](docs/integration/README.md),
[applications](applications/README.md) and the [review notebook](notebooks/README.md).
The old experiment is preserved at tag `legacy-ml-2026-10-25`.
