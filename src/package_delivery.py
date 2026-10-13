"""Package the verified ML deliverables with the minimum reproducible input subset."""
from pathlib import Path
import hashlib,json,zipfile
import pandas as pd
from audit_data import ROOT,DATA
from train_evaluate import FEATURES

def main():
    output=ROOT/'output';dest=output/'Kian_ML_Delivery.zip'
    dictionary=pd.read_csv(DATA/'data_dictionary.csv').set_index('column').to_dict('index')
    dictionary.update({
        'fire_today':{'unit_or_type':'0/1','definition':'Eligible satellite detection in the same park cell on feature_date.'},
        'fire_neighbour_today':{'unit_or_type':'0/1','definition':'Eligible detection on feature_date in any of eight neighbours from the original 52-cell panel.'},
        'fire_days_last_7':{'unit_or_type':'days','definition':'Count of eligible detection days in the seven-day causal window ending on feature_date, 0 to 7.'},
        'days_since_rain_5mm':{'unit_or_type':'days','definition':'Days since daily precipitation at least 5 mm; capped at 120; initial prior dry history is unknown.'},
        'rain_history_days':{'unit_or_type':'days','definition':'Number of observed rain days available including the initial 30 June 2019 rainfall day.'},
    })
    for n in [7,30,90]:dictionary[f'precipitation_{n}d_mm']={'unit_or_type':'mm','definition':f'Causal {n}-day rainfall sum ending on feature_date; partial history at the panel start.'}
    contract={'target':'fire_positive on target_date = feature_date + one UTC day',
        'prediction_time_assumption':'Completed feature UTC day plus data availability; retrospective ERA5-Land inputs do not simulate operational forecast latency.',
        'park_filter':'park_area_fraction >= 0.10','features':FEATURES,'dictionary':dictionary,
        'excluded_columns':sorted(set(pd.read_csv(DATA/'blue_mountains_model_table_2019_2020_extended.csv',nrows=0).columns)-set(FEATURES['full'])),
        'decision_rule':'Highest validation precision subject to recall >=0.80. Preserve model-specific metadata threshold.',
        'interpretation':'Raw ranking score for satellite active-fire detection, including continuing fire; not calibrated ignition probability.',
        'display':'Percentage score = 100 * raw score; threshold percentages use the same conversion. Labels and metric calculations retain their original scale.',
        'forecast_horizon_days':1,
        'unobserved_factors':'Human ignition and suppression activities are not explicit inputs; low scores do not establish safety.'}
    (output/'feature_contract.json').write_text(json.dumps(contract,indent=2))
    files=[]
    for directory in [ROOT/'src',output]:
        files.extend(p for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.zip' and p.name!='delivery_verification.json')
    files.extend([ROOT/'requirements.txt',ROOT/'README.md',ROOT/'.gitignore',ROOT/'.gitattributes'])
    files.extend(p for p in (ROOT/'docs').rglob('*') if p.is_file())
    files.extend(p for p in (ROOT/'.github').rglob('*') if p.is_file())
    files.extend(DATA.glob('*'))
    files.extend([DATA.parent/'raw/era5_land/era5_land_2019_07.nc',DATA.parent/'processed/blue_mountains_national_park_boundary.geojson'])
    files.extend((DATA.parent/'metadata').glob('*.csv'))
    files.extend((DATA.parent/'scripts').glob('*'))
    # Avoid any previous archive-validation payload; the explicit input list controls scope.
    files=sorted(set(p for p in files if p.is_file()))
    manifest={p.relative_to(ROOT).as_posix():{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files}
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:z.write(p,p.relative_to(ROOT).as_posix())
        z.writestr('DELIVERY_MANIFEST.json',json.dumps(manifest,indent=2))
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        assert 'src/train_evaluate.py' in z.namelist()
        assert 'output/models/chronological_xgb_full.ubj' in z.namelist()
        assert len(z.namelist())==len(files)+1
    if (output/'overleaf').is_dir():
        with zipfile.ZipFile(output/'ENGG2112_Overleaf.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
            for p in (output/'overleaf').rglob('*'):
                if p.is_file():z.write(p,p.relative_to(output/'overleaf').as_posix())
    report={'archive':dest.name,'files':len(files)+1,'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
        'archive_integrity_passed':True,'scope':'Kian experiment input subset; complete raw GIS downloads remain in original supplied archive.'}
    (output/'delivery_verification.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
