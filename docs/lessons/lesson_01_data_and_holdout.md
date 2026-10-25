# Lesson 1: data, labels and the holdout

## The question

For one park grid cell and one feature date, estimate the probability of at
least one eligible satellite fire detection on the next UTC day.

- `X`: information available by the end of the feature day.
- `y`: `fire_positive`, the next-day observed binary outcome.
- `p`: the model's estimated probability of `y = 1`; the display is `100 * p`.

Training on known outcomes is normal supervised learning. Leakage occurs when
the outcome, future-only inputs, or evaluation information enters the learning
or decision-selection process. A high score alone does not prove leakage.

## What arrived

The supplied package contains 65 files, including raw weather, fire and terrain
sources, processed outputs, metadata and four Python preparation scripts.
The base model table has 18,980 rows and 31 columns. The extended table has the
same keys and shared values, plus eight columns, for 39 columns in total.
Each table covers 52 cells and 365 feature dates.

The 31-column base table has a preparation script and data dictionary. The
extended table's generation script and eight additional dictionary entries are
not supplied. The audit independently reconstructs the eight additions on
development data. It does not execute code supplied inside the data package.

The supplier's 16 recorded source hashes all match. A local inventory records
SHA-256 hashes of all 65 delivered files. Files are not overwritten.

## Three kinds of columns

| Kind | Examples | Treatment |
| --- | --- | --- |
| Legitimate candidate inputs | Temperature, previous rainfall, elevation, same-day fire | Use only explicit, reviewed feature lists |
| Outcome and direct answer proxies | `fire_positive`, next-day fire-detection counts | Keep the label separate; never use outcome counts as inputs |
| Metadata or potential shortcuts | Grid/date identifiers, coordinates, seasonal encodings, overlap and history flags | Retain where needed for grouping/quality; exclude from the first model |

Dates and coordinates are not inherently label leakage. They are omitted from
the first model to make a single-season result less dependent on memorising
when and where that season burned. Adding them later would be a documented
experiment, not automatic evidence of cheating.

## The frozen partition

The original data already defines a forward test period from 2020-01-01.
We retain it and purge the seven feature days before validation and before
testing. Splits are based on dates and predefined geometry, not on model scores.
The public partition manifest contains row counts, dates and hashes only.

Rows under the same feature date are never randomly divided between partitions.
The same cells occur at different dates: this tests later observations at known
locations. It does not test transfer to a different region or a different year.

Seven days is a prespecified adjacency buffer, not a proven fire-event duration.
A large fire can continue across both sides of a gap. Conclusions and uncertainty
must reflect the small number of dependent events.

Test rows are copied into a separate ignored directory and never parsed by the
development audit. Hash verification reads bytes only, without interpreting
outcomes. Development loaders accept only the training and validation names.
No final-test model predictions or scores have been generated.

Aggregate test information was already visible in supplier documents. We cannot
erase that prior knowledge. If a previous experiment used this same period for
model selection, its reuse cannot be called a fresh blind test. A genuinely new
season, or independent data retained by a teammate, would then be necessary for
a stronger evaluation claim.

## Why accuracy can mislead

The frozen training file contains 143 positive cell-days among 6,923 rows
(2.07%). Predicting no fire every time gives 97.93% training accuracy and zero
fire recall. This counterexample uses no learned model and proves that a high
accuracy can arise without good fire prediction.

Validation contains 160 positives among 387 rows (41.34%). This is a short,
extreme fire interval with a very different base rate. It should not be described
as representative of a normal year, and a calibrator fitted only to it may not
transfer to quieter conditions. The calibration strategy must be designed before
the final evaluation, using development observations only.

Average precision will be the main ranking metric, with its exact definition
stated. Probability reliability also needs calibration curves and appropriate
proper scores. Precision, recall and alerts per day connect threshold choices to
missed detections and unnecessary alerts. A score of 30% is a claim about event
frequency among comparable cases, not 30% model accuracy.

## Source derivations that were checked

- Current fire equals the label for the feature day, not the following day.
- Seven-day fire history includes the feature day and six previous days.
- Neighbour fire is the same-day maximum over eight adjacent grid cells,
  using all supplied park-intersecting cells before the overlap filter.
- The 7/30/90-day rainfall sums include a 30 June accumulation from the 1 July
  00 UTC source record. They use only earlier/current rainfall, but early windows
  are incomplete. The base three-day sum starts on 1 July instead.
- `rain_history_days` counts available observations from 30 June.
- The dry-spell counter starts at 120 and resets after a day with at least 5 mm.
  The initial 120 is a coding convention, not evidence of 120 known dry days.
- Weather means, extremes, humidity, wind and available daily rainfall were
  independently compared against hourly source records in development months.

## Before fitting the first model

1. Use only the 16 approved core conditions inputs.
2. Drop 1 and 2 July training rows because their three-day rainfall history is partial.
3. Fit imputation/scaling and any class weights on the training partition only.
4. Run simple baselines and inspect validation performance, with no holdout access.
5. Resolve unknown dry-history and rainfall warm-up rules before enabling extended features.
6. Define out-of-sample development calibration and threshold selection before
   claiming a reliable percentage. Never use test labels for these decisions.

## Work record

Stage 1 was AI-assisted: dataset inventory, code review, audit implementation,
partition preparation and this explanation were produced with Codex. Verification
includes source hashes, raw-weather reconstruction, causal-feature comparisons
and automated separation tests. The team should retain the prompts and outputs,
review these choices and record its modifications for the course appendix.

No model has been fitted. GIS terrain extraction and raw point-in-polygon fire
labelling were reviewed in source code but were not independently rerun. The
archival reanalysis and satellite inputs do not establish real-time availability.
