"""Guard the one-input comparison against answer leakage and design drift."""

import copy
import json
import unittest

import numpy as np
import pandas as pd

from bushfire_ml.baselines import CONFIG_PATH as BASELINE_CONFIG
from bushfire_ml.current_fire import CONFIG_PATH, check_comparison_settings
from bushfire_ml.data import model_matrix, read_protocol
from bushfire_ml.models import fit_logistic


class CurrentFireTests(unittest.TestCase):
    def test_exactly_one_reviewed_input_is_added(self):
        columns = read_protocol()["feature_sets"]["conditions_core"]
        frame = pd.DataFrame({column: [1.0, 2.0] for column in columns})
        frame["fire_today"] = [0, 1]
        frame["fire_positive"] = [1, 0]
        frame["eligible_fire_detection_count"] = [999, 0]
        core = model_matrix(frame)
        plus = model_matrix(frame, "core_plus_fire_today")
        self.assertEqual(list(plus.columns), [*columns, "fire_today"])
        pd.testing.assert_frame_equal(core, plus.drop(columns="fire_today"))
        altered = frame.assign(fire_positive=[0, 1], eligible_fire_detection_count=[0, 999])
        pd.testing.assert_frame_equal(plus, model_matrix(altered, "core_plus_fire_today"))

    def test_nonbinary_or_unknown_current_fire_is_rejected(self):
        for value in [0.5, np.nan, -1, 2]:
            with self.assertRaises(ValueError):
                model_matrix(pd.DataFrame({"fire_today": [value]}), "core_plus_fire_today")

    def test_comparison_rejects_another_setting_changed(self):
        baseline = json.loads(BASELINE_CONFIG.read_text())
        candidate = json.loads(CONFIG_PATH.read_text())
        check_comparison_settings(candidate, baseline)
        for key, replacement in [("diagnostic_threshold", 0.2), ("training_warmup_end_inclusive", "2019-07-03")]:
            changed = copy.deepcopy(candidate)
            changed[key] = replacement
            with self.assertRaises(ValueError):
                check_comparison_settings(changed, baseline)
        changed = copy.deepcopy(candidate)
        changed["logistic_regression"]["C"] = 10
        with self.assertRaises(ValueError):
            check_comparison_settings(changed, baseline)

    def test_seventeenth_scaler_statistic_comes_from_training_only(self):
        columns = read_protocol()["feature_sets"]["conditions_core"]
        rng = np.random.default_rng(7)
        training = pd.DataFrame(rng.normal(size=(24, 16)), columns=columns)
        training["fire_today"] = [0, 0, 0, 1]*6
        training["fire_positive"] = [0, 0, 1, 1]*6
        config = json.loads(CONFIG_PATH.read_text())
        model = fit_logistic(training, config)
        scaler = model.named_steps["scaler"]
        self.assertAlmostEqual(scaler.mean_[-1], 0.25)
        means = scaler.mean_.copy()
        validation = training.copy()
        validation[columns] = 10000.0
        validation["fire_today"] = 1
        model.predict_proba(model_matrix(validation, "core_plus_fire_today"))
        np.testing.assert_array_equal(scaler.mean_, means)
        self.assertEqual(int(scaler.n_samples_seen_), 24)


if __name__ == "__main__":
    unittest.main()
