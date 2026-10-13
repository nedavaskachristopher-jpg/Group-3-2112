# Forecast horizons and continuing fire

## What the current model predicts

Given the completed UTC feature day t, the current model scores eligible active-fire detection in the park portion of a grid cell on day t+1. It includes continuing or spreading fire. It does not estimate confirmed ignition, the remaining burning duration, or a precise fire front.

Scores and thresholds can be displayed as percentages, but these remain uncalibrated model scores. Percentage formatting does not change the forecast horizon, account for missing variables, or make the score a reliable probability.

## A fire has already been detected

If fire is detected on day t, `fire_today` is 1; the seven-day and neighbouring-fire features are updated using observations available through t. The full model uses these inputs with weather, rainfall and terrain to score detection on t+1. It does not automatically output 100% or guarantee continued burning.

After day t+1 is observed, update weather, rainfall histories, fire state and neighbouring detections, then issue a new next-day score for t+2. Repeat after t+2 to score t+3. These are successive one-day predictions issued on different days, not three forecasts all available on t. The workflow remains retrospective until real-time feature availability is established.

| Issue time | Information used | Target day |
| --- | --- | --- |
| After completed day t | Observations through t | t+1 |
| After completed day t+1 | Updated observations through t+1 | t+2 |
| After completed day t+2 | Updated observations through t+2 | t+3 |

A later no-detection label does not prove extinction, because satellite observations can miss active fire. Detection on three consecutive cell-days does not establish three independent incidents or uninterrupted burning between observations. Evaluation counts cell-days; incident-level analysis requires event identity and suitable ground truth.

## Forecasting two or three days ahead from today

This is a different task. An appropriate future experiment can use separate horizon targets: Y(t,h)=1 when eligible detection occurs on t+h, for h=1,2,3, with predictors available at the same issue time t. Each horizon needs its own model selection, calibration assessment, error analysis and unseen-date evaluation. These additional horizons have not been implemented or validated in the current project.

Labels must be aligned within each cell by date, and rows without a known future target must be excluded. Time partitions must ensure the latest training target precedes validation inputs and the latest validation target precedes test inputs; increase gaps where required by the maximum horizon. Keep dates grouped and investigate fire-event dependence. If weather forecasts are used, retain only forecasts actually available at issue time; realised future weather is not a valid substitute.

Do not copy tomorrow's score onto later dates, insert a predicted future fire state as an observed feature, or assume fire continues with a fixed daily decay. Such approaches require their own explicitly defined and validated modelling design.

## Fire on any day in the next three days

This is also different from predicting fire on exactly day t+3. A window target can be defined as 1 if any eligible detection occurs on t+1, t+2 or t+3, and 0 otherwise. It requires separate training and evaluation, with overlapping windows and event dependence considered. Scores for individual days must not simply be added or multiplied: future fire states are dependent, and current scores are uncalibrated. No three-day window probability is currently produced.

## Human activity and uncertainty

Deliberate or accidental ignition, recreation, land-management actions and suppression are not explicit predictors. Historical labels can include their effects, but particular future actions cannot be anticipated without information. Percentage display or probability calibration cannot supply an omitted predictor. Future data additions should have a justified link to the task, suitable data rights and timestamps showing availability before prediction. Current scores should support research discussion and human review, not assurances of safety or operational public warnings.
