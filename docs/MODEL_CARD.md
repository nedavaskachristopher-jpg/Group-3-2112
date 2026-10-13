# Model card

## Prediction target and inputs

For each retained weather grid cell and completed UTC feature day, predict eligible satellite active-fire detection inside the park on the following day. There are 23 full-model inputs: eight weather features, six rainfall/dryness features, six terrain features and three recent-fire features. The conditions-only variant omits the three recent-fire features.

The full feature names and definitions are in `output/feature_contract.json`. Dates, grid identifiers, coordinates and tomorrow's detection count/label are excluded from model predictors. Day-complete features and satellite observations must be available before inference; the experiment does not simulate operational data latency.

## Training and evaluation

The dataset covers the 2019–20 Blue Mountains fire season. Positive records receive additional training weight. Logistic Regression tries four regularisation settings; XGBoost tries twelve parameter configurations with early stopping. Model settings and alert thresholds are chosen using validation only. The threshold maximises validation precision subject to validation recall of at least 0.80; this does not guarantee test recall of 0.80.

Prevalence and persistence baselines are compared with full and conditions-only learned models. Interleaved weekly partitions and five-fold evaluation measure within-season interpolation and can train on weeks after test dates. The forward experiment trains on earlier dates, validates on later December dates and tests January onwards, with boundary gaps.

## Observed performance

Full XGBoost weekly AP is 0.823682, with 82 TP, 16 FP and 25 FN. Five-fold mean AP is 0.692174 (sample SD 0.093025). Forward AP is 0.185871, with 13 TP, 35 FP and 32 FN. Forward recall is 0.288889. All 32 no-fire-today positive test rows are missed at the selected full-model threshold.

Counts refer to cell-days, not independent fire events. The `new_fire` evaluation name denotes no detection on the feature day, not confirmed ignition. Stored AP, trapezoidal PR area and XGBoost's training `aucpr` are distinct measures.

## Use and limitations

Suitable for reproducing a coursework experiment and investigating retrospective ranking. The current evidence does not establish prospective warning performance. Scores are uncalibrated and must not be presented as official warnings or percentages of ignition risk.

Limitations include a single season, correlated ongoing fire events, overlapping rolling histories, incomplete initial rainfall history, satellite detection errors, coarse spatial aggregation, missing direct fuel information, retrospective weather data and a threshold that transfers poorly to later dates. SHAP explains fitted model behaviour and does not establish causality.

Further validation should use multiple independent seasons, event-aware evaluation, stronger labels, fuel information, point-in-time feature availability, independent calibration data and stakeholder-defined alert costs.
