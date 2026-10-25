# Revised ML handoff

The evaluated implementation is [research/](../../research/README.md). Exact
features and outputs are in the [contract](../../docs/technical/model_contract.json).
Use the [runbook](../../docs/technical/runbook.md),
[final evidence](../../research/reports/final_holdout.md),
[English ML sections](../../report/ml_sections.md) and
[integrated draft](../../report/group_report.md).

The final primary model is eight-tree XGBoost 17. Inputs, preprocessing, artifact
identity, uncalibrated score decision and both inclusive cutoffs remain frozen.
The one-time receipt still records one evaluation and one final CSV read.
Poor final results and the stronger logistic ranking are retained honestly.

Public results, verification, notebook review and CI need no private model.
Optional inference needs the exact private model; final dates are blocked.
The map reads the original score cache only. There is no new SHAP or live API.

The two experiments use the same original table. This is protected retrospective
evaluation, not a new independent season. Human data/domain/author review is
pending and must be recorded by the responsible members.
