# Revised model card

## Target and inputs

One row represents a retained ERA5-Land grid cell and completed UTC feature day.
The target is an eligible VIIRS detection in its park portion on the next UTC
day, including continuing fire. It is not confirmed ignition, severity, spread
or an official danger rating. Reanalysis and satellite publication latency are
not reproduced.

The conditions-only comparison has 16 inputs; the selected version adds the
audited same-day `fire_today` flag. Longer rainfall/dry-history and other recent-
fire candidates remain disabled. The ordered list, availability and score meaning
are in the [feature catalogue](technical/feature_catalog.md) and
[contract](technical/model_contract.json). NDVI/fuel moisture, Random Forest and
new SHAP analysis were not implemented.

## Method and evaluation

Compare training prevalence, persistence, logistic regression and XGBoost on
matched 16/17-input populations. Training-only scaling/class weights and
explicit AP stopping are recorded. Chronological partitions have seven-day
gaps; rainfall warm-up removes the first two training dates. Later time checks
select and refit tree counts on past data. Final XGBoost 17 has eight trees.

Calibration was tested in separate development designs but not adopted.
The frozen raw cutoffs are 0.6658568382263184 and 0.4193871319293976, with inclusive
comparisons. Their names denote 80%/90% development recall targets, not final
guarantees. The committed freeze precedes one release; no final fitting or tuning
occurred. The original study is [versioned evidence](../research/reports/README.md).

## Final findings

The 7,783 cell-days contain 49 positive targets. The higher cutoff gives 16 TP,
39 FP and 33 FN (32.7% recall, 29.1% precision). The lower gives 34 TP, 2,434 FP
and 15 FN (69.4% recall, 1.38% precision). The higher policy matches persistence
counts. Without current detections it finds none of 33 positives; the lower finds
18 with 2,395 false alerts. XGBoost 17 AP is 0.1062, persistence 0.0992 and the
prespecified logistic 17 comparison 0.2113. All calendar months remain reported.

Raw scores substantially overstate observed frequencies. A constant no-alert
answer reaches 99.37% accuracy while missing every positive. These results do
not establish reliable warnings or calibrated probabilities. See the
[complete final report](../research/reports/final_holdout.md).

## Scope and use

Both old and revised experiments identify the same 2019-20 source table and
overlapping dates/cells. Different features and populations prevent a direct
algorithm ranking from their headline AP values. The one-time protected release
is not a new independent season or previously unknown dataset.

Public review uses cached aggregates. Optional inference requires a privately
supplied exact model, rejects labels/final-period rows and returns both unchanged
policies. The new map illustrates original cached scores on the first frozen
date. Old SHAP and maps remain historical. No live weather API, validated multi-
day model, incident-level generalisation or operational deployment is delivered.

Future work needs independent seasons/events, stronger observation/ignition
labels, point-in-time inputs, fuel information and stakeholder-agreed evaluation
of false-alert/missed-detection costs. Human source review remains pending.
