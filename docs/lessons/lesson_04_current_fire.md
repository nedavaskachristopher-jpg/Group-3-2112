# Lesson 4: change one input and compare fairly

## The question

Does the audited same-day `fire_today` flag add useful predictive information to
the first logistic model?

The reference model uses 16 weather and terrain inputs. The candidate uses the
same 16 plus this one binary flag. Both use the same 6,837 training rows and 387
validation rows, training-only standardisation, balanced class weights, `C=1`,
solver and iteration limit. The diagnostic threshold stays at 0.5.

We refit the candidate, so all its learned weights can change. We do not manually
add a fixed percentage when a fire is present. The comparison holds the learning
method and data population fixed while adding information.

## Why this is not direct answer leakage

`fire_today` records detections on the feature date. The answer records eligible
detections on the following target date. The development audit checked the
same-day alignment against the supplied daily label panel.

We assume prediction after the UTC feature day ends. The historical satellite
archive and reanalysis do not reproduce actual publication delays; operational
availability would require a separate check. Next-day detection counts remain
excluded. The sealed split protocol and source data are unchanged.

## What the experiment found

| Method | TP | FP | FN | Validation AP |
| --- | ---: | ---: | ---: | ---: |
| Logistic, 16 inputs | 92 | 140 | 68 | 0.3716 |
| Logistic, 17 inputs | 124 | 86 | 36 | 0.6090 |
| Fire persistence rule | 123 | 32 | 37 | 0.7056 |

The candidate improves over the first logistic baseline at the fixed threshold:
32 more positive cell-days detected and 54 fewer false alerts. Its AP also rises.

However, relative to persistence it adds only one true-positive cell-day and
54 false alerts. These are net counts on this validation interval, not a proven
operational benefit or a measured staffing cost.

For the 232 rows without a current detection, there are 37 next-day positives:

- The 16-input model detects 7, with 114 false alerts.
- The 17-input model detects 1, with 54 false alerts.
- Persistence detects none and issues no alerts in this subset by construction.

The candidate catches all 123 continuing-detection positives at the diagnostic
threshold. The improvement in overall recall is dominated by these cases. It has
not established effective prediction of new detections, which can be spread or
previously missed fire rather than confirmed new ignitions.

## What the result does not establish

- A better score than the first model does not establish a better practical
  alternative to persistence. Compare all relevant benchmarks.
- Validation has already informed model development, so it is not an independent
  final performance estimate. The final test remains sealed.
- Overall Brier improves from 0.3649 to 0.2465, but log loss worsens from 1.0315
  to 1.1024. These proper scores penalise errors differently; the probabilities
  are not established as reliable merely because one score improves.
- In the candidate's highest-score bin, the mean score is about 98.32%, while
  about 71.10% of 173 rows are positive. No calibrator has been fitted.
- All original labels and the 22 December observation-quality concern remain
  unchanged. No difficult date was removed to raise the score.

## Next modelling question

Can a nonlinear model use the same inputs more effectively? Compare algorithm
choices using matched input sets and unchanged evaluation dates, preserving the
logistic references and no-current-detection subgroup. Do not jump directly to a
deployment threshold or interpret uncalibrated scores as operational probabilities.

## Reproduce

```powershell
.\.venv\Scripts\python.exe -m bushfire_ml.current_fire
```

- [Settings recorded before fitting](../../research/config/current_fire_v1.json)
- [Validation comparison and plot](../../research/reports/current_fire_comparison.md)
- [Machine-readable results](../../research/reports/current_fire_comparison.json)

## Oral review explanation

> We added only the current-day detection flag while keeping the training rows,
> classifier settings and validation period fixed. It improved over the original
> conditions-only logistic model, but added 54 false alerts for just one extra
> true positive relative to persistence at the fixed diagnostic threshold. The
> gains were dominated by continuing fire, and the final test remains sealed.

This lesson and its code, tests and explanations were AI-assisted. Retain the
prompts/outputs and record team verification for the course appendix.
