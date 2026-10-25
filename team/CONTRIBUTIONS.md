# Actual contributions and reviews

Record completed work with evidence. Folder ownership and task assignment alone do not establish completion. Commit counts are not a substitute for describing data work, coding, literature, interpretation, review, integration or presentation work.

## Existing evidence

| Evidence | What is established | What still needs member confirmation |
| --- | --- | --- |
| [Data PR #1](https://github.com/nedavaskachristopher-jpg/Group-3-2112/pull/1), merged as `f089153` | Jin's data integration/provenance documentation is integrated | Final data handoff and source/licence confirmation |
| [ML model card](../docs/MODEL_CARD.md), [run manifest](../output/results/run_manifest.json), [AI assistance record](../docs/AI_ASSISTANCE.md) | ML code, fitted artifacts and experiment records are present; AI-assisted implementation/checking is documented | Kian's actual human review, reruns, interpretation and changes |
| This workflow and member folders | An organisational structure has been prepared at Kian's request | Member task/date confirmations and later completed work |

## Member completion record

| Member | Work actually completed | Deliverable or issue/PR | Actual review or reproduction | Date and status |
| --- | --- | --- | --- | --- |
| Kian | To be completed with actual work performed | To be linked | To be completed | To be completed |
| Chris | To be completed with actual work performed | To be linked | To be completed | To be completed |
| Jin | Integrated and documented the five public sources; audited provenance, FIRMS cleaning, label construction, UTC/date alignment, monthly coverage and data/ML interface | [Data PR #1](https://github.com/nedavaskachristopher-jpg/Group-3-2112/pull/1), [final audit](jin_data_engineering/FINAL_DATA_AUDIT.md), [audit code](../src/audit_data_handoff.py) and [JSON evidence](../output/results/data_handoff_audit.json) | Reconstructed the clean FIRMS table and daily labels from retained sources; verified all listed hashes and 12 ERA5 months; recorded observation/absence limits | 2026-10-25; data task complete, current branch awaiting review/merge |
| Seb | To be completed with actual work performed | To be linked | To be completed | To be completed |

## Review record

| Artifact or task | Reviewer | What was checked | Outcome and remaining action | Evidence/date |
| --- | --- | --- | --- | --- |
| Data/ML interface and final data audit | Kian and Jin | Target, 23/20 predictors, park filter, partitions, counts, provenance, label construction and coverage | Interface approved; zero labels remain unverified fire absence/observation completeness and must be described accordingly | Kian's repository review comment and [final audit](jin_data_engineering/FINAL_DATA_AUDIT.md), 2026-10-25 |

## AI assistance and human checking

Continue the [existing AI assistance record](../docs/AI_ASSISTANCE.md). Record the member's actual checks and edits and use the official course disclosure format where specified.

| Tool and purpose | Output used | Member's actual checking or changes | Relevant artifact |
| --- | --- | --- | --- |
| Codex used to help implement and run a reproducible final data-handoff audit and draft documentation | Audit script, JSON evidence and data-method wording | Outputs were checked against repository hashes and retained raw sources; all AI-assisted material remains subject to member review before submission | [audit code](../src/audit_data_handoff.py), [evidence](../output/results/data_handoff_audit.json) and [data handoff](jin_data_engineering/DATA_HANDOFF.md) |

## Report contribution statement

Complete only after the work and reviews have occurred:

> Kian coordinated [actual workflow work] and checked/interpreted [actual ML work and the role of AI assistance]. Chris completed [actual project framing, integration and submission work]. Jin prepared and documented [actual data work]. Seb developed [actual literature, stakeholder and ethics analysis]. Members reviewed [specific completed reviews]. The evaluated experiment and final report use [repository/commit/report version].
