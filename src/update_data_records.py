"""Add extended-table and modelling-subset sections to the dataset quality and provenance records.

Keys written by scripts/build_model_ready_dataset.py are preserved and the new sections are
appended. Every added value is recomputed from repository files, and the script asserts that
the extended table, the feature contract, the run manifest and the saved model metadata agree.
Running it again gives the same result. Run from the repository root:

    python src/update_data_records.py
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

DATASET = ROOT / 'inputs/dataset/blue_mountains_2019_2020'
DATA = DATASET / 'model_ready'
EXT_NAME = 'blue_mountains_model_table_2019_2020_extended.csv'
BASE_NAME = 'blue_mountains_model_table_2019_2020.csv'
UPDATED = '2026-10-18'
PARK_FILTER = 0.1


def split_weekly(frame):
    """Match the whole-date weekly partition in src/train_evaluate.py."""
    week = ((frame.feature_date - pd.Timestamp('2019-07-01')).dt.days // 7)
    slot = week % 5
    role = np.select([slot < 3, slot == 3], ['train', 'validation'], default='test')
    buffer = (((frame.feature_date - pd.Timestamp('2019-07-01')).dt.days % 7 == 0)
              & ((week == 0) | (slot == 0) | (slot == 3) | (slot == 4)))
    return pd.Series(np.where(buffer, 'buffer', role), index=frame.index)


def split_chronological(frame):
    """Match the purged chronological partition in src/train_evaluate.py."""
    return pd.Series(np.select([
        frame.feature_date <= pd.Timestamp('2019-12-14'),
        frame.feature_date.between('2019-12-17', '2019-12-30'),
        frame.feature_date >= pd.Timestamp('2020-01-02'),
    ], ['train', 'validation', 'test'], default='buffer'), index=frame.index)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return path.relative_to(ROOT).as_posix()


base = pd.read_csv(DATA / BASE_NAME, parse_dates=['feature_date', 'target_date'])
ext = pd.read_csv(DATA / EXT_NAME, parse_dates=['feature_date', 'target_date'])
ext = ext.sort_values(['grid_id', 'feature_date']).reset_index(drop=True)
added = [c for c in ext.columns if c not in base.columns]
kept = ext[ext.park_area_fraction >= PARK_FILTER].copy()
dropped = ext[ext.park_area_fraction < PARK_FILTER]
contract = json.loads((ROOT / 'output/feature_contract.json').read_text(encoding='utf-8'))
manifest = json.loads((ROOT / 'output/results/run_manifest.json').read_text(encoding='utf-8'))
audit = json.loads((ROOT / 'output/results/data_audit.json').read_text(encoding='utf-8'))
rebuild = json.loads((ROOT / 'output/results/extended_rebuild_verification.json').read_text(encoding='utf-8'))
FEATURES = contract['features']

# Consistency checks between the data, the published feature contract and the ML run records.
assert FEATURES == manifest['features']
assert len(FEATURES['full']) == 23 and len(FEATURES['conditions']) == 20
assert set(FEATURES['full']) <= set(ext.columns)
assert contract['park_filter'] == 'park_area_fraction >= 0.10'
assert sha(DATA / EXT_NAME) == audit['sha256'] == manifest['input_sha256']
assert list(ext.shape) == audit['shape'] == [rebuild['rows'], rebuild['columns']]
assert len(kept) == audit['retained_rows'] and kept.grid_id.nunique() == audit['retained_cells']
assert int(kept.fire_positive.sum()) == audit['retained_positives']
assert rebuild['passed'] is True
assert not ext.duplicated(['grid_id', 'feature_date']).any()
assert ext.groupby('grid_id').size().eq(365).all()
assert ext.notna().all().all()
assert ((ext.target_date - ext.feature_date).dt.days == 1).all()
assert np.isfinite(kept[FEATURES['full']].to_numpy(dtype=float)).all()
shared = [c for c in base.columns]
merged = base.merge(ext[shared], on=['grid_id', 'feature_date'], suffixes=('_base', '_ext'))
for col in shared:
    if col in ('grid_id', 'feature_date'):
        continue
    a, b = merged[f'{col}_base'], merged[f'{col}_ext']
    if pd.api.types.is_numeric_dtype(a):
        # Two columns differ only by CSV floating-point rounding (largest difference about 3e-14).
        assert np.allclose(a, b, rtol=0, atol=1e-9), col
    else:
        assert a.astype(str).equals(b.astype(str)), col


def partition_summary(roles, frame):
    out = {}
    for role in ['train', 'validation', 'test', 'buffer']:
        part = frame[roles == role]
        out[role] = {
            'rows': int(len(part)),
            'positive_rows': int(part.fire_positive.sum()),
            'first_feature_date': part.feature_date.min().date().isoformat(),
            'last_feature_date': part.feature_date.max().date().isoformat(),
        }
    return out


chron = split_chronological(kept)
weekly = split_weekly(kept)
chron_summary = partition_summary(chron, kept)
weekly_summary = partition_summary(weekly, kept)
chron_train = kept[chron == 'train']
chron_weight = float((len(chron_train) - chron_train.fire_positive.sum()) / chron_train.fire_positive.sum())
weekly_train = kept[weekly == 'train']
weekly_weight = float((len(weekly_train) - weekly_train.fire_positive.sum()) / weekly_train.fire_positive.sum())
saved = json.loads((ROOT / 'output/models/chronological_xgb_full.json').read_text(encoding='utf-8'))
assert abs(saved['parameters']['scale_pos_weight'] - chron_weight) < 1e-9
saved_weekly = json.loads((ROOT / 'output/models/weekly_holdout_xgb_full.json').read_text(encoding='utf-8'))
assert abs(saved_weekly['parameters']['scale_pos_weight'] - weekly_weight) < 1e-9
counts = pd.read_csv(ROOT / 'output/results/split_counts.csv').set_index(['experiment', 'partition'])
for name, summary in [('chronological', chron_summary), ('weekly_holdout', weekly_summary)]:
    for role, values in summary.items():
        assert counts.loc[(name, role), 'size'] == values['rows']
        assert counts.loc[(name, role), 'sum'] == values['positive_rows']

month_positives = {str(k): int(v) for k, v in
                   kept.groupby(kept.target_date.dt.to_period('M')).fire_positive.sum().items()}

# ---------------------------------------------------------------- quality report
qpath = DATA / 'quality_report.json'
quality = json.loads(qpath.read_text(encoding='utf-8'))
quality['report_scope'] = (
    'Keys from checks_passed to fire_label_audit were generated by scripts/build_model_ready_dataset.py '
    'for the 31-column base table and its Data Engineer split. The sections below were added on '
    f'{UPDATED} to describe the 39-column extended table, the park filter and the partitions used by '
    'the ML Engineer; their values are recomputed from the repository files.')
quality['base_split_usage'] = {
    'split_column_used_by_reported_ml_results': False,
    'note': ('split_summary and recommended_xgboost_scale_pos_weight_from_training_only describe the base-table '
             'split on all 52 cells. The ML code excludes the split column, applies the park filter and '
             'defines its own partitions; XGBoost scale_pos_weight is recomputed from each training partition.'),
}
quality['extended_model_table'] = {
    'file': EXT_NAME,
    'sha256': sha(DATA / EXT_NAME),
    'rows': int(len(ext)),
    'columns': int(ext.shape[1]),
    'grid_cells': int(ext.grid_id.nunique()),
    'base_columns_carried_over': len(base.columns),
    'added_columns': added,
    'missing_values': int(ext.isna().sum().sum()),
    'positive_rows': int(ext.fire_positive.sum()),
    'checks_passed': {
        'unique_grid_feature_date_keys': True,
        'complete_365_feature_days_per_cell': True,
        'one_day_target_shift': True,
        'base_columns_match_base_table_within_1e-9': True,
        'labels_and_fire_history_reconstructed_from_daily_labels': True,
        'eight_neighbour_fire_reconstructed': True,
        'causal_rainfall_windows_reconstructed': True,
        'all_39_columns_reproduced_by_rebuild_script': True,
    },
    'verification_records': [
        'output/results/data_audit.json',
        'output/results/extended_rebuild_verification.json',
    ],
    'rain_rolling_max_abs_error_mm': audit['rain_rolling_max_abs_error'],
    'rows_with_less_than_90_days_rain_history': int((ext.rain_history_days < 90).sum()),
}
quality['modelling_subset'] = {
    'filter': 'park_area_fraction >= 0.1',
    'retained_cells': int(kept.grid_id.nunique()),
    'retained_rows': int(len(kept)),
    'retained_positive_rows': int(kept.fire_positive.sum()),
    'retained_positive_rate': float(kept.fire_positive.mean()),
    'retained_park_area_fraction_min': float(kept.park_area_fraction.min()),
    'excluded_cells': sorted(dropped.grid_id.unique().tolist()),
    'excluded_rows': int(len(dropped)),
    'excluded_positive_rows': int(dropped.fire_positive.sum()),
    'excluded_park_area_fraction_max': float(dropped.park_area_fraction.max()),
    'positive_rows_without_detection_on_feature_day': int(((kept.fire_today == 0) & (kept.fire_positive == 1)).sum()),
    'positive_rows_with_detection_on_feature_day': int(((kept.fire_today == 1) & (kept.fire_positive == 1)).sum()),
    'retained_rows_with_less_than_90_days_rain_history': int((kept.rain_history_days < 90).sum()),
    'retained_positive_rows_by_target_month': month_positives,
    'missing_or_non_finite_model_feature_values': 0,
}
quality['model_features'] = {
    'source': 'output/feature_contract.json',
    'full_model_feature_count': len(FEATURES['full']),
    'full_model_features': FEATURES['full'],
    'conditions_only_feature_count': len(FEATURES['conditions']),
    'conditions_only_excludes': [f for f in FEATURES['full'] if f not in FEATURES['conditions']],
    'columns_not_used_as_predictors': contract['excluded_columns'],
}
quality['ml_partitions'] = {
    'source': 'output/results/split_counts.csv',
    'note': ('Partitions are assigned by whole feature dates on the filtered 43-cell table. Buffer rows separate '
             'roles and are not used for training or evaluation. Five-fold and sensitivity experiments are '
             'listed in the source file.'),
    'chronological': chron_summary,
    'weekly_holdout': weekly_summary,
    'xgboost_scale_pos_weight_used': {
        'chronological_training_partition': chron_weight,
        'weekly_holdout_training_partition': weekly_weight,
    },
}
added_limitations = [
    ('Rolling rainfall features have partial history at the start of the panel: '
     f"{quality['modelling_subset']['retained_rows_with_less_than_90_days_rain_history']:,} retained rows have "
     'less than 90 days of rainfall history.'),
    'fire_neighbour_today uses neighbours from the original 52-cell panel, including cells removed by the park filter.',
    ('The extension is reproduced from the base table, the daily label panel and the July 2019 ERA5-Land file; '
     'the full raw GIS pipeline is not rerun in this repository.'),
]
quality['limitations'] = quality['limitations'] + [x for x in added_limitations if x not in quality['limitations']]
qpath.write_text(json.dumps(quality, indent=2), encoding='utf-8', newline='\n')

# ---------------------------------------------------------------- provenance
ppath = DATA / 'provenance.json'
prov = json.loads(ppath.read_text(encoding='utf-8'))
for src in prov['sources']:
    local = DATASET / src['relative_path'].replace('\\', '/')
    present = local.is_file()
    src['in_this_repository'] = present
    if present:
        assert local.stat().st_size == src['bytes'] and sha(local) == src['sha256'], local
        src['repository_path'] = rel(local)
prov['record_scope'] = (
    'Keys generated_by to sources were written by scripts/build_model_ready_dataset.py and describe the inputs '
    'of the base build; source paths are relative to the original dataset root, which is '
    'inputs/dataset/blue_mountains_2019_2020 in this repository. Later keys were added on '
    f'{UPDATED} for the extended table and its use by the ML code.')
prov['record_updated'] = UPDATED
prov['source_register'] = 'metadata/data_register.csv'
prov['raw_download_checksums'] = 'metadata/sha256_manifest.csv'
present = sum(s['in_this_repository'] for s in prov['sources'])
prov['source_availability_note'] = (
    f'{present} of the {len(prov["sources"])} listed base-build sources '
    f'{"is" if present == 1 else "are"} included in this repository. '
    'The others are retained only as historical checksums; see docs/DATA_NOTES.md.')
other_inputs = [DATASET / 'processed/blue_mountains_national_park_boundary.geojson']
prov['other_files_in_repository'] = [
    {'repository_path': rel(p), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in other_inputs]
outputs = []
for name in [BASE_NAME, EXT_NAME, 'daily_weather_features_2019_2020.csv', 'terrain_features.csv',
             'daily_fire_labels_2019_2020.csv', 'blue_mountains_era5_grid.gpkg', 'data_dictionary.csv']:
    p = DATA / name
    outputs.append({
        'file': f'model_ready/{name}',
        'bytes': p.stat().st_size,
        'sha256': sha(p),
        'produced_by': ('extension of the base table; see derived_tables' if name == EXT_NAME
                        else 'scripts/build_model_ready_dataset.py'),
    })
prov['model_ready_files'] = outputs
prov['derived_tables'] = [{
    'file': f'model_ready/{EXT_NAME}',
    'sha256': sha(DATA / EXT_NAME),
    'inputs': [
        f'model_ready/{BASE_NAME}',
        'model_ready/daily_fire_labels_2019_2020.csv',
        'raw/era5_land/era5_land_2019_07.nc',
    ],
    'added_columns': added,
    'method': ('Base columns are carried over (equal to the base table within 1e-9). fire_today is the eligible-detection label of the feature date; '
               'fire_days_last_7 is its seven-day causal count; fire_neighbour_today uses the eight neighbouring '
               'cells of the 52-cell grid. Rainfall windows and days_since_rain_5mm add a 30 June 2019 rainfall '
               'value taken from the 2019-07-01 00 UTC ERA5-Land total precipitation before the panel start.'),
    'reproduced_by': 'src/rebuild_extended.py',
    'verification': 'output/results/extended_rebuild_verification.json',
}]
prov['modelling_use'] = {
    'loaded_by': 'src/audit_data.py',
    'trained_and_evaluated_by': 'src/train_evaluate.py',
    'input_file': f'model_ready/{EXT_NAME}',
    'input_sha256_recorded_in': 'output/results/run_manifest.json',
    'park_filter': 'park_area_fraction >= 0.1',
    'full_model_feature_count': len(FEATURES['full']),
    'conditions_only_feature_count': len(FEATURES['conditions']),
    'feature_contract': 'output/feature_contract.json',
}
ppath.write_text(json.dumps(prov, indent=2), encoding='utf-8', newline='\n')
print('Updated quality_report.json and provenance.json.')
