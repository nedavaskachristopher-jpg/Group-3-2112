# ML methods and findings contribution

Owner: Kian. This concise starting text reflects existing artifacts and requires the owner's final review and connection to the complete report.

We modelled eligible next-day active-fire detection on park-intersecting ERA5-Land cells. The full input has 23 weather, antecedent-rainfall, terrain and recent-fire features. A conditions-only variant omits the three recent-fire features. Target-day counts, labels, dates, identifiers and coordinates were excluded from the primary predictors. The main panel retained cells with at least 10% park overlap.

Prevalence and persistence baselines were compared with weighted Logistic Regression and XGBoost. Logistic Regression used training-fitted preprocessing. Model settings, early stopping and alert thresholds were selected on validation data; the threshold maximised validation precision subject to recall of at least 0.80. Test data were used for evaluation. AP, confusion counts, precision, recall, F1 and Brier score described ranking, alert errors and score quality. No-fire-today subsets were evaluated at the same thresholds.

Weekly holdout and five-fold blocked experiments assessed within-season interpolation; they can include training weeks after test dates. A separate forward test fitted earlier dates and evaluated later dates with boundary gaps. The available panel did not support the independently heldout fire season proposed originally.

Full XGBoost weekly AP was 0.824, with 82 true positives, 16 false positives and 25 false negatives. Five-fold mean AP was 0.692 with sample SD 0.093. Forward AP was 0.186 and recall was 0.289: 13 of 45 positive cell-days were detected, with 35 false positives. None of the 32 forward positives without feature-day fire detection triggered an alert at the full-model threshold. Strong overall ranking therefore did not establish a reliable new-fire alert rule.

The current evidence is retrospective and single-season. Continuing fire, event dependence, partial initial rainfall history, proxy labels, absent direct fuel information and point-in-time availability limit interpretation. Percentage display does not calibrate model scores. Existing SHAP analysis describes fitted-model associations rather than causal effects. Representative error analysis and the saved-model verification correction should be linked when completed.

Final owner checks and additional error-analysis paragraph: To be completed. See the [model card](../../docs/MODEL_CARD.md), [run manifest](../../output/results/run_manifest.json), [metrics](../../output/results/metrics.csv) and [ML handoff](ML_HANDOFF.md) for the supporting artifacts.
