"""Reproduce Kian's experiments. Run from the project root with Python 3.12."""
from pathlib import Path
import argparse, json, hashlib, platform, time
import numpy as np
import pandas as pd
import sklearn, xgboost as xgb, joblib
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, precision_recall_curve, auc,
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix,
    brier_score_loss, roc_auc_score)
from audit_data import ROOT, load_and_audit

WEATHER=['temperature_max_c','temperature_mean_c','temperature_min_c','dewpoint_mean_c',
    'relative_humidity_min_pct','relative_humidity_mean_pct','wind_speed_max_ms','wind_speed_mean_ms']
RAIN=['precipitation_sum_mm','precipitation_3d_mm','precipitation_7d_mm','precipitation_30d_mm',
    'precipitation_90d_mm','days_since_rain_5mm']
TERRAIN=['slope_mean_deg','aspect_sin','aspect_cos','elevation_mean_m','elevation_min_m','elevation_max_m']
FIRE=['fire_today','fire_neighbour_today','fire_days_last_7']
FEATURES={'full':WEATHER+RAIN+TERRAIN+FIRE,'conditions':WEATHER+RAIN+TERRAIN}
OUT=ROOT/'output'; RESULTS=OUT/'results'; MODELS=OUT/'models'
SEED=2112
# Fixed before observing test scores. 12 combinations including depth 3-6.
CANDIDATES=[dict(max_depth=depth,learning_rate=lr,min_child_weight=mcw,
    subsample=sub,colsample_bytree=col) for depth in [3,4,6]
    for lr,mcw,sub,col in [(.03,1,.8,.8),(.05,5,.8,1.),(.1,10,1.,.7),(.1,5,.9,.9)]]

def dates_near(dates, forbidden, gap):
    return dates.isin(
        pd.DatetimeIndex(sorted({pd.Timestamp(v)+pd.Timedelta(days=i) for v in forbidden for i in range(-gap,gap+1)})))

def split_weekly(d):
    week=((d.feature_date-pd.Timestamp('2019-07-01')).dt.days//7)
    slot=week%5
    role=np.select([slot<3,slot==3],['train','validation'],default='test')
    # Buffer Monday when role changes, including test -> train.
    buffer=((d.feature_date-pd.Timestamp('2019-07-01')).dt.days%7==0)&((week==0)|(slot==0)|(slot==3)|(slot==4))
    return pd.Series(np.where(buffer,'buffer',role),index=d.index)

def split_chronological(d):
    # Gaps at both boundaries prevent adjacent label/feature dates being reused.
    return pd.Series(np.select([d.feature_date<=pd.Timestamp('2019-12-14'),
        d.feature_date.between('2019-12-17','2019-12-30'),
        d.feature_date>=pd.Timestamp('2020-01-02')],['train','validation','test'],default='buffer'),index=d.index)

def split_outer(d,fold,gap=1):
    slot=((d.feature_date-pd.Timestamp('2019-07-01')).dt.days//7)%5
    test=slot==fold; val=slot==(fold+1)%5
    # Every date carries all cells; purge whole dates rather than individual rows.
    val &= ~dates_near(d.feature_date,d.loc[test,'feature_date'].unique(),gap)
    train=~slot.isin([fold,(fold+1)%5])
    train &= ~dates_near(d.feature_date,d.loc[test|val,'feature_date'].unique(),gap)
    role=pd.Series(np.select([test,val,train],['test','validation','train'],default='buffer'),index=d.index)
    assert not dates_near(d.loc[train,'feature_date'],d.loc[test|val,'feature_date'].unique(),gap).any()
    assert not dates_near(d.loc[val,'feature_date'],d.loc[test,'feature_date'].unique(),gap).any()
    return role

def threshold(y,p):
    precision,recall,levels=precision_recall_curve(y,p)
    valid=np.flatnonzero(recall[:-1]>=.8)
    best=max(valid,key=lambda i:(precision[i],levels[i]))
    return float(levels[best])

def metrics(y,p,t):
    y=np.asarray(y); p=np.asarray(p); h=(p>=t).astype(int)
    tn,fp,fn,tp=confusion_matrix(y,h,labels=[0,1]).ravel()
    positive=int(y.sum()); n=len(y)
    pr,rc,_=precision_recall_curve(y,p)
    return dict(n=n,positives=positive,prevalence=positive/n if n else None,
        average_precision=float(average_precision_score(y,p)) if positive else None,
        pr_auc_trapezoid=float(auc(rc,pr)) if positive else None,
        roc_auc=float(roc_auc_score(y,p)) if positive and positive<n else None,
        accuracy=float(accuracy_score(y,h)),precision=float(precision_score(y,h,zero_division=0)),
        recall=float(recall_score(y,h,zero_division=0)) if positive else None,
        f1=float(f1_score(y,h,zero_division=0)),brier=float(brier_score_loss(y,p)),
        false_positive_rate=float(fp/(fp+tn)) if fp+tn else None,
        threshold=float(t),tn=int(tn),fp=int(fp),fn=int(fn),tp=int(tp),alerts=int(h.sum()))

def fit_lr(train,val,features):
    candidates=[]; best=None
    for c in [.01,.1,1.,10.]:
        model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),
            LogisticRegression(C=c,class_weight='balanced',max_iter=3000,random_state=SEED))
        model.fit(train[features],train.fire_positive)
        ap=average_precision_score(val.fire_positive,model.predict_proba(val[features])[:,1])
        candidates.append(dict(C=c,validation_ap=float(ap)))
        if best is None or ap>best[0]: best=(ap,model,dict(C=c))
    return best[1],best[2],candidates

