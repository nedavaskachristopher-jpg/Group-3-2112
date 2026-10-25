"""Check AP early stopping, training-only weights and model persistence."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score
from xgboost import XGBClassifier

from bushfire_ml.data import model_matrix, read_protocol
from bushfire_ml.models import fit_xgboost
from bushfire_ml.xgboost_experiment import CONFIG_PATH


class XGBoostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rng = np.random.default_rng(35)
        columns = read_protocol()["feature_sets"]["conditions_core"]
        cls.training = pd.DataFrame(rng.normal(size=(80, 16)), columns=columns)
        cls.validation = pd.DataFrame(rng.normal(size=(40, 16)), columns=columns)
        cls.training["fire_positive"] = (cls.training[columns[0]].rank() > 64).astype(int)
        cls.validation["fire_positive"] = (cls.validation[columns[0]] > 0).astype(int)
        cls.training["feature_date"], cls.training["target_date"] = "2019-11-01", "2019-11-02"
        cls.validation["feature_date"], cls.validation["target_date"] = "2019-12-16", "2019-12-17"
        cls.config = json.loads(CONFIG_PATH.read_text())
        cls.config["xgboost"].update(n_estimators=30, max_depth=2, min_child_weight=1, n_jobs=1)
        cls.config["early_stopping"]["rounds"] = 4
        cls.model = fit_xgboost(cls.training, cls.validation, cls.config, "conditions_core")

    def test_class_emphasis_uses_only_training_counts(self):
        self.assertEqual(self.model.get_params()["scale_pos_weight"], 4.0)
        self.assertEqual(list(self.model.feature_names_in_), list(model_matrix(self.training).columns))

    def test_retained_booster_maximises_reported_average_precision(self):
        history = self.model.evals_result()["validation_1"]["average_precision_score"]
        predicted_ap = average_precision_score(self.validation.fire_positive,
                                               self.model.predict_proba(model_matrix(self.validation))[:, 1])
        self.assertAlmostEqual(predicted_ap, max(history), places=5)
        self.assertEqual(self.model.get_booster().num_boosted_rounds(), self.model.best_iteration+1)

    def test_saved_native_model_reproduces_predictions(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "synthetic_model.ubj"
            self.model.save_model(path)
            restored = XGBClassifier()
            restored.load_model(path)
            np.testing.assert_allclose(restored.predict_proba(model_matrix(self.validation)),
                                       self.model.predict_proba(model_matrix(self.validation)))

    def test_temporal_overlap_and_wrong_stopping_direction_are_rejected(self):
        overlap = self.validation.copy()
        overlap["feature_date"] = "2019-11-01"
        with self.assertRaises(ValueError):
            fit_xgboost(self.training, overlap, self.config, "conditions_core")
        wrong = copy.deepcopy(self.config)
        wrong["early_stopping"]["maximize"] = False
        with self.assertRaises(ValueError):
            fit_xgboost(self.training, self.validation, wrong, "conditions_core")


if __name__ == "__main__":
    unittest.main()
