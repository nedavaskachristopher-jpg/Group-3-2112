"""Draw an illustrative map from existing receipt-matching prediction scores."""

import argparse
import csv
import hashlib
import json
import math
import sqlite3
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = 'inputs/dataset/blue_mountains_2019_2020'


def selected_scores(path, root=ROOT, feature_date=None):
    from review import cached_results
    cached_results(root)
    receipt = json.loads((root / 'research/reports/final_release.json').read_text())
    frozen = json.loads((root / 'research/reports/final_freeze.json').read_text())
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != receipt['predictions_sha256']:
        raise ValueError('Prediction cache differs from the completed receipt; never regenerate it')
    selected = feature_date or frozen['test_population']['first_feature_date']
    period = frozen['test_population']
    if not period['first_feature_date'] <= selected <= period['last_feature_date']:
        raise ValueError('Selected date is outside the frozen score cache')
    scores = {}
    with Path(path).open(encoding='utf-8', newline='') as stream:
        for row in csv.DictReader(stream):
            if row['feature_date'] != selected:
                continue
            grid, value = row['grid_id'], float(row['xgboost_17_score'])
            if grid in scores or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError('Duplicate grid or invalid cached score')
            scores[grid] = value
    if set(scores) != set(frozen['grid_ids']):
        raise ValueError('Cached map must include every frozen cell')
    return selected, scores, receipt


def grid_centres(root=ROOT):
    path = root / DATASET / 'model_ready/blue_mountains_era5_grid.gpkg'
    with sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True) as db:
        return {grid: (lon, lat) for grid, lat, lon in db.execute('SELECT grid_id, latitude, longitude FROM analysis_grid')}


def render(cache, output, root=ROOT, feature_date=None):
    selected, scores, receipt = selected_scores(cache, root, feature_date)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PatchCollection
    from matplotlib.patches import Rectangle
    centres = grid_centres(root)
    boundary = root / DATASET / 'processed/blue_mountains_national_park_boundary.geojson'
    geo = json.loads(boundary.read_text())
    fig, axis = plt.subplots(figsize=(8, 7))
    fig.subplots_adjust(left=0.13, right=0.86, bottom=0.14, top=0.86)
    patches = [Rectangle((centres[grid][0] - 0.05, centres[grid][1] - 0.05), 0.1, 0.1) for grid in sorted(scores)]
    collection = PatchCollection(patches, cmap='YlOrRd', edgecolor='#4b5563', linewidth=0.5, alpha=0.85)
    collection.set_array([scores[grid] * 100 for grid in sorted(scores)])
    collection.set_clim(0, 100)
    axis.add_collection(collection)
    for feature in geo['features']:
        geom = feature['geometry']
        polygons = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
        for polygon in polygons:
            for ring in polygon:
                axis.plot([p[0] for p in ring], [p[1] for p in ring], color='#14532d', linewidth=0.6)
    axis.autoscale_view()
    axis.set_aspect(1 / math.cos(math.radians(sum(centres[g][1] for g in scores) / len(scores))))
    axis.set(xlabel='Longitude (degrees)', ylabel='Latitude (degrees)',
             title=f'Frozen next-day detection research scores\nFeature day {selected}; target day {date.fromisoformat(selected) + timedelta(days=1)}')
    fig.colorbar(collection, ax=axis, shrink=0.8, label='Experimental raw model score (%)')
    fig.text(0.5, 0.025, f'Cached scores only | {len(scores)} retained cells | Not calibrated probabilities or official warnings',
             ha='center', fontsize=8)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180)
    plt.close(fig)
    frozen = json.loads((root / 'research/reports/final_freeze.json').read_text())
    provenance = {'feature_date': selected, 'target_date': str(date.fromisoformat(selected) + timedelta(days=1)),
                  'selection': 'First frozen feature date; fixed without inspecting outcomes' if feature_date is None else 'Explicit user-supplied feature date',
                  'model': f"Frozen {frozen['models']['xgboost_17']['trees']}-tree XGBoost 17", 'score_cache_sha256': receipt['predictions_sha256'],
                  'freeze_commit': receipt['freeze_commit'], 'rows': len(scores), 'prediction_performed': False,
                  'outcome_columns_used': False, 'geometry': 'Native 0.1 degree grid cells and supplied park boundary; cells are not clipped',
                  'figure_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                  'boundary_sha256': hashlib.sha256(boundary.read_bytes()).hexdigest()}
    output.with_suffix('.json').write_text(json.dumps(provenance, indent=2) + '\n')
    return provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True, help='Private original final_predictions.csv')
    parser.add_argument('--output', type=Path, default=ROOT / 'report/figures/frozen_score_map.png')
    parser.add_argument('--date', help='UTC feature date; default is the first frozen date')
    args = parser.parse_args()
    print(json.dumps(render(args.cache, args.output, feature_date=args.date), indent=2))


if __name__ == '__main__':
    main()
