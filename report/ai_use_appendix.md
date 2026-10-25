# AI assistance and verification record

Substantive AI assistance supported code, explanations, analysis design,
report drafting and packaging. The supplied assessment material requires
prompts, outputs and the team's modifications or verification to be retained
in an appendix. This record supports that appendix; it is not a claim that
each student has already reviewed or approved the work.

## Selected interaction record

The prompts below are condensed English translations of Chinese requests in
the Codex conversation, not a verbatim transcript. Preserve the original
conversation and relevant outputs separately for submission evidence.

| Request in English translation | Output or decision | Inspectable evidence |
| --- | --- | --- |
| Reserve part of the data for a blind test and explain the ML steps | Protected chronological split, excluded answer columns and shared baselines | [Protocol](../research/config/protocol_v1.json), [baseline lesson](../docs/lessons/lesson_02_baselines.md) |
| Keep code simple and commits clear and detailed | Shared fitting/evaluation helpers and explanatory English commit bodies | [Source map](../docs/technical/source_map.md), Git history |
| Explain why XGBoost is used and compare it with earlier models | Matched-input experiment and technical explanation | [XGBoost lesson](../docs/lessons/lesson_05_xgboost.md) |
| Check whether results are stable across different dates | Daily/block descriptions and past-only forward checks | [Temporal evidence](../research/reports/temporal_stability.md) |
| Check probability reliability and compare 80% and 90% recall policies | Separated calibration/assessment designs, no calibration adoption and exact candidate cutoffs | [Probability evidence](../research/reports/probability_reliability.md) |
| Freeze both policies, evaluate once and do not adjust them after seeing results | Freeze commit `ef45cdf`, one-time release and unchanged adverse results | [Freeze](../research/reports/final_freeze.json), [receipt](../research/reports/final_release.json), [result](../research/reports/final_holdout.md) |
| Organise the ML deliverables, English report material and repository | Aggregate-derived report exports, navigation, source/claim indexes and public/private separation | [Handover](README.md), [manifest](../docs/evidence/delivery_manifest.json) |

## Verification actually recorded

The original 48 automated synthetic/unit checks passed before final release.
They cover leakage, chronology, feature matching, metrics, calibration/cutoff
isolation, exact-score replay and one-time release recovery. Frozen source,
model, configuration and data hashes were verified after the single release.
The plots were visually inspected. The delivered verification record reports
the additional packaging checks separately. These are tool-assisted checks,
not a substitute for student understanding or independent scientific replication.

The team should record its own modifications and checks: which code/functions
were reviewed, which commands were run, which source facts were confirmed,
which figures/tables were checked, and what was changed. Do not mark a review
complete merely because the AI generated a file.

## Member verification to complete

| Role | Required confirmation | Status in this delivery |
| --- | --- | --- |
| ML engineer | Explain metrics, frozen policy selection and limitations; inspect key functions | Student confirmation not yet recorded |
| Data engineer | Confirm source/geometry/licensing and target construction | Student confirmation not yet recorded |
| Domain researcher | Check literature interpretation, stakeholder implications and ethics | Student confirmation not yet recorded |
| Report editor | Check authors, citations, public link, page count and whole-report consistency | Student confirmation not yet recorded |

The final holdout is already exposed. No AI-generated suggestion may be used
to retune it and then describe a repeat as fresh blind evidence. No operational
deployment, manual stakeholder consultation or team sign-off is claimed.
