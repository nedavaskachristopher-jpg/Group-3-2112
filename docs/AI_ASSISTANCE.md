# AI assistance

Codex assisted with revised ML implementation, explanations, evaluation design,
code organisation, group integration, tests, figures and report drafting. Kian
directed the work and explicitly authorised the five integration stages and
default-branch merge after acceptance. This does not imply every member reviewed
the generated material.

The [report appendix](../report/ai_use_appendix.md) records condensed English
translations of prompts, outputs and automated checks. Original conversations
should be retained privately for the course disclosure. Members must record
their actual changes and verification rather than copying an AI-generated
completion statement. Historical AI records remain at the preserved legacy tag.

On 25 October 2026, Codex also assisted the Data Engineer with a read-only
handoff audit. The audit was migrated to the revised repository on 28 October
and updated to verify the frozen 17/16-input contract. It checks prepared-table
integrity, source hashes, FIRMS cleaning, label construction, UTC alignment,
monthly coverage and retained raw sources without fitting or evaluating a
model. The script and machine-readable evidence are
[`tools/audit_data_handoff.py`](../tools/audit_data_handoff.py) and
[`docs/evidence/data_handoff_audit.json`](evidence/data_handoff_audit.json).
The unresolved observation/absence limitations remain explicit and require
human review before submission.
