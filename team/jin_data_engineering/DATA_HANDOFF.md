# Data handoff to ML engineering

Owner: Jin. Reviewer: Kian. The final data audit was completed on 25 October 2026 without retraining or changing model outputs.

| Item | Current contract |
| --- | --- |
| Input table | `inputs/dataset/blue_mountains_2019_2020/model_ready/blue_mountains_model_table_2019_2020_extended.csv` |
| Input SHA-256 | `c9b4391f9616dce86172605419793e42a39a20adf1aecb30da11b4965afccb8b` |
| Unit | ERA5-Land 0.1-degree cell and completed UTC feature day |
| Target | Eligible detection in the same park cell on the following UTC day; includes continuing fire |
| Original panel | 52 cells, 365 feature dates, 18,980 rows, 39 columns |
| Main filter | `park_area_fraction >= 0.10` |
| Retained panel | 43 cells, 15,695 rows, 566 positive targets |
| Full/conditions-only predictors | 23/20; exact ordered lists in the shared feature contract |
| Excluded from main predictors | Target and target-day counts; IDs, coordinates, dates, original split, park fraction and other audit fields |
| Data split | CSV split is historical metadata; ML code defines evaluation partitions after filtering |
| Rain-history limitation | First 88 feature days have incomplete 90-day rain history; 3,784 retained rows affected |
| Neighbour fire | Derived on the original 52-cell panel before filtering |
| Reproducibility scope | Prepared-data/extension reconstruction is supported; the full original raw GIS delivery is not included |

Authoritative references: [feature contract](../../output/feature_contract.json), [quality report](../../inputs/dataset/blue_mountains_2019_2020/model_ready/quality_report.json), [provenance](../../inputs/dataset/blue_mountains_2019_2020/model_ready/provenance.json), [training manifest](../../output/results/run_manifest.json).

## Confirmation for final report integration

- [x] Source access dates and licence/attribution requirements are recorded in the source register.
- [x] FIRMS confidence selection, whole-row deduplication and prescribed-burn matching are documented and reconstructed from source data.
- [x] UTC aggregation, the next-midnight precipitation rule and raw-data availability limits are documented.
- [x] The target shift, 23/20 feature lists, park-overlap filter and input hash match the current ML implementation.
- [x] Omitted repository raw inputs are identified; the retained external source folder was used for the final source-level audit.
- [x] Kian recorded an interface review confirming that the target, predictors, filter, partitions, counts and provenance match the ML implementation.

| Confirmation | Name/date/evidence |
| --- | --- |
| Data owner confirmation | Jin, 2026-10-25: [final audit](FINAL_DATA_AUDIT.md), [machine-readable evidence](../../output/results/data_handoff_audit.json) and [reproducible audit script](../../src/audit_data_handoff.py) |
| ML interface review | Kian: repository review confirmed the target definition, 23/20 predictors, park-overlap filter, temporal partitions, counts and provenance records; no training CSV, model or evaluation output was changed |
| Remaining issue and owner | Kian/Chris must preserve the label limitation in ML interpretation and the final report: a zero denotes no eligible FIRMS detection, not independently confirmed fire absence or complete satellite observation |
