# Frozen-result error analysis

Use the [final aggregate](../../research/reports/final_holdout.json) and
[final report](../../research/reports/final_holdout.md). No new metrics are
computed from final labels during integration.

| Existing observation | Implication | Limit |
| --- | --- | --- |
| Higher cutoff: 16 TP, 39 FP, 33 FN | Fewer alerts, substantial missed detections | These are cell-days, not independent incidents |
| Lower cutoff: 34 TP, 2,434 FP, 15 FN | More detections at a much larger review burden | Staffing/cost acceptability has not been established |
| Without current detections: higher cutoff misses all 33 positives | Current-fire information does not establish new-ignition warning ability | The subset is a detection transition, not confirmed ignition |
| Lower cutoff in that subset: 18 TP, 2,395 FP | Limited recall gain comes with many false alerts | Satellite non-detection is an imperfect negative label |
| Logistic 17 AP 0.2113 exceeds XGBoost 17 AP 0.1062 | Nonlinear complexity did not establish better final ranking | Do not replace the frozen primary model after seeing results |
| Zero-positive later months remain reported | Accuracy can look high without useful detection | Observation coverage requires data-owner review |
| Raw-score frequencies are overstated | Percentages cannot be trusted as event probabilities | No correction is fitted on final outcomes |

The cached first-date map is illustrative, not a representative-case performance
claim. No event causes or individual fire histories are invented. Further
case-level interpretation would require independent event/coverage evidence;
any outcome-motivated modelling belongs to a new development cycle.
