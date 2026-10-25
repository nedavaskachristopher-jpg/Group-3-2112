# Lesson 7: reliable percentages and useful reminder cutoffs

This lesson implements milestone 6 of the project workflow. It checks
probability reliability, tests one calibration candidate and records two
provisional reminder policies. The final test remains sealed.

## What a probability should mean

If a model repeatedly assigns a score of about 0.7 to comparable cell-days,
roughly 70% should have the target detection for that number to be a reliable
probability. The target here is eligible VIIRS detection on the next UTC day,
including continuing fire. It is not confirmed ignition, spread or severity.

Multiplying a score by 100 changes its display. It does not establish that
the number matches observed frequencies. Our base classifiers use positive
class weights, and development prevalence changes strongly through time.
Neither the sigmoid output layer nor class weighting establishes calibration.

Reliability diagrams group similar scores and compare their mean with the
observed positive fraction. We show bin sample counts and separately examine
cells with and without current detections. The latter prevents a reasonable
overall average from hiding a poor estimate for currently unflagged cells.

Brier score is the mean squared difference between the score and binary label.
Log loss penalises confident wrong predictions more strongly. Lower values
indicate better overall probability predictions, but both also depend on
discrimination and event prevalence. They do not isolate calibration alone.
The binned absolute gap is another descriptive diagnostic, not a certificate.

## Fitting and checking must remain separate

For each scenario, we perform the following steps in time order:

1. Fit and stop the base model using only past development observations.
2. Keep that base model fixed and predict the later calibration period.
3. Fit a sigmoid mapping and select reminder cutoffs on those calibration rows.
4. Apply the fixed model, mapping and cutoffs to still-later assessment dates.

We retain seven calendar gap days between each main period and around inner
early stopping. We never calibrate on base-training predictions, and never
use the later assessment labels to select the mapping or cutoffs. The base
model cannot be refitted after calibration without a new transfer check.

Two fixed scenarios expose the available-data limitation:

| Scenario | Base fitting ends | Calibration feature dates | Later assessment feature dates |
| --- | --- | --- | --- |
| Earlier model, a week of calibration | 24 November | 2-8 December | 16-24 December |
| More recent model, one calibration day | 8 December | 16 December | 24 December |

All dates are in 2019. The first model has very few historical positives. The
more recent model has more fitting evidence, but leaves only one calibration
day and one assessment day under the gaps. Its tree count is selected using
past stopping data, rather than the original nine-day validation outcomes.
The original models and reports are preserved.

These dates and model results have already been reviewed during development.
The assessments are excluded from fitting within each scenario, but they are
not newly untouched data. The assessment scenarios overlap and may contain
the same ongoing fires; do not call them independent replications.

## The calibration candidate

We compare raw scores, one nondecreasing sigmoid candidate, and the constant
positive rate from the past calibration period. Matched raw logistic and
XGBoost models with 16 and 17 inputs remain visible alongside persistence.

The candidate transforms the clipped raw-score logit using
`sigmoid(a * logit(score) + b)`, with `a >= 0`. It minimises ordinary binary
log loss with an L2 penalty on the slope. The intercept is unpenalised and
calibration labels are not class-balanced. The mapping can change probability
values while keeping ordering, or collapse to a constant if its slope is zero.
Clipping or a zero slope can introduce ties. This explicit implementation is
not claimed to reproduce scikit-learn's Platt calibration exactly.

We do not fit a flexible isotonic mapping on the sparse temporal evidence.
We also do not divide by class weight and declare the result calibrated:
changing prevalence and model approximation prevent that from being sufficient.

Before fitting, we recorded a conservative project adoption gate requiring
adequate class counts, a week of calibration and assessment support, and
improvements in Brier and log loss across two disjoint assessment windows.
The counts are research heuristics, not universal statistical standards.
Calendar windows alone do not guarantee independent fire events.

The [generated report](../../research/reports/probability_reliability.md) shows that the
gate is not met. The longer calibration scenario does not improve subsequent
probability quality. The recent one-day scenario improves but cannot establish
dependable transfer. The decision is to leave sigmoid unadopted and retain
raw experimental scores, without claiming reliable probability percentages.

## Why the reminder cutoff is a separate decision

Calibration asks whether the number means what it appears to mean. Threshold
selection asks when that number should trigger a reminder. A monotone
calibration can change the numerical cutoff without changing the selected
cell-days. It cannot create missing predictive information or automatically
remove the false-alert versus missed-detection trade-off.

Kian requested two parallel research scenarios: target at least 80% recall and
target at least 90% recall on the calibration selection rows. For each target,
we select the highest observed cutoff satisfying that recall constraint. Since
higher cutoffs produce fewer alerts, this minimises selection-row alerts subject
to the constraint. Score ties remain together; no arbitrary cell is favoured.

The target is a selection constraint, not a promise for later dates. The later
check can fall short. If many cells have tied or similar scores, raising recall
can require alerting almost everywhere. We report both false alerts and missed
positive cell-days, rather than describing a high recall alone as success.

The recent-model draft records both exact raw-score cutoffs and their inclusive
`score >= cutoff` comparison. These are on the model's 0-1 score scale, not
validated probability percentages. The 80% selection policy falls below its
target on the later day. The 90% selection policy alerts all study cells on
that day. Neither is an established operational warning threshold.

We do not invent a monetary penalty for missing a fire or a staffing cost for
each false alert. Cell-day alerts are not fire incidents or dispatch counts.
A defensible operational threshold would require agreed response actions,
costs or capacity constraints and stronger external validation.

## Artifacts and next step

- [Configuration fixed before calibration fitting](../../research/config/probability_v1.json)
- [Probability results and figure](../../research/reports/probability_reliability.md)
- [Draft model, artifact hashes and exact cutoffs](../../research/reports/draft_probability_policy.json)

Local base models, sigmoid parameters and row-level predictions remain under
ignored `.local_data/lesson_07_probability_v1/`. The saved models are reloaded
and checked against the exact original scores. CSV scores use sufficient digits
and a verified round trip so rounding cannot change decisions at tied cutoffs.
Use full-precision JSON cutoffs, not the rounded report table, for replay.

The next milestone is to freeze the complete research pipeline and both
predeclared operating-point comparisons before the single final holdout
evaluation. Do not choose a preferred cutoff or refit a calibrator after seeing
that test. The current policy is a reviewable draft, not an already frozen
pipeline or an automatic alert service.

## Oral review explanation

> We distinguished risk ranking, probability calibration and reminder decisions.
> We fitted calibration and selected 80% and 90% recall cutoffs using later
> development observations excluded from base fitting, then checked them on
> still-later dates. Calibration did not improve consistently, and the recent
> comparison had only one day of support. We therefore did not claim reliable
> percentages. Raising recall could require alerting every grid cell. Both
> cutoffs remain provisional research choices, and the final test stays sealed.

## Reproduce and disclosure

```powershell
.\.venv\Scripts\python.exe -m bushfire_ml.probability_experiment
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

- [scikit-learn: calibration, reliability and proper scoring rules](https://scikit-learn.org/stable/modules/calibration.html)
- [scikit-learn: threshold tuning and separate selection data](https://scikit-learn.org/stable/modules/classification_threshold.html)

This work was AI-assisted. Retain prompts and outputs, review the equations,
reproduce the run and record team verification for the course AI-use appendix.
