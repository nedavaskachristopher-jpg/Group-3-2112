> Historical pre-integration record. Numerical claims and roles describe the legacy version; see the current team index.

# Data handoff to ML engineering

Owner: Jin. Reviewer: Kian. Values below describe the current artifacts; human confirmation fields remain open.

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

Authoritative references: [feature contract](https://github.com/nedavaskachristopher-jpg/Group-3-2112/blob/legacy-ml-2026-10-25/output/feature_contract.json), [quality report](https://github.com/nedavaskachristopher-jpg/Group-3-2112/blob/legacy-ml-2026-10-25/inputs/dataset/blue_mountains_2019_2020/model_ready/quality_report.json), [provenance](https://github.com/nedavaskachristopher-jpg/Group-3-2112/blob/legacy-ml-2026-10-25/inputs/dataset/blue_mountains_2019_2020/model_ready/provenance.json), [training manifest](https://github.com/nedavaskachristopher-jpg/Group-3-2112/blob/legacy-ml-2026-10-25/output/results/run_manifest.json).

## Confirm before final report integration

- [ ] Jin confirms source versions, access dates and licence/attribution requirements.
- [ ] Jin explains FIRMS confidence/type filters, deduplication and prescribed-burn matching with script/source evidence.
- [ ] Jin explains UTC aggregation, the next-midnight precipitation accumulation and raw-data availability limits.
- [ ] Jin and Kian confirm the target shift, feature list, filter and input hash.
- [ ] Jin and Kian identify omitted raw inputs and do not claim a full raw-pipeline rerun.
- [ ] Kian records the actual interface review and any remaining issue.

| Confirmation | Name/date/evidence |
| --- | --- |
| Data owner confirmation | To be completed |
| ML interface review | To be completed |
| Remaining issue and owner | To be completed |
