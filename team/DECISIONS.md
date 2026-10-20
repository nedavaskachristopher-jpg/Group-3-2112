# Project decision record

Kian maintains this index. Technical owners confirm the entries affecting their work. Record new choices when they change scope, inputs, labels, evaluation, reported evidence or collaboration arrangements.

| ID | Recorded position | Basis | Owners and follow-up |
| --- | --- | --- | --- |
| O-01 | Kian coordinates group workflow and ML; Chris owns report integration; Jin owns data; Seb owns domain research | Kian's workflow-management instruction on 21 October 2026 and existing role context | All members confirm assigned tasks and dates; GitHub permissions remain unchanged |
| T-01 | Predict eligible detection in the same park cell on the following UTC day; includes continuing fire | [Model card](../docs/MODEL_CARD.md) and [data notes](../docs/DATA_NOTES.md) | Jin and Kian confirm wording in their handoffs |
| T-02 | Main panel uses park overlap at least 0.10; 23 full features and 20 conditions-only features | [Feature contract](../output/feature_contract.json) | Jin and Kian confirm input/version identity |
| T-03 | Original CSV split is metadata; ML code regenerates partitions | [Training code](../src/train_evaluate.py) and [quality report](../inputs/dataset/blue_mountains_2019_2020/model_ready/quality_report.json) | Kian owns evaluation design; Jin reviews the data interface |
| T-04 | Interleaved weekly experiments are within-season interpolation; the forward test is separate | [Model card](../docs/MODEL_CARD.md) | All report authors preserve this distinction |
| T-05 | Percentage presentation does not calibrate probabilities; current models have a one-day horizon | [Forecast horizons](../docs/FORECAST_HORIZONS.md) | Kian and Seb check interpretation |
| V-01 | Merged data-documentation baseline is `f089153`; original numerical training manifest identifies the evaluated input | [Data PR #1](https://github.com/nedavaskachristopher-jpg/Group-3-2112/pull/1) and [run manifest](../output/results/run_manifest.json) | Chris and Kian identify the final report/release version separately |

These entries describe instructions and existing artifacts. They are not a claim that all members have signed off.

## New decisions

| Date | Decision | Reason and evidence | Actual participants | Affected files/results | Follow-up |
| --- | --- | --- | --- | --- | --- |
| To be completed | To be completed | To be completed | To be completed | To be completed | To be completed |
