# Planned work and implemented work

This comparison distinguishes the user-supplied proposal and later team
specification from the method actually implemented and evaluated. The final
frozen evidence governs claims about completed work.

| Planned or suggested item | Implemented decision | Reason and evidence |
| --- | --- | --- |
| Daily bushfire-risk prototype | Next-UTC-day eligible VIIRS detection per retained cell | Observable target includes ongoing fire; it is not ignition or physical severity. [Protocol](../research/config/protocol_v1.json) |
| Weather, terrain and satellite fuel-moisture/vegetation inputs | Sixteen weather/terrain inputs, then one audited current-detection flag | No NDVI/fuel-moisture input is present in the approved model matrix. [Feature review](../docs/technical/feature_catalog.md) |
| All 23 inputs in the later specification | Matched 16-input and 17-input experiments | Long rainfall windows have warm-up gaps and dry-spell initialisation has unknown prior history. Additional current-fire inputs were not enabled. [Audit](../research/reports/development_audit.md) |
| Interleaved weekly splits in the later specification | Chronological supplier test boundary plus seven-day development gaps | Avoid training on later dates to predict earlier periods. Gaps reduce adjacency but do not prove independent events. [Frozen split](../research/reports/partition_manifest.json) |
| Chronologically held-out season | Later portion of the supplied season | This is retrospective temporal holdout evidence with earlier aggregate disclosure, not an unseen-season or double-blind study. [Final manifest](../research/reports/final_freeze.json) |
| PR-AUC and built-in `aucpr` stopping | Explicit sklearn average precision, explicitly maximised for stopping | Do not silently mix interpolated PR-AUC definitions with AP. [Model code](../research/bushfire_ml/models.py) |
| Validation search over multiple XGBoost settings | One shallow configuration plus past-only tree-count selection | Sparse early positives and limited development support constrained model complexity. [XGBoost settings](../research/config/xgboost_v1.json) |
| Random Forest if time permits | Not implemented | Do not describe an optional model as evaluated. Existing comparisons cover constant prevalence, persistence, logistic and XGBoost. |
| Probability output and a high-recall warning threshold | Calibration tested but unadopted; two raw-score research policies frozen | Later probability checks were inconsistent or too small. Neither recall target transferred to final data. [Reliability](../research/reports/probability_reliability.md), [final result](../research/reports/final_holdout.md) |
| SHAP explanation of the final model | No SHAP analysis delivered | Earlier tree inspection is illustrative, not a SHAP or causal analysis. [XGBoost lesson](../docs/lessons/lesson_05_xgboost.md) |
| Risk-map proof of concept | ML scores and reviewable evidence; no operational map service | Raw percentages were not validated, and real publication latency was not simulated. Study-area map integration remains with the group editor/data owner. |
| Five-fold mean/spread over interleaved weeks | Explicit past-only forward-window diagnostics and one frozen final release | Missing-class windows remain visible; dependent overlapping periods are not treated as independent replications. [Temporal report](../research/reports/temporal_stability.md) |

The supplied course template contains fictional examples. Its random-split,
notebook, feature-selection and high-accuracy claims are not evidence of work
done here. Keep its useful report structure while replacing the example text
with the recorded method and measured findings.
