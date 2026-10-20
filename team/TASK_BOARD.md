# Group task board

Coordinator: Kian. Update after each handoff or review. Statuses: `To do`, `In progress`, `In review`, `Done`. Due fields currently identify a workflow gate; Kian replaces them with dates agreed by the team once Chris confirms the official deadline.

| ID | Owner | Task and expected output | Reviewer | Status | Due or dependency |
| --- | --- | --- | --- | --- | --- |
| W-01 | Kian | Establish this workflow and four member folders | All members | In review | Stage 1 |
| W-02 | Kian | Confirm each member's tasks, dates and review/merge arrangements | Chris and each owner | To do | Stage 1 |
| P-01 | Chris | Record official brief, deadline, length/format and submission requirements in the report plan | Kian | To do | Before task dates are finalised |
| D-01 | Jin | Document data integration, the extended table and modelling provenance | Kian is the ML-interface reviewer | Done | Merged as `f089153`; evidence is PR #1 |
| D-02 | Jin | Confirm the populated data handoff, source/licence evidence and remaining data limits | Kian | To do | Stage 2; uses D-01 |
| M-01 | Kian | Confirm existing model/result handoff and identify the report's evaluated version | Jin | In review | Before results are integrated |
| M-02 | Kian | Fix model verification so corrupt/missing UBJ files fail without replacement | Jin or Chris reproduces the check | To do | Before final reproducibility sign-off |
| M-03 | Kian | Run a saved-model demonstration on a teammate's machine and record actual results | A second member | To do | Stage 3 |
| M-04 | Kian | Complete representative forward-test error analysis | Seb and Jin | To do | Before limitations/recommendations are final |
| R-01 | Seb | Complete a cited related-work synthesis | Kian and Chris | To do | Stage 4 |
| R-02 | Seb | Link measured errors to stakeholders, ethics and realistic recommendations | Kian | To do | After M-04 |
| P-02 | Chris | Complete framing, proposal adaptation and report assembly | All technical owners | To do | After D-02, M-01, R-01 and R-02 |
| W-03 | All; Kian coordinates | Complete actual contribution/review and AI-assistance records | Each member checks their own entry | To do | Before final report review |
| P-03 | Chris; Kian coordinates checks | Freeze the report version and complete final submission checks | All members | To do | Stage 6; official deadline to be entered |

`D-01` records a merged repository change, not final sign-off on every source or the complete original GIS pipeline. `M-01` records artifacts already present; the final member review remains open. Other tasks are assignments, not claims of completed work.

## Update format

When changing a status, add evidence below or link a GitHub issue/PR. Report what happened rather than an intended action.

| Date | Task ID | Owner | Progress or blocker | Evidence | Next action |
| --- | --- | --- | --- | --- | --- |
| 2026-10-21 | D-01 | Jin | Data documentation/provenance update merged | [PR #1](https://github.com/nedavaskachristopher-jpg/Group-3-2112/pull/1) | Complete the final data handoff |

If using GitHub Issues for live tracking, put the issue link in the task row and use its discussion for detailed updates. Keep this board concise.
