# Final data audit

Date: 25 October 2026. Scope: data provenance, label construction, date alignment and observation coverage. This audit does not retrain a model or tune against the exposed final test period.

## Outcome

The data handoff passes all 52 verifiable checks. Two non-critical questions remain not independently verifiable, so the overall result is `pass_with_limitations`:

1. The FIRMS archive contains active-fire detections, not a record of every successful satellite overpass or clear-sky observation opportunity.
2. No independent incident or observation-availability panel was supplied to confirm fire absence on zero-label dates.

Accordingly, `fire_positive = 0` means **no eligible FIRMS detection was present in the supplied archive for that cell and UTC date**. It must not be described as proof that no fire occurred.

The complete machine-readable evidence is in [`data_handoff_audit.json`](../../output/results/data_handoff_audit.json). Reproduce it from the repository root with:

```powershell
python src/audit_data_handoff.py --source-root "C:\path\to\the\retained\Dataset"
```

## Verified handoff

| Check | Result |
| --- | --- |
| Prepared panel | 18,980 rows: 52 cells by 365 feature dates |
| Main modelling subset | 15,695 rows, 43 cells and 566 positive targets after `park_area_fraction >= 0.10` |
| Date alignment | Every model target date equals its feature date plus one day |
| Label rule | `eligible = raw - prescribed`; `fire_positive = 1` when eligible detections are greater than zero |
| Input identity | Extended-table SHA-256 matches the training run manifest |
| Repository provenance | All listed model-ready file hashes verified |
| Retained source provenance | 16 of 16 source hashes and 6 of 6 raw-download manifest hashes verified |
| ERA5-Land | All 12 months and 8,784 continuous hours verified; `t2m`, `d2m`, `tp`, `u10` and `v10` have no missing values |
| FIRMS cleaning | The supplied clean table was exactly reconstructed from the archive and park boundary |
| Daily labels | The supplied 52-cell daily label panel was exactly reconstructed |
| Fire-history date window | The current subset omitted no polygon that overlapped the study period |

## FIRMS and label audit

The archive contains 44,211 records, including 40,320 in the 2019-07-01 to 2020-06-30 study period. Retaining normal/high confidence and points inside Blue Mountains National Park gives 17,290 clean records: 15,954 normal-confidence and 1,336 high-confidence records. Whole-row duplicate removal removed zero records. One dated prescribed-burn polygon matched 18 detections; these were retained in audit counts but removed from eligible labels. The remaining 17,272 eligible detections produced 578 positive cell-days on the original 52-cell panel and 566 positive targets after the park-overlap filter.

| Month | Raw detections | Prescribed-burn detections | Eligible detections | Positive cell-days |
| --- | ---: | ---: | ---: | ---: |
| 2019-07 | 0 | 0 | 0 | 0 |
| 2019-08 | 35 | 18 | 17 | 4 |
| 2019-09 | 0 | 0 | 0 | 0 |
| 2019-10 | 0 | 0 | 0 | 0 |
| 2019-11 | 295 | 0 | 295 | 21 |
| 2019-12 | 15,689 | 0 | 15,689 | 493 |
| 2020-01 | 1,052 | 0 | 1,052 | 51 |
| 2020-02 | 219 | 0 | 219 | 9 |
| 2020-03 | 0 | 0 | 0 | 0 |
| 2020-04 | 0 | 0 | 0 | 0 |
| 2020-05 | 0 | 0 | 0 | 0 |
| 2020-06 | 0 | 0 | 0 | 0 |

The long zero-detection periods are therefore real properties of this supplied archive, but their observation completeness is not established. They may reflect no detection, fire-season concentration, cloud/smoke or observation limitations and should be treated as a label limitation rather than silently assumed perfect negatives.

## Source and licence record

The five required sources, their official pages, local access date and licence/terms are recorded in [`data_register.csv`](../../inputs/dataset/blue_mountains_2019_2020/metadata/data_register.csv). Local raw-file creation times support an access date of 7 October 2026. Official records identify Creative Commons Attribution for both NSW sources, Creative Commons Attribution 4.0 International for the GA WCS product, NASA open-data/citation terms for FIRMS, and a CC-BY licence for ERA5-Land.

## Handoff conclusion

The prepared data, one-day target shift, main filter and training-input identity are suitable for the documented research prototype. The data do not support claims of confirmed ignition, complete satellite observation, verified absence of fire, operational warning performance or transfer to another fire season. Model improvement after seeing the current final test requires a new development cycle and genuinely independent seasons or events for final validation.
