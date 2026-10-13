from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon
from matplotlib.collections import PatchCollection
from matplotlib.ticker import PercentFormatter
from sklearn.metrics import precision_recall_curve, average_precision_score
from sklearn.calibration import calibration_curve
from scipy.stats import spearmanr
from audit_data import ROOT, DATA

RESULTS=ROOT/'output/results'; FIG=ROOT/'output/figures'
NAMES={'prevalence':'Prevalence','persistence':'Persistence','lr_full':'Logistic full',
       'lr_conditions':'Logistic conditions','xgb_full':'XGBoost full','xgb_conditions':'XGBoost conditions'}
COLORS=['#9CA3AF','#4B5563','#238C9B','#8AC7C9','#AE4C25','#E8A66A']
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':120,'savefig.dpi':220,'font.family':'DejaVu Sans'})

def save(fig,name):
    fig.savefig(FIG/f'{name}.png',bbox_inches='tight',facecolor='white')
    fig.savefig(FIG/f'{name}.pdf',bbox_inches='tight',facecolor='white')
    plt.close(fig)

def main():
    FIG.mkdir(parents=True,exist_ok=True)
    m=pd.read_csv(RESULTS/'metrics.csv'); pred=pd.read_csv(RESULTS/'predictions.csv',parse_dates=['feature_date','target_date'])
    data=pd.read_csv(DATA/'blue_mountains_model_table_2019_2020_extended.csv',parse_dates=['feature_date','target_date'])
    d=data[data.park_area_fraction>=.1]
    daily=d.groupby('target_date').fire_positive.sum()
    fig,ax=plt.subplots(figsize=(9,2.8));ax.bar(daily.index,daily.values,color='#AE4C25',width=1)
    ax.set(ylabel='Positive cells per UTC day',xlabel='Target date',title='Fire labels are concentrated in one Black Summer episode')
    ax.axvline(pd.Timestamp('2020-01-03'),color='#238C9B',ls='--',label='Forward test starts Jan 3 target day');ax.legend(fontsize=8)
    save(fig,'01_label_timeline')
    for experiment in ['weekly_holdout','chronological']:
        fig,axes=plt.subplots(1,2,figsize=(10,3.7))
        for ax,view in zip(axes,['all','new_fire']):
            for (name,label),color in zip(NAMES.items(),COLORS):
                p=pred[(pred.experiment==experiment)&(pred.model==name)]
                if view=='new_fire':p=p[p.fire_today==0]
                pr,rc,_=precision_recall_curve(p.fire_positive,p.score)
                ap=average_precision_score(p.fire_positive,p.score)
                ax.step(rc,pr,where='post',color=color,label=f'{label} AP {ap:.3f}')
            ax.set(xlabel='Recall',ylabel='Precision',title='All cell days' if view=='all' else 'Cells without fire on feature day',xlim=(0,1),ylim=(0,1.04))
            ax.legend(fontsize=7,loc='upper right')
        fig.suptitle('Within season weekly holdout' if experiment=='weekly_holdout' else 'Strictly forward chronological test')
        fig.tight_layout();save(fig,f'02_pr_{experiment}')
    cv=m[(m.experiment.str.startswith('blocked_fold_'))&(m.view=='all')]
    fig,ax=plt.subplots(figsize=(8.4,3.3))
    keys=list(NAMES)
    for i,key in enumerate(keys):
        vals=cv[cv.model==key].average_precision.to_numpy()
        ax.scatter(np.repeat(i,len(vals))+np.linspace(-.08,.08,len(vals)),vals,color=COLORS[i],alpha=.7)
        ax.errorbar(i,vals.mean(),yerr=vals.std(ddof=1),fmt='s',color=COLORS[i],capsize=5)
    ax.set_xticks(range(len(keys)),[NAMES[k].replace(' ','\n') for k in keys]);ax.set(ylabel='Average precision',ylim=(0,1),title='Five outer folds: points, mean and sample standard deviation')
    save(fig,'03_blocked_cv')
    fig,axes=plt.subplots(1,2,figsize=(7.7,3.2))
    for ax,exp in zip(axes,['weekly_holdout','chronological']):
        row=m[(m.experiment==exp)&(m.model=='xgb_full')&(m.view=='all')].iloc[0]
        a=np.array([[row.tn,row.fp],[row.fn,row.tp]],dtype=int)
        ax.imshow(a,cmap='Blues')
        for i in range(2):
            for j in range(2):ax.text(j,i,str(a[i,j]),ha='center',va='center',color='white' if a[i,j]>a.max()/2 else '#111111',fontsize=15)
        ax.set_xticks([0,1],['No alert','Alert']);ax.set_yticks([0,1],['No detection','Detection'])
        ax.set(xlabel='Prediction',ylabel='Actual proxy label',title=f'{exp.replace("_"," ")}\nScore threshold {row.threshold*100:.2f}% (uncalibrated)')
    fig.tight_layout();save(fig,'04_confusion')
    fig,axes=plt.subplots(1,2,figsize=(9,3.5))
    for ax,exp in zip(axes,['weekly_holdout','chronological']):
        ax.plot([0,1],[0,1],color='grey',ls='--')
        for model,color in [('xgb_full','#AE4C25'),('xgb_full_platt','#238C9B')]:
            p=pred[(pred.experiment==exp)&(pred.model==model)]
            observed,score=calibration_curve(p.fire_positive,p.score,n_bins=8,strategy='quantile')
            brier=m[(m.experiment==exp)&(m.model==model)&(m.view=='all')].brier.iloc[0]
            ax.plot(score,observed,'o-',color=color,label=f'{"Raw" if model=="xgb_full" else "Platt"} Brier {brier:.4f}')
        ax.set(xlabel='Mean score (%)',ylabel='Observed detection rate (%)',title=exp.replace('_',' '),xlim=(0,1),ylim=(0,1));ax.legend(fontsize=8)
        ax.xaxis.set_major_formatter(PercentFormatter(xmax=1))
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1))
    fig.tight_layout();save(fig,'05_calibration')
    findings=[]
    fig,axes=plt.subplots(1,2,figsize=(10,4.5))
    for ax,variant in zip(axes,['full','conditions']):
        s=pd.read_csv(RESULTS/f'shap_weekly_holdout_{variant}.csv');x=pd.read_csv(RESULTS/f'shap_inputs_weekly_holdout_{variant}.csv')
        imp=s.abs().mean().sort_values(ascending=False)
        imp.head(10).sort_values().plot.barh(ax=ax,color='#AE4C25' if variant=='full' else '#238C9B')
        ax.set(title=f'XGBoost {variant}',xlabel='Mean absolute TreeSHAP contribution in log odds')
        for name in s:
            rho=float(spearmanr(x[name],s[name]).statistic) if x[name].nunique()>1 else None
            findings.append(dict(variant=variant,feature=name,mean_abs_shap=float(imp[name]),value_shap_spearman=rho))
    fig.tight_layout();save(fig,'06_shap_importance')
    s=pd.read_csv(RESULTS/'shap_weekly_holdout_conditions.csv');x=pd.read_csv(RESULTS/'shap_inputs_weekly_holdout_conditions.csv')
    fig,axes=plt.subplots(1,3,figsize=(10,3))
    for ax,name in zip(axes,['relative_humidity_min_pct','wind_speed_max_ms','days_since_rain_5mm']):
        ax.scatter(x[name],s[name],s=4,color='#238C9B',alpha=.16)
        ax.axhline(0,color='grey',lw=.7);ax.set(xlabel=name.replace('_',' '),ylabel='TreeSHAP in log odds')
    fig.suptitle('Conditional associations from the conditions model are not causal effects');fig.tight_layout()
    save(fig,'07_shap_dependence')
    pd.DataFrame(findings).to_csv(RESULTS/'shap_summary.csv',index=False)
    # Choose the highest observed positive day from the weekly heldout dates, explicitly illustrative.
    p=pred[(pred.experiment=='weekly_holdout')&(pred.model=='xgb_full')]
    example=p.groupby('target_date').fire_positive.sum().idxmax()
    fig=plt.figure(figsize=(9.2,6.5))
    gs=fig.add_gridspec(1,3,width_ratios=[1,1,.055],wspace=.23,top=.83,bottom=.08,left=.07,right=.95)
    axes=[fig.add_subplot(gs[0,i]) for i in range(2)]
    cax=fig.add_subplot(gs[0,2])
    geo=json.loads((DATA.parent/'processed/blue_mountains_national_park_boundary.geojson').read_text())
    for ax,name in zip(axes,['xgb_full','xgb_conditions']):
        sub=pred[(pred.experiment=='weekly_holdout')&(pred.model==name)&(pred.target_date==example)]
        patches=[Rectangle((r.longitude-.05,r.latitude-.05),.1,.1) for r in sub.itertuples()]
        pc=PatchCollection(patches,cmap='YlOrRd',edgecolor='#333333',linewidth=.4)
        pc.set_array(sub.score.to_numpy()*100);pc.set_clim(0,100);ax.add_collection(pc)
        for f in geo['features']:
            geom=f['geometry'];polys=geom['coordinates'] if geom['type']=='MultiPolygon' else [geom['coordinates']]
            for poly in polys:
                ring=np.array(poly[0]);ax.plot(ring[::max(1,len(ring)//5000),0],ring[::max(1,len(ring)//5000),1],color='#1F5135',lw=.5)
        truth=sub[sub.fire_positive==1];ax.scatter(truth.longitude,truth.latitude,s=20,marker='x',color='black',label='Next day detected fire')
        ax.set(xlim=(149.73,150.77),ylim=(-34.38,-33.23),xlabel='Longitude east',ylabel='Latitude north',title=NAMES[name]);ax.set_aspect(1/np.cos(np.deg2rad(-33.8)));ax.legend(fontsize=7,loc='lower right')
    axes[1].set_ylabel('')
    fig.colorbar(pc,cax=cax,label='Model score (%) - uncalibrated, not probability')
    fig.suptitle(f'Illustrative heldout map for {example.date()} UTC\nDate selected for visible detections, not representative performance',fontsize=10)
    save(fig,'08_illustrative_map')
    (RESULTS/'map_example.json').write_text(json.dumps({'target_date':str(example.date()),'selection':'Heldout day with maximum observed positive cells; illustrative only'},indent=2))
    # Cluster bootstrap preserves all cells within a weekly block; no independent cell assumption.
    rng=np.random.default_rng(2112); uncertainty=[]
    for exp in ['weekly_holdout','chronological']:
        subset=pred[(pred.experiment==exp)&pred.model.isin(['xgb_full','lr_full'])]
        a=subset[subset.model=='xgb_full'].sort_values(['feature_date','grid_id']).reset_index(drop=True)
        b=subset[subset.model=='lr_full'].sort_values(['feature_date','grid_id']).reset_index(drop=True)
        assert np.array_equal(a.fire_positive,b.fire_positive)
        blocks=((a.feature_date-pd.Timestamp('2019-07-01')).dt.days//7).to_numpy()
        groups=[np.flatnonzero(blocks==w) for w in np.unique(blocks)]
        deltas=[]
        for _ in range(1000):
            indices=np.concatenate([groups[i] for i in rng.integers(0,len(groups),len(groups))])
            y=a.fire_positive.to_numpy()[indices]
            if y.sum()==0:continue
            deltas.append(average_precision_score(y,a.score.to_numpy()[indices])-average_precision_score(y,b.score.to_numpy()[indices]))
        uncertainty.append(dict(experiment=exp,test_weeks=len(groups),positive_weeks=int(a.assign(week=blocks).groupby('week').fire_positive.sum().gt(0).sum()),valid_bootstraps=len(deltas),
            ap_difference_xgb_minus_lr=float(average_precision_score(a.fire_positive,a.score)-average_precision_score(b.fire_positive,b.score)),
            bootstrap_95_percentile_interval=[float(v) for v in np.quantile(deltas,[.025,.975])],
            caveat='Descriptive weekly cluster resampling; sparse episodes and interweek dependence prevent a reliable population confidence claim'))
    (RESULTS/'uncertainty.json').write_text(json.dumps(uncertainty,indent=2))
    print(json.dumps(uncertainty,indent=2))

if __name__=='__main__':main()
