# Evidence index

These are the original aggregate evidence files, in chronological research
order. They remain unchanged. Development results must not be presented as
independent final evidence, and historical sealing flags describe their time
of creation.

| Stage | Human-readable evidence | Machine-readable source |
| --- | --- | --- |
| Partition acceptance | [Partition manifest](partition_manifest.json) | Same manifest; geography/date counts and hashes |
| Development audit | [Audit](development_audit.md) | [Audit JSON](development_audit.json) |
| Initial baselines | [Baseline report](baseline_validation.md) | [Baseline JSON](baseline_validation.json) |
| Error analysis | [Errors](baseline_error_analysis.md) | [Errors JSON](baseline_error_analysis.json) |
| Audited current-fire feature | [Matched logistic comparison](current_fire_comparison.md) | [Comparison JSON](current_fire_comparison.json) |
| First XGBoost comparison | [XGBoost report](xgboost_comparison.md) | [XGBoost JSON](xgboost_comparison.json) |
| Time stability | [Temporal report](temporal_stability.md) | [Temporal JSON](temporal_stability.json) |
| Reliability and cutoff selection | [Probability report](probability_reliability.md) | [Probability JSON](probability_reliability.json) |
| Development policy candidate | [Draft policy](draft_probability_policy.json) | Historical candidate, superseded by the frozen manifest |
| Committed final freeze | [Frozen plan](final_freeze.json) | Exact models, cutoffs, versions and source hashes |
| Single final evaluation | [Final report](final_holdout.md) | [Final JSON](final_holdout.json) |
| Final access status | [Release receipt](final_release.json) | One release, aggregate/prediction hashes and freeze commit |

PNG figures beside the relevant reports are the original rendered outputs.
The [handover tables](../../report/tables/README.md) provide aggregate CSV exports
for report editing. The [claim catalogue](../../docs/evidence/claims.json)
maps exported values back to JSON paths. No row-level labels or predictions
are published.
