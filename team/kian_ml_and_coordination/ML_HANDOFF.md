# ML evidence handoff

Owner: Kian. Data reviewer: Jin. Interpretation reviewer: Seb. Report integrator: Chris.

## Existing results

| Full XGBoost evaluation | AP | Recall | Precision | TP | FP | FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Weekly holdout | 0.823682 | 0.766355 | 0.836735 | 82 | 16 | 25 |
| Strictly forward | 0.185871 | 0.288889 | 0.270833 | 13 | 35 | 32 |

Five-fold within-season mean AP is 0.692174, with sample SD 0.093025. The forward no-fire-today subset has 32 positives; none triggered a full-model alert at its validation-selected threshold. Counts describe cell-days, not independent incidents. Check final report numbers against [metrics.csv](../../output/results/metrics.csv), not rounded examples alone.

Full models use 23 predictors; conditions-only models omit the three recent-fire predictors. Weights, preprocessing, tuning and thresholds are fitted within the designated training/validation partitions. Weekly/blocked experiments measure same-season interpolation and can use later training weeks. The forward test uses earlier fitting dates but still covers the same season/cells. Raw percentage-formatted scores are uncalibrated; current models predict the next UTC day only.

## Open checks and completion evidence

- [x] Data interface signed off with Jin using [DATA_HANDOFF.md](../jin_data_engineering/DATA_HANDOFF.md); the final source-level audit passes 52 verifiable checks and records two observation/absence limitations.
- [ ] Model verification reads delivered UBJ files without rewriting them. Healthy artifacts pass and corrupt/missing files fail; regression checks preserve model hashes.
- [ ] Another member reproduces prepared inference from repository instructions; record environment, command, expected comparison and outcome.
- [ ] Representative errors reviewed with Seb/Jin in [ERROR_ANALYSIS.md](ERROR_ANALYSIS.md).
- [ ] Methods/results/limitations use consistent targets, partitions, metrics and evaluated versions.
- [ ] Actual human checks, edits and AI assistance recorded.

## Prepared inference demonstration

From the repository root, install `requirements.txt` in a Python 3.12 environment, then run:

```powershell
python src/predict.py --input output/example_features.csv --model output/models/chronological_xgb_full.json --output output/reproduced_example_scores.csv
```

Compare raw scores and alerts with [example_scores.csv](../../output/example_scores.csv), allowing the documented numerical tolerance. Percentage rounding is presentation only. The interface consumes already prepared feature rows and does not download live weather.

| Demonstration record | Actual value |
| --- | --- |
| Member/machine/date | To be completed |
| Environment and command | To be completed |
| Score/alert comparison | To be completed |
| Remaining issue | To be completed |

## Next actions after the data audit

1. Preserve the audited label wording in all ML and report text: zero means no eligible FIRMS detection in the supplied archive, not confirmed fire absence.
2. Keep the current final test results unchanged. It is already exposed and cannot be reused as a fresh blind test after further tuning.
3. Complete model-artifact verification without rewriting UBJ files: healthy artifacts must pass, missing/corrupt artifacts must fail, and model hashes must remain unchanged.
4. Ask another member to reproduce prepared inference from the command above and record the environment, comparison and outcome.
5. Complete the representative forward-test error analysis with Seb and the Data Engineer, including false alerts, misses and dates with no recorded positives.
6. Check that the final methods, results and limitations use the same target, 23/20 predictors, `park_area_fraction >= 0.10` filter, temporal partitions and evaluated versions.
7. Record actual human checks and AI assistance. If the team continues model development, reserve independent additional seasons or events for the next final validation.
