"""Recreate the supplied extended features from the base table and raw initial rainfall."""
import json
import numpy as np
import pandas as pd
import netCDF4
from audit_data import DATA,ROOT

def main():
    # Independently reconstruct the extension rather than copying audit_data's
    # computed features. The base table and label panel are still supplied inputs.
    # Flow: join today's labels -> fire history/neighbours -> rainfall -> compare.
    base=pd.read_csv(DATA/'blue_mountains_model_table_2019_2020.csv',parse_dates=['feature_date','target_date'])
    labels=pd.read_csv(DATA/'daily_fire_labels_2019_2020.csv',parse_dates=['target_date'])
    # Relabel the date key so current fire is joined on the feature day, not t+1.
    current=labels[['grid_id','target_date','fire_positive']].rename(columns={'target_date':'feature_date','fire_positive':'fire_today'})
    out=base.merge(current,on=['grid_id','feature_date'],validate='one_to_one').sort_values(['grid_id','feature_date']).reset_index(drop=True)
    out['fire_days_last_7']=out.groupby('grid_id').fire_today.transform(lambda s:s.rolling(7,min_periods=1).sum()).astype(int)
    # Neighbours use all source cells, before any later modelling park filter.
    coords=out.groupby('grid_id')[['latitude','longitude']].first()
    delta=np.abs(coords.to_numpy()[:,None,:]-coords.to_numpy()[None,:,:]).max(axis=2)
    adjacency=(delta<=.10001)&(delta>.00001)
    fire=out.pivot(index='feature_date',columns='grid_id',values='fire_today')[coords.index]
    neighbours=pd.DataFrame((fire.to_numpy()@adjacency.T>0).astype(int),index=fire.index,columns=fire.columns).stack()
    out['fire_neighbour_today']=[neighbours.loc[(r.feature_date,r.grid_id)] for r in out.itertuples()]
    # July 1 midnight is the previous UTC day's accumulated precipitation.
    # Opening from bytes avoids the NetCDF library's Windows Unicode-path limit.
    with netCDF4.Dataset('inmemory',memory=(DATA.parent/'raw/era5_land/era5_land_2019_07.nc').read_bytes()) as nc:
        tv=nc.variables['valid_time'];times=netCDF4.num2date(tv[:],tv.units)
        ti=next(i for i,t in enumerate(times) if str(t)=='2019-07-01 00:00:00')
        initial=np.array(nc.variables['tp'][ti]).squeeze();lats=np.array(nc.variables['latitude'][:]);lons=np.array(nc.variables['longitude'][:])
    for name in ['precipitation_7d_mm','precipitation_30d_mm','precipitation_90d_mm','days_since_rain_5mm','rain_history_days']:out[name]=0.
    # Prepend June 30 independently for each cell; drop that extra row after
    # rolling. The base table's 3-day rainfall column is intentionally unchanged.
    for grid,g in out.groupby('grid_id',sort=False):
        r=g.iloc[0];rain0=max(0.,float(initial[np.abs(lats-r.latitude).argmin(),np.abs(lons-r.longitude).argmin()])*1000)
        rain=pd.Series(np.r_[rain0,g.precipitation_sum_mm.to_numpy()])
        for n in [7,30,90]:out.loc[g.index,f'precipitation_{n}d_mm']=rain.rolling(n,min_periods=1).sum().to_numpy()[1:]
        # Antecedent dry history is unknown: cap the counter at 120, resetting
        # only when a recorded day reaches at least 5 mm of precipitation.
        dry=[];elapsed=120
        for value in rain:
            elapsed=0 if value>=5 else min(120,elapsed+1)
            dry.append(elapsed)
        out.loc[g.index,'days_since_rain_5mm']=dry[1:]
        out.loc[g.index,'rain_history_days']=np.arange(2,len(g)+2)
    # Match supplied column order and compare every column, allowing only stated
    # numerical rounding tolerances. Assertions require Python without -O.
    supplied=pd.read_csv(DATA/'blue_mountains_model_table_2019_2020_extended.csv',parse_dates=['feature_date','target_date']).sort_values(['grid_id','feature_date']).reset_index(drop=True)
    out=out[supplied.columns]
    for col in supplied:
        if pd.api.types.is_numeric_dtype(supplied[col]):assert np.allclose(out[col],supplied[col],atol=1e-4,rtol=1e-5),col
        else:assert out[col].equals(supplied[col]),col
    # Write a separate reconstruction and report, never replace source inputs.
    output=ROOT/'output/rebuilt_model_table.csv';out.to_csv(output,index=False)
    (ROOT/'output/results/extended_rebuild_verification.json').write_text(json.dumps({'passed':True,'rows':len(out),'columns':len(out.columns),'numeric_atol':1e-4,'numeric_rtol':1e-5,
        'input_note':'Base model table and current labels are Data Engineer outputs. This reconstructs the extension, not all raw GIS processing.'},indent=2))
    print('All 39 columns reproduced within the stated numerical tolerance.')

if __name__=='__main__':main()
