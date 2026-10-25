# Data-owner review handoff

The existing source data are retained under `inputs/dataset/blue_mountains_2019_2020/`.
The [partition manifest](../../research/reports/partition_manifest.json) records
the table identity and retained geography. The
[current feature contract](../../docs/technical/model_contract.json) selects
17 ordered inputs from the wider table; not all 39 columns are predictors.

Please record source versions/access/rights; explain UTC target/precipitation
alignment, grid/park geometry, confidence/type filters and prescribed-burn
matching; confirm omitted raw inputs and publication latency; and review whether
zero-positive months reflect adequate observation coverage. Non-detection is not
proof of no physical fire. Do not drop dates or relabel data to improve metrics.

The complete GIS pipeline was not independently rerun during ML integration.
The [source register](../../inputs/dataset/blue_mountains_2019_2020/metadata/data_register.csv)
and provenance JSON remain historical source records. Both old and revised
experiments use the same extended-table SHA-256.

| Confirmation | Actual name/date/evidence |
| --- | --- |
| Source/rights and missing inputs | Pending data-owner review |
| Target, timing and geometry | Pending data-owner review |
| Observation coverage and burn exclusion | Pending data-owner review |
| Interface checked with Kian | Pending member record |