def fit_xgb(train,val,features):
    weight=float((len(train)-train.fire_positive.sum())/train.fire_positive.sum())
    candidates=[]; best=None
    for params in CANDIDATES:
        model=xgb.XGBClassifier(**params,n_estimators=500,early_stopping_rounds=35,
            eval_metric='aucpr',objective='binary:logistic',tree_method='hist',
            scale_pos_weight=weight,reg_lambda=2.,random_state=SEED,n_jobs=4)
        model.fit(train[features],train.fire_positive,eval_set=[(val[features],val.fire_positive)],verbose=False)
        ap=average_precision_score(val.fire_positive,model.predict_proba(val[features])[:,1])
        record=dict(**params,scale_pos_weight=weight,best_iteration=int(model.best_iteration),validation_ap=float(ap))
        candidates.append(record)
        if best is None or ap>best[0]: best=(ap,model,record)
    return best[1],best[2],candidates

def evaluate(d,roles,experiment,only_xgb=False,save_models=False):
    parts={r:d.loc[roles==r].copy() for r in ['train','validation','test']}
    train,val,test=[parts[x] for x in ['train','validation','test']]
    assert all(x.fire_positive.nunique()==2 for x in parts.values())
    splitinfo=d.assign(partition=roles).groupby('partition').fire_positive.agg(['size','sum','mean']).reset_index()
    splitinfo.insert(0,'experiment',experiment); splits.append(splitinfo)
    specs=[('xgb',v) for v in FEATURES] if only_xgb else [('lr',v) for v in FEATURES]+[('xgb',v) for v in FEATURES]
    predictions=[]; summary=[]
    if not only_xgb:
        p0=float(train.fire_positive.mean())
        for name,p,t in [('prevalence',np.full(len(test),p0),.5),('persistence',test.fire_today.to_numpy(),.5)]:
            pack=(name,p,t,None,None,[])
            predictions.append(pack)
    for kind,variant in specs:
        features=FEATURES[variant]
        model,params,trials=(fit_lr if kind=='lr' else fit_xgb)(train,val,features)
        pv=model.predict_proba(val[features])[:,1]; pt=model.predict_proba(test[features])[:,1]
        t=threshold(val.fire_positive,pv)
        name=f'{kind}_{variant}'
        predictions.append((name,pt,t,model,params,trials))
        selections.append(dict(experiment=experiment,model=name,parameters=params,validation_threshold=t,
            validation=metrics(val.fire_positive,pv,t),trials=trials))
        if save_models:
            joblib.dump(model,MODELS/f'{experiment}_{name}.joblib')
            if kind=='xgb':model.get_booster()[:model.best_iteration+1].save_model(MODELS/f'{experiment}_{name}.ubj')
            meta=dict(experiment=experiment,model=name,features=features,threshold=t,parameters=params,
                training_dates=[str(train.feature_date.min().date()),str(train.feature_date.max().date())],
                validation_dates=[str(val.feature_date.min().date()),str(val.feature_date.max().date())],
                calibrated=False,interpretation='Retrospective ranking score; not an operational warning probability')
            (MODELS/f'{experiment}_{name}.json').write_text(json.dumps(meta,indent=2))
        if kind=='xgb' and experiment in ['weekly_holdout','chronological']:
            # Native exact TreeSHAP at the selected boosting iteration, in log-odds units.
            booster=model.get_booster()[:model.best_iteration+1]
            contrib=booster.predict(xgb.DMatrix(test[features]),pred_contribs=True)
            margin=booster.predict(xgb.DMatrix(test[features]),output_margin=True)
            assert np.allclose(contrib.sum(axis=1),margin,atol=2e-4)
            pd.DataFrame(contrib[:,:-1],columns=features).to_csv(RESULTS/f'shap_{experiment}_{variant}.csv',index=False)
            test[features].to_csv(RESULTS/f'shap_inputs_{experiment}_{variant}.csv',index=False)
            # Platt calibration is an exploratory use of the same validation block, not a separate calibration set.
            logits=lambda a: np.log(np.clip(np.asarray(a,dtype=np.float64),1e-6,1-1e-6)/(1-np.clip(np.asarray(a,dtype=np.float64),1e-6,1-1e-6))).reshape(-1,1)
            calibrator=LogisticRegression(C=1.,max_iter=1000).fit(logits(pv),val.fire_positive)
            calibrated=calibrator.predict_proba(logits(pt))[:,1]
            calibrations.append(dict(experiment=experiment,model=name,raw_brier=float(brier_score_loss(test.fire_positive,pt)),
                calibrated_brier=float(brier_score_loss(test.fire_positive,calibrated)),
                calibration_slope=float(calibrator.coef_[0,0]),validation_prevalence=float(val.fire_positive.mean())))
            predictions.append((name+'_platt',calibrated,float(calibrator.predict_proba(logits(np.array([t])))[0,1]),None,None,[]))
    for name,p,t,model,params,trials in predictions:
        for view,mask in [('all',np.ones(len(test),dtype=bool)),('new_fire',test.fire_today.to_numpy()==0)]:
            row=dict(experiment=experiment,model=name,view=view,**metrics(test.fire_positive.to_numpy()[mask],p[mask],t))
            rows.append(row); summary.append(row)
        pred=test[['grid_id','feature_date','target_date','latitude','longitude','fire_positive','fire_today','park_area_fraction']].copy()
        pred['experiment']=experiment; pred['model']=name; pred['score']=p; pred['threshold']=t; pred['alert']=(p>=t).astype(int)
        predictions_all.append(pred)
    print(experiment,[(r['model'],round(r['average_precision'],4),round(r['recall'],3)) for r in summary if r['view']=='all'],flush=True)

