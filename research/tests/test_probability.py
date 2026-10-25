"""Verify monotone calibration, threshold ties and held-later answer isolation."""

import copy
import json
import unittest

import numpy as np
import pandas as pd

from bushfire_ml.calibration import apply_sigmoid, fit_sigmoid, select_recall_threshold
from bushfire_ml.data import ROOT, read_protocol
from bushfire_ml.probability_experiment import CONFIG_PATH, calibration_decision, fit_scenario


class CalibrationTests(unittest.TestCase):
    config = {"C": 1.0, "clip": 1e-6, "max_iterations": 1000}

    def test_constant_scores_fit_natural_prevalence_without_class_rebalancing(self):
        scores, labels = np.full(100, 0.9), np.r_[np.ones(20), np.zeros(80)]
        fitted = fit_sigmoid(scores, labels, self.config)
        np.testing.assert_allclose(apply_sigmoid(scores, fitted), 0.2, atol=1e-6)
        self.assertIsNone(fitted["class_weight"])

    def test_mapping_is_finite_and_nondecreasing_including_endpoint_scores(self):
        scores = np.linspace(0, 1, 50)
        labels = (np.arange(50) % 5 < 2).astype(int)
        fitted = fit_sigmoid(scores, labels, self.config)
        predicted = apply_sigmoid(scores, fitted)
        self.assertTrue(np.isfinite(predicted).all())
        self.assertTrue((np.diff(predicted) >= 0).all())
        self.assertGreaterEqual(fitted["slope"], 0)

    def test_threshold_is_highest_feasible_and_keeps_ties(self):
        scores, labels = np.array([0.9, 0.8, 0.8, 0.8, 0.1]), np.array([1, 1, 1, 0, 0])
        policy = select_recall_threshold(scores, labels, 0.8)
        self.assertEqual(policy["threshold"], 0.8)
        self.assertEqual(policy["selection_alerts"], 4)
        self.assertEqual(policy["selection_recall"], 1.0)
        self.assertLess(labels[scores > 0.8].sum()/labels.sum(), 0.8)

    def test_bad_scores_single_class_and_invalid_recall_targets_are_rejected(self):
        for scores in [[float("nan"), 0.5], [-0.1, 0.5], [1.1, 0.5]]:
            with self.assertRaises(ValueError):
                fit_sigmoid(scores, [0, 1], self.config)
        with self.assertRaises(ValueError):
            fit_sigmoid([0.1, 0.8], [0, 0], self.config)
        for target in [0, 1.1]:
            with self.assertRaises(ValueError):
                select_recall_threshold([0.1, 0.8], [0, 1], target)

    def test_monotone_calibration_transforms_the_cutoff_without_changing_alerts(self):
        fitted = {"slope": 1.5, "intercept": -0.4, "clip": 1e-6}
        scores, labels = np.array([0.2, 0.4, 0.7, 0.8]), [0, 1, 0, 1]
        calibrated = apply_sigmoid(scores, fitted)
        first = select_recall_threshold(scores, labels, 0.8)
        second = select_recall_threshold(calibrated, labels, 0.8)
        np.testing.assert_array_equal(scores >= first["threshold"], calibrated >= second["threshold"])


class ProbabilityChronologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rng = np.random.default_rng(91)
        dates = pd.date_range("2019-10-01", "2019-12-24").repeat(3)
        features = read_protocol()["feature_sets"]["conditions_core"]
        cls.frame = pd.DataFrame(rng.normal(size=(len(dates), len(features))), columns=features)
        cls.frame["grid_id"] = np.tile([1, 2, 3], len(dates)//3)
        cls.frame["feature_date"] = dates.strftime("%Y-%m-%d")
        cls.frame["target_date"] = (dates+pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        cls.frame["fire_positive"] = (np.arange(len(dates)) % 3 == 0).astype(int)
        cls.frame["fire_today"] = (np.arange(len(dates)) % 4 == 0).astype(int)
        cls.config = json.loads(CONFIG_PATH.read_text())
        cls.scenario = cls.config["scenarios"][-1]
        cls.logistic = json.loads((ROOT / "config/baseline_v1.json").read_text())
        cls.xgb = json.loads((ROOT / "config/xgboost_v1.json").read_text())
        cls.xgb["xgboost"].update(n_estimators=5, min_child_weight=1, n_jobs=1)
        cls.xgb["early_stopping"]["rounds"] = 2

    def test_changing_assessment_answers_changes_neither_models_calibrator_nor_cutoffs(self):
        changed = self.frame.copy()
        mask = changed.feature_date.eq("2019-12-24")
        changed.loc[mask, "fire_positive"] = 1-changed.loc[mask, "fire_positive"]
        first, predictions, _ = fit_scenario(self.frame, self.scenario, self.config, self.logistic, self.xgb)
        second, altered, _ = fit_scenario(changed, self.scenario, self.config, self.logistic, self.xgb)
        self.assertEqual(first["base_fits"], second["base_fits"])
        self.assertEqual(first["sigmoid_fit"], second["sigmoid_fit"])
        self.assertEqual([(p["threshold"], p["selection_recall"]) for p in first["policies"]],
                         [(p["threshold"], p["selection_recall"]) for p in second["policies"]])
        np.testing.assert_allclose(predictions.filter(like="_score"), altered.filter(like="_score"))
        self.assertEqual(first["base_refitting"]["feature_end"], "2019-12-08")
        self.assertEqual(first["calibration_population"]["feature_end"], "2019-12-16")
        self.assertEqual(first["assessment_population"]["feature_start"], "2019-12-24")

    def test_calibration_assessment_overlap_or_short_gap_is_rejected(self):
        for start in ["2019-12-16", "2019-12-23"]:
            scenario = copy.deepcopy(self.scenario)
            scenario["assessment"] = {"start": start, "end": "2019-12-24"}
            with self.assertRaises(ValueError):
                fit_scenario(self.frame, scenario, self.config, self.logistic, self.xgb)

    def test_overlapping_or_one_day_assessments_cannot_satisfy_evidence_gate(self):
        def result(name, start, end, days):
            population = {"days": days, "rows": 100, "positives": 40, "feature_start": start, "feature_end": end}
            return {"name": name, "calibration_population": dict(population), "assessment_population": dict(population),
                    "assessment_metrics": {"all_rows": {"sigmoid_xgboost_17": {"brier_score": 0.1, "log_loss": 0.2},
                        "xgboost_17": {"brier_score": 0.2, "log_loss": 0.4},
                        "calibration_prevalence": {"brier_score": 0.25, "log_loss": 0.5}}}}
        windows = [result("a", "2019-12-16", "2019-12-24", 9), result("b", "2019-12-18", "2019-12-24", 7),
                   result("c", "2019-12-24", "2019-12-24", 1)]
        decision = calibration_decision(windows, self.config["calibration_evidence_gate"])
        self.assertFalse(decision["sigmoid_adopted"])
        self.assertEqual(decision["disjoint_improved_windows"], 1)
        self.assertEqual(decision["supported_windows"], ["a", "b"])


if __name__ == "__main__":
    unittest.main()
