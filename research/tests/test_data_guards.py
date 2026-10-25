"""Checks for consequential outcome leakage and partition-integrity failures."""

import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from bushfire_ml.data import PROTOCOL_PATH, load_development, model_matrix, partition_for, read_protocol, sha256, verify_seal


class DataGuardTests(unittest.TestCase):
    def setUp(self):
        self.protocol = read_protocol()

    def test_future_holdout_and_two_seven_day_gaps(self):
        start = date(2019, 7, 1)
        groups = {}
        for index in range(365):
            day = start+timedelta(days=index)
            groups.setdefault(partition_for(day.isoformat(), self.protocol), []).append(day)
        self.assertEqual(len(groups["embargo"]), 14)
        self.assertEqual(min(groups["final_test"]), date(2020, 1, 1))
        self.assertEqual(max(groups["final_test"]), date(2020, 6, 29))
        self.assertEqual((min(groups["validation"])-max(groups["train"])).days, 8)
        self.assertEqual((min(groups["final_test"])-max(groups["validation"])).days, 8)
        self.assertLess(max(groups["train"])+timedelta(days=1), min(groups["validation"]))
        self.assertLess(max(groups["validation"])+timedelta(days=1), min(groups["final_test"]))

    def test_outside_dates_fail_instead_of_becoming_test(self):
        for day in ["2019-06-30", "2020-06-30"]:
            with self.assertRaises(ValueError):
                partition_for(day, self.protocol)

    def test_holdout_cannot_be_requested_through_development_loader(self):
        for name in ["test", "final_test", "holdout", "../holdout/final_test"]:
            with self.assertRaises(ValueError):
                load_development(name, Path("does-not-exist"))

    def test_numeric_answer_columns_are_not_selected(self):
        columns = self.protocol["feature_sets"]["conditions_core"]
        frame = pd.DataFrame({column: [1.0, 2.0] for column in columns})
        frame["fire_positive"] = [0, 1]
        frame["eligible_fire_detection_count"] = [0, 9999]
        frame["fire_detection_count_raw"] = [0, 9999]
        frame["grid_id"] = [0, 1]
        selected = model_matrix(frame)
        self.assertEqual(list(selected.columns), columns)
        self.assertTrue(set(self.protocol["excluded_predictors"]).isdisjoint(selected.columns))

    def test_extended_inputs_are_blocked_until_review(self):
        with self.assertRaises(ValueError):
            model_matrix(pd.DataFrame(), "full")

    def test_protocol_rejects_an_answer_added_as_a_feature(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "unsafe.json"
            self.protocol["feature_sets"]["conditions_core"].append("fire_positive")
            path.write_text(json.dumps(self.protocol), encoding="utf-8")
            with self.assertRaises(ValueError):
                read_protocol(path)

    def test_tampered_sealed_data_is_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data = root / "final_test.csv"
            data.write_text("synthetic holdout bytes\n", encoding="utf-8")
            manifest = {"protocol_sha256": sha256(PROTOCOL_PATH),
                        "file_sha256": {data.name: sha256(data)}}
            (root / "seal_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            verify_seal(root)
            data.write_text("changed synthetic bytes\n", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                verify_seal(root)


if __name__ == "__main__":
    unittest.main()
