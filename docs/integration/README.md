# Revised ML integration

The user authorised five sequential integration stages on 25 October 2026
(Australia/Sydney), each with a separate explanatory English commit, followed
by clean-checkout acceptance and integration into the group default branch.

| Stage | Scope |
| --- | --- |
| 1 | Preserve the old version, establish the integration branch and classify every existing file |
| 2 | Import the revised evaluated research and public review workflow with hash/test checks |
| 3 | Reconcile inference, the review notebook, cached-score map, historical outputs and CI |
| 4 | Align group documentation, report sections, evidence and actual contribution records |
| 5 | Validate from a clean clone, record acceptance evidence and integrate without rewriting history |

## Version boundaries

- Group baseline: `504f027576376d8a61c87350ccef7b4cd2fb7204`.
- Preserved tag: `legacy-ml-2026-10-25`.
- Integration branch: `integration/revised-ml`.
- Revised source repository: `kianluo024/ENGG2112-Blue-Mountain-Bushfire-prediction-ML-`.
- Imported source commit: `1b3d7dd170583333327c887f95132bb5913e7ccd`.
- Original freeze and one-time release remain authoritative; neither threshold
  may change and no second final evaluation is authorised by this migration.

The source dataset is unchanged between the two studies. Earlier experiments
already examined overlapping dates/cells. This integration does not create a
new independent season or previously unknown test dataset.

## File decisions

[migration_inventory.json](migration_inventory.json) records every baseline
tracked file's action and hash. Preserve source data and real attribution;
supersede the old active ML outputs through versioned history. Retired code,
weights, row-level predictions, SHAP and maps remain available at the preserved
tag rather than being relabelled as revised-model evidence.

The exact frozen models and row-level prediction cache stay private. Any new
inference demonstration must load a user-supplied matching frozen artifact;
public review and CI must work without it. Maps may use existing cached scores
without predicting again, computing new test metrics or selecting dates from
outcomes. Human member review remains distinct from automated acceptance.
