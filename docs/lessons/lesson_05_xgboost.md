# Lesson 5: why and how we test XGBoost

## The idea in plain language

XGBoost means Extreme Gradient Boosting. Our implementation builds decision
trees in sequence. Each new tree makes a small correction to the score produced
by the earlier trees. The corrections are chosen to reduce the training loss,
with a penalty discouraging an unnecessarily complex model.

A decision tree asks a sequence of questions about the inputs. A path might ask
about temperature, then humidity, then recent rainfall. This represents a
combination of conditions rather than one fixed global effect per input.
These are illustrative questions; their thresholds are learned, not manually
chosen as physical fire-danger rules.

For binary classification, the model adds tree contributions to a raw score and
applies a sigmoid to obtain a number between zero and one. It does not simply
ask all trees to vote. Later trees are fitted to loss gradients and curvature;
they do not only reread the rows with incorrect binary predictions.

## Comparison with the existing methods

| Method | How it combines information | Strength | Limitation |
| --- | --- | --- | --- |
| Prevalence | The same training-derived probability for every row | Transparent reference | Cannot rank individual cell-days |
| Persistence | Repeat today's binary detection flag | Strong continuation reference | Cannot flag a new detection where today's flag is zero |
| Logistic regression | Weighted sum followed by a sigmoid | Simple, inspectable and regularised | Log-odds are linear in supplied inputs unless interactions/transformations are added |
| XGBoost | Sequential trees with learned conditional branches | Can learn thresholds, nonlinear responses and feature interactions | More settings, less direct interpretation, and a greater need to control complexity |

Logistic regression probabilities are not straight lines, but its log-odds
remain linear in the provided inputs. It is therefore inaccurate to describe
logistic regression as unable to classify nonlinear-looking probabilities at all.

## Why it is reasonable for this project

Our inputs are a structured table of weather and terrain values. We want to
test whether their combined effects matter: for example, whether the association
with high temperature differs under low humidity or different rainfall history.
A tree can express such conditional effects without us manually writing every
interaction. This is a modelling hypothesis, not a guaranteed improvement.

The tree implementation also provides shrinkage, depth limits, regularisation
and subsampling. Tree split decisions do not require the standardisation used
by our logistic pipeline. XGBoost can route missing values, but that does not
remove the need for a scientifically justified missing-data policy. The approved
development matrices currently contain no missing inputs.

We are not feeding images or a fire-spread simulation into XGBoost. It sees the
same tabular features as each matched logistic reference. It cannot recover
unobserved ignition causes, satellite coverage or omitted fuel information just
because the algorithm is more flexible.

## The prespecified first configuration

| Setting | Value | Reason |
| --- | --- | --- |
| Maximum tree depth | 3 | Limit the number of nested decisions and complexity |
| Learning rate | 0.05 | Add small corrections rather than large changes |
| Maximum boosting rounds | 400 | Upper bound, not a requirement to retain all trees |
| Early-stopping patience | 25 rounds | Stop when validation AP no longer improves |
| L2 leaf regularisation | 5 | Penalise large leaf scores |
| Minimum child weight | 5 | Discourage splits supported by too little weighted curvature |
| Row subsampling | 0.8 | Randomly use a fraction of training rows per round |
| Feature subsampling per tree | 0.9 | Limit the available input subset per tree |
| Positive weight | Training negatives / positives = 46.8112 | Increase positive-class emphasis using training information only |

Minimum child weight is a Hessian-weight threshold, not literally five samples.
Subsampling does not mix training and validation rows. All settings were recorded
before this first fit, and only one configuration was tried for each input set.
The relative positive/negative loss emphasis matches balanced logistic regression,
but the absolute loss scale and regularisation differ between the algorithms.

Two experiments use identical fitting rows and validation dates:

1. XGBoost with the 16 weather and terrain inputs.
2. XGBoost with those inputs plus the audited same-day `fire_today` flag.

Neither includes next-day detection counts, dates, coordinates or the target as
an input. Current-day fire is assumed available after the full UTC feature day;
the real-world publication latency limitation remains.

## How early stopping works

After each tree is added, we evaluate validation average precision (AP). If it
does not improve for 25 rounds, training stops and only the best prefix of trees
is retained. A fresh callback is created for each fit.

