# Stakeholders impact ethics and recommendations

Owner: Seb. Numerical evidence is available; stakeholder interpretation and final recommendations require Seb's work and technical review.

## Evidence to use

Full XGBoost forward testing detected 13 of 45 positive cell-days, missed 32 and produced 35 false alerts. None of the 32 positives without a feature-day detection triggered an alert. Forward conditions-only XGBoost detected 14 positives but produced 1,073 false alerts. These are cell-days, not independent incidents. See [metrics](../../output/results/metrics.csv) and the [model card](../../docs/MODEL_CARD.md).

Discuss what these errors would mean for a proposed use. Do not describe the prototype as already deployed or infer that a no-detection label proves safety. Percentage-formatted scores are uncalibrated, and the experiment lacks operational feature-availability validation.

## Stakeholder analysis

| Stakeholder | Plausible decision/use | Consequence tied to measured limits | Proposed safeguard | Further consultation/evidence needed |
| --- | --- | --- | --- | --- |
| RFS and emergency services | To be completed | To be completed | To be completed | To be completed |
| NPWS and land managers | To be completed | To be completed | To be completed | To be completed |
| Residents and local councils | To be completed | To be completed | To be completed | To be completed |
| Traditional Owners | To be completed | To be completed | To be completed | To be completed |

## Recommendations

| Evidence gap | Specific action | How to judge success | Owner/dependency |
| --- | --- | --- | --- |
| Single-season and persistent events | Define independent-season/event-aware evaluation | Appropriate unseen data and disclosed event dependence | Jin and Kian |
| Weak new-fire threshold performance | Define the decision and alert-cost requirements with relevant stakeholders before a new threshold study | A documented policy evaluated on suitable heldout data | Seb with Kian; consultation not yet completed |
| Label and prescribed-burn uncertainty | Identify independent event/observation evidence | Documented label audit and remaining ambiguity | Jin with domain input |
| Missing fuels and real-time availability | Identify justified fuel predictors and timestamped issue-time inputs | Data are valid for the target and available before prediction | Jin and Kian |

These are proposed research steps, not completed validation or endorsed operational policy. Add appropriate sources and distinguish what the team can finish in this assessment from longer-term work.

## Report discussion

Develop a reasoned discussion of false reassurance, false alerts, reliance on human judgement, uncertainty, data representation and relevant governance/consultation. Connect recommendations to findings rather than repeating a generic ethics checklist.

Working discussion and sources: To be completed.
