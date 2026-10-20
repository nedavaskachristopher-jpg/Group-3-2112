# Forward test error analysis

Owner: Kian. Review partners: Seb and Jin. This is an analysis workspace; the example rows have not yet been selected or interpreted by members.

Use the `chronological` / `xgb_full` records from [predictions.csv](../../output/results/predictions.csv). Retain the evaluated threshold. Inspect representative true positives, false positives and false negatives, including no-fire-today cases. Link each observation to the corresponding input row and explain the selection rule so examples are not presented as representative performance by themselves.

| Grid and feature/target dates | Outcome and score/threshold | Fire today/neighbour/history | Relevant weather/rainfall | Observation | Possible explanation and evidence | Reviewer |
| --- | --- | --- | --- | --- | --- | --- |
| To be selected | To be completed | To be completed | To be completed | To be completed | To be completed | To be completed |

Questions to investigate:

1. Which errors involve cells with no detected fire on the feature day?
2. Do false alerts often follow a detection today, and can next-day satellite non-detection be checked independently?
3. Does the conditions-only model behave differently on the same rows?
4. Are mistakes concentrated in a small number of dates or connected cells?
5. Which interpretations are supported by the records, and which need independent event/observation evidence?

Separate observations from hypotheses. Do not infer causality from one example or assume a negative satellite label proves extinction. Keep the original test results frozen. A new feature or threshold motivated by these errors is a subsequent exploratory method and needs a suitable new evaluation design.

## Handoff to the report

Write a short explanation of observed patterns, limits of the interpretation and the next evidence needed. Seb connects errors to stakeholder consequences; Jin checks label/observation limitations. Record completed reviews and source rows.

Checked findings: To be completed.
