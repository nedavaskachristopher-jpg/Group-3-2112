"""Application guards must reject incompatible inputs without repairing artifacts."""

import copy
import csv
import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np

from applications import cached_map, predict


class InferenceTests(unittest.TestCase):
    def setUp(self):
        self.frozen, self.spec = predict.contract()
        with (predict.ROOT / 'examples/synthetic_features.csv').open() as stream:
            self.rows = list(csv.DictReader(stream))

    def read(self, rows, columns=None):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'features.csv'
            with path.open('w', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=columns or list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            return predict.read_features(path, self.frozen, self.spec)

    def test_label_and_unapproved_history_columns_are_rejected(self):
        for name in ['fire_positive', 'eligible_fire_detection_count', 'precipitation_90d_mm']:
            rows = [{**row, name: 'DO_NOT_USE'} for row in self.rows]
            with self.assertRaisesRegex(ValueError, 'labels and audit'):
                self.read(rows)

    def test_released_dates_require_cache_instead_of_prediction(self):
        rows = copy.deepcopy(self.rows)
        rows[0].update(feature_date='2020-01-01', target_date='2020-01-02')
        with self.assertRaisesRegex(ValueError, 'cached scores'):
            self.read(rows)

    def test_bad_dates_grids_duplicates_and_values_are_rejected(self):
        mutations = [{'target_date': '2019-10-03'}, {'grid_id': 'unknown'},
                     {'temperature_mean_c': 'nan'}, {'fire_today': '0.5'}, {'park_area_fraction': '0.01'}]
        for change in mutations:
            rows = copy.deepcopy(self.rows)
            rows[0].update(change)
            with self.assertRaises(ValueError):
                self.read(rows)
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.read([self.rows[0], self.rows[0]])

    def test_header_order_does_not_change_ordered_model_inputs(self):
        columns = list(reversed(list(self.rows[0])))
        records = self.read(self.rows, columns)
        self.assertEqual([key for key in records[0] if key in self.spec['columns']], self.spec['columns'])

    def test_corrupt_and_missing_models_are_not_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'model.ubj'
            with self.assertRaises(FileNotFoundError):
                predict.verify_model(path, self.spec)
            self.assertFalse(path.exists())
            path.write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError, 'no repair'):
                predict.verify_model(path, self.spec)
            self.assertEqual(path.read_bytes(), b'corrupt')

    def test_raw_tied_cutoff_decisions_survive_identical_display_rounding(self):
        cutoff = self.frozen['policies'][0]['threshold']
        rows = predict.score_rows(self.rows, [cutoff - 1e-12, cutoff], self.frozen)
        self.assertEqual([row['alert_80'] for row in rows], [0, 1])
        self.assertEqual(round(rows[0]['model_score_percent'], 2), round(rows[1]['model_score_percent'], 2))
        self.assertEqual([row['alert_90'] for row in rows], [1, 1])

    def test_saved_model_inference_never_fits_and_checks_tree_count(self):
        records = self.read(self.rows)
        fake = Mock()
        fake.feature_names_in_ = self.spec['columns']
        fake.get_booster.return_value.num_boosted_rounds.return_value = self.spec['trees']
        fake.predict_proba.return_value = np.array([[0.6, 0.4], [0.3, 0.7]])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic.ubj'
            path.write_bytes(b'synthetic model bytes')
            spec = {**self.spec, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            with patch('xgboost.XGBClassifier', return_value=fake):
                rows = predict.predict_frame(records, path, self.frozen, spec)
                self.assertEqual([row['alert_80'] for row in rows], [0, 1])
                self.assertEqual(list(fake.predict_proba.call_args.args[0].columns), self.spec['columns'])
                fake.fit.assert_not_called()
                fake.get_booster.return_value.num_boosted_rounds.return_value += 1
                with self.assertRaisesRegex(ValueError, 'tree count'):
                    predict.predict_frame(records, path, self.frozen, spec)
            self.assertEqual(path.read_bytes(), b'synthetic model bytes')


class CachedApplicationTests(unittest.TestCase):
    def test_map_rejects_changed_cache_without_regenerating_it(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'scores.csv'
            path.write_bytes(b'not the original prediction cache')
            with self.assertRaisesRegex(ValueError, 'never regenerate'):
                cached_map.selected_scores(path)
            self.assertEqual(path.read_bytes(), b'not the original prediction cache')

    def test_map_uses_only_existing_scores_and_first_date_without_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reports = root / 'research/reports'
            reports.mkdir(parents=True)
            path = root / 'scores.csv'
            path.write_text('grid_id,feature_date,xgboost_17_score,fire_positive\na,2020-01-01,0.2,NOT_AN_OUTCOME\nb,2020-01-01,0.7,NOT_AN_OUTCOME\n')
            receipt = {'predictions_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            (reports / 'final_release.json').write_text(json.dumps(receipt))
            frozen = {'test_population': {'first_feature_date': '2020-01-01', 'last_feature_date': '2020-01-01'}, 'grid_ids': ['a', 'b']}
            (reports / 'final_freeze.json').write_text(json.dumps(frozen))
            with patch('review.cached_results'):
                day, scores, _ = cached_map.selected_scores(path, root)
            self.assertEqual(day, '2020-01-01')
            self.assertEqual(scores, {'a': 0.2, 'b': 0.7})

    def test_notebook_code_replays_without_changing_frozen_evidence(self):
        root = predict.ROOT
        paths = list((root / 'research').rglob('*.py')) + list((root / 'research').rglob('*.json'))
        before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
        notebook = json.loads((root / 'notebooks/ML_Review.ipynb').read_text())
        namespace = {'__name__': 'cached_review_test'}
        with redirect_stdout(io.StringIO()):
            for cell in notebook['cells']:
                if cell['cell_type'] == 'code':
                    exec(compile(''.join(cell['source']), '<cached_review>', 'exec'), namespace)
        self.assertEqual(before, {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths})


if __name__ == '__main__':
    unittest.main()
