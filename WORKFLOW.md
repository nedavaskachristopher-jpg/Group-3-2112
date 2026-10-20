# Group 3 project workflow

Kian coordinates the group workflow and also owns ML engineering. Chris owns project framing and report integration, Jin owns data engineering, and Seb owns domain research, stakeholders and ethics. This document is the working arrangement requested by Kian on 21 October 2026. Each member confirms their tasks and dates at the next team check-in; no confirmation or completed work is implied by an assignment here.

Start with your [member folder](team/README.md), then check the [task board](team/TASK_BOARD.md). Record completed work in [contributions](team/CONTRIBUTIONS.md) and changes to technical assumptions in [decisions](team/DECISIONS.md).

## Responsibilities

| Owner | Accountable work | Main deliverables | Review partner |
| --- | --- | --- | --- |
| Kian | Task coordination, dependency tracking, ML implementation, evaluation and reproducibility | Workflow and task board; feature contract; model checks; results/error analysis; ML report contribution | Jin checks data assumptions; Seb checks interpretation; Chris checks report integration |
| Chris | Project scope, motivation, objectives, report assembly and submission coordination | Project framing; proposal changes; integrated report; references/layout and submission checklist | Each member checks their technical sections; Kian checks task closure |
| Jin | Data sources, labels, spatial/UTC alignment, dataset quality and provenance | Data handoff; source/licence evidence; data report contribution; responses to ML data questions | Kian checks the data/model interface; Seb checks domain assumptions |
| Seb | Literature, physical interpretation, stakeholders, ethics and recommendations | Related-work synthesis; cited domain reasoning; error-consequence analysis and realistic recommendations | Kian checks numerical claims; Chris checks narrative and referencing |

Kian manages the task list and follows up on handoffs. Each member remains responsible for understanding, checking and explaining their own contribution. Chris assembles the report; all members review their material before submission. The team agrees who clicks Merge and who submits the final assessment. This workflow does not change GitHub permissions.

## Folder ownership

| Folder | Owner and purpose |
| --- | --- |
| [team/kian_ml_and_coordination](team/kian_ml_and_coordination/README.md) | Kian's coordination, ML handoff, error analysis and report section |
| [team/chris_project_and_report](team/chris_project_and_report/README.md) | Chris's project framing, report plan and report sections |
| [team/jin_data_engineering](team/jin_data_engineering/README.md) | Jin's data handoff and data report section |
| [team/seb_domain_research](team/seb_domain_research/README.md) | Seb's literature review, stakeholders and ethics |

Members write and update their assigned content in these folders. Running code stays in `src/`, datasets in `inputs/`, generated evidence in `output/`, and shared technical documentation in `docs/`. Member folders link to those authoritative files. This keeps paths and experiment versions consistent without maintaining separate copies of the same dataset or model.

## Current baseline

- PR #1, the data integration and provenance update, was merged into `main` on 21 October 2026. Integration baseline: `f089153`.
- The model input remains the extended 18,980-row, 39-column panel. The main filter retains 43 cells, 15,695 rows and 566 positive cell-days.
- Full models use 23 features; conditions-only models use 20. The target is eligible next-day satellite detection, including continuing fire.
- Existing models and evaluation artifacts are available. The [model card](docs/MODEL_CARD.md) gives the current results and limits.
- The saved-model verification issue remains a separate ML task: verification must inspect delivered UBJ files without regenerating them first.
- Workflow setup does not constitute team sign-off, a new training run or a final report submission.

## Work stages and handoffs

| Stage | Owner | Work | Ready to move on when |
| --- | --- | --- | --- |
| 1 Confirm the plan | Kian with all members | Confirm ownership, course deadline, check-in time and review/merge arrangements | Each task has an owner, output, reviewer and agreed due date |
| 2 Confirm the data handoff | Jin -> Kian | Check sources, target, timestamps, features, filter and input hash | The data handoff is complete and Kian records the interface review |
| 3 Close ML checks | Kian -> Jin and Seb | Fix model verification; demonstrate inference; inspect representative errors | Existing models are checked without replacement, example scores reproduce and error notes are traceable |
| 4 Complete interpretation | Seb with Kian and Jin | Connect literature, physical assumptions, error consequences and recommendations | Claims have appropriate sources and match measured results |
| 5 Assemble the report | Chris with all members | Integrate sections, proposal changes, figures, references and contributions | Every rubric area is covered and all reported numbers identify their experiment |
| 6 Review and submit | Kian coordinates; Chris handles submission arrangements | Freeze the evaluated version, review the full report and follow the official course instructions | Technical owners have recorded reviews and the required submission files are ready |

