> Historical pre-integration record. Numerical claims and roles describe the legacy version; see the current team index.

# Jin data engineering workspace

Jin owns data engineering and provenance. Start with [WORKFLOW.md](https://github.com/nedavaskachristopher-jpg/Group-3-2112/blob/legacy-ml-2026-10-25/WORKFLOW.md) and tasks D-01/D-02 on the [task board](https://github.com/nedavaskachristopher-jpg/Group-3-2112/blob/legacy-ml-2026-10-25/team/TASK_BOARD.md).

## Your files

- [https://github.com/nedavaskachristopher-jpg/Group-3-2112/blob/legacy-ml-2026-10-25/team/jin_data_engineering/DATA_HANDOFF.md](https://github.com/nedavaskachristopher-jpg/Group-3-2112/blob/legacy-ml-2026-10-25/team/jin_data_engineering/DATA_HANDOFF.md): the populated data/model interface for you and Kian to confirm.
- [https://github.com/nedavaskachristopher-jpg/Group-3-2112/blob/legacy-ml-2026-10-25/team/jin_data_engineering/REPORT_SECTION.md](https://github.com/nedavaskachristopher-jpg/Group-3-2112/blob/legacy-ml-2026-10-25/team/jin_data_engineering/REPORT_SECTION.md): a data-methods draft based on the merged documentation, with explicit source/processing details still to complete.

## Existing authoritative work

- [Data integration notes](https://github.com/nedavaskachristopher-jpg/Group-3-2112/blob/legacy-ml-2026-10-25/docs/DATA_NOTES.md).
- [Prepared dataset README](https://github.com/nedavaskachristopher-jpg/Group-3-2112/blob/legacy-ml-2026-10-25/inputs/dataset/blue_mountains_2019_2020/model_ready/README.md).
- [Quality report](https://github.com/nedavaskachristopher-jpg/Group-3-2112/blob/legacy-ml-2026-10-25/inputs/dataset/blue_mountains_2019_2020/model_ready/quality_report.json).
- [Provenance](https://github.com/nedavaskachristopher-jpg/Group-3-2112/blob/legacy-ml-2026-10-25/inputs/dataset/blue_mountains_2019_2020/model_ready/provenance.json).
- [Source register](https://github.com/nedavaskachristopher-jpg/Group-3-2112/blob/legacy-ml-2026-10-25/inputs/dataset/blue_mountains_2019_2020/metadata/data_register.csv).
- [Metadata update script](https://github.com/nedavaskachristopher-jpg/Group-3-2112/blob/legacy-ml-2026-10-25/src/update_data_records.py) and [extension reconstruction](https://github.com/nedavaskachristopher-jpg/Group-3-2112/blob/legacy-ml-2026-10-25/src/rebuild_extended.py).
- [Merged PR #1](https://github.com/nedavaskachristopher-jpg/Group-3-2112/pull/1).

## Completion and review

Confirm source versions/licences, confidence/deduplication and prescribed-burn rules, spatial/UTC alignment and the boundary between reproducible prepared-data work and omitted raw inputs. Kian checks the model interface and partitions. Seb checks the physical and label interpretation. Record actual checks and unresolved issues in the handoff and contribution record.

Keep numerical data and processing scripts in their shared locations. A data-value change requires an explicit input hash/version and discussion with Kian about rerunning dependent results.
