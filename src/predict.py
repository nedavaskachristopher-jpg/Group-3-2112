"""Score already prepared retrospective rows using the saved feature contract."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
import xgboost as xgb
from score_display import add_score_percentages, SCORE_INTERPRETATION

def predict_frame(frame,metadata_path):
    # Contract: prepared feature rows in, next-day scores/alerts out. This function
    # does not fetch weather, build GIS features, or forecast two/three days ahead.
    metadata_path=Path(metadata_path)
    metadata=json.loads(metadata_path.read_text())
    # Fail before inference if required predictors or the park-overlap constraint
    # are violated. Metadata order must match the order used when fitting trees.
    missing=set(metadata['features'])-set(frame.columns)
    if missing:raise ValueError(f'Missing required features: {sorted(missing)}')
    if 'park_area_fraction' in frame and (frame.park_area_fraction<.1).any():
        raise ValueError('The model requires cells with at least 10 percent park overlap.')
    x=frame[metadata['features']].apply(pd.to_numeric,errors='raise')
    if not np.isfinite(x.to_numpy()).all():raise ValueError('Inputs must be finite and complete.')
    # Load the portable model beside its JSON contract. Reading bytes avoids
    # native-library filename issues on Windows paths containing Unicode.
    model=xgb.Booster();model.load_model(bytearray(metadata_path.with_suffix('.ubj').read_bytes()))
    score=model.predict(xgb.DMatrix(x))
    output=frame[[c for c in ['grid_id','feature_date','target_date'] if c in frame]].copy()
    output['model_score']=np.asarray(score,dtype=np.float64);output['threshold']=metadata['threshold']
    # Compare unrounded raw scores, then add percentage display columns. The
    # uncalibrated percentage is not an estimated probability of ignition.
    output['alert']=(score>=metadata['threshold']).astype(int)
    output=add_score_percentages(output)
    output['forecast_horizon_days']=1
    output['score_interpretation']=SCORE_INTERPRETATION
    return output

if __name__=='__main__':
    # CLI writes a separate output CSV; the model and input CSV remain unchanged.
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True);parser.add_argument('--model',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=predict_frame(pd.read_csv(args.input),args.model)
    args.output.parent.mkdir(parents=True,exist_ok=True);result.to_csv(args.output,index=False)
    print(f'Saved {len(result)} next-day scores with percentage display columns. Percentages are uncalibrated scores, not fire probabilities; raw scores and alerts are retained.')
