# Group workflow after revised ML integration

Kian authorised the five-stage migration and integration into the group default
branch after automated acceptance. That authorisation does not establish peer
approval, stakeholder endorsement or readiness to submit the assessment.

| Current contact | Responsibility | Review still needed |
| --- | --- | --- |
| Kian | Revised ML, integration, code/evidence explanation | Personal understanding, reproducibility and interpretation |
| Chris | Project framing, full-report assembly and submission coordination | Official deadline, authors, page limit and final report consistency |
| Penelope | Current dataset handoff and data-owner contact | Source versions, geometry, labels, observation coverage and licences |
| Seb | Domain literature, stakeholder consequences and ethics | Primary-source synthesis and interpretation of adverse results |

Penelope is both the original data contributor and the current contact identified
by the user and later role document. Her earlier data PR and documents retain
their actual historical attribution to the same person. See
[history](team/history/README.md) and [contributions](team/CONTRIBUTIONS.md).

## Authoritative technical version

The active study is in `research/`, imported from the exact revised ML commit
recorded in [source_import.json](docs/integration/source_import.json).
The target is next-day eligible VIIRS detection, including continuing fire.
The main comparison uses 16/17 inputs. Seven-day gaps and past-only checks
precede one frozen final release; no threshold was changed after outcomes.

Use [the model card](docs/MODEL_CARD.md), [final result](research/reports/final_holdout.md)
and [report package](report/README.md). Old weekly, SHAP and forward results
are historical and must not be mixed into a current-model table.

## Working process

1. Start from current main and use a focused task branch.
2. Keep scientific source/configuration frozen. Any further model development
   requires a new research cycle and independent evaluation data.
3. Write an English commit explaining the problem, change, evidence and checks.
4. Run public verification, integration checks and relevant synthetic tests.
5. Record actual peer review separately; a green check is not literature or
   data-owner approval. Integrate only work authorised for that branch/task.

The current integration was explicitly authorised by Kian. Future contributions
can use PR review according to the team's agreed arrangements. Avoid changing
historical contribution attribution or marking a review complete without evidence.

## Completion states

- Engineering complete: an artifact and its automated/visual checks are recorded.
- Member review pending: the responsible person has not yet recorded their checks.
- Submission ready: only the group can confirm the final report, identities,
  course rules, actual reviews and submission arrangements.

The [task board](team/TASK_BOARD.md) separates these states. Calendar deadlines
are not invented; Chris must obtain the official deadline from the course.

## Report coverage

The supplied rubric allocates 4 points each to objectives/background, methods
and findings/evidence, and 3 to recommendations/stakeholders/ethics. The recorded
course screenshots require a PDF, public code link, at most ten body pages and
an AI-use appendix; the exact exclusions are recorded in the integration guide.
Chris verifies these against the current official brief before submission.

Use [contribution records](team/CONTRIBUTIONS.md), [decisions](team/DECISIONS.md),
[AI disclosure](report/ai_use_appendix.md) and [acceptance](docs/integration/acceptance.md).
The old meeting agenda and Penelope documents are historical, not current instructions.
