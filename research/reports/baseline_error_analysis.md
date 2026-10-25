# Baseline error analysis

Existing validation predictions only; no model refit or test-label analysis.

## Current fire versus no current detection

| Fire detected on feature day | Rows | Next-day positives | TP | FP | FN | TN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| No | 232 | 37 | 7 | 114 | 30 | 81 |
| Yes | 155 | 123 | 85 | 26 | 38 | 6 |

The conditions-only logistic model detected 7 of 37 positive outcomes among cells without a current detection, with 114 false alerts. New detections can be spread or previously missed fire, not necessarily new ignitions.

## Daily error trace

| Feature date | Target date | Positives | TP | FP | FN | Archive detections | Clean park detections |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2019-12-16 | 2019-12-17 | 20 | 14 | 12 | 6 | 1738 | 905 |
| 2019-12-17 | 2019-12-18 | 22 | 6 | 1 | 16 | 2044 | 945 |
| 2019-12-18 | 2019-12-19 | 23 | 23 | 20 | 0 | 2040 | 959 |
| 2019-12-19 | 2019-12-20 | 22 | 21 | 21 | 1 | 1567 | 662 |
| 2019-12-20 | 2019-12-21 | 22 | 20 | 20 | 2 | 1907 | 914 |
| 2019-12-21 | 2019-12-22 | 0 | 0 | 43 | 0 | 10 | 0 |
| 2019-12-22 | 2019-12-23 | 15 | 0 | 2 | 15 | 288 | 154 |
| 2019-12-23 | 2019-12-24 | 15 | 8 | 20 | 7 | 210 | 86 |
| 2019-12-24 | 2019-12-25 | 21 | 0 | 1 | 21 | 620 | 269 |

## What these observations suggest

- Current-fire persistence is a strong benchmark. The first logistic model omits this information, so the comparison does not isolate algorithm quality.
- The fitted training positive rate is 2.09%, versus 41.34% in validation. Validation maximum temperature is about 1.69 training standard deviations higher on average; 20.67% of its maximum-temperature values exceed the observed training range. These are descriptive shifts, not proof of the cause of every error.
- The highest logistic-score bin averages 88.07%, but only 31.58% of its 114 validation rows are positive. These outputs are not established event probabilities.
- For target day 2019-12-22, the archive has 10 detections in its supplied region and the cleaned park file has zero. The baseline flagged all 43 model cells, contributing 43 of its 140 false positives against the detection labels. This is not an all-region instrument outage established by these files.
- Zero park detections on that day do not establish that all fire stopped. Cloud, smoke, observation coverage or genuinely different activity remain unverified possibilities. The point archive contains no complete cloud/valid-observation mask.
- Keep this day, its labels and its error contribution unchanged. Do not remove a difficult date or relabel it to improve the score. Additional observation-quality evidence must support any later data revision.

## Next controlled experiment

After reviewing label quality, add only `fire_today` to the 16 core features, with the same training rows, scaler policy, classifier settings and validation dates. This 17-feature logistic experiment would test the value of current-fire information while holding the algorithm fixed. Preserve the original 16-feature baseline. Continue to report the fire_today=0 subset separately.

Only after interpreting that comparison should we test nonlinear models, then design calibration and alert thresholds on development data. Final-test labels remain sealed.

## Official source context

NASA explains that clouds and smoke can obscure detections; this general limitation does not establish the cause on our flagged date.

- [NASA FIRMS alert notes](https://firms.modaps.eosdis.nasa.gov/alerts/notes.php)
- [NASA Earthdata: active-fire caveats and missing observations](https://forum.earthdata.nasa.gov/viewtopic.php?t=5188)

## Reproduce

```powershell
.\.venv\Scripts\python.exe -m bushfire_ml.error_analysis
```
