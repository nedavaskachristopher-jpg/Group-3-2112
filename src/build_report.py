"""Build the English ML report, editable text, and Overleaf contribution from actual results."""
from pathlib import Path
import json,shutil,html
import numpy as np
import pandas as pd
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from audit_data import ROOT

OUT=ROOT/'output';R=OUT/'results';F=OUT/'figures';REPORT=OUT/'report';OVERLEAF=OUT/'overleaf'
REFERENCES=[
('firms','NASA','FIRMS active fire and thermal anomaly information','https://firms.modaps.eosdis.nasa.gov/map/'),
('era5','Copernicus Climate Data Store','ERA5 Land hourly data from 1950 to present','https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview'),
('chen','T Chen and C Guestrin','XGBoost A Scalable Tree Boosting System 2016','https://arxiv.org/abs/1603.02754'),
('ap','scikit learn developers','Average precision score documentation','https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html'),
('xgbparams','XGBoost developers','XGBoost parameters documentation','https://xgboost.readthedocs.io/en/stable/parameter.html'),
('xgbapi','XGBoost developers','Python API reference and SHAP contribution outputs','https://xgboost.readthedocs.io/en/stable/python/python_api.html'),
('calibration','scikit learn developers','Probability calibration documentation','https://scikit-learn.org/stable/modules/calibration.html'),
('roberts','D R Roberts et al','Cross validation strategies for data with temporal spatial hierarchical or phylogenetic structure Ecography 40 913 to 929 2017','https://doi.org/10.1111/ecog.02881'),
('rfs','NSW Rural Fire Service','Fire Weather Viewer explanation of fire behaviour and fuel inputs','https://fireweather.aig.apps.rfs.nsw.gov.au/about.html'),
]
LABELS={'prevalence':'Prevalence','persistence':'Persistence','lr_full':'Logistic full','lr_conditions':'Logistic conditions','xgb_full':'XGBoost full','xgb_conditions':'XGBoost conditions'}

