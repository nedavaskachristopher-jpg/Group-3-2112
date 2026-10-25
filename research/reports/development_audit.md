# Development data audit

Development data only; final-test outcomes were not profiled or scored.

Verified 65 source-file hashes and all 16 supplier provenance hashes.

## Frozen partitions

| Partition | Feature dates (UTC) | Rows |
| --- | --- | ---: |
| train | 2019-07-01 to 2019-12-08 | 6,923 |
| validation | 2019-12-16 to 2019-12-24 | 387 |
| final_test | 2020-01-01 to 2020-06-29 | 7,783 |

The two seven-day gaps contain 602 excluded rows. Whole feature dates are assigned together.

## Development label balance

| Partition | Positive cell-days | Positive rate | All-negative accuracy |
| --- | ---: | ---: | ---: |
| train | 143 | 2.07% | 97.93% |
| validation | 160 | 41.34% | 58.66% |

Final-test label counts, example outcomes and model scores are intentionally absent.

## Checks

- PASS: unique grid date keys.
- PASS: no missing development values.
- PASS: binary development target.
- PASS: next day target.
- PASS: label matches eligible target count.
- PASS: target count accounting.
- PASS: fire today matches same day label.
- PASS: humidity in range.
- PASS: temperature order.
- PASS: nonnegative weather.
- PASS: terrain static per grid.
- PASS: base extended shared fields agree.
- PASS: daily weather recomputed from raw.
- PASS: precipitation 3d causal window.
- PASS: precipitation 7d causal window.
- PASS: precipitation 30d causal window.
- PASS: precipitation 90d causal window.
- PASS: fire last7 includes today only and past.
- PASS: rain history length.
- PASS: dry spell initialisation reproduced.
- PASS: fire neighbour is current day 8 neighbour flag.

## Findings and limits

- The 39-column extended table has no supplied generation script or complete data dictionary; its shared fields and eight additions were independently checked on development data.
- The 7/30/90-day rainfall sums include a 30 June 2019 accumulation from the 1 July 00 UTC weather record. Early windows are partial, not full-duration histories.
- The dry-spell counter starts at 120 without 120 days of preceding observations. Treat these initial values as unknown; exclude or repair before using extended features.
- The first two development feature days have incomplete three-day rainfall history. Drop these warm-up rows before the first core-feature fit.
- Validation is a short high-fire interval with a much larger positive rate than training. Probability calibration and threshold stability need development-only checks.
- Seven-day gaps reduce adjacency but do not guarantee that long-lived fire events are independent across partitions.
- No independent-season or independent-location generalisation is demonstrated.
- Terrain extraction and raw point-to-polygon fire labelling were reviewed in the supplied scripts, not independently rerun with GIS software.
- Known prescribed burns are partially excluded using retrospective fire-history polygons. Satellite non-detection is not confirmed absence of fire.
- ERA5-Land reanalysis and full-day satellite archives do not reproduce real-time data publication latency.

## Next lesson

Fit simple baselines on the training partition, using only the 16 approved core conditions features. Remove the first two warm-up days. Inspect validation results only. Keep the final test sealed. No estimator has been fitted in this stage.
