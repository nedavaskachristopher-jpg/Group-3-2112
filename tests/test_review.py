"""Review access must remain read-only even when records are missing or corrupt."""

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from review import ROOT, cached_results


def completed_fixture(root):
    folder = root / "research/reports"
    folder.mkdir(parents=True)
    result = {"freeze_commit": "synthetic", "all_rows": {
        "population": {"rows": 4, "positives": 1},
        "models": {"synthetic_model": {"average_precision": 0.25}}, "policies": {}}}
    aggregate = folder / "final_holdout.json"
    aggregate.write_bytes(json.dumps(result).encode())
    receipt = {"status": "completed", "evaluation_runs": 1, "test_csv_reads": 1,
               "aggregate_sha256": hashlib.sha256(aggregate.read_bytes()).hexdigest()}
    receipt_path = folder / "final_release.json"
    receipt_path.write_text(json.dumps(receipt))
    return aggregate, receipt_path, receipt


class ReviewTests(unittest.TestCase):
    def test_completed_cache_needs_no_data_or_model_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            completed_fixture(root)
            result = cached_results(root)
            self.assertTrue(result["cached_result_only"])
            self.assertEqual(result["population"], {"rows": 4, "positives": 1})
            self.assertFalse((root / ".local_data").exists())

    def test_corrupt_aggregate_is_rejected_without_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            aggregate, _, _ = completed_fixture(root)
            aggregate.write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "differs"):
                cached_results(root)
            self.assertEqual(aggregate.read_bytes(), b"tampered")

    def test_incomplete_or_repeated_release_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, receipt_path, receipt = completed_fixture(root)
            for changes in [{"status": "started"}, {"status": "metrics_cached"},
                            {"evaluation_runs": 2}, {"test_csv_reads": 2}]:
                receipt_path.write_text(json.dumps({**receipt, **changes}))
                with self.assertRaisesRegex(ValueError, "completed single-release"):
                    cached_results(root)

    def test_missing_records_are_not_recreated(self):
        for missing in ["final_holdout.json", "final_release.json"]:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                completed_fixture(root)
                path = root / "research/reports" / missing
                path.unlink()
                with self.assertRaises(FileNotFoundError):
                    cached_results(root)
                self.assertFalse(path.exists())

    def test_cli_resolves_its_own_workspace_without_third_party_packages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            completed_fixture(root)
            script = root / "review.py"
            shutil.copyfile(ROOT / "review.py", script)
            caller = root / "unrelated_directory"
            caller.mkdir()
            command = [sys.executable, "-S", str(script), "results", "--json"]
            completed = subprocess.run(command, cwd=caller, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["freeze_commit"], "synthetic")
            (root / "research/reports/final_release.json").unlink()
            failed = subprocess.run(command, cwd=caller, capture_output=True, text=True)
            self.assertNotEqual(failed.returncode, 0)
            self.assertFalse((root / ".local_data").exists())


if __name__ == "__main__":
    unittest.main()
