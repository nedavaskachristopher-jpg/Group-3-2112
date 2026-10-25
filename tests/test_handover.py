"""Delivery checks operate on aggregates and temporary files, never test rows."""

import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.build_handover import ROOT, build_pages, read_evidence
from tools.verify_handover import check_claims, check_links, check_model_table, check_records, contained


class HandoverTests(unittest.TestCase):
    def test_report_values_are_derived_from_aggregate_not_manual_constants(self):
        evidence = copy.deepcopy(read_evidence())
        evidence["final"]["all_rows"]["population"]["positives"] = 12345
        evidence["final"]["all_rows"]["policies"]["recall_90_policy"]["false_positives"] = 87654
        pages = build_pages(evidence)
        content = json.dumps(pages)
        self.assertIn("12345 positive", content)
        self.assertIn("87,654", content)
        self.assertEqual(len(pages), 4)

    def test_exported_model_table_and_claims_match_exact_sources(self):
        final = json.loads((ROOT / "research/reports/final_holdout.json").read_text())
        check_model_table(ROOT, final)
        self.assertGreater(check_claims(ROOT), 100)

    def test_broken_links_and_repository_escape_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, target = root / "a.md", root / "b.md"
            source.write_text("[Valid](b.md) [External](https://example.com)")
            target.write_text("Target")
            self.assertEqual(check_links(root, [source]), 1)
            target.unlink()
            with self.assertRaises(ValueError):
                check_links(root, [source])
            with self.assertRaises(ValueError):
                contained(root, "../outside.txt")

    def test_altered_csv_is_detected_without_reading_private_data(self):
        final = json.loads((ROOT / "research/reports/final_holdout.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "report/tables"
            folder.mkdir(parents=True)
            with (ROOT / "report/tables/final_models.csv").open(newline="") as stream:
                rows = list(csv.DictReader(stream))
            next(row for row in rows if row["model"] == "xgboost_17")["average_precision"] = "0.999"
            with (folder / "final_models.csv").open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaises(ValueError):
                check_model_table(root, final)

    def test_undefined_csv_metric_stays_empty_and_changed_count_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "monthly.csv"
            expected = [{"month": "synthetic", "recall": None, "false_positives": 7}]
            path.write_text("month,recall,false_positives\nsynthetic,,7\n")
            check_records(path, expected)
            path.write_text("month,recall,false_positives\nsynthetic,0,0\n")
            with self.assertRaises(ValueError):
                check_records(path, expected)


if __name__ == "__main__":
    unittest.main()
