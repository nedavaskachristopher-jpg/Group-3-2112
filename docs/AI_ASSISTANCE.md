# AI assistance record

Codex assisted with data audits, reconstruction code, training/evaluation code, running the original experiments, checking metrics and saved models, generating figures, and drafting the ML report and explanations. The original delivery includes executed notebook outputs and stored verification records.

The user subsequently requested a Git repository containing the previously written code and model prediction content. Repository preparation added English documentation, Git configuration files and automated verification, preserved model/data artifacts, and removed a student identifier from public report-generation code and its stored content record. The report and assignment/chat screenshots are kept outside the public repository.

The user then specified the team's repository, `nedavaskachristopher-jpg/Group-3-2112`, and required English uploads. The contribution was prepared for that repository with an English dataset directory name, a group README, and checks for Chinese characters in text and non-ASCII file names. Modelling inputs, fitted models and historical experiment results were preserved.

On 25 October 2026, Codex also assisted the Data Engineer with a read-only final handoff audit. It created and executed `src/audit_data_handoff.py` against both the repository tables and the retained original source folder; generated `output/results/data_handoff_audit.json`; checked source licences/access records; and drafted data-handoff, methods and limitation wording. The audit did not retrain a model or alter any training CSV, fitted model or evaluation result. Its two unresolved findings are stated explicitly: FIRMS detections do not document every satellite observation opportunity, and zero detections do not independently confirm fire absence. Members must review the wording and record any edits before submission.

## Prompt themes

- Complete the Kian ML Engineer contribution using the supplied project materials and grading requirements; provide guides for the other members.
- Explain the completed work step by step in plain Chinese for a team discussion.
- Provide a shorter English explanation for international teammates.
- Create a Git repository and upload the existing code and prediction content.
- Use the Group 3 repository and ensure all uploaded content is in English.
- Display scores and alert thresholds as percentages while preserving evaluation accuracy; document unobserved human activity and explain continuing-fire and two-/three-day forecast limitations.
- Audit data provenance, label construction, date alignment and monthly observation coverage without changing the exposed final test results.

## Evidence and team review

Model outputs, per-row predictions, metrics, selected parameters and original software versions are in `output/`. Original verification results are retained, while checks performed during publication are recorded separately in `docs/PUBLICATION_CHECKS.md`.

The team should record the exact prompts/outputs required by the course, its actual code reviews or reruns, and any edits to the final submission. No human review, consultation or approval is claimed on behalf of the team here. This record is a starting point for the required final-report appendix and does not replace that appendix.