We explicitly maximise scikit-learn's `average_precision_score`. XGBoost's
built-in `aucpr` uses continuous interpolation and is not the identical metric.
This avoids silently selecting trees with one definition and reporting another.

Validation therefore influences the chosen number of trees. It is development
data, not an untouched final assessment. The temporal test remains sealed.

## What our first fit actually retained

- The 16-input model retained 1 tree after evaluating 26 rounds.
- The 17-input model retained 18 trees after evaluating 43 rounds.

The 16-input validation did not support keeping more trees under this fixed
configuration. That may reflect poor transfer, weak inputs or noisy validation;
it does not by itself prove the cause. Training and validation AP also have
different prevalence references, so their raw values are not directly comparable
as an isolated diagnosis of overfitting.

In the retained 17-input model's first tree, the root split is `fire_today`.
Rows without a current detection are then split using temperature and other
conditions. This is a learned association, not a causal explanation or a manually
programmed persistence rule. Leaf values are raw-score corrections, not direct
probability percentages.

## Validation results

| Method | AP | TP | FP | FN |
| --- | ---: | ---: | ---: | ---: |
| Logistic 16 | 0.3716 | 92 | 140 | 68 |
| XGBoost 16 | 0.4535 | 94 | 115 | 66 |
| Logistic 17 | 0.6090 | 124 | 86 | 36 |
| XGBoost 17 | 0.7283 | 123 | 32 | 37 |
| Persistence | 0.7056 | 123 | 32 | 37 |

Decision counts use the unchanged diagnostic threshold of 0.5. Units are cell-days,
not independent fire incidents or measured staffing requirements.

XGBoost 17 improves the ranking relative to both logistic references and slightly
relative to persistence on this validation interval. However, its binary alerts
are exactly the same as persistence at this threshold. A ranking gain has not
established a reduction in false alerts or additional fire detections.

For cells without a current detection, XGBoost 17 identifies zero of 37 positives
at threshold 0.5. Its AP is 0.1228, below the constant-score reference of 0.1595
for that subset. Overall performance is dominated by continuation of existing
detections. The environmental 16-input XGBoost identifies 18 of 37 positives but
issues 90 false alerts in this subset, so that result also needs careful review.

## What remains before a final model claim

1. Check sensitivity to time intervals using development observations only.
2. Examine the limited new-detection ranking separately from continuing fire.
3. Design out-of-sample probability reliability/calibration and alert trade-offs.
4. Freeze the complete pipeline, then evaluate once on the protected temporal test.

No labels were changed or difficult validation dates removed. The 22 December
observation-quality question remains open. These nine dependent validation days,
already used for model development and stopping, do not establish year-to-year
performance. Class-weighted sigmoid scores are not automatically calibrated
probabilities or operational warnings.

## Reproduce and code organisation

```powershell
.\.venv\Scripts\python.exe -m bushfire_ml.xgboost_experiment
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

- `models.py`: short fitting functions for logistic regression and XGBoost.
- `evaluation.py`: shared metric definitions and reliability bins.
- `reporting.py`: aggregate tables and figures, separate from fitting.
- `xgboost_experiment.py`: load, fit, predict and compare on development data.
- [Settings recorded before fitting](../../research/config/xgboost_v1.json)
- [Results and comparison figure](../../research/reports/xgboost_comparison.md)

## Oral review explanation

> We chose XGBoost to test nonlinear relationships and interactions among the
> same weather, terrain and current-fire inputs used by our logistic baselines.
> It adds shallow decision trees sequentially to improve a regularised objective.
> We controlled complexity and used validation AP for early stopping. It improved
> overall validation ranking, but its alerts matched persistence at the fixed
> threshold and it did not improve new detections. The final test remains sealed.

## Primary sources and disclosure

- [XGBoost: introduction to boosted trees](https://xgboost.readthedocs.io/en/stable/tutorials/model.html)
- [XGBoost parameter definitions](https://xgboost.readthedocs.io/en/stable/parameter.html)
- [Early stopping and the sklearn interface](https://xgboost.readthedocs.io/en/stable/python/sklearn_estimator.html)
- [Callable metrics and maximisation](https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.callback.EarlyStopping)
- [Chen and Guestrin, 2016: XGBoost](https://arxiv.org/abs/1603.02754)

The implementation, experiments, tests, source review and explanation were
AI-assisted. Keep prompts/outputs and record team verification for the appendix.