def tex_escape(text):
    return ''.join({'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}.get(c,c) for c in str(text))

def main():
    REPORT.mkdir(parents=True,exist_ok=True);OVERLEAF.mkdir(parents=True,exist_ok=True)
    m=pd.read_csv(R/'metrics.csv');splits=pd.read_csv(R/'split_counts.csv');manifest=json.loads((R/'run_manifest.json').read_text())
    audit=json.loads((R/'data_audit.json').read_text());selected=json.loads((R/'model_selection.json').read_text())
    uncertainty=json.loads((R/'uncertainty.json').read_text());shap=pd.read_csv(R/'shap_summary.csv')
    cv=m[m.experiment.str.startswith('blocked_fold_')].groupby(['model','view'])
    get=lambda exp,model,view='all':m[(m.experiment==exp)&(m.model==model)&(m.view==view)].iloc[0]
    w=get('weekly_holdout','xgb_full');c=get('chronological','xgb_full')
    wc=get('weekly_holdout','xgb_conditions');wn=get('weekly_holdout','xgb_full','new_fire');cn=get('chronological','xgb_full','new_fire')
    p=lambda x:f'{x:.3f}';pct=lambda x:f'{100*x:.1f}%'
    pages=[]
    def page(title):
        a={'title':title,'items':[]};pages.append(a);return a['items']
    def para(items,text):items.append(('p',text))
    def table(items,headers,rows,widths=None):items.append(('table',(headers,rows,widths)))
    def fig(items,name,caption,height):items.append(('fig',(name,caption,height)))
    a=page('Blue Mountains Bushfire Modelling')
    para(a,'ML engineering evidence and report contribution | Kian Luo | ENGG2112 Tutorial 01 Group 03 | 14 October 2026')
    para(a,f'XGBoost improves the ranking of next-day satellite fire detections within the 2019-20 season, but its classification threshold transfers poorly to later dates. The full model achieved weekly-holdout average precision (AP) of {w.average_precision:.3f}, compared with 0.571 for persistence, and five-fold AP of 0.692 +/- 0.093. In the strictly forward test, AP fell to {c.average_precision:.3f}, recall was {pct(c.recall)}, and no new-fire positive cell-days were detected at the validation-selected threshold. These results support a reproducible retrospective proof of concept and do not establish operational warning capability.')
    para(a,'The prediction unit is a native 0.1 degree ERA5-Land cell on a UTC feature day t. The target is 1 when at least one eligible FIRMS detection is present within that cell and inside Blue Mountains National Park on day t+1. This includes continuing or spreading fire. A transition from no detection today to detection tomorrow is reported separately; it is not a confirmed ignition record.')
    table(a,['Verified property','Result'],[
        ['Main extended table','18,980 rows, 39 columns, 52 cells, 365 feature days'],
        ['Feature and target dates','1 Jul 2019 to 29 Jun 2020; targets 2 Jul 2019 to 30 Jun 2020'],
        ['Retained modelling panel','43 cells, 15,695 rows, 566 positive cell-days after 10% park filter'],
        ['Detection transitions','132 new-fire positive cell-days; 434 of 566 follow a detection today'],
        ['Quality checks','Unique cell-date keys, finite inputs, no missing values, target alignment verified'],
    ],[160,335])
    fig(a,'01_label_timeline','Figure 1. Retained positive labels by target date. The concentration in December limits what a single-season validation can establish.',155)

    a=page('1 Data preparation and feature design')
    para(a,'The Data Engineer outputs align weather to the whole ERA5-Land cell, while terrain and fire labels describe its park portion. A cell spans approximately 11 km north-south by 9 km east-west. We retained park_area_fraction >= 0.10 to reduce predominantly outside-park negative examples. This removed 3,285 rows and only 12 positive cell-days. The cutoff is a modelling choice, so an unfiltered comparison is also reported.')
    groups=manifest['features'];table(a,['Feature group','Inputs and rationale'],[
        ['Weather 8','Maximum, mean and minimum temperature; mean dew point; minimum and mean relative humidity; maximum and mean wind speed. These describe heat, atmospheric drying and wind conditions.'],
        ['Rainfall and dryness 6','Daily rainfall; 3, 7, 30 and 90 day rainfall totals; days since at least 5 mm rain, capped at 120. These are antecedent wetness proxies, not measurements of live or dead fuel moisture.'],
        ['Terrain 6','Mean slope; aspect sine and cosine; mean, minimum and maximum elevation. These summarise park-only terrain and encode circular aspect without an angular discontinuity.'],
        ['Current fire 3','Fire today; fire in any of the eight neighbouring cells today; number of fire days over the seven-day window ending today. Neighbours are computed on all 52 source cells before edge filtering.'],
    ],[120,375])
    para(a,'The full model uses all 23 numerical features. The conditions-only model uses the 20 weather, rainfall and terrain features. Neither model uses the target, target-day detection counts, dates, partition labels, cell identifiers, coordinates, seasonal encodings, raw aspect angle, terrain pixel counts, park fraction or the rainfall-history flag. Target-day counts would reveal the answer. Cell and calendar identifiers can encourage memorisation of one episode; static terrain can still encode location indirectly, so this exclusion does not demonstrate spatial transfer.')
    para(a,'Current fire and seven-day histories were reconstructed from the daily labels, and rainfall totals were reconstructed from daily precipitation plus the 30 June 2019 rainfall represented by the 1 July 00 UTC raw accumulation. All 39 extended columns were reproduced from the base table, label panel and that raw weather record within absolute tolerance 0.0001 and relative tolerance 0.00001. This checks the extension; it does not rerun all original GIS processing.')
    para(a,'The 90-day rainfall window is incomplete for the first 88 feature days, affecting 3,784 retained rows. The primary experiment retains these partial windows, and a sensitivity experiment requires rain_history_days >= 90. Initial days-since-rain values are capped rather than verified from a full pre-season history. No categorical encoding is needed. Logistic Regression uses a training-fitted median imputer and StandardScaler; there are no missing values to impute in this panel. XGBoost uses the numerical inputs without scaling.')

    a=page('2 Evaluation design and temporal separation')
    para(a,'The original proposal specified training on earlier seasons and testing on a later season. The available modelling panel covers only one season, so year-to-year generalisation cannot be measured. We therefore separate a strictly forward chronological assessment from weekly experiments that measure interpolation within the same season. Every date is assigned as a group containing all retained cells. No random row split is used. Structured validation should match the intended transfer task [8].')
    for exp,label in [('weekly_holdout','Table 1. Weekly holdout with starting-day and transition-day buffers'),('chronological','Table 2. Strictly forward split with two-day boundary gaps')]:
        para(a,label)
        s=splits[splits.experiment==exp].set_index('partition')
        table(a,['Partition','Rows','Positive cell days','Rate'],[[r,f'{int(s.loc[r,"size"]):,}',str(int(s.loc[r,'sum'])),pct(s.loc[r,'mean'])] for r in ['train','validation','test','buffer']],[120,110,155,110])
    para(a,'Weekly holdout numbers weeks from 1 July 2019, rotating train, train, train, validation, test. The first feature day and the first day of each week where the role changes are discarded as buffers. The test contains 107 positives across three positive weeks among ten test weeks. The training set includes dates after some test dates; this is not a forecast simulation. A one-day buffer prevents immediate boundary reuse but cannot isolate a long-running fire or remove shared rainfall histories.')
    para(a,'For the forward test, training ends 14 December 2019; validation covers 17-30 December; testing covers 2 January-29 June 2020, corresponding to target days 3 January-30 June. Four buffer dates remove 172 rows and 46 positives. Training labels precede the first validation feature date, and validation labels precede the first test feature date. No later dates are fitted. This test still spans one season and the same cells.')
    para(a,'For five-fold blocked evaluation, the outer test slot is k in the five-week rotation, the inner validation slot is (k+1) mod 5, and the other three slots train. Training dates within one day of either evaluation partition are removed; validation dates within one day of test are also removed. Tuning, preprocessing, imbalance weights and thresholds are refitted within each outer fold. Every retained row is tested exactly once. Three-day purging is an additional diagnostic. Seven-day symmetric purging removes the inner validation weeks, so that rotation cannot support a valid seven-day nested experiment.')

    a=page('3 Model development and decision rule')
    para(a,'We implemented a prevalence score equal to the training positive fraction and a persistence rule equal to fire_today. Both use a fixed alert threshold of 0.5 and neither is tuned. Persistence tests whether machine learning adds more than continuing yesterday\'s observed fire. Weighted Logistic Regression provides a linear comparison, and XGBoost captures nonlinear combinations of weather, wetness, terrain and recent fire [3]. Both learned models were fitted in full and conditions-only versions.')
    para(a,'Logistic Regression searches C in {0.01, 0.1, 1, 10}, with balanced class weights, maximum 3,000 iterations and seed 2112. The entire imputer and scaler pipeline is fitted only on training rows. XGBoost searches 12 configurations: depths 3, 4 and 6, crossed with four preset learning-rate, minimum-child-weight and sampling combinations recorded in run_manifest.json. Learning rates range from 0.03 to 0.10, minimum-child weights from 1 to 10, row sampling from 0.8 to 1.0 and column sampling from 0.7 to 1.0. L2 regularisation is 2; the tree method is hist; up to 500 trees are allowed with 35 rounds of early-stopping patience. Four CPU threads and seed 2112 are used.')
    para(a,'The training-only XGBoost positive weight is negatives divided by positives [5]. Early stopping monitors validation aucpr, while the winning candidate maximises validation AP. These are different PR summaries: XGBoost aucpr uses continuous interpolation; scikit-learn AP sums precision weighted by recall increments [4,5]. Our reported primary score is AP. Trapezoidal PR area, ROC area and false-positive rate are retained in the results file and are not substituted for AP.')
    table(a,['Experiment and version','Depth','Rate','Trees','Positive weight','Score threshold'],[
        [f'{x["experiment"].replace("_"," ")} {x["model"].replace("xgb_","")}',str(x['parameters']['max_depth']),str(x['parameters']['learning_rate']),str(x['parameters']['best_iteration']+1),f'{x["parameters"]["scale_pos_weight"]:.2f}',f'{x["validation_threshold"]*100:.2f}%']
        for x in selected if x['experiment'] in ['weekly_holdout','chronological'] and x['model'].startswith('xgb')
    ],[185,40,45,45,90,90])
    para(a,'For each learned model, the threshold maximises precision on validation subject to validation recall >= 0.80; ties select the higher threshold. This is an explicit illustrative preference for fewer missed fires, not a cost validated with stakeholders. The threshold is frozen before test evaluation. Meeting the validation constraint does not guarantee 80% recall on test, particularly when class prevalence and fire state change.')
    para(a,'Accuracy, precision, recall, F1, confusion counts and Brier score supplement AP. New-fire metrics use the subset fire_today = 0, including its negative examples, with exactly the same threshold. We do not retune on this test subset. The sparse positives and persistent fire mean high overall accuracy can coexist with weak detection of new fire.')

    a=page('4 Weekly holdout findings and errors')
    para(a,'Table 3. Weekly test performance at thresholds fixed on validation')
    table(a,['Model','AP','Accuracy','Precision','Recall','F1','Brier'],[[LABELS[k],p(get('weekly_holdout',k).average_precision),pct(get('weekly_holdout',k).accuracy),p(get('weekly_holdout',k).precision),p(get('weekly_holdout',k).recall),p(get('weekly_holdout',k).f1),f'{get("weekly_holdout",k).brier:.4f}'] for k in LABELS],[145,50,65,60,55,55,65])
    para(a,f'The full XGBoost model ranks positive days better than persistence and Logistic Regression, but its threshold recalls the same {int(w.tp)} of 107 positives as persistence. Its advantage at that threshold is fewer false alerts: {int(w.fp)} versus 30. It produces {int(w.alerts)} alerts, misses {int(w.fn)} positive cell-days and has a false-positive rate of {pct(w.false_positive_rate)}. Conditions-only XGBoost detects {int(wc.tp)} positives but produces {int(wc.fp)} false positives; the tradeoff is higher recall with substantially greater alert burden.')
    fig(a,'02_pr_weekly_holdout','Figure 2. Weekly holdout PR curves for all cell-days and the no-fire-today subset. A constant baseline has AP equal to test prevalence.',185)
    para(a,f'For new-fire evaluation, 25 positives remain among 2,468 rows. Full XGBoost AP is {wn.average_precision:.3f}, compared with {get("weekly_holdout","lr_full","new_fire").average_precision:.3f} for full Logistic Regression, and it detects none of these 25 positives at its all-fire threshold. Conditions-only XGBoost has AP {get("weekly_holdout","xgb_conditions","new_fire").average_precision:.3f} and detects 13 of 25, but only 13 of its 209 new-fire alerts are positive. Removing current fire exposes useful conditions ranking but does not solve a low-false-alarm ignition problem.')
    para(a,'The no-alert prevalence baseline already achieves 95.9% overall accuracy and 99.0% accuracy in the new-fire subset. Accuracy alone would conceal every missed positive. The full model is primarily effective for ranking established fire; the error counts and subset evaluation qualify the headline AP.')

    a=page('5 Strictly forward findings and transfer limits')
    para(a,'Table 4. Forward test performance on 7,740 rows with 45 positives')
    table(a,['Model','AP','Precision','Recall','F1','False alerts','Brier'],[[LABELS[k],p(get('chronological',k).average_precision),p(get('chronological',k).precision),p(get('chronological',k).recall),p(get('chronological',k).f1),str(int(get('chronological',k).fp)),f'{get("chronological",k).brier:.4f}'] for k in LABELS],[145,50,60,55,55,65,65])
    para(a,f'Full XGBoost AP of {c.average_precision:.3f} is above prevalence ({get("chronological","prevalence").average_precision:.4f}), persistence (0.081) and full Logistic Regression (0.130), but the operationally relevant threshold performance is poor. At score threshold {c.threshold*100:.2f}% (uncalibrated), it detects 13 of 45 positives, misses 32 and issues 35 false alerts. Its 99.1% accuracy is below the 99.4% no-alert baseline. Conditions-only XGBoost AP is only 0.0096 and it produces 1,073 false alerts while detecting 14 positives.')
    fig(a,'02_pr_chronological','Figure 3. Forward PR curves. Results are not directly comparable to the weekly curves because both test prevalence and episodes differ.',185)
    para(a,'The forward validation block has 245 positives in 602 rows, or 40.7%, whereas the later test has 45 in 7,740, or 0.58%. The validation block lies within the intense December episode and does not represent the later test distribution. This change is consistent with poor transfer of the threshold and calibration; the experiment does not isolate prevalence shift from changing environmental conditions, fire persistence or satellite observation effects.')
    para(a,f'The new-fire subset has 32 positives among 7,691 rows. Full XGBoost AP is {cn.average_precision:.3f}, but at the fixed threshold it detects zero positives and makes one false alert. Conditions-only XGBoost detects eight positives with 1,067 false alerts. A useful ranking score therefore does not establish a usable warning threshold. A threshold specifically for new-fire transitions could be investigated using a separate validation design; it must not be selected from these test outcomes.')

    a=page('6 Blocked evaluation and robustness')
    para(a,'Table 5. Five-fold means and sample standard deviations; folds are correlated within one season')
    rows=[]
    for k in LABELS:
        group=cv.get_group((k,'all'));new=cv.get_group((k,'new_fire'))
        rows.append([LABELS[k],f'{group.average_precision.mean():.3f} +/- {group.average_precision.std():.3f}',f'{group.recall.mean():.3f} +/- {group.recall.std():.3f}',f'{new.average_precision.mean():.3f} +/- {new.average_precision.std():.3f}'])
    table(a,['Model','All fire AP','All fire recall','New fire AP'],rows,[140,120,120,115])
    fig(a,'03_blocked_cv','Figure 4. Individual outer-fold AP values. The spread shows dependence on which weeks are withheld.',170)
    para(a,'XGBoost full exceeds full Logistic Regression by only 0.016 in mean AP; its mean recall is lower, 0.709 versus 0.799, and its raw mean Brier score is worse, 0.0524 versus 0.0396. For new-fire ranking, full Logistic Regression leads 0.176 versus 0.152. No single model dominates all metrics. Each model\'s threshold is fitted independently to validation, so classification tradeoffs are reported alongside ranking.')
    table(a,['Sensitivity experiment','XGBoost full AP','Conditions AP'],[
        ['Weekly panel with 10% edge filter','0.824','0.555'],
        ['Weekly panel without edge filter',p(get('no_edge_filter','xgb_full').average_precision),p(get('no_edge_filter','xgb_conditions').average_precision)],
        ['Weekly panel with complete 90 day rainfall history',p(get('complete_rain_history','xgb_full').average_precision),p(get('complete_rain_history','xgb_conditions').average_precision)],
        ['Outer folds with three day purging',f'{m[(m.experiment.str.startswith("purge3_fold_"))&(m.model=="xgb_full")&(m.view=="all")].average_precision.mean():.3f}',f'{m[(m.experiment.str.startswith("purge3_fold_"))&(m.model=="xgb_conditions")&(m.view=="all")].average_precision.mean():.3f}'],
        ['Calendar diagnostic added to full model',p(get('calendar_diagnostic','xgb_seasonal_diagnostic').average_precision),'Not fitted'],
    ],[280,110,105])
    para(a,'Unfiltered and warm-history panels change both fitted data and test composition; their differences are sensitivity evidence, not paired estimates of a filter\'s causal benefit. Adding sine and cosine calendar features did not improve weekly AP (0.814 versus 0.824), so these features remain excluded. Weekly cluster bootstrap differences between full XGBoost and full Logistic Regression were 0.081 with a descriptive 95% interval [-0.001, 0.086], and 0.056 with [-0.026, 0.205] in the forward test. Samples without positives were omitted. Only three and five positive weeks respectively, with interweek dependence, make these intervals too fragile for a strong superiority claim.')

    a=page('7 Probability quality and alert decisions')
    para(a,'Prediction scores and alert thresholds are displayed as percentages by multiplying the raw 0-1 values by 100. These are uncalibrated scores, not percentages of fire occurrence. Binary observation labels, raw scores, alert decisions and metric calculations are retained. Brier score compares the raw score with the binary label; reliability curves compare binned scores with observed frequencies [7]. A lower Brier score alone does not establish reliable probability calibration.')
    fig(a,'05_calibration','Figure 5. Quantile-binned reliability curves for full XGBoost before and after exploratory Platt calibration. Bins and estimates are sparse and season dependent.',190)
    para(a,'Exploratory unweighted Platt calibration fitted to validation logits reduces the full-model weekly Brier score from 0.0201 to 0.0138 and forward Brier from 0.0192 to 0.0102. The forward calibrated full-model Brier is still worse than the prevalence baseline of 0.0065. For conditions-only XGBoost, forward calibration makes Brier worse, 0.0864 versus 0.0457. Calibration fitted to a December block does not reliably transfer to a low-prevalence later period.')
    para(a,'The exploratory calibrator uses the same validation data as hyperparameter selection and threshold tuning, not an independent calibration sample. It is not used by the saved inference interface. Its positive sigmoid slope preserves ranking and the corresponding transformed threshold preserves alert decisions. A future deployment needs separately reserved, representative calibration data and prospective checks of alert rate and probability reliability.')
    fig(a,'04_confusion','Figure 6. Full XGBoost confusion counts at validation-selected thresholds. These are cell-days rather than independent fire incidents.',165)

    a=page('8 Model explanation and physical interpretation')
    para(a,'We computed exact native TreeSHAP contributions through XGBoost pred_contribs at the selected number of trees. Each row\'s feature contributions plus the bias were checked against its raw prediction margin to absolute tolerance 0.0002. Contributions are measured in log odds, not probabilities [6]. Explanation uses test inputs after model selection and does not alter fitted features, hyperparameters or thresholds.')
    fig(a,'06_shap_importance','Figure 7. Mean absolute TreeSHAP contributions on weekly test inputs. Correlated features can share or exchange attributed importance.',205)
    para(a,'The full model is dominated by seven-day fire history, neighbouring fire and fire_today. This supports the observed gap between its all-fire and new-fire performance. The conditions-only model is led by 30- and 90-day rainfall and mean temperature. Its associations are consistent with antecedent drying and heat, but those variables also follow the single season\'s calendar, so the explanation cannot separate a physical mechanism from episode-specific timing.')
    fig(a,'07_shap_dependence','Figure 8. Selected conditions-model feature values against their own SHAP contributions. Each dot is a test cell-day.',145)
    para(a,'Maximum wind speed has a positive value-contribution Spearman association of 0.719, and mean relative humidity has a negative association of -0.765. Minimum humidity (-0.055) and days since 5 mm rain (0.068) have weak monotonic associations in this fitted model. We therefore do not claim that every effect follows the expected physical direction. The weak dryness pattern may reflect correlation with cumulative rainfall, capping and limited seasonal variation. Spearman summaries are descriptive and are not significance tests or causal effects. Fuel type, load, live moisture and burn age are absent, even though fuel information is relevant to fire behaviour [9].')

    a=page('9 Illustrative spatial output')
    para(a,'The example map displays the two XGBoost model scores on the weekly-heldout target day 19 December 2019. The date was deliberately selected as the heldout day with the largest observed number of positive cells so that spatial correspondence can be seen. This selection is illustrative; aggregate performance is established by the complete test tables, not by the map.')
    fig(a,'08_illustrative_map','Figure 9. Native weather-grid cell scores and park boundary. Crosses indicate positive next-day detections somewhere within the park portion of a cell, not the precise fire location.',420)
    para(a,'Cells extend outside the park because the weather grid determines the prediction unit. Colours display model score percentages and must not be interpreted as calibrated ignition probabilities or official fire danger ratings. The model averages terrain over coarse cells and does not predict a fine-scale fire front. All cells in this experiment are also represented in training, so this map does not demonstrate generalisation to a new location.')
    para(a,'Each score concerns the next day only. Following a detected fire, update the observed fire state, weather and histories each day to issue a new next-day score. This does not provide a two- or three-day forecast issued today, guarantee continued burning, or identify independent incidents. Longer horizons require new aligned targets, models and time-safe validation; current scores must not be added or multiplied into a multi-day probability.')

    a=page('10 Limitations and changes from the proposal')
    table(a,['Limitation','Implication and next evidence needed'],[
        ['One extreme fire season','493 of the original 578 target-positive cell-days occur in December 2019. Add ordinary and extreme independent seasons; retain a final unseen season.'],
        ['Detection labels','Cloud, obscuration and satellite sampling can miss active fires [1]. A negative label is no detection, not proof of no fire. Validate against independent incident records.'],
        ['Partial prescribed burn exclusion','Only 18 detections were excluded by dated NPWS polygons in the source audit. Remaining planned burns can contaminate labels; validate event identity and dates.'],
        ['Persistence and continuing fires','434 of 566 retained positives follow a detection today. Group entire events and evaluate genuine new incidents with independent labels.'],
        ['Unobserved human activity','Deliberate or accidental ignition and suppression are not explicit inputs. Historical labels can include these effects, but specific unobserved actions cannot be anticipated. Percentage display does not remove this uncertainty.'],
        ['Interleaved validation','Short gaps and rolling features do not isolate long events. Nested fold scores remain within-season interpolation.'],
        ['Coarse cells and missing fuels','Native weather resolution is approximately 100 square km; terrain is averaged and fuel type/load/moisture are absent. Test richer fuel data and appropriate finer weather support.'],
        ['Point in time availability','Full UTC-day statistics and the next midnight precipitation accumulation require completed-day data. ERA5-Land is retrospective reanalysis [2]. Validate timestamps, latency and forecast inputs before a prospective use claim.'],
        ['Threshold and calibration shift','December validation prevalence is 40.7%; forward test is 0.58%. Use representative validation and an independent calibration block; monitor false alerts and misses.'],
    ],[140,355])
    para(a,'We retained the next-day detection target, native weather grid, XGBoost, Logistic Regression, public-data inputs and validation-only decisions from the proposal. We added persistence as a stronger baseline, conditions-only ablation, new-fire evaluation, nested blocked folds, longer-purge diagnostics, complete-history checks, exact TreeSHAP and explicit probability-quality analysis. The planned heldout independent fire season was not achieved. Fuel moisture, weather-station checks and Random Forest were optional and were not implemented. A finer-resolution or cross-season performance claim is not supported by the completed experiments.')
    para(a,'The results could guide retrospective research into which areas or conditions deserve further investigation, but they do not justify issuing public warnings, choosing burn dates or allocating emergency resources directly. Recommended next steps are to verify event-level labels and prescribed burns, obtain multiple complete seasons and fuel data, reserve an unseen season, validate feature availability at the actual issue time, and evaluate a stakeholder-agreed cost and calibration policy. Human review and existing official information remain necessary. The Domain Researcher should connect these engineering limits to affected groups and practical decisions.')

    a=page('11 Reproducibility and references')
    versions=manifest['versions']
    para(a,f'Experiments ran with Python {versions["python"]}, NumPy {versions["numpy"]}, pandas {versions["pandas"]}, scikit-learn {versions["sklearn"]} and XGBoost {versions["xgboost"]}, using seed 2112. The model-input SHA-256 is {audit["sha256"]}. The numerical reconstruction and stored-result checks pass. The executed notebook includes all training, tuning and evaluation steps. Original inputs are preserved.')
    table(a,['Artifact','Purpose'],[
        ['Kian_ML_Analysis.ipynb','Executed, validated notebook with audit, model development and evaluation outputs'],
        ['src/train_evaluate.py and src/predict.py','Reproducible experiments and strict feature-contract inference'],
        ['results/metrics.csv and predictions.csv','126 metric rows and 226,228 stored experiment-model predictions'],
        ['results/model_selection.json and run_manifest.json','Validation scores, all tuning trials, parameters, thresholds and software versions'],
        ['models/','Training-only learned models, selected XGBoost trees in UBJ format and metadata'],
        ['overleaf/','Completed ML contribution, group scaffold, verified references and report figures'],
    ],[215,280])
    para(a,'Online references were checked on 14 October 2026. The dataset inventory and original GIS/source provenance are retained with the input materials; those acquisition details should be confirmed in the group report by the Data Engineer.')
    for i,(_,author,title,url) in enumerate(REFERENCES,1):para(a,f'[{i}] {author}. {title}. {url}')

    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ReportBody',fontName='Helvetica',fontSize=10.2,leading=14.0,spaceAfter=9,textColor=colors.HexColor('#20252B')))
    styles.add(ParagraphStyle(name='ReportTitle',fontName='Helvetica-Bold',fontSize=22,leading=27,spaceAfter=15,textColor=colors.black))
    styles.add(ParagraphStyle(name='ReportHeading',fontName='Helvetica-Bold',fontSize=16,leading=20,spaceAfter=13,textColor=colors.black))
    styles.add(ParagraphStyle(name='ReportCell',fontName='Helvetica',fontSize=8.7,leading=11,spaceAfter=0))
    styles.add(ParagraphStyle(name='ReportCaption',fontName='Helvetica',fontSize=8.7,leading=11,spaceBefore=5,spaceAfter=10,textColor=colors.HexColor('#4B5563')))
    body=[];md=[]
    for page_i,page_data in enumerate(pages):
        if page_i:body.append(PageBreak())
        body.append(Paragraph(html.escape(page_data['title']),styles['ReportTitle' if page_i==0 else 'ReportHeading']))
        md.append(('# ' if page_i==0 else '## ')+page_data['title']+'\n')
        for kind,item in page_data['items']:
            if kind=='p':
                # Allow long source URLs and checksum to wrap without shrinking body text.
                style=styles['ReportBody']
                if item.startswith('['):style=styles['ReportCaption']
                body.append(Paragraph(html.escape(item),style));md.append(item+'\n')
            elif kind=='table':
                headers,rows,widths=item
                values=[[Paragraph(html.escape(str(v)),styles['ReportCell']) for v in row] for row in [headers]+rows]
                tab=Table(values,colWidths=widths,repeatRows=1,hAlign='LEFT')
                tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E8EDF1')),('VALIGN',(0,0),(-1,-1),'TOP'),
                    ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
                    ('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#B8C1CA')),('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#D7DDE3'))]))
                body.extend([tab,Spacer(1,10)])
                md.append('| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in rows)+'\n')
            else:
                name,caption,height=item;im=Image(str(F/f'{name}.png'))
                scale=min(495/im.imageWidth,height/im.imageHeight);im.drawWidth=im.imageWidth*scale;im.drawHeight=im.imageHeight*scale
                body.append(KeepTogether([im,Paragraph(html.escape(caption),styles['ReportCaption'])]))
                md.append(f'![{caption}](../figures/{name}.png)\n')
    def footer(canvas,doc):
        canvas.saveState();canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#626C76'))
        canvas.drawString(50,28,'ENGG2112  |  Kian Luo  |  ML engineering')
        canvas.drawRightString(A4[0]-50,28,str(doc.page));canvas.restoreState()
    pdf=REPORT/'Kian_ML_Report.pdf'
    SimpleDocTemplate(str(pdf),pagesize=A4,rightMargin=50,leftMargin=50,topMargin=45,bottomMargin=45,
        title='Blue Mountains Bushfire Modelling',author='Kian Luo',subject='ENGG2112 ML engineering contribution').build(body,onFirstPage=footer,onLaterPages=footer)
    (REPORT/'Kian_ML_Report.md').write_text('\n'.join(md),encoding='utf-8')
    (R/'report_content.json').write_text(json.dumps(pages,indent=2),encoding='utf-8')
    # The ML contribution is a drop-in section. It contains the complete methods and results.
    tex=[]
    for page_data in pages[1:-1]:
        title=page_data['title'].split(' ',1)[1]
        tex.append(r'\subsection{'+tex_escape(title)+'}')
        for kind,item in page_data['items']:
            if kind=='p':tex.append(tex_escape(item)+'\n')
            elif kind=='table':
                headers,rows,widths=item
                fractions=[v/sum(widths)*.90 for v in widths]
                columns=''.join('p{'+f'{f:.3f}'+r'\linewidth}' for f in fractions)
                tex.append(r'{\setlength{\tabcolsep}{3pt}\begin{center}\small\begin{tabular}{'+columns+r'}\toprule')
                tex.append(' & '.join(tex_escape(v) for v in headers)+r' \\ \midrule')
                tex.extend(' & '.join(tex_escape(v) for v in row)+r' \\' for row in rows)
                tex.append(r'\bottomrule\end{tabular}\end{center}}')
            else:
                name,caption,height=item
                tex.extend([r'\begin{figure}[htbp]\centering',r'\includegraphics[width=\linewidth,height='+f'{min(height/72,5.8):.2f}'+r'in,keepaspectratio]{figures/'+name+'.png}',r'\caption{'+tex_escape(caption.split('. ',1)[-1])+r'}\end{figure}'])
    # Convert the report's numeric references into bibliography citations for the group document.
    text='\n'.join(tex)
    for i,(key,*_) in enumerate(REFERENCES,1):text=text.replace(f'[{i}]',r'\cite{'+key+'}')
    text=text.replace('[4,5]',r'\cite{ap,xgbparams}')
    (OVERLEAF/'kian_section.tex').write_text(text,encoding='utf-8')
    chunks=text.split(r'\subsection{')
    complete=[r'\subsection{'+chunk for chunk in chunks[1:]]
    (OVERLEAF/'kian_methods.tex').write_text('\n'.join(complete[:3]),encoding='utf-8')
    (OVERLEAF/'kian_results.tex').write_text('\n'.join(complete[3:9]),encoding='utf-8')
    (OVERLEAF/'kian_limitations.tex').write_text('\n'.join(complete[9:]),encoding='utf-8')
    bib=[]
    for key,author,title,url in REFERENCES:
        bib.append('@misc{'+key+',\n  author = {'+tex_escape(author)+'},\n  title = {'+tex_escape(title)+'},\n  howpublished = {\\url{'+url+'}},\n  note = {Accessed 14 October 2026}\n}')
    (OVERLEAF/'refs.bib').write_text('\n\n'.join(bib),encoding='utf-8')
    (OVERLEAF/'figures').mkdir(exist_ok=True)
    for path in F.glob('*.png'):shutil.copy2(path,OVERLEAF/'figures'/path.name)
    logo=ROOT/'inputs/report_template/the-university-of-sydney-vector-logo.png'
    if logo.is_file():shutil.copy2(logo,OVERLEAF/'the-university-of-sydney-vector-logo.png')
    print('Built report:',pdf)

if __name__=='__main__':main()
