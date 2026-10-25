# Forecast horizon and continuing fire

The current model scores eligible satellite detection on the next UTC day from
completed-day inputs. Continuing fire counts as positive. It does not estimate
confirmed ignition, severity, remaining burning duration or a fire front.
The current recent-fire input is only audited `fire_today`; neighbouring and
seven-day fire features belong to the wider source table/legacy study and are
not enabled in the revised model.

Updating actual observations tomorrow and issuing another one-day score is a
rolling update, not a two-/three-day forecast issued today. Genuine additional
horizons need appropriate target alignment, point-in-time inputs, model selection,
calibration and independent time-safe evaluation. Future realised weather or
predicted fire state cannot silently be substituted for observations available
at issue time. Summing or multiplying these uncalibrated scores does not produce
a validated multi-day probability.

Human ignition and suppression actions are not explicit inputs. Satellite
non-detection does not prove extinction or safety. Percentage formatting cannot
recover missing information. The current private-model interface accepts only
prepared known-grid rows and blocks re-prediction of the released final dates.
See [the model card](MODEL_CARD.md) and [application scope](../applications/README.md).
