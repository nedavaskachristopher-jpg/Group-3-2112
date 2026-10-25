# Lesson 2: establish simple baselines

## Goal

Ask whether environmental inputs improve prediction over simple alternatives.
This lesson fits one prespecified logistic model and evaluates only validation
observations. It does not tune XGBoost, optimise a threshold, fit a calibrator or
open the final test for predictions or evaluation.

## The three comparisons

| Method | How it works | What it tests |
| --- | --- | --- |
| Training prevalence | Give every validation row the training positive fraction | Whether different locations and dates can be ranked at all |
| Fire persistence | Predict next-day fire exactly when `fire_today = 1` | Whether a model improves on continuation of existing fire |
| Logistic regression | Learn weights for 16 weather and terrain inputs | Whether environmental conditions carry predictive information |

Persistence uses current fire, while the first logistic model deliberately uses
conditions only. This is a useful operational comparator, but differences cannot
be attributed solely to the model algorithm. A later feature-matched comparison
is required to separate the effects of inputs and model complexity.

The persistence rule produces hard zeros and ones. It does not mean there is
truly zero or 100% probability of a next-day detection.

## Prepare X and y

Load the two permitted development files. Remove the first two July training
days because their three-day rainfall history is incomplete. This removes 86
rows without changing the frozen split files. The resulting fitting matrix has
6,837 rows and 16 columns. Validation has 387 rows and the same 16 input columns.

`y_train` is the training `fire_positive` column. `y_validation` is used only for
evaluation. Grid/date identifiers, next-day detection counts and the label are
not features. The exact whitelist comes from the frozen protocol.

## Standardise on training data only

Temperature, elevation and rainfall have different units and numerical scales.
For each input, StandardScaler calculates its training mean and standard
deviation, then applies `(x - training_mean) / training_std`.

Logistic regression combines features with regularisation. Comparable scales
make the penalty less dependent on measurement units and improve optimisation.
Standardisation changes units; it does not create observations or remove the
rare-fire imbalance. Validation uses the same stored training transformation,
never a newly fitted validation scaler.

The scaler and classifier are combined in a Pipeline. The fitting function
receives training data only. Automated checks confirm that validation prediction
does not update either the scaler or the classifier.

## Fit a transparent first model

Logistic regression computes a weighted sum of inputs, then maps it through the
sigmoid function:

`z = intercept + w1*x1 + ... + w16*x16`

`score = 1 / (1 + exp(-z))`

Despite the name, logistic regression is a classification method. It learns the
weights from training labels. Its log-odds are linear in the supplied inputs;
it will not automatically discover every interaction or nonlinear response.

The first fit uses fixed `C=1`, the `lbfgs` solver and at most 2,000 iterations.
`C` is the inverse regularisation strength. These settings were recorded before
the fit in `config/baseline_v1.json`; no validation-based search is performed.

Following the proposal, `class_weight="balanced"` increases the influence of
rare positive training observations. Each class weight is
`N / (2 * number_of_training_rows_in_that_class)`. It changes the loss, not the
dataset sizes, and all counts come from training only.

Class weights change the fitting objective. Their sigmoid outputs should not
automatically be presented as calibrated event probabilities, especially when
the event rate changes markedly between training and validation. The exported
percentage column is explicitly named `logistic_uncalibrated_percent`.

## Evaluate ranking and decisions separately

Average precision (AP) evaluates scores before applying a decision threshold.
It summarises precision across increases in recall. It is not identical to
trapezoidal PR-AUC, so the implementation and metric name must be stated.

A constant score has AP equal to the positive fraction in the evaluation data.
This does not mean it learned that fraction: its predicted value still comes
from training. On a high-fire validation interval, even an uninformative ranking
therefore has a numerically high AP reference.

For this first diagnostic, all methods use a fixed threshold of 0.5:

- True positive: an alerted cell-day with a next-day detection.
- False positive: an alerted cell-day without a recorded next-day detection.
- False negative: a next-day detection without an alert.
- True negative: no alert and no recorded next-day detection.
- Precision: `TP / (TP + FP)`.
- Recall: `TP / (TP + FN)`.
- Alerts per day: `(TP + FP) / number_of_validation_days`.

An alert is one flagged grid cell-day, not a unique fire incident, a dispatch or
a measured staffing cost. Satellite non-detection can also miss a real fire.

The 0.5 threshold is a teaching reference, not a chosen operational policy. No
threshold is selected for deployment in this lesson. Later development work
must examine the trade-off between missed detections and alert burden.

## Check probabilities without calibrating them yet

Brier score is the mean of `(score - observed_binary_outcome)^2`; lower is
better on the same evaluation population. It measures overall probability
forecast quality and does not isolate calibration alone.

The reliability diagram compares predicted probabilities with observed positive
fractions in five fixed bins and displays bin counts. A diagonal is the ideal
reliability reference. These nine dependent validation days cannot establish
long-term probability reliability. No recalibration is fitted here.

## Run and read the results

```powershell
.\.venv\Scripts\python.exe -m bushfire_ml.baselines
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Read [the result table](../../research/reports/baseline_validation.md) and
[validation figure](../../research/reports/baseline_validation.png). Row-level development
predictions and the fitted pipeline remain in the ignored local data directory.

The model is also evaluated on rows where `fire_today = 0`, retaining both
positive and negative next-day outcomes. Persistence must miss all positives in
this subset by construction. Newly detected cell-days are not confirmed new
ignitions and may include spread or earlier satellite misses.

## What the first run found

The core logistic model has validation AP 0.3716, below the constant-score
reference of 0.4134. Persistence has AP 0.7056. At threshold 0.5, logistic
regression identifies 92 of 160 positive cell-days, issues 140 false alerts and
misses 68 positives. Persistence identifies 123 positives, with 32 false alerts
and 37 misses, using its additional current-fire information.

This first environmental linear model has not established a benefit over the
benchmarks on this interval. That is not proof that environmental conditions
contain no signal. Retain the result and investigate distribution shifts, input
differences and model limitations before tuning or adding complexity. Do not
move the sealed test boundary to improve scores.

The reliability diagnostic also shows that the sigmoid outputs are not reliable
percentages on this interval. The highest-score bin contains 114 rows with an
observed positive fraction of about 32%, despite a mean predicted score around
88%. Do not interpret this nine-day diagnostic as a universal correction rule.

## Oral review questions

1. Why compare with prevalence and persistence before using a complex model?
2. Which 16 variables enter logistic regression, and which columns are excluded?
3. Why does the scaler learn its statistics from training only?
4. What does class weighting change, and why is it not probability calibration?
5. How do precision and recall differ, and which errors matter to stakeholders?
6. Why is this validation result not the final independent performance claim?

Suggested short explanation:

> We first established prevalence and persistence baselines, then fitted a
> class-weighted logistic regression using 16 weather and terrain features.
> Standardisation and model fitting used training data only. We evaluated
> validation ranking with average precision and examined false alerts and missed
> detections at a fixed diagnostic threshold. The outputs are not yet calibrated
> probabilities, and the final temporal test set remains sealed.

## Sources and work record

- [LogisticRegression and balanced class weights](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html)
- [StandardScaler training statistics](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html)
- [Average precision definition](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html)
- [Probability calibration and Brier score limits](https://scikit-learn.org/stable/modules/calibration.html)

This lesson's implementation, tests, result report and explanation were
AI-assisted. The team should retain prompts/outputs, review the results and
record its verification and modifications for the course appendix.
