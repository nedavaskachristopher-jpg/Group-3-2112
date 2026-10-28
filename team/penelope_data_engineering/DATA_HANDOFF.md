# Final data-owner handoff

Owner: Penelope. Reviewer: Kian. The source-level audit was completed on
25 October 2026 and migrated to the revised repository on 28 October 2026. It
does not retrain a model or change frozen evaluation results.

| Item | Current contract |
| --- | --- |
| Input table | `inputs/dataset/blue_mountains_2019_2020/model_ready/blue_mountains_model_table_2019_2020_extended.csv` |
| Input SHA-256 | `c9b4391f9616dce86172605419793e42a39a20adf1aecb30da11b4965afccb8b` |
| Unit | ERA5-Land 0.1-degree cell and completed UTC feature day |
| Target | At least one eligible VIIRS detection in the same park cell on the following UTC day; continuing fire is included |
| Source panel | 18,980 rows, 52 cells, 365 feature dates and 39 columns |
| Main filter | `park_area_fraction >= 0.10`, retaining 15,695 rows, 43 cells and 566 positive targets |
| Full/conditions-only inputs | 17/16; the conditions-only comparison omits only `fire_today` |
| Data partitions | The historical CSV split is not used; the revised partition manifest defines the protected temporal partitions |

The [model contract](../../docs/technical/model_contract.json) records the exact
17 inputs, and the [feature catalogue](../../docs/technical/feature_catalog.md)
explains their availability. Target-day counts, labels, dates, coordinates,
grid ID and partition fields are not predictors. The source-data hash matches
the `source_table_sha256` recorded in the revised partition manifest.

The audit verifies prepared-table integrity, provenance hashes, the one-day
target shift and the 17/16-input interface. Against the retained source folder,
it also reconstructs the cleaned FIRMS table and daily labels, checks all twelve
ERA5-Land months and verifies the recorded raw-source hashes. The
[source register](../../inputs/dataset/blue_mountains_2019_2020/metadata/data_register.csv)
records historical access dates and licence/attribution terms.

Two limitations remain. FIRMS is a detection archive, not a complete record of
successful clear-sky observation opportunities, and no independent incident
panel confirms fire absence. Therefore `fire_positive = 0` means no eligible
FIRMS detection was present in the supplied archive; it does not prove that no
physical fire occurred. Publication latency and operational availability are
also not reproduced.

| Confirmation | Actual name/date/evidence |
| --- | --- |
| Source, labels, timing and observation coverage | Penelope, 2026-10-25: [final audit](FINAL_DATA_AUDIT.md), [script](../../tools/audit_data_handoff.py) and [JSON evidence](../../docs/evidence/data_handoff_audit.json) |
| Active data/ML interface | Migrated 2026-10-28 to the frozen 17/16-input contract; Kian review pending |
| Remaining action | Kian and Chris retain the detection/absence and retrospective-availability limitations in ML interpretation and the final report |
