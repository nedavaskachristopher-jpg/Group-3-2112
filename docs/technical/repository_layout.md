# Repository layout and relocation

## Responsibilities

The previous handover added several indexes but left historical experiments and
report exports at the same browsing level. This revision physically separates
the completed study, report material, documentation and delivery utilities.

| Previous location at commit `7e94d61` | Current location | Responsibility |
| --- | --- | --- |
| `bushfire_ml/` | `research/bushfire_ml/` | Evaluated Python implementation |
| `config/` | `research/config/` | Original experiment settings |
| `reports/` | `research/reports/` | Original evidence and release records |
| Original research tests | `research/tests/` | Original 48 synthetic checks |
| `requirements.txt` | `research/requirements.txt` | Frozen ML environment |
| `handover/group_report/` | `report/` | English report contribution and figures |
| `handover/tables/` | `report/tables/` | Aggregate CSV exports |
| `handover/technical/` | `docs/technical/` | Source map, contract and runbook |
| `handover/evidence/` | `docs/evidence/` | Claim and verification records |
| `handover/manifest.json` | `docs/evidence/delivery_manifest.json` | Export integrity manifest |
| Original `docs/` | `docs/lessons/` | Teaching sequence and decisions |
| Packaging tests | `tests/` | Delivery and review-command checks |
| `requirements-handover.txt` | `tools/requirements-report.txt` | Optional PDF dependencies |

The [machine-readable relocation map](../evidence/relocation.json) records all
moved tracked files. No duplicate compatibility source tree is maintained.

## Frozen-study boundary

The original freeze lists paths such as `bushfire_ml/data.py` and
`config/protocol_v1.json`. They are now resolved relative to `research/`.
The source, original tests, configurations and evidence hashes are unchanged;
the original freeze and release receipts are not rewritten. The final aggregate
retains its exact recorded CRLF bytes through a file-specific Git attribute.

The evaluated Python package stays together so its relative imports and
study-relative paths remain consistent. Internal module names are retained to
preserve the evaluated implementation. Folder separation is for navigation;
there was no new training, prediction, threshold selection or evaluation.

Private artifacts retain their original location in root `.local_data/`.
`python review.py verify --local-artifacts` checks their recorded byte hashes.
Historical private experiment runners need their original checkout/workspace;
the current root commands are the supported public review path.

## One review entry point

`review.py` provides `results`, `verify` and `test`. Paths are anchored to the
script location, so the caller's working directory does not select another
study or test folder. Results are read from the completed receipt-matching
aggregate only. Missing or inconsistent records produce an error; they never
start evaluation or try to reconstruct results from private labels.

Original research tests run with `research/` as their working directory.
Delivery tests run at the repository root. Both use synthetic fixtures or public
aggregates. The result and verification commands require no ML dependencies.
