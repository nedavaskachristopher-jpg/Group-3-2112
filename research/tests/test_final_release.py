"""Synthetic-only checks before the irreversible first final-outcome release."""

import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd

from bushfire_ml import final_release, freeze_final
from bushfire_ml.data import read_protocol, sha256
from bushfire_ml.final_metrics import final_results, predict_frozen, validate_population
from bushfire_ml.final_reporting import write_final_report


def synthetic_fixture():
    columns = read_protocol()["feature_sets"]["conditions_core"]
    frame = pd.DataFrame({column: [1.0, 2.0, 3.0, 4.0] for column in columns})
    frame["grid_id"] = ["a", "b", "a", "b"]
    frame["feature_date"] = ["2020-01-01", "2020-01-01", "2020-01-02", "2020-01-02"]
    frame["target_date"] = ["2020-01-02", "2020-01-02", "2020-01-03", "2020-01-03"]
    frame["fire_positive"], frame["fire_today"] = [1, 0, 0, 1], [1, 0, 1, 0]
    frame["park_area_fraction"] = 0.5
    frozen = {"test_population": {"rows": 4, "first_feature_date": "2020-01-01", "last_feature_date": "2020-01-02"},
              "grid_ids": ["a", "b"], "minimum_park_area_fraction": 0.1, "models": {},
              "data_hashes": {"holdout/final_test.csv": "synthetic hash"}, "training_prevalence": 0.1,
              "prior_information": "Synthetic test only", "availability_assumption": "Synthetic test only",
              "policies": [{"name": "recall_80_policy", "threshold": 0.6658568382263184},
                           {"name": "recall_90_policy", "threshold": 0.4193871319293976}],
              "configuration": {"experiment": "synthetic", "primary_model": "xgboost_17", "diagnostic_threshold": 0.5,
                                "reliability_bins": 5, "calendar_months": ["2020-01"], "pr_display_max_points": 201}}
    scores = {"training_prevalence": np.full(4, 0.1), "persistence": frame.fire_today.to_numpy(dtype=float),
              "xgboost_17": np.array([0.6658568382263184, 0.4193871319293976]*2)}
    return frame, frozen, scores


class FinalMetricTests(unittest.TestCase):
    def test_population_rejects_missing_duplicate_shifted_and_invalid_rows(self):
        frame, frozen, _ = synthetic_fixture()
        validate_population(frame, frozen)
        broken = [frame.iloc[:-1], pd.concat([frame.iloc[:-1], frame.iloc[:1]])]
        shifted = frame.copy()
        shifted.loc[0, "target_date"] = "2020-01-03"
        broken.append(shifted)
        invalid = frame.copy()
        invalid["fire_positive"] = invalid.fire_positive.astype(float)
        invalid.loc[0, "fire_positive"] = 0.5
        broken.append(invalid)
        for population in broken:
            with self.assertRaises(ValueError):
                validate_population(population, frozen)

    def test_predictor_excludes_answers_and_never_calls_fit(self):
        frame, frozen, _ = synthetic_fixture()
        columns = [*read_protocol()["feature_sets"]["conditions_core"], "fire_today"]
        frozen["models"] = {"logistic_17": {"artifact": "synthetic.joblib", "feature_set": "core_plus_fire_today", "columns": columns}}
        model = Mock()
        model.feature_names_in_ = columns
        received = []

        def predict(matrix):
            received.append(list(matrix.columns))
            probabilities = 0.2+0.6*matrix.fire_today.to_numpy()
            return np.column_stack([1-probabilities, probabilities])

        model.predict_proba.side_effect = predict
        with patch("bushfire_ml.final_metrics.joblib.load", return_value=model):
            first = predict_frozen(frame, frozen)
            changed = frame.copy()
            changed["fire_positive"] = 1-changed.fire_positive
            changed["eligible_fire_detection_count"] = 99999
            second = predict_frozen(changed, frozen)
        np.testing.assert_array_equal(first["logistic_17"], second["logistic_17"])
        self.assertEqual(received, [columns, columns])
        model.fit.assert_not_called()

    def test_zero_positive_period_is_retained_and_reporting_handles_undefined_ap(self):
        frame, frozen, scores = synthetic_fixture()
        frame["fire_positive"] = 0
        result = final_results(frame, scores, frozen)
        self.assertIsNone(result["all_rows"]["models"]["xgboost_17"]["average_precision"])
        self.assertIsNone(result["monthly"][0]["all_rows"]["policies"]["recall_80_policy"]["recall"])
        self.assertEqual(result["all_rows"]["policies"]["recall_90_policy"]["false_positives"], 4)
        result.update(configuration=frozen["configuration"], freeze_commit="synthetic", freeze_manifest_sha256="synthetic",
                      pr_curves={}, prior_information="Synthetic", availability_assumption="Synthetic")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "reports").mkdir()
            with patch("bushfire_ml.final_reporting.ROOT", root):
                write_final_report(result)
            self.assertIn("N/A", (root / "reports/final_holdout.md").read_text())
            self.assertTrue((root / "reports/final_holdout.png").is_file())


class FinalReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "reports").mkdir()
        (self.root / "local").mkdir()
        self.release = self.root / "local/release"
        manifest = self.root / "reports/final_freeze.json"
        manifest.write_text("{}\n")
        self.frame, self.frozen, self.scores = synthetic_fixture()
        self.enterContext(patch.object(final_release, "ROOT", self.root))
        self.enterContext(patch.object(final_release, "LOCAL_ROOT", self.root / "local"))
        self.enterContext(patch.object(final_release, "RELEASE_DIR", self.release))
        self.enterContext(patch.object(final_release, "MANIFEST_PATH", manifest))
        self.verify = self.enterContext(patch.object(final_release, "verify_freeze", return_value=self.frozen))
        self.enterContext(patch.object(final_release, "git_output", return_value="synthetic_freeze_commit"))
        self.predict = self.enterContext(patch.object(final_release, "predict_frozen", return_value=self.scores))
        self.render = self.enterContext(patch.object(final_release, "write_final_report"))
        self.reader = self.enterContext(patch.object(final_release.pd, "read_csv", side_effect=self.read_synthetic))

    def read_synthetic(self, path, usecols):
        receipt = json.loads((self.release / "release_receipt.json").read_text())
        self.assertEqual(receipt["status"], "started")
        self.assertNotIn("eligible_fire_detection_count", usecols)
        return self.frame.copy()

    def run_silently(self):
        with redirect_stdout(io.StringIO()):
            final_release.main()

    def test_first_release_claims_before_read_and_next_call_uses_cache_only(self):
        self.run_silently()
        self.run_silently()
        self.reader.assert_called_once()
        self.predict.assert_called_once()
        self.verify.assert_called_once_with(require_committed=True)
        receipt = json.loads((self.release / "release_receipt.json").read_text())
        self.assertEqual(receipt["status"], "completed")
        self.assertEqual(receipt["test_csv_reads"], 1)
        self.assertTrue((self.root / "reports/final_release.json").is_file())

    def test_interrupted_release_cannot_be_reopened(self):
        self.release.mkdir()
        (self.release / "release_receipt.json").write_text(json.dumps({"status": "started"}))
        with self.assertRaises(RuntimeError):
            self.run_silently()
        self.reader.assert_not_called()
        self.predict.assert_not_called()

    def test_published_receipt_prevents_new_release_when_local_state_is_absent(self):
        self.run_silently()
        (self.release / "release_receipt.json").unlink()
        self.run_silently()
        self.reader.assert_called_once()
        self.predict.assert_called_once()

    def test_orphaned_aggregate_refuses_a_new_release(self):
        (self.root / "reports/final_holdout.json").write_text("{}")
        with self.assertRaises(RuntimeError):
            self.run_silently()
        self.reader.assert_not_called()

    def test_changed_aggregate_cannot_trigger_a_second_evaluation(self):
        self.run_silently()
        (self.root / "reports/final_holdout.json").write_text("{}")
        with self.assertRaises(RuntimeError):
            self.run_silently()
        self.reader.assert_called_once()
        self.predict.assert_called_once()

    def test_reporting_failure_resumes_from_metrics_without_rereading(self):
        self.render.side_effect = RuntimeError("Synthetic rendering failure")
        with self.assertRaises(RuntimeError):
            self.run_silently()
        receipt = json.loads((self.release / "release_receipt.json").read_text())
        self.assertEqual(receipt["status"], "metrics_cached")
        self.render.side_effect = None
        self.run_silently()
        self.reader.assert_called_once()
        self.predict.assert_called_once()

    def test_read_failure_preserves_release_and_refuses_retry(self):
        self.reader.side_effect = RuntimeError("Synthetic reading failure")
        with self.assertRaises(RuntimeError):
            self.run_silently()
        with self.assertRaises(RuntimeError):
            self.run_silently()
        self.reader.assert_called_once()
        receipt = json.loads((self.release / "release_receipt.json").read_text())
        self.assertEqual(receipt["status"], "failed_after_release_started")

    def test_uncommitted_freeze_stops_before_release_or_read(self):
        self.verify.side_effect = RuntimeError("Synthetic dirty working tree")
        with self.assertRaises(RuntimeError):
            self.run_silently()
        self.assertFalse((self.release / "release_receipt.json").exists())
        self.reader.assert_not_called()

    def test_saved_score_precision_preserves_both_inclusive_cutoff_decisions(self):
        self.run_silently()
        with (self.release / "final_predictions.csv").open() as stream:
            predictions = list(csv.DictReader(stream))
        scores = np.array([float(row["xgboost_17_score"]) for row in predictions])
        np.testing.assert_array_equal(scores, self.scores["xgboost_17"])
        result = json.loads((self.root / "reports/final_holdout.json").read_text())
        for policy in self.frozen["policies"]:
            alerts = int((scores >= policy["threshold"]).sum())
            self.assertEqual(alerts, result["all_rows"]["policies"][policy["name"]]["alert_cell_days"])


