# Lesson 3: understand baseline errors before changing the model

## Goal

Explain what is going wrong using existing development results. Do not change
the test period, remove difficult cases or start a broad parameter search.
No model is fitted or recalibrated in this lesson.

## Questions to ask

1. Are errors concentrated in cells already burning, or cells without a current detection?
2. Are training and validation conditions similar?
3. Does a high predicted percentage correspond to a high observed event rate?
4. Are labels a direct measure of fire presence, or a fallible satellite proxy?

## What we found

For cells without a current detection, the first logistic model detects 7 of
37 next-day positives and issues 114 false alerts at the fixed 0.5 threshold.
Its useful coverage of new detections is therefore limited. This is not an
evaluation of confirmed new ignitions.

Training and validation also have substantially different event rates and
temperature distributions. These differences may contribute to poor transfer,
but observational diagnostics alone do not establish a causal explanation.

The highest-score bin averages about 88%, while its observed positive fraction
is about 32%. Converting the raw scores into percentage text does not fix this.
Calibration needs a separate development-only design after model comparison.

One target date, 22 December 2019, has no cleaned park detections despite many
on surrounding dates. The model alerts on all 43 cells, producing 43 of its
140 false positives against the detection labels. The supplied regional archive
still has 10 detections that day. A coverage/cloud issue is possible, not proven.
Retain the original data and results while seeking independent observation-quality evidence.

The retained development fire records also contain 42 inferred type-3 detections
across 17 cell-days. The supplier's script does not filter the `type` field.
The VIIRS guide defines type 3 as a water/offshore detection, not a presumed
vegetation-fire type. In a development-only nearest-grid check, each affected
cell-day has more eligible detections than non-type-0 detections, so removing
these records alone would not change those binary positive labels. Clarify the
type policy with the data engineer; do not silently revise the sealed dataset.

## A fair next experiment

The persistence rule receives current-fire information; the 16-feature logistic
model does not. To check the value of that information, next compare:

- Existing logistic model: 16 core weather and terrain inputs.
- Candidate logistic model: those same 16 inputs plus `fire_today`.

Keep the rows, dates, scaling, class weights, regularisation and threshold fixed.
Changing one factor makes the comparison easier to interpret. It does not prove
causation, and adding current fire will not automatically solve new-detection prediction.

Preserve the original baseline even if the candidate performs better. Later,
compare nonlinear models using matched features, then address calibration and
the cost of false alerts versus missed detections. The final test stays sealed.

## Oral review explanation

> After establishing baselines, we analysed false alerts and missed detections
> on validation data. We separated continuing-fire cases from cells without a
> current detection, checked changes in conditions and examined label-quality
> concerns. We will then change one factor at a time while keeping the evaluation
> fixed. No final-test results are used to guide these changes.

## Files and references

- [Error analysis report](../../research/reports/baseline_error_analysis.md)
- [Machine-readable diagnostics](../../research/reports/baseline_error_analysis.json)
- [NASA: active-fire data caveats](https://forum.earthdata.nasa.gov/viewtopic.php?t=5188)
- [VIIRS Collection 2 guide, type definitions](https://ladsweb.modaps.eosdis.nasa.gov/archive/Document%20Archive/Science%20Data%20Product%20Documentation/VIIRS_C2_AF-375m_User_Guide_1.0.pdf)

This analysis and explanation were AI-assisted. Retain the prompts/outputs and
the team's review or modifications for the course disclosure appendix.
