# Lesson 8: freeze the research pipeline, then evaluate once

Kian explicitly authorised freezing both research thresholds and performing
one final evaluation. This document records the procedure before release.
Its execution status is recorded in the committed freeze, final report and
release receipt, rather than by rewriting historical development records.

## Frozen research question and population

Predict whether a retained Blue Mountains National Park grid cell has at
least one eligible VIIRS detection on the next UTC day. The label includes
continuing fire; it is not confirmed ignition, severity or a fire-spread map.
Non-detection does not prove that no fire occurred.

The protected evaluation has 7,783 cell-days across 43 previously retained
cells, with feature dates 1 January to 29 June 2020. These dimensions were
known from the original date/geography split, without profiling outcomes.
Every sealed row, date and calendar month must be retained. No missing-data
policy, difficult-date exclusion or alternative label is introduced after
release. The original area fraction rule and feature whitelist are unchanged.

The supplier's aggregate summaries and the team's season-level information
were previously available. This is a protected retrospective temporal
holdout, not a double-blind study or an unseen fire season. Publication latency
of the retrospective ERA5 and VIIRS inputs is not reproduced.

## Frozen model and comparisons

The primary model is the existing, saved eight-tree XGBoost with seventeen
approved inputs: sixteen weather/terrain inputs plus the audited `fire_today`
flag. It was refitted through feature date 8 December 2019, using 6,837 rows
after warm-up removal. Its tree count was selected using earlier stopping
data, without the final test. The model is copied byte-for-byte; no training
is performed during freezing or final evaluation.

Calibration is not adopted, following the development reliability check.
The output remains an experimental raw score. We preserve both development
selection policies without a test-based choice between them:

| Development recall target | Exact raw-score cutoff | Comparison |
| --- | ---: | --- |
| At least 80% | 0.6658568382263184 | score >= cutoff |
| At least 90% | 0.4193871319293976 | score >= cutoff |

The targets describe selection rows, not promised final recall. Use the exact
JSON values. Rounding an inclusive cutoff can change decisions for an entire
tied group.

The prespecified comparisons are training prevalence, persistence, and matched
16/17-input logistic and XGBoost models. All four fitted artifacts come from
the same recent-model development scenario. Logistic scalers remain embedded
in their saved training-fitted pipelines; XGBoost inputs are not scaled.
The sixteen-input XGBoost has six trees. Original experiment reports are not
overwritten or relabelled as final results.

## Frozen reporting rules

- Primary ranking metric: scikit-learn average precision on raw scores.
- Additional evidence: precision, recall, F1, accuracy, confusion counts,
  Brier score, log loss and cell-day alert burden. Accuracy is secondary.
- Report both selected policies alongside persistence. A cutoff of 0.5 is
  retained only as the diagnostic reference for all model comparisons.
- Report the entire population and the subset with `fire_today == 0`, keeping
  both target classes wherever present. This is not confirmed ignition detection.
- Report every calendar month from January through June, including zero-positive
  months. AP and recall are undefined with no positives; false alerts remain valid.
- Show five fixed-width reliability bins. Brier and log loss measure overall
  probability quality, not calibration alone. Do not fit calibration here.
- AP can change with prevalence. Do not call cross-period changes isolated
  evidence of model deterioration or improvement.
- PR curves are sampled to at most the fixed display limit; AP uses all scores.
- Cells, dates and ongoing fires are dependent. Do not invent independent-event
  confidence claims or staffing savings from cell-day counts.

## Freeze before opening outcomes

Run the full synthetic/unit checks first. The freeze command verifies the data
seal, reviewed development references and saved-model hashes. It copies the
four model files to a separate ignored snapshot directory and writes a manifest
with exact features, preprocessing, model hashes, both cutoffs, metrics, software
versions, source hashes and the known test population.

The manifest is created exclusively and is never silently overwritten. Text
hashes normalise LF/CRLF source newlines; model and data hashes use exact bytes.
The complete freeze, runner, checks and plan are committed before release. The
dedicated final runner rejects an uncommitted or modified frozen source, changed
artifacts, changed data seal or a different runtime.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m bushfire_ml.freeze_final
# Commit the complete reviewed freeze before the next command.
.\.venv\Scripts\python.exe -m bushfire_ml.final_release
```

Development loaders continue to reject final-test access. Only the authorised
final runner parses the approved holdout columns after verifying the committed
freeze. Target-day detection counts and other excluded columns are not loaded
as predictors.

## One-time release and recovery

The runner claims release using an exclusively created local receipt before
the first CSV parse. It validates every frozen grid/date pair, predicts from
saved models without fitting, and computes all frozen comparisons in one run.
Row-level predictions remain ignored, while aggregate results and a public
release receipt are saved for review.

If plotting fails after aggregate results have been cached, reporting can
resume from that cache without reopening the holdout or rerunning prediction.
A completed repeat command returns cached results only. An interrupted release
before a valid cache exists is recorded and refuses an automatic retry; a crash
cannot silently restore the claim that the outcomes were never opened.

The original preparation seal is historical and is preserved. It must not be
edited to update its old `holdout_evaluated` field. The final-release receipt
records the later status and links the exact freeze and aggregate hashes.

These controls are an auditable workflow, not encryption or access control.
They do not prevent a human with filesystem access from bypassing the scripts.
The result must be described honestly as a single protected temporal evaluation.

## After release

Keep both policies and report disappointing results. Do not use the test to
select a new cutoff, choose a favourite month, remove false alarms, adjust
class weights, refit a calibrator or replace the model. Further development
requires new independent evaluation data and must be distinguished from this
first final result. Reformatting cached results does not create another blind
evaluation or justify changing the frozen analysis.

The next project deliverable is the ML handover: methods, final findings,
limitations, reproducible commands, figures and review notes for the group report.
The implementation and documentation were AI-assisted; retain prompts, outputs
and team verification for the course appendix.
