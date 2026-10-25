"""Guard chronology, absent-class folds and isolation of outer outcomes."""

import json
import unittest

import numpy as np
import pandas as pd

from bushfire_ml.data import ROOT, read_protocol
from bushfire_ml.evaluation import evaluate
from bushfire_ml.models import fit_xgboost_fixed
from bushfire_ml.temporal_stability import CONFIG_PATH, fit_forward_window, forward_parts, require_complete_days


class TemporalStabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rng = np.random.default_rng(52)
        dates = pd.date_range("2019-10-01", "2019-12-24").repeat(2)
        columns = read_protocol()["feature_sets"]["conditions_core"]
        cls.frame = pd.DataFrame(rng.normal(size=(len(dates), len(columns))), columns=columns)
        cls.frame["grid_id"] = np.tile([1, 2], len(dates)//2)
        cls.frame["feature_date"] = dates.strftime("%Y-%m-%d")
        cls.frame["target_date"] = (dates+pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        cls.frame["fire_positive"] = (np.arange(len(dates)) % 3 == 0).astype(int)
        cls.frame["fire_today"] = (np.arange(len(dates)) % 4 == 0).astype(int)
        cls.config = json.loads(CONFIG_PATH.read_text())
        cls.window = cls.config["forward_windows"][-1]
        cls.logistic = json.loads((ROOT / "config/baseline_v1.json").read_text())
        cls.xgb = json.loads((ROOT / "config/xgboost_v1.json").read_text())
        cls.xgb["xgboost"].update(n_estimators=5, min_child_weight=1, n_jobs=1)
        cls.xgb["early_stopping"]["rounds"] = 2

    def test_calendar_gaps_and_past_refitting_population(self):
        inner, stop, refit, outer = forward_parts(self.frame, self.window, self.config)
        self.assertEqual(inner.feature_date.max(), "2019-11-24")
        self.assertEqual(stop.feature_date.min(), "2019-12-02")
        self.assertEqual(stop.feature_date.max(), "2019-12-08")
        self.assertEqual(refit.feature_date.max(), "2019-12-08")
        self.assertEqual(outer.feature_date.min(), "2019-12-16")
        self.assertTrue(set(stop.index).issubset(refit.index))
        self.assertTrue(set(refit.index).isdisjoint(outer.index))
        wrong = dict(self.config, gap_days=0)
        with self.assertRaises(ValueError):
            forward_parts(self.frame, self.window, wrong)

    def test_outer_answer_changes_do_not_change_any_fitted_scores(self):
        changed = self.frame.copy()
        mask = changed.feature_date.between(self.window["start"], self.window["end"])
        changed.loc[mask, "fire_positive"] = 1-changed.loc[mask, "fire_positive"]
        first, scores = fit_forward_window(self.frame, self.window, self.config, self.logistic, self.xgb)
        second, altered = fit_forward_window(changed, self.window, self.config, self.logistic, self.xgb)
        self.assertEqual(first["fits"], second["fits"])
        self.assertEqual(len(first["metrics"]), 6)
        np.testing.assert_allclose(scores.filter(like="_score"), altered.filter(like="_score"))

    def test_missing_class_stopping_window_remains_visible(self):
        frame = self.frame.copy()
        frame.loc[frame.feature_date.between("2019-12-02", "2019-12-08"), "fire_positive"] = 0
        result, predictions = fit_forward_window(frame, self.window, self.config, self.logistic, self.xgb)
        self.assertEqual(result["fits"]["xgboost_17"]["status"], "unavailable")
        self.assertNotIn("xgboost_17", result["metrics"])
        self.assertEqual(result["days"], 9)
        self.assertEqual(len(predictions), 18)
        self.assertIn("persistence", result["metrics"])

    def test_missing_grid_and_duplicate_cell_days_are_rejected(self):
        day = self.frame.loc[self.frame.feature_date.eq("2019-12-16")]
        two_days = self.frame.loc[self.frame.feature_date.between("2019-12-16", "2019-12-17")]
        for broken in [two_days.iloc[:-1], pd.concat([two_days, day.iloc[:1]])]:
            with self.assertRaises(ValueError):
                require_complete_days(broken, "2019-12-16", "2019-12-17")

    def test_fixed_refit_uses_all_past_class_counts_and_selected_length(self):
        _, _, refit, _ = forward_parts(self.frame, self.window, self.config)
        model = fit_xgboost_fixed(refit, self.xgb, "conditions_core", 3)
        self.assertEqual(model.get_booster().num_boosted_rounds(), 3)
        self.assertEqual(model.get_params()["scale_pos_weight"], float(refit.fire_positive.eq(0).sum()/refit.fire_positive.sum()))
        self.assertIsNone(model.get_params().get("callbacks"))
        for count in [0, 6]:
            with self.assertRaises(ValueError):
                fit_xgboost_fixed(refit, self.xgb, "conditions_core", count)

    def test_zero_positive_day_keeps_false_alerts_and_undefined_ranking(self):
        metrics = evaluate([0, 0], [0.8, 0.1], 0.5, 1)
        self.assertIsNone(metrics["average_precision"])
        self.assertIsNone(metrics["recall"])
        self.assertEqual(metrics["false_positives"], 1)
        self.assertAlmostEqual(metrics["brier_score"], 0.325)


if __name__ == "__main__":
    unittest.main()
