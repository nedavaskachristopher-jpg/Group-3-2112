# Aggregate table exports

All CSV files in this directory are regenerated from committed aggregate JSON.
They contain summary records, not cell-level answers or prediction rows.

| Export | Intended use |
| --- | --- |
| [final_models.csv](final_models.csv) | All prespecified final models at the diagnostic cutoff |
| [final_policies.csv](final_policies.csv) | Both frozen policies and persistence, overall and without current detections |
| [monthly_policies.csv](monthly_policies.csv) | Every prespecified month, including zero-positive periods |
| [reliability_bins.csv](reliability_bins.csv) | Raw XGBoost 17 score-bin means and observed frequencies |
| [partitions.csv](partitions.csv) | Date boundaries, gaps and known row counts |
| [development_summary.csv](development_summary.csv) | Historical development comparisons, explicitly labelled development |

Use the JSON source paths in [claims.json](../../docs/evidence/claims.json) for exact
values and provenance. Empty AP/recall fields mean undefined because no
positive outcomes are present; they do not mean perfect or zero performance.
Do not round an exact cutoff before applying its inclusive comparison.
