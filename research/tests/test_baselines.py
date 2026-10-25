"""Verify training-only preprocessing and the meaning of reported metrics."""

import json
import unittest

import numpy as np
import pandas as pd

from bushfire_ml.baselines import CONFIG_PATH
from bushfire_ml.data import model_matrix, read_protocol
from bushfire_ml.evaluation import evaluate, reliability_bins
from bushfire_ml.models import fit_logistic


class BaselineTests(unittest.TestCase):
    def test_validation_prediction_does_not_refit_scaler_or_classifier(self):
        columns = read_protocol()["feature_sets"]["conditions_core"]
        random = np.random.default_rng(21)
        training = pd.DataFrame(random.normal(size=(24, len(columns))), columns=columns)
        training["fire_positive"] = [0, 0, 0, 1]*6
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        model = fit_logistic(training, config)
        means_before = model.named_steps["scaler"].mean_.copy()
        coefficients_before = model.named_steps["classifier"].coef_.copy()
        validation = pd.DataFrame(np.full((4, len(columns)), 10000.0), columns=columns)
        scores = model.predict_proba(model_matrix(validation))[:, 1]
        np.testing.assert_allclose(means_before, model_matrix(training).mean().to_numpy())
        np.testing.assert_array_equal(model.named_steps["scaler"].mean_, means_before)
        np.testing.assert_array_equal(model.named_steps["classifier"].coef_, coefficients_before)
        self.assertEqual(int(model.named_steps["scaler"].n_samples_seen_), len(training))
        self.assertTrue(np.isfinite(scores).all())

    def test_average_precision_uses_scores_before_thresholding(self):
        result = evaluate([0, 1, 0, 1], [0.1, 0.4, 0.2, 0.3], threshold=0.5, days=2)
        self.assertAlmostEqual(result["average_precision"], 1.0)
        self.assertEqual(result["recall"], 0.0)
        self.assertEqual(result["alert_cell_days"], 0)

    def test_confusion_matrix_and_alert_burden_have_correct_denominators(self):
        result = evaluate([1, 1, 0, 0], [0.9, 0.1, 0.8, 0.1], threshold=0.5, days=2)
        self.assertEqual([result[k] for k in ["true_positives", "false_positives", "false_negatives", "true_negatives"]], [1, 1, 1, 1])
        self.assertAlmostEqual(result["precision"], 0.5)
        self.assertAlmostEqual(result["recall"], 0.5)
        self.assertAlmostEqual(result["alerts_per_day"], 1.0)
        self.assertAlmostEqual(result["false_alerts_per_day"], 0.5)

    def test_constant_score_ap_equals_evaluation_prevalence(self):
        result = evaluate([0, 0, 0, 1], [0.02]*4, threshold=0.5, days=1)
        self.assertAlmostEqual(result["average_precision"], 0.25)

    def test_reliability_bins_include_both_probability_endpoints(self):
        bins = reliability_bins([0, 1, 0, 1], [0.0, 1.0, 0.5, 0.5], bins=5)
        self.assertEqual(sum(item["rows"] for item in bins), 4)
        self.assertEqual(bins[0]["mean_probability"], 0.0)
        self.assertEqual(bins[-1]["mean_probability"], 1.0)

    def test_fractional_labels_are_rejected(self):
        with self.assertRaises(ValueError):
            evaluate([0, 0.5, 1], [0.1, 0.5, 0.8], threshold=0.5, days=1)


if __name__ == "__main__":
    unittest.main()
