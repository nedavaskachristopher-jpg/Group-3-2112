# Kian ML engineering and coordination workspace

Kian coordinates the whole group's workflow while retaining ownership of ML engineering. Start with [WORKFLOW.md](../../WORKFLOW.md) and the [task board](../TASK_BOARD.md).

## Coordination duties

Keep tasks assigned, dependencies visible and dates agreed. Follow up on missing handoffs, connect owners/reviewers and track integration readiness. Chris assembles the report; Jin and Seb remain accountable for their own technical contributions. Record substantive scope/technical choices in [DECISIONS.md](../DECISIONS.md) and actual work/reviews in [CONTRIBUTIONS.md](../CONTRIBUTIONS.md).

## Your files

- [ML_HANDOFF.md](ML_HANDOFF.md): current model/result evidence and open engineering checks.
- [ERROR_ANALYSIS.md](ERROR_ANALYSIS.md): a working structure for representative forward-test errors.
- [REPORT_SECTION.md](REPORT_SECTION.md): a concise methods/results contribution for integration.

## Authoritative implementation

- [Training/evaluation](../../src/train_evaluate.py), [inference](../../src/predict.py) and [verification](../../src/verify_results.py).
- [Executed notebook](../../output/Kian_ML_Analysis.ipynb).
- [Feature contract](../../output/feature_contract.json), [model metadata](../../output/models/chronological_xgb_full.json) and [run manifest](../../output/results/run_manifest.json).
- [Metrics](../../output/results/metrics.csv), [prediction records](../../output/results/predictions.csv) and [model card](../../docs/MODEL_CARD.md).

## Next engineering work

Close tasks M-01 to M-04: review the handoff, fix verification, arrange a teammate's inference reproduction and complete bounded error analysis. Keep model changes separate from organisational/documentation changes. Existing AI-assisted artifacts need actual member checking and interpretation; update the assistance/contribution record with what you performed.
