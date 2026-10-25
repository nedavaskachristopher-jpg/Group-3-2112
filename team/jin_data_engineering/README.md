# Jin data engineering workspace

Jin owns data engineering and provenance. Start with [WORKFLOW.md](../../WORKFLOW.md) and tasks D-01/D-02 on the [task board](../TASK_BOARD.md).

## Your files

- [DATA_HANDOFF.md](DATA_HANDOFF.md): the populated data/model interface for you and Kian to confirm.
- [REPORT_SECTION.md](REPORT_SECTION.md): checked data-methods wording with source, processing and limitation details.
- [FINAL_DATA_AUDIT.md](FINAL_DATA_AUDIT.md): the final human-readable source, label, alignment and coverage audit.
- [Machine-readable audit](../../output/results/data_handoff_audit.json) and [audit script](../../src/audit_data_handoff.py): reproducible evidence for the final handoff.

## Existing authoritative work

- [Data integration notes](../../docs/DATA_NOTES.md).
- [Prepared dataset README](../../inputs/dataset/blue_mountains_2019_2020/model_ready/README.md).
- [Quality report](../../inputs/dataset/blue_mountains_2019_2020/model_ready/quality_report.json).
- [Provenance](../../inputs/dataset/blue_mountains_2019_2020/model_ready/provenance.json).
- [Source register](../../inputs/dataset/blue_mountains_2019_2020/metadata/data_register.csv).
- [Metadata update script](../../src/update_data_records.py) and [extension reconstruction](../../src/rebuild_extended.py).
- [Merged PR #1](https://github.com/nedavaskachristopher-jpg/Group-3-2112/pull/1).

## Completion and review

The final audit confirms source versions/licences, confidence/deduplication and prescribed-burn rules, spatial/UTC alignment and the boundary between repository artifacts and retained raw inputs. Kian has checked the model interface and partitions. Seb should use the documented observation/absence limitation in the physical and stakeholder interpretation. Actual checks and unresolved issues are recorded in the handoff and contribution record.

Keep numerical data and processing scripts in their shared locations. A data-value change requires an explicit input hash/version and discussion with Kian about rerunning dependent results.
