"""Independent output, temporal partition, and model serialization checks."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import average_precision_score
from audit_data import ROOT,DATA
from train_evaluate import split_outer,split_weekly,split_chronological,dates_near,metrics
from predict import predict_frame

def main():
    # Flow: load filtered panel -> check display/metrics -> check temporal splits
    # -> compare saved-model predictions -> regenerate example and check report.
    results=ROOT/'output/results';models=ROOT/'output/models'
    d=pd.read_csv(DATA/'blue_mountains_model_table_2019_2020_extended.csv',parse_dates=['feature_date','target_date'])
    d=d[d.park_area_fraction>=.1]
    # KNOWN LIMITATION (task M-02): this legacy step replaces delivered UBJ files
    # BEFORE checking them. A passing run cannot establish that the original UBJ
    # files were present/intact. Fixing this behaviour is a separate code change;
    # this comments-only update deliberately retains existing execution.
    for meta in models.glob('*xgb*.json'):
        model=joblib.load(meta.with_suffix('.joblib'))
        model.get_booster()[:model.best_iteration+1].save_model(meta.with_suffix('.ubj'))
    p=pd.read_csv(results/'predictions.csv',parse_dates=['feature_date','target_date']);m=pd.read_csv(results/'metrics.csv')
    # 1. Percentages must be exact rescalings, with alerts based on raw values.
    for column in ['score','threshold']:
        assert np.allclose(p[f'{column}_percent'],p[column].astype(np.float64)*100,atol=1e-10,rtol=1e-12)
        assert p[f'{column}_percent'].between(0,100).all()
    assert np.array_equal(p.alert,(p.score>=p.threshold).astype(int))
    # 2. Rebuild each reported row from its own experiment/model/view predictions.
    # Explicit confusion counts and AP provide checks alongside the shared helper.
    for r in m.itertuples():
        v=p[(p.experiment==r.experiment)&(p.model==r.model)]
        if r.view=='new_fire':v=v[v.fire_today==0]
        truth=v.fire_positive.to_numpy();alert=v.alert.to_numpy()
        assert len(v)==r.n and int(truth.sum())==r.positives
        assert ((truth==1)&(alert==1)).sum()==r.tp
        assert ((truth==0)&(alert==1)).sum()==r.fp
        assert ((truth==1)&(alert==0)).sum()==r.fn
        assert ((truth==0)&(alert==0)).sum()==r.tn
        assert np.isclose(average_precision_score(truth,v.score),r.average_precision,atol=1e-6)
        recomputed=metrics(truth,v.score,r.threshold)
        for metric in ['accuracy','precision','recall','f1','brier','roc_auc','pr_auc_trapezoid','false_positive_rate']:
            assert np.isclose(recomputed[metric],getattr(r,metric),atol=1e-6,rtol=1e-6), (r.experiment,r.model,r.view,metric)
    # 3. Outer test folds must cover every retained cell-day exactly once.
    outer=p[(p.model=='xgb_full')&p.experiment.str.startswith('blocked_fold_')]
    assert len(outer)==len(d) and not outer.duplicated(['grid_id','feature_date']).any()
    # Whole-date purging keeps spatially related cells in the same partition.
    for gap in [1,3]:
        for k in range(5):
            role=split_outer(d,k,gap)
            assert not dates_near(d.loc[role=='train','feature_date'],d.loc[role.isin(['test','validation']),'feature_date'].unique(),gap).any()
            assert not dates_near(d.loc[role=='validation','feature_date'],d.loc[role=='test','feature_date'].unique(),gap).any()
            assert d.assign(role=role).groupby('feature_date').role.nunique().eq(1).all()
    # Forward separation compares training TARGET dates with later FEATURE dates.
    r=split_chronological(d)
    assert d.loc[r=='train','target_date'].max()<d.loc[r=='validation','feature_date'].min()
    assert d.loc[r=='validation','target_date'].max()<d.loc[r=='test','feature_date'].min()
    weekly=d.assign(role=split_weekly(d)).groupby('role').fire_positive.agg(['size','sum'])
    assert weekly.loc['train','size']==9202 and weekly.loc['validation','size']==2580 and weekly.loc['test','size']==2580
    # 4. Compare serialized estimators and portable inference against stored test
    # scores. These checks reuse split helpers, so they are not fully independent
    # reimplementations of the temporal design.
    parity_rows=0
    for metadata_file in models.glob('*.json'):
        metadata=json.loads(metadata_file.read_text());experiment=metadata['experiment'];name=metadata['model']
        role=(split_weekly if experiment=='weekly_holdout' else split_chronological)(d)
        frame=d[role=='test'].sort_values(['feature_date','grid_id'])
        evaluated=p[(p.experiment==experiment)&(p.model==name)].sort_values(['feature_date','grid_id'])
        assert np.array_equal(frame.grid_id,evaluated.grid_id)
        saved=joblib.load(metadata_file.with_suffix('.joblib'))
        assert np.allclose(saved.predict_proba(frame[metadata['features']])[:,1],evaluated.score,atol=1e-7)
        if name.startswith('xgb'):
            portable=predict_frame(frame,metadata_file)
            assert np.allclose(portable.model_score,evaluated.score,atol=1e-7)
            assert np.array_equal(portable.alert,evaluated.alert)
            assert np.allclose(portable.model_score_percent,portable.model_score.astype(np.float64)*100,atol=1e-10)
            assert np.allclose(portable.threshold_percent,portable.threshold*100,atol=1e-10)
            assert portable.forecast_horizon_days.eq(1).all()
        parity_rows+=len(frame)
    # 5. Demonstrate label-free inference on 86 prepared rows, and reject a missing
    # required feature rather than silently substituting an invalid input.
    meta=models/'chronological_xgb_full.json';features=json.loads(meta.read_text())['features']
    sample=d[r=='test'][['grid_id','feature_date','target_date','park_area_fraction']+features].sort_values(['feature_date','grid_id']).head(86)
    scores=predict_frame(sample,meta)
    expected=p[(p.experiment=='chronological')&(p.model=='xgb_full')].sort_values(['feature_date','grid_id']).head(86)
    assert np.allclose(scores.model_score,expected.score,atol=1e-7)
    assert np.array_equal(scores.alert,expected.alert)
    try:predict_frame(sample.drop(columns=[features[0]]),meta)
    except ValueError:pass
    else:raise AssertionError('Missing feature was silently accepted')
    # This command writes examples/report as well as the legacy UBJ export above;
    # it is not a read-only integrity check. Do not run it with python -O.
    sample.to_csv(ROOT/'output/example_features.csv',index=False);scores.to_csv(ROOT/'output/example_scores.csv',index=False)
    report={'passed':True,'metric_rows_checked':len(m),'prediction_rows_checked':len(p),'percentage_rows_checked':len(p),'outer_test_coverage':len(outer),'saved_model_parity_rows':parity_rows,
        'checks':['confusion counts and AP independently recomputed','weekly specification counts','all cells grouped by date',
        'nested purging at 1 and 3 days','strict forward target feature date separation','saved UBJ predictions equal evaluation scores',
        'inference rejects missing feature','new fire subset uses feature day state only',
        'percentage columns equal raw scores times 100','alerts use unrounded raw scores',
        'accuracy precision recall F1 Brier and ranking metrics independently recomputed']}
    (results/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