rows=[]; predictions_all=[]; splits=[]; selections=[]; calibrations=[]

def main():
    # Notebook cells can be rerun in the same process without duplicating artifacts.
    rows.clear();predictions_all.clear();splits.clear();selections.clear();calibrations.clear()
    started=time.time(); MODELS.mkdir(parents=True,exist_ok=True); RESULTS.mkdir(parents=True,exist_ok=True)
    raw,d,audit=load_and_audit()
    evaluate(d,split_weekly(d),'weekly_holdout',save_models=True)
    evaluate(d,split_chronological(d),'chronological',save_models=True)
    for fold in range(5): evaluate(d,split_outer(d,fold,1),f'blocked_fold_{fold}')
    # Robustness to longer event/feature overlap: does not make interleaved CV causal.
    for fold in range(5): evaluate(d,split_outer(d,fold,3),f'purge3_fold_{fold}',only_xgb=True)
    evaluate(raw,split_weekly(raw),'no_edge_filter',only_xgb=True)
    warm=d[d.rain_history_days>=90]
    evaluate(warm,split_weekly(warm),'complete_rain_history',only_xgb=True)
    seasonal=FEATURES['full']+['day_of_year_sin','day_of_year_cos']
    FEATURES['seasonal_diagnostic']=seasonal
    evaluate(d,split_weekly(d),'calendar_diagnostic',only_xgb=True)
    FEATURES.pop('seasonal_diagnostic')
    m=pd.DataFrame(rows); m.to_csv(RESULTS/'metrics.csv',index=False)
    pd.concat(predictions_all,ignore_index=True).to_csv(RESULTS/'predictions.csv',index=False)
    pd.concat(splits,ignore_index=True).to_csv(RESULTS/'split_counts.csv',index=False)
    (RESULTS/'model_selection.json').write_text(json.dumps(selections,indent=2))
    (RESULTS/'calibration.json').write_text(json.dumps(calibrations,indent=2))
    cv=m[m.experiment.str.startswith('blocked_fold_')]
    cv.groupby(['model','view'])[['average_precision','recall','precision','f1','brier']].agg(['mean','std','min','max']).to_csv(RESULTS/'blocked_cv_summary.csv')
    versions=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,sklearn=sklearn.__version__,xgboost=xgb.__version__,joblib=joblib.__version__)
    (RESULTS/'run_manifest.json').write_text(json.dumps(dict(versions=versions,seed=SEED,elapsed_seconds=time.time()-started,
        input_sha256=audit['sha256'],features=FEATURES,candidates=CANDIDATES,
        threshold_rule='Highest validation precision subject to recall >= 0.80; ties choose higher threshold',
        cv_rule='Outer test slot k; inner validation slot (k+1)%5; remaining slots train; symmetric whole-date purge',
        limitations=['Interleaved weekly experiments are within-season interpolation','One-day buffer cannot isolate entire fire events',
            'Rolling histories may overlap across partitions','Seven-day symmetric purging removes inner validation weeks and is infeasible with this five-week rotation',
            'ERA5-Land reanalysis and full UTC-day inputs lack operational availability at day start']),indent=2))
    print('Finished in',round(time.time()-started,1),'seconds',flush=True)

if __name__=='__main__': main()
