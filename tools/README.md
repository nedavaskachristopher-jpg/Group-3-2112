# Delivery utilities

Use [review.py](../review.py) at the repository root for normal review.
The scripts here implement aggregate-only export and verification.

| Script | Purpose |
| --- | --- |
| [build_handover.py](build_handover.py) | Export report text, LaTeX, tables, figures and source indexes from public aggregates |
| [render_handover_pdf.py](render_handover_pdf.py) | Render the shared report content into the reading PDF |
| [verify_handover.py](verify_handover.py) | Check unchanged research hashes, release identity, exports and links |
| [requirements-report.txt](requirements-report.txt) | Optional PDF-export dependencies |

See the [runbook](../docs/technical/runbook.md). Source-of-truth measurements
remain in `research/reports/`. Export scripts do not read raw data, predict or fit.
Only explicit optional verification reads private files, and only as bytes.
