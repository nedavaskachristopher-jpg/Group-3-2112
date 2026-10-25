# Review and export runbook

## Review the public repository

From the repository root, using Python 3.12:

```powershell
python review.py results
python review.py verify
```

These commands use only the standard library. They do not need private data,
fitted models, pandas or XGBoost. `results --json` returns exact cached values;
the default output is a short policy comparison. Incomplete receipts or changed
aggregate bytes cause an error, not another evaluation.

To use a local virtual environment and run the full synthetic test suite:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r research/requirements.txt
.\.venv\Scripts\python.exe review.py test
```

The test command runs the original research suite followed by delivery tests.
The [research test index](../../research/tests/README.md) and
[delivery test index](../../tests/README.md) describe their scope. The command
returns a failing exit status if either suite fails.

## Optional private byte-hash checks

```powershell
python review.py verify --local-artifacts
```

This additionally hashes existing root `.local_data/` model snapshots, sealed
data files and the saved prediction CSV. It never parses raw CSV rows, calls a
model or fits parameters. Private paths remain as recorded in the original
freeze; only the public study files moved into `research/`.

## Regenerate report exports

```powershell
.\.venv\Scripts\python.exe tools/build_handover.py
.\.venv\Scripts\python.exe -m pip install -r tools/requirements-report.txt
.\.venv\Scripts\python.exe tools/render_handover_pdf.py
.\.venv\Scripts\python.exe review.py verify
```

The builder reads only listed public aggregate/configuration JSON files under
`research/`. It writes report material under `report/`, numerical provenance
and hashes under `docs/evidence/`, and input documentation under `docs/technical/`.
The PDF renderer consumes shared report content and figures. Visually inspect
the rendered PDF after changing its content/layout. Optional PDF dependencies
are separate from the unchanged research requirements.

The final aggregate is protected by a specific `-text -eol` Git attribute.
Do not reformat its JSON or normalise its line endings: the original receipt
checks exact bytes. See the [initial verification record](../evidence/verification.md).

## Historical experiments

Original runners and teaching examples remain in the research workspace and
lessons. To reproduce a past development experiment, use a separate checkout
of its original commit and matching private data. These commands can overwrite
historical output and are not part of the current review workflow.

| Commit | Milestone |
| --- | --- |
| `aa0fdf8` | Protected data split, baselines and current-fire comparison |
| `4f02dbe` | Shared fitting and evaluation |
| `8abfd9e` | Matched XGBoost comparison |
| `96fc3f9` | Past-only time checks |
| `ad81139` | Probability assessment and two reminder cutoffs |
| `ef45cdf` | Pipeline frozen before final evaluation |
| `39d1230` | Single final evaluation and findings |
| `7e94d61` | Initial English ML handover |

The exposed final period must not be used to tune a model and then described
as new blind evidence. Further modelling needs independent evaluation data.
The original one-time release runner is retained for audit; current review uses
cached aggregates exclusively.
