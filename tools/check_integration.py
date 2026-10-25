"""Read-only checks for preserved inputs and current application provenance."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(root=ROOT):
    inventory = json.loads((root / 'docs/integration/migration_inventory.json').read_text())
    records = inventory['files']
    if len(records) != 129 or len({row['path'] for row in records}) != len(records):
        raise ValueError('Every legacy baseline path must be classified once')
    preserved = 0
    for row in records:
        if row['action'] != 'preserve':
            continue
        if hashlib.sha256((root / row['path']).read_bytes()).hexdigest() != row['baseline_sha256']:
            raise ValueError(f"Preserved source input changed: {row['path']}")
        preserved += 1
    source = root / 'inputs/dataset/blue_mountains_2019_2020/model_ready/blue_mountains_model_table_2019_2020_extended.csv'
    partition = json.loads((root / 'research/reports/partition_manifest.json').read_text())
    if hashlib.sha256(source.read_bytes()).hexdigest() != partition['source_table_sha256']:
        raise ValueError('Group source table differs from the revised study input')
    if (root / 'output/models').exists() or (root / 'output/results').exists() or (root / 'src/train_evaluate.py').exists():
        raise ValueError('An ambiguous active legacy pipeline remains')
    from applications.predict import contract
    frozen, _ = contract(root)
    receipt = json.loads((root / 'research/reports/final_release.json').read_text())
    provenance = json.loads((root / 'report/figures/frozen_score_map.json').read_text())
    if provenance['prediction_performed'] or provenance['outcome_columns_used'] or provenance['score_cache_sha256'] != receipt['predictions_sha256']:
        raise ValueError('Map does not describe original cached scores only')
    if provenance['feature_date'] != frozen['test_population']['first_feature_date'] or provenance['rows'] != len(frozen['grid_ids']):
        raise ValueError('Default map selection changed')
    figure = root / 'report/figures/frozen_score_map.png'
    if hashlib.sha256(figure.read_bytes()).hexdigest() != provenance['figure_sha256']:
        raise ValueError('Cached score map differs from its provenance')
    notebook = json.loads((root / 'notebooks/ML_Review.ipynb').read_text())
    code = [cell for cell in notebook['cells'] if cell['cell_type'] == 'code']
    if len(code) != 4 or [cell['execution_count'] for cell in code] != list(range(1, 5)):
        raise ValueError('Review notebook is not completely executed')
    if any(output['output_type'] == 'error' for cell in code for output in cell['outputs']):
        raise ValueError('Review notebook contains errors')
    return {'preserved_input_files_checked': preserved, 'source_table_hash_matches': True,
            'cached_map_provenance_checked': True, 'executed_review_cells': len(code)}


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
