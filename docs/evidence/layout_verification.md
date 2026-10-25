# Layout verification

This revision physically separates the completed research workspace, group
report material, documentation and delivery utilities. The original handover
record remains in [verification.md](verification.md); this record covers the
subsequent relocation.

Checks were completed on 25 October 2026 (Australia/Sydney). A clean export
contained 126 tracked files across five top-level directories. Public checks
covered 59 delivery files, 290 exact claims, six CSV tables and 264 local links.
All 58 tests passed in that export; result display and verification also ran
with third-party site packages disabled. Optional private hash checks passed in
the original workspace.

## Integrity checks

- All original frozen Python, research tests, settings, requirements and
  development JSON references retain their canonical text hashes. Paths in the
  original freeze are resolved from `research/`.
- The final aggregate retains its exact receipt-matching bytes. The freeze,
  release receipt, original aggregate values and both cutoffs are unchanged.
- Root private data/model/prediction hashes are checked without parsing rows.
- All 290 claim values and six aggregate CSV exports are checked against their
  relocated source JSON. Every local Markdown link is checked across the
  research, report, documentation, tools and delivery-test folders.
- The original 48 research checks and ten delivery/review checks pass through
  the unified entry point. The five new checks cover missing/corrupt/incomplete
  release records and dependency-free cached access from another directory.
- Public verification, result display and tests are checked in a clean export
  of tracked files without private data. No fitting or final evaluation is run.
- The four-page report reading copy is rendered and visually checked after
  updating the source URL. Report figures and measured values are unchanged.

The [relocation map](relocation.json) records the previous and current paths.
The [delivery manifest](delivery_manifest.json) records current export hashes.
Use the [runbook](../technical/runbook.md) to repeat the public checks.
