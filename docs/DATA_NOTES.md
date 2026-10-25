# Data lineage and the current ML interface

The existing `inputs/dataset/blue_mountains_2019_2020/` source files are retained.
The extended table SHA-256 is
`c9b4391f9616dce86172605419793e42a39a20adf1aecb30da11b4965afccb8b`, matching both
the previous experiment and the revised partition manifest. Integration hashes
the files but does not parse final labels or rerun the raw GIS pipeline.

The source table has 18,980 rows, 39 columns and 52 cells. Keeping park overlap
at least 0.10 retains 43 cells. An available column is not automatically an
approved predictor: the active comparisons use 16/17 inputs, not the previous
20/23. Source quality/provenance JSON describes the supplied table and previous
processing context; it is not the active fitted feature contract.

## Source roles

| Source in the supplied register | Role |
| --- | --- |
| NASA FIRMS VIIRS | Eligible next-day detection labels and audited same-day detection flag |
| ERA5-Land | Retrospective daily weather and short rainfall summaries |
| Geoscience Australia SRTM | Park-portion elevation, slope and aspect summaries |
| NPWS estate boundary | Study area and park-overlap fraction |
| NPWS fire history | Partial retrospective prescribed-burn exclusion |

Source URLs and historical acquisition details remain in the
[source register](../inputs/dataset/blue_mountains_2019_2020/metadata/data_register.csv)
and [provenance JSON](../inputs/dataset/blue_mountains_2019_2020/model_ready/provenance.json).
The current [feature catalogue](technical/feature_catalog.md) defines what enters
the model. Dates, keys, coordinates and target-day counts are not predictors.

Long rainfall windows have incomplete early history, and the initial dry-spell
state has unknown prior history. The revised method excludes these candidates
and removes two early dates for the three-day core window. Full raw FIRMS, DEM,
fire-history GIS and eleven weather months are absent from this supplied public
subset. Retaining original acquisition scripts does not mean they were rerun.

The current data contact is Penelope; Jin's original PR attribution is preserved.
The group still needs to confirm source licences/versions, geometry, UTC timing,
observation coverage and prescribed-burn handling. Satellite non-detection does
not prove no physical fire. Zero-positive final months require source-owner
review but are not silently dropped. Existing provider terms remain applicable;
no new code or dataset licence is asserted by this integration.
