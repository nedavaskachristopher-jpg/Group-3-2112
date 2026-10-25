# Final findings and oral review notes

This interpretation was written after the authorised final evaluation. The
model, inputs, preprocessing, calibration decision, two cutoffs, comparison
models and metrics were frozen in commit `ef45cdf` before final outcomes were
parsed. The [generated report](../../research/reports/final_holdout.md) is the numerical
source; the [release receipt](../../research/reports/final_release.json) records one run.
No fitting or threshold adjustment occurred during or after that release.

## What the held-out data show

The final feature dates cover 1 January to 29 June 2020, with targets on the
following UTC day. There are 7,783 cell-days across 43 cells and 181 dates,
including 49 positive target cell-days. These are not 49 independent fires.
The positive rate is 0.63%, much lower than the 41.34% in the nine-day original
development validation interval. AP and accuracy must be read with this
different event prevalence in mind.

| Frozen policy | TP | FP | FN | Precision | Recall |
| --- | ---: | ---: | ---: | ---: | ---: |
| 80% development selection-recall policy | 16 | 39 | 33 | 29.1% | 32.7% |
| 90% development selection-recall policy | 34 | 2,434 | 15 | 1.4% | 69.4% |
| Persistence | 16 | 39 | 33 | 29.1% | 32.7% |

Neither recall target transfers. The higher-cutoff policy matches persistence
in these counts and detects none of the 33 positive targets in cells without
current detections. The lower-cutoff policy detects 18 of those 33, accompanied
by 2,395 false alerts within that subset. Raising recall carries a substantial
false-alert burden; these counts cannot be translated directly into staffing
or dispatch costs.

XGBoost 17 AP is 0.1062, slightly above persistence AP 0.0992. The prespecified
logistic 17 comparison has AP 0.2113 on the same population, exceeding the
selected XGBoost on this ranking metric. At the unchanged diagnostic cutoff
of 0.5, logistic 17 still has 326 false alerts and 18 missed positive targets.
A higher AP here does not make it an established operational replacement.
We retain it as the planned comparison and do not switch the primary model,
retune its threshold or claim a second blind evaluation on the same data.

## Why accuracy and displayed percentages are insufficient

At its fixed cutoff, the training-prevalence reference predicts no positives
and achieves 99.37% accuracy while missing all 49 positive targets. High accuracy
in this rare-positive period does not demonstrate useful fire detection.

The frozen XGBoost's raw scores also overstate observed detection frequencies:

| Fixed score bin | Cell-days | Mean score | Observed positive rate |
| --- | ---: | ---: | ---: |
| 0.2-0.4 | 4,831 | 34.92% | 0.10% |
| 0.4-0.6 | 2,897 | 43.97% | 0.97% |
| 0.6-0.8 | 55 | 66.59% | 29.09% |

These bins describe this test population and dependent observations, not precise
universal probabilities. They reinforce the earlier decision not to advertise
the raw scores as reliable risk percentages. We do not fit a correction using
these test frequencies.

## Time support and label meaning

The positive targets occur in the January and February feature-month groups.
March through June have no positive targets in the supplied label table, but
the lower cutoff still produces false alerts. Every month remains in the report;
AP and recall are marked undefined when their positive denominator is zero.
An absence of eligible satellite detections is not evidence that the physical
landscape had no fires. Satellite observation quality and label completeness
remain limitations of the study, not reasons to revise this test's labels.

Large prevalence changes, sparse early training positives, limited calibration
days and dependence among ongoing events restrict the claims we can make.
These observations do not identify one proven cause of poor transfer. The
evaluation is a protected retrospective temporal holdout from the supplied
season, with earlier aggregate disclosure, rather than independent-season or
prospective operational validation. Real publication latencies are not modelled.

## What can be claimed in the project report

The project built an auditable ML comparison with temporal separation, explicit
feature review, baselines, probability checks, development-only cutoff selection
and a committed freeze before one final evaluation. It found that the chosen
XGBoost and its development recall-target policies did not establish reliable
temporal transfer or useful calibrated warning probabilities.

Report that outcome directly. Do not describe the project as a successful
deployment, interpret the target as ignition, hide unfavourable comparator
results or omit quiet months to increase reported precision. Scientific value
comes from the tested hypotheses and honest limits, including a simpler model's
better final ranking result.

Further work could obtain independent seasons/events, reconcile detection labels
with observation coverage and domain evidence, assess features available at real
forecast time, and collect enough temporally separated support for calibration
and response-capacity decisions. Any resulting model needs a new independent
evaluation. This exposed holdout cannot provide a fresh blind claim.

## Oral review explanation

> We froze the model, feature order, preprocessing and two development-selected
> cutoffs before opening the protected temporal holdout. On 7,783 cell-days,
> the 80% policy achieved 32.7% recall with 39 false alerts, while the 90% policy
> achieved 69.4% recall with 2,434 false alerts. The simpler logistic comparison
> ranked better than the selected XGBoost, and the raw scores were not reliable
> percentages. We reported all comparisons and months without retuning. The
> result supports a research prototype with clear limitations, not an operational
> warning system. Future improvement requires new independent evaluation data.

This interpretation was AI-assisted. Team members should verify the frozen
manifest and report, retain prompts and outputs, and record their own review
for the course AI-use appendix.
