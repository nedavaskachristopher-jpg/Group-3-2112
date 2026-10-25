"""Score prepared non-holdout rows with an explicitly supplied frozen model."""

import argparse
import csv
import hashlib
import json
import math
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METADATA = ['grid_id', 'feature_date', 'target_date', 'park_area_fraction']


def contract(root=ROOT):
    from review import cached_results
    cached_results(root)
    frozen = json.loads((root / 'research/reports/final_freeze.json').read_text())
    public = json.loads((root / 'docs/technical/model_contract.json').read_text())
    spec = frozen['models']['xgboost_17']
    if public['ordered_inputs'] != spec['columns'] or public['model_artifact_sha256'] != spec['sha256']:
        raise ValueError('Public input contract differs from the frozen model')
    if public['research_flags'] != frozen['policies']:
        raise ValueError('Public policies differ from the frozen thresholds')
    return frozen, spec


def verify_model(path, spec):
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != spec['sha256']:
        raise ValueError('Model bytes do not match the frozen artifact; no repair or export is performed')
    return data


def read_features(path, frozen, spec):
    allowed = set(spec['columns'] + METADATA)
    required = set(spec['columns'] + METADATA[:3])
    records, keys = [], set()
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        names = reader.fieldnames or []
        if len(names) != len(set(names)) or not required.issubset(names) or set(names) - allowed:
            raise ValueError('Supply only the exact model inputs and allowed metadata; labels and audit columns are rejected')
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError('Feature rows must match the CSV header')
            day, target = date.fromisoformat(row['feature_date']), date.fromisoformat(row['target_date'])
            if target != day + timedelta(days=1):
                raise ValueError('Targets must be the following UTC day')
            period = frozen['test_population']
            if period['first_feature_date'] <= day.isoformat() <= period['last_feature_date']:
                raise ValueError('The released holdout must use cached scores; refuse a second prediction pass')
            key = (row['grid_id'], day)
            if row['grid_id'] not in frozen['grid_ids'] or key in keys:
                raise ValueError('Unknown grid or duplicate cell-day')
            keys.add(key)
            values = {column: float(row[column]) for column in spec['columns']}
            if not all(math.isfinite(value) for value in values.values()) or values['fire_today'] not in (0, 1):
                raise ValueError('Finite inputs and a binary same-day detection flag are required')
            if 'park_area_fraction' in row and not frozen['minimum_park_area_fraction'] <= float(row['park_area_fraction']) <= 1:
                raise ValueError('Park overlap differs from the frozen geographic rule')
            records.append({**{key: row[key] for key in METADATA[:3]}, **values})
    if not records:
        raise ValueError('No feature rows were supplied')
    return records


def score_rows(records, scores, frozen):
    if len(records) != len(scores):
        raise ValueError('Prediction count differs from input count')
    rows = []
    for record, value in zip(records, scores):
        score = float(value)
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError('Invalid model score')
        row = {key: record[key] for key in METADATA[:3]}
        row.update(model_score=score, model_score_percent=100 * score, forecast_horizon_days=1,
                   score_interpretation='Experimental uncalibrated score; not fire probability')
        for policy in frozen['policies']:
            suffix = int(policy['recall_target'] * 100)
            row[f'threshold_{suffix}'] = policy['threshold']
            row[f'alert_{suffix}'] = int(score >= policy['threshold'])
        rows.append(row)
    return rows


def predict_frame(records, model_path, frozen, spec):
    verify_model(model_path, spec)
    import pandas as pd
    from xgboost import XGBClassifier
    model = XGBClassifier()
    model.load_model(model_path)
    if list(model.feature_names_in_) != spec['columns'] or model.get_booster().num_boosted_rounds() != spec['trees']:
        raise ValueError('Saved feature order or tree count differs from the frozen model')
    matrix = pd.DataFrame(records).loc[:, spec['columns']]
    return score_rows(records, model.predict_proba(matrix)[:, 1], frozen)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--model', type=Path, required=True, help='Private exact frozen xgboost_17.ubj; never regenerated')
    parser.add_argument('--output', type=Path, required=True, help='New CSV path; existing files are not overwritten')
    args = parser.parse_args(argv)
    frozen, spec = contract()
    verify_model(args.model, spec)
    records = read_features(args.input, frozen, spec)
    rows = predict_frame(records, args.model, frozen, spec)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f'Saved {len(rows)} research scores with both unchanged policies. Scores are not validated probabilities.')


if __name__ == '__main__':
    main()
