# Initial handover verification record

Checks below were completed on 25 October 2026 (Australia/Sydney). They are
automated and visual packaging checks, not student sign-off or independent
scientific replication.

| Check | Recorded result |
| --- | --- |
| Unit and synthetic tests | All 53 passed, including the original 48 and five handover checks |
| Frozen source and development reference hashes | Unchanged |
| Final aggregate and release receipt | Exact byte hash matches; one evaluation and one test CSV read remain recorded |
| Published numerical claim catalogue | 290 exact source values/transforms checked |
| Aggregate CSV exports | All six tables checked against their source JSON, including undefined metrics |
| Private model, data and saved prediction hashes | Checked locally by reading bytes only |
| Public review without private files | Staged tracked files exported to a separate clean directory; verifier and all 53 tests passed |
| Public final-result entry point | Returned `cached_result_only: true` without private data or model files |
| Report reading copy | Four pages rendered and visually inspected for legibility, clipping and table/figure placement |
| Report figures | PNG and vector PDF exports inspected; captions identify cell-day counts and raw scores |
| Publication content | English text; no raw data, row-level answers/predictions, models, environments or credentials staged |

## Exact-byte preservation for the released aggregate

The original completed release recorded the SHA-256 of the Windows CRLF
aggregate file. Git had normalised that file to LF in the initial results
commit, causing the exact-byte receipt check to fail in a clean export.
The handover commit restores the original recorded bytes to the Git index
and adds a specific `-text -eol` attribute for
`reports/final_holdout.json`. Its SHA-256 remains
`50fdf78aae6e37d89286a3ea9d07dcc565643e1cc998cc7a152d4233b78c3e4b`.

This is a storage correction only: the JSON values, release receipt, frozen
protocol, source, models and thresholds are unchanged. The aggregate diff is
empty when ignoring line endings. The handover manifest uses canonical LF
hashes for text exports; the release receipt deliberately checks the original
aggregate bytes. No evaluation, prediction, fitting or recalibration was
performed to correct this publishing issue.

## Repeatable review commands

Follow the [runbook](../technical/runbook.md) for the public verifier, tests
and cached-result entry point. Optional private verification hashes local
artifacts without parsing holdout rows. The [manifest](delivery_manifest.json)
records the delivered export hashes. Regeneration reads existing aggregates;
it does not establish another blind result.

The whole-group LaTeX document has not been assembled or compiled in this
delivery. The group must check its final layout, bibliography, author details,
source/licence documentation and AI-use appendix after integration.

This record describes the initial handover at commit `7e94d61`. The subsequent
[layout verification](layout_verification.md) records relocation checks separately.
