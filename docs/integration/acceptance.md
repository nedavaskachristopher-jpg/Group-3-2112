# Clean-clone integration acceptance

Engineering acceptance was performed on 25 October 2026 (Australia/Sydney).
The complete stage-4 implementation was cloned from the remote integration
branch into a separate directory. A new Python 3.12.14 virtual environment was
created and all pinned research and optional PDF dependencies were downloaded
and installed from scratch. No private model or row-prediction files were supplied.

The machine-readable [fresh-clone record](clean_clone_acceptance.json) identifies
the checked implementation commit and exact runtime. The stage-5 commit adds this
record, a reusable acceptance command and formatting corrections. Its final head
is validated again from a fresh clone and by the current CI before the authorised
merge; the integration PR and Actions logs record that exact final-head run.

| Gate | Result |
| --- | --- |
| Frozen source, settings and development references | Original hashes retained |
| Final aggregate and receipt | Exact bytes match; one evaluation and one test CSV read |
| Synthetic tests | All 68 pass: 48 original and 20 delivery/application checks |
| Numerical exports | 290 exact claim paths and all six summary CSV tables match |
| Original source inputs | All 18 preserved input files match baseline bytes |
| Public result/verification commands | Work with third-party site packages disabled |
| Notebook and map | Four executed cached-review cells and first-date cache provenance checked |
| Saved-model check | Exact private artifact checked earlier on two synthetic rows; native parity; no repair/write |
| Report layout | Eight-page group draft and four-page ML contribution rendered and visually inspected |
| Report consistency | Group scientific blocks exactly reuse the ML contribution |
| Public artifacts | English/privacy checks pass; tracked files unchanged by acceptance |
| Scientific boundary | No real-data training, new final prediction, recalibration or threshold adjustment |

GitHub CI runs the same acceptance command on pushes and PRs using the recorded
Python version and pinned dependencies. Local success is not substituted for a
remote outcome: inspect the actual run associated with the PR/head before merge.

```powershell
python -m pip install -r requirements.txt -r tools/requirements-report.txt
python -m tools.acceptance --pdf
```

Only the optional PDF parsing needs the report dependencies. The default public
review and result commands use the standard library. The prior self-repairing
UBJ verifier is retired, and corrupt/missing model bytes are rejected.

Text formatting corrections preserve data bytes: Markdown documentation under
`inputs/` uses LF, while numerical/GIS source inputs retain their original bytes.
The exact-CRLF final aggregate has its own byte-preserving attribute. LaTeX source
trailing blank lines were removed; the scientific report content is unchanged.

This acceptance is an automated/visual engineering result. Actual member
understanding, source licences/geometry/coverage, literature interpretation,
author details, the official deadline and final assessment approval remain
human responsibilities. No completed peer review or stakeholder endorsement is
claimed. The authorised main-branch merge preserves all five stage commits and
the historical `legacy-ml-2026-10-25` tag without rewriting previous history.