Calendar deadlines are not available in the supplied materials. Chris records the official submission deadline below; Kian sets task dates with members. Until then, task-board due fields refer to these stages rather than invented calendar dates.

| Schedule item | Agreed value |
| --- | --- |
| Official submission deadline | To be entered by Chris from the course brief |
| Next team check-in | To be set by Kian with the group |
| Member section handoff | To be agreed before report integration |
| Final report review | To be agreed before submission |
| Submission operator | To be confirmed by the group |

## Working on a task

1. Read the task and relevant member README. Confirm its deliverable, reviewer and completion condition.
2. Start from current `main` and create a short task branch, for example `data/source-notes`, `ml/model-verification`, `research/related-work` or `report/integration`.
3. Update the assigned member folder or the relevant authoritative shared file. Keep one task focused on one coherent outcome.
4. Open a pull request. State what changed, why, what was checked and which report section is affected. Link the task ID.
5. Ask the listed review partner to check the change. Data and ML changes need interface checks; research and report changes need source and consistency checks.
6. Address comments and applicable automated checks. A green check alone does not validate literature, physical reasoning or report claims.
7. After review, the agreed integrator merges the PR. Update the task board and actual contribution record with evidence.

For text-only work, use GitHub's web editor: open the file, edit it, commit to a new branch and create a PR. Command-line Git is optional for writing and reviewing documents. If someone helps upload another member's text, record the content author and the uploader's actual roles; the content owner still checks it.

## Status and completion rules

Use `To do`, `In progress`, `In review` and `Done` on the task board. `Done` requires an artifact, relevant checks, a recorded peer review and integration where applicable. Existing artifacts can be available while their final human review remains pending.

A technical task should include a command/result or review evidence. A writing task should include a readable section, supporting sources where needed, and resolution of factual comments. The owner records blockers promptly and Kian coordinates dependencies. Do not treat assignment, an AI-generated draft or a proposed review as completed personal work.

## Changes that affect other members

- Data values, label rules, feature definitions or time partitions: Jin and Kian check the input hash and decide which models/results must be regenerated.
- Model settings, thresholds or metric calculations: Kian records the experiment and updates the affected result tables and interpretation.
- Target or scope wording: Kian, Jin and Seb check consistency; Chris updates project framing and conclusions.
- Documentation-only changes: explicitly state whether inputs, models and results remain unchanged.
- Previously examined test outcomes stay part of the recorded experiment. New methods motivated by those outcomes need a clear exploratory label and appropriate new evaluation design.

Record substantive choices in [DECISIONS.md](team/DECISIONS.md). Keep prior experiment evidence identifiable rather than silently replacing the report's supporting version.

## Report coverage

| Supplied rubric area | Points | Lead contribution | Supporting members |
| --- | --- | --- | --- |
| Objectives, motivation and background | 4 | Chris | Seb supplies domain sources; Jin and Kian confirm feasibility and scope |
| Methods | 4 | Jin and Kian | Seb checks domain reasoning; Chris connects changes to the proposal |
| Findings, analysis and evidence | 4 | Kian | Jin checks data interpretation; Seb connects results to literature and implications |
| Recommendations, stakeholders, impact and ethics | 3 | Seb | Kian supplies measured errors/limits; Jin supplies data limits; Chris integrates the conclusions |

These are coverage responsibilities, not a new grading formula. Check the official brief for separate personal-contribution, presentation, word/page-limit and AI-disclosure requirements. The main report follows a connected research argument. A concise contribution table can go in the appropriate section or appendix.

## Review and release checklist

- [ ] Data/ML interface, target and evaluated version are consistent across sections.
- [ ] Weekly interpolation is distinguished from forward testing; no cross-season or multi-day result is invented.
- [ ] Percentages are labelled as uncalibrated model scores; AP is not described as accuracy.
- [ ] False alerts, missed detections and new-fire-subset limits are discussed alongside headline scores.
- [ ] References support their claims and figures have readable captions and units.
- [ ] Actual member contributions, reviews and AI assistance are recorded.
- [ ] The final report's repository/commit, course format and submission requirements are checked.
- [ ] Each member has reviewed their material and the group has confirmed submission readiness.

This document describes the human workflow. Automated checks remain under `.github/workflows/`.
