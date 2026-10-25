# Lesson 6: does performance hold across time?

## The question

A pooled score can hide days with many false alerts or missed detections. We
ask whether the apparent gain over persistence remains visible in different
periods, using development observations only. We keep the original labels,
seven-day embargoes, feature whitelist and protected final test unchanged.

The answer from these checks is that dependable temporal stability has not
been established. The detailed values and figure are generated from the
[temporal results](../../research/reports/temporal_stability.md).

## Two different checks

First, we reuse the saved model scores and report every validation day plus
three consecutive three-day blocks. These reveal where the existing model
succeeds or fails. They do not create new independent tests: those same nine
validation days were already used to choose the original XGBoost tree count.

Second, we simulate moving forward through four calendar windows. For every
window, training and model selection use earlier observations only. A model
never uses a later window to predict an earlier window. All grid cells from
the same day remain together.

The calendar windows were chosen after inspecting development label coverage
and the original validation slices, before these new fits. This is a
retrospective development diagnostic, not a previously unseen evaluation.
The final holdout is the reserved evaluation after complete pipeline freeze.

## Keeping early stopping out of the checked period

Simply fitting XGBoost with the checked period as `eval_set` would allow its
answers to choose the number of trees. Instead, each forward check follows
this sequence:

1. Set the outer checking dates and reserve the preceding seven calendar days.
2. Use the latest seven days before that gap as the inner stopping window.
3. Leave another seven-day gap before that stopping window. Fit the selection
   model on earlier rows and choose its tree count using only the stopping rows.
4. Refit that fixed count on all available past development rows before the
   outer gap. This can include the old inner gap and stopping rows because they
   are now past observations. Do not supply an evaluation set during refitting.
5. Fit logistic regression on those identical refitting rows. Compute scaling,
   class weights and the constant prevalence score from those rows only.
6. Predict the later checking dates, then calculate metrics. Repeat with the
   next outer window, allowing past observations to join its training history.

For the final development window, the inner fit ends on 24 November, inner
stopping runs from 2 to 8 December, refitting ends on 8 December, and checking
runs from 16 to 24 December. The intervening calendar days provide the gaps.
The frozen 9 to 15 December embargo rows are never loaded.

The two earlier stopping windows have no positive examples. Our AP-based
stopping procedure cannot meaningfully select trees from them. We explicitly
mark XGBoost unavailable for those windows and retain the other models and
evaluation dates. This is a limitation of the specified procedure and available
data; it does not mean XGBoost software cannot be trained without early stopping.

## Reading the findings correctly

- Compare algorithms on the same window. AP also changes with the positive
  rate, so an AP decline across periods does not by itself prove deterioration.
- Include persistence. The original model's modest AP advantage produces the
  same alerts at 0.5, and the past-only checks do not show a consistent AP win.
- Inspect cell-days with no current detection. This separates future
  detections in currently unflagged cells from continuation of existing fire.
  It still does not establish confirmed new ignitions.
- Keep zero-positive dates. AP and recall are undefined on such dates, but
  false alerts and probability errors can still be reported. The feature date
  21 December predicts target date 22 December and retains the known
  observation-quality concern without changing its label.
- Keep unavailable windows visible. An average of just the available XGBoost
  windows would conceal the lack of early positive examples.
- A positive cell-day is not an independent fire incident. Shared cells,
  consecutive days and ongoing fires make these observations dependent.

The sparse early fits and changing event prevalence limit what we can infer.
These data do not separate the causes of poor transfer, nor do they establish
performance in another year. Seven-day gaps reduce adjacency but cannot make
long fire events independent. No confidence interval or four-fold average is
claimed from these dependent, partially unavailable comparisons.

## What this means for percentages

Ranking performance and probability reliability answer different questions.
A model can order some ongoing fires reasonably well while its displayed
percentages are inaccurate or its threshold produces the same alerts as
persistence. These results do not justify presenting raw scores as trusted
fire-risk percentages.

The next stage is to design development-only out-of-sample probability checks
and inspect false-alert versus missed-detection trade-offs. The small number
of usable time windows may prevent a defensible calibration claim. Record that
limitation instead of using the final test to fit a calibrator or choose a
threshold. More seasons or independent events would strengthen later evidence.

## Verification and reproduction

```powershell
.\.venv\Scripts\python.exe -m bushfire_ml.temporal_stability
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The added checks cover calendar gaps, complete grid-day groups, missing-class
stopping windows, fixed-tree refitting, zero-positive metrics and outer-answer
isolation. The last check changes only outer labels and verifies that all
fitted prediction scores and chosen tree counts stay identical. It does not
prove the absence of every possible data-quality issue.

All row-level forward predictions remain in ignored local storage. Public
artifacts contain aggregate metrics, hashes, configuration and the figure.
Original baseline reports and data hashes are verified and left unchanged.

## Oral review explanation

> We checked whether a good pooled score held across different dates. We first
> described the saved validation predictions by day and by three-day block.
> We then used earlier data to select the number of trees, refitted on past
> observations, and predicted later windows with seven-day gaps. Early positive
> examples were too scarce for some comparisons. The model did not consistently
> outperform persistence, so we cannot claim stable performance or reliable
> risk percentages. The final test remains sealed.

## References and disclosure

- [scikit-learn: temporal evaluation](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-of-time-series-data)
- [XGBoost: early stopping](https://xgboost.readthedocs.io/en/stable/python/sklearn_estimator.html#early-stopping)

The experiment, explanation, code, reports and checks were AI-assisted. Team
members should inspect the configuration, reproduce the run and retain the
prompt/output and verification records needed for the course AI-use appendix.
