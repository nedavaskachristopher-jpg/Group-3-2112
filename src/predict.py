"""Score already prepared retrospective rows using the saved feature contract."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
import xgboost as xgb

def predict_frame(frame,metadata_path):
    metadata_path=Path(metadata_path)
    metadata=json.loads(metadata_path.read_text())
    missing=set(metadata['features'])-set(frame.columns)
    if missing:raise ValueError(f'Missing required features: {sorted(missing)}')
    if 'park_area_fraction' in frame and (frame.park_area_fraction<.1).any():
        raise ValueError('The model requires cells with at least 10 percent park overlap.')
    x=frame[metadata['features']].apply(pd.to_numeric,errors='raise')
    if not np.isfinite(x.to_numpy()).all():raise ValueError('Inputs must be finite and complete.')
    model=xgb.Booster();model.load_model(bytearray(metadata_path.with_suffix('.ubj').read_bytes()))
    score=model.predict(xgb.DMatrix(x))
    output=frame[[c for c in ['grid_id','feature_date','target_date'] if c in frame]].copy()
    output['model_score']=score;output['threshold']=metadata['threshold']
    output['alert']=(score>=metadata['threshold']).astype(int)
    return output

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True);parser.add_argument('--model',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=predict_frame(pd.read_csv(args.input),args.model)
    args.output.parent.mkdir(parents=True,exist_ok=True);result.to_csv(args.output,index=False)
    print(f'Saved {len(result)} retrospective scores. These scores are not operational warning probabilities.')