class FreezeIntegrityTests(unittest.TestCase):
    def test_text_hash_normalises_git_newlines_but_model_bytes_remain_strict(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, model, manifest = root / "module.py", root / "model.ubj", root / "freeze.json"
            source.write_bytes(b"line1\nline2\n")
            digest = freeze_final.text_sha256(source)
            source.write_bytes(b"line1\r\nline2\r\n")
            self.assertEqual(freeze_final.text_sha256(source), digest)
            model.write_bytes(b"synthetic model")
            frozen = {"data_hashes": {"synthetic": "hash"}, "original_protocol_sha256": "protocol",
                      "source_hashes": {source.name: digest}, "development_reference_hashes": {},
                      "models": {"xgboost_17": {"artifact": model.name, "sha256": sha256(model)}}, "software_versions": {}}
            manifest.write_text(json.dumps(frozen))
            with patch.object(freeze_final, "ROOT", root), patch.object(freeze_final, "MANIFEST_PATH", manifest), \
                 patch.object(freeze_final, "verify_seal", return_value={"file_sha256": frozen["data_hashes"], "protocol_sha256": "protocol"}), \
                 patch.object(freeze_final, "software_versions", return_value={}):
                freeze_final.verify_freeze()
                model.write_bytes(b"changed model")
                with self.assertRaises(RuntimeError):
                    freeze_final.verify_freeze()
                model.write_bytes(b"synthetic model")
                source.write_bytes(b"changed code\n")
                with self.assertRaises(RuntimeError):
                    freeze_final.verify_freeze()


if __name__ == "__main__":
    unittest.main()
