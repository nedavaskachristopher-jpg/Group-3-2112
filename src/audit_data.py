# Validate the delivered extended panel before any model is fitted.
# Flow: load -> structural checks -> reconstruct fire/rain -> park filter -> report.
# This audits the supplied 2019-20 dataset, not an arbitrary live input feed.
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
import netCDF4

ROOT = Path(__file__).resolve().parents[1]
# The repository currently supplies one dataset with a model_ready directory.
DATA = next((ROOT/'inputs/dataset').glob('*/model_ready'))

def load_and_audit():
    # Return (all source rows, park-filtered rows, audit summary). Sorting first
    # makes row-based rolling windows chronological within each grid cell.
    path = DATA/'blue_mountains_model_table_2019_2020_extended.csv'
    d = pd.read_csv(path, parse_dates=['feature_date','target_date']).sort_values(['grid_id','feature_date']).reset_index(drop=True)
    labels = pd.read_csv(DATA/'daily_fire_labels_2019_2020.csv', parse_dates=['target_date'])
    # 1. Enforce this delivered panel's size, unique keys and complete finite data.
    # These assertions require normal Python execution; do not run with python -O.
    assert d.shape == (18980,39)
    assert not d.duplicated(['grid_id','feature_date']).any()
    assert d.notna().all().all() and np.isfinite(d.select_dtypes('number')).all().all()
    assert ((d.target_date-d.feature_date).dt.days == 1).all()
    assert d.groupby('grid_id').size().eq(365).all()
    # 2. Join the same independent label panel twice: today's state is a predictor,
    # whereas tomorrow's state is the outcome and must never enter the features.
    today = d[['grid_id','feature_date']].merge(labels[['grid_id','target_date','fire_positive']], left_on=['grid_id','feature_date'],right_on=['grid_id','target_date'],validate='one_to_one').fire_positive.to_numpy()
    assert np.array_equal(today,d.fire_today)
    target = d[['grid_id','target_date']].merge(labels[['grid_id','target_date','fire_positive']],on=['grid_id','target_date'],validate='one_to_one').fire_positive.to_numpy()
    assert np.array_equal(target,d.fire_positive)
    # The seven-day count includes the feature day, never the target day.
    fire7 = d.groupby('grid_id').fire_today.transform(lambda s:s.rolling(7,min_periods=1).sum())
    assert np.array_equal(fire7,d.fire_days_last_7)
    # 3. Max coordinate distance identifies the eight surrounding 0.1-degree
    # cells, excluding the cell itself. Keep all 52 source cells here, including
    # edge cells that will later be removed from the modelling subset.
    coords=d.groupby('grid_id')[['latitude','longitude']].first()
    distance=np.abs(coords.to_numpy()[:,None,:]-coords.to_numpy()[None,:,:]).max(axis=2)
    adjacent=(distance<=.10001)&(distance>.00001)
    # Matrix multiplication counts burning neighbours for every date/cell;
    # thresholding converts a positive count into the stored binary indicator.
    panel=d.pivot(index='feature_date',columns='grid_id',values='fire_today')[coords.index]
    neighbours=pd.DataFrame((panel.to_numpy()@adjacent.T>0).astype(int),index=panel.index,columns=panel.columns).stack()
    expected=np.array([neighbours.loc[(r.feature_date,r.grid_id)] for r in d.itertuples()])
    assert np.array_equal(expected,d.fire_neighbour_today)
    # The extended table uses an extra rainfall day, June 30, from July 1 00 UTC.
    # Reconstruct it from the raw accumulated variable rather than guessing an off-by-one bug.
    # In-memory open avoids the Windows NetCDF C library's Unicode filename limit.
    with netCDF4.Dataset('inmemory',memory=(DATA.parent/'raw/era5_land/era5_land_2019_07.nc').read_bytes()) as nc:
        time_var=nc.variables['valid_time']
        times=netCDF4.num2date(time_var[:],time_var.units)
        t0=next(i for i,t in enumerate(times) if str(t)=='2019-07-01 00:00:00')
        initial=np.array(nc.variables['tp'][t0]).squeeze()
        lats=np.array(nc.variables['latitude'][:]); lons=np.array(nc.variables['longitude'][:])
    # 4. Match the delivered rainfall conventions, not a new feature definition.
    # The base 3-day window starts at the panel boundary; extended 7/30/90-day
    # windows also include June 30 until that extra day leaves their window.
    rain_errors={}
    for n in [3,7,30,90]:
        expected=d.groupby('grid_id').precipitation_sum_mm.transform(lambda s:s.rolling(n,min_periods=1).sum()).copy()
        if n>3:
            for grid,group in d.groupby('grid_id',sort=False):
                r=group.iloc[0]
                rain0=float(initial[np.abs(lats-r.latitude).argmin(),np.abs(lons-r.longitude).argmin()])*1000
                expected.loc[group.index[:n-1]]+=max(0,rain0)
        # CSV rounding is permitted within the stated absolute/relative tolerance.
        rain_errors[str(n)]=float(np.max(np.abs(expected-d[f'precipitation_{n}d_mm'])))
        assert np.allclose(expected,d[f'precipitation_{n}d_mm'],atol=1e-4,rtol=1e-5)
    # The first row has two observed rainfall days: June 30 and July 1.
    actual_history=d.groupby('grid_id').cumcount()+2
    assert np.array_equal(d.rain_history_days,actual_history)
    # 5. Filter only after reconstruction; preserve the original row indices so
    # rainfall-history counts remain aligned when summarising retained rows.
    filtered=d[d.park_area_fraction>=.1].copy()
    # "New fire" below means a detection-state transition, not verified ignition.
    audit={
        'sha256':hashlib.sha256(path.read_bytes()).hexdigest(), 'shape':list(d.shape),
        'missing_values':int(d.isna().sum().sum()), 'retained_rows':len(filtered),
        'retained_cells':int(filtered.grid_id.nunique()), 'retained_positives':int(filtered.fire_positive.sum()),
        'dropped_positives':int(d.fire_positive.sum()-filtered.fire_positive.sum()),
        'new_fire_positives':int(((filtered.fire_today==0)&(filtered.fire_positive==1)).sum()),
        'persistence_true_positives':int(((filtered.fire_today==1)&(filtered.fire_positive==1)).sum()),
        'rain_rolling_max_abs_error':rain_errors,
        'extra_rain_history_day':'2019-06-30 verified against July 1 00 UTC raw precipitation',
        'short_90d_history_rows_retained':int((actual_history[filtered.index]<90).sum()),
        'target_month_positives':{str(k):int(v) for k,v in d.groupby(d.target_date.dt.to_period('M')).fire_positive.sum().items()},
        'checks':['unique keys','finite complete inputs','one day target shift','labels reconstructed','fire_today reconstructed','7 day fire reconstructed','8 neighbour fire reconstructed','causal rainfall windows reconstructed'],
    }
    # Record input identity and check results; the source CSV is never rewritten.
    (ROOT/'output/results').mkdir(parents=True,exist_ok=True)
    (ROOT/'output/results/data_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    return d,filtered,audit

if __name__=='__main__':
    print(json.dumps(load_and_audit()[2],indent=2))
