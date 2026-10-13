"""Create and execute a self-contained analysis notebook using the delivered modules."""
import contextlib,io,base64,sys,json
from pathlib import Path
import nbformat
import matplotlib.pyplot as plt
from audit_data import ROOT

def main():
    nb=nbformat.v4.new_notebook()
    nb.metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
        'language_info':{'name':'python','version':sys.version.split()[0]},
        'analysis_date':'2026-10-14','author':'Kian Luo','course':'ENGG2112',
        'note':'All code cells executed against the supplied dataset. Run from the extracted project root or output folder.'}
    cells=[
        ('md','# Blue Mountains next day active fire modelling\n\nKian Luo, ML Engineer. This notebook audits and reconstructs the features, trains the baselines and XGBoost, and evaluates both within-season interpolation and strictly forward testing. Prediction scores and alert thresholds are displayed as percentages; they are uncalibrated scores, not fire probabilities. Raw 0-1 scores and binary observation labels remain unchanged for evaluation.'),
        ('code',"from pathlib import Path\nimport sys, json\nROOT = Path.cwd()\nif not (ROOT / 'src').exists():\n    ROOT = ROOT.parent\nassert (ROOT / 'src').exists(), 'Open this notebook inside the delivered project'\nsys.path.insert(0, str(ROOT / 'src'))\nimport pandas as pd\nimport matplotlib.pyplot as plt\nfrom audit_data import DATA, load_and_audit\nfrom train_evaluate import FEATURES, split_weekly, split_chronological\nprint('Project:', ROOT.name)\nprint('Predictors:', {k: len(v) for k, v in FEATURES.items()})"),
        ('md','## Audit and feature reconstruction\n\nLabels, next-day alignment, neighbouring fire, rolling rainfall and completeness are checked before fitting. Reconstruction preserves the input files.'),
        ('code',"raw, data, audit = load_and_audit()\nprint(json.dumps(audit, indent=2))\nfrom rebuild_extended import main as rebuild\nrebuild()"),
        ('md','## Define the prediction and splits\n\nThe target is one or more eligible FIRMS detections in a cell on the following UTC day. Interleaved weekly partitions use future weeks and measure interpolation. The forward split is the evidence relevant to later dates. Date groups always contain every retained cell.'),
        ('code',"for name, role in [('Weekly holdout', split_weekly(data)), ('Forward test', split_chronological(data))]:\n    print(name)\n    print(data.assign(partition=role).groupby('partition').fire_positive.agg(['size','sum','mean']).to_string())\nprint('Full feature contract:', FEATURES['full'])"),
        ('md','## Train and tune\n\nTwelve fixed XGBoost configurations and four Logistic Regression regularisation values are scored on validation only. The threshold maximises validation precision subject to recall at least 0.80. Each outer fold has its own validation partition, scaler, class weights, early stopping and threshold. Test results do not guide any fitted parameter.'),
        ('code',"import train_evaluate\ntrain_evaluate.main()"),
        ('md','## Evaluate rankings and classification errors\n\nAverage precision is the main metric. Trapezoidal PR area is saved separately. New-fire evaluation keeps all cells without a detection on the feature day; this is a detection-state transition, not verified ignition.'),
        ('code',"metrics = pd.read_csv(ROOT / 'output/results/metrics.csv')\ncols = ['experiment','model','view','average_precision','precision','recall','f1','brier','tp','fp','fn','tn']\nprint(metrics[metrics.experiment.isin(['weekly_holdout','chronological'])][cols].to_string(index=False))\nfrom make_figures import main as make_figures\nmake_figures()"),
        ('code',"plt.figure(figsize=(12,5))\nplt.imshow(plt.imread(ROOT / 'output/figures/02_pr_chronological.png'))\nplt.axis('off')\nplt.show()"),
        ('md','## Blocked cross validation and sensitivity\n\nThe five outer test slots cover every retained row exactly once. Results remain correlated within one fire season. Three-day purging is a sensitivity analysis; seven-day symmetric purging removes the inner validation weeks and is not estimable with this rotation.'),
        ('code',"cv = metrics[metrics.experiment.str.startswith('blocked_fold_')]\nprint(cv.groupby(['model','view'])[['average_precision','recall','precision','brier']].agg(['mean','std']).to_string())\nprint((ROOT / 'output/results/uncertainty.json').read_text())"),
        ('md','## Probability quality and explanation\n\nPlatt calibration is exploratory and uses the same validation weeks as tuning. Native exact TreeSHAP is evaluated at the selected tree count and checked for additivity in log-odds units. Correlated covariates and the single season limit causal interpretation.'),
        ('code',"print((ROOT / 'output/results/calibration.json').read_text())\nplt.figure(figsize=(12,6))\nplt.imshow(plt.imread(ROOT / 'output/figures/06_shap_importance.png'))\nplt.axis('off')\nplt.show()"),
        ('md','## Verify saved results and inference\n\nThis independently recomputes metric counts and AP, verifies date separation and outer test coverage, checks saved-model prediction parity, and requires the exact input feature schema.'),
        ('code',"from verify_results import main as verify\nverify()\nexample = pd.read_csv(ROOT / 'output/example_scores.csv').head()\ncolumns = ['grid_id','feature_date','target_date','model_score_percent','threshold_percent','alert','forecast_horizon_days']\nprint(example[columns].to_string(index=False, formatters={name: lambda value: f'{value:.2f}%' for name in ['model_score_percent','threshold_percent']}))\nprint('Percentages are uncalibrated model scores, not fire probabilities. Alerts use the unrounded raw score.')"),
        ('md','## Interpretation and unobserved human activity\n\nThe evidence supports within-season ranking improvement over prevalence and persistence. The strict forward test has only 45 positive cell-days and detects no new-fire positives with the full model at its validation threshold. Deliberate or accidental ignition, recreation, land-management actions and suppression are not explicit model inputs. Historical labels can contain their effects, but the model cannot anticipate a specific unobserved action. A low score does not establish safety. Multiple independently heldout seasons, event grouping, complete fuel data and point-in-time weather availability are needed before a stronger use claim.'),
        ('md','## Forecast horizon\n\nEach prediction concerns the next UTC day only. If fire is detected today, the full model uses that observation to score continued or spreading fire tomorrow. With newly observed weather and fire state tomorrow, the model can be run again for the following day. This is rolling next-day prediction, not a two- or three-day forecast issued today. True two-/three-day forecasts require horizon-specific labels, training and time-safe evaluation. Do not reuse tomorrow\'s score for later days, insert predicted fire states as observed facts, or add/multiply these uncalibrated scores to obtain a multi-day probability. See docs/FORECAST_HORIZONS.md.'),
    ]
    namespace={'__name__':'notebook_execution'}
    count=0;figure_outputs=[]
    original_show=plt.show
    def capture_show(*args,**kwargs):
        for number in plt.get_fignums():
            buf=io.BytesIO();plt.figure(number).savefig(buf,format='png',bbox_inches='tight')
            figure_outputs.append(nbformat.v4.new_output('display_data',data={'image/png':base64.b64encode(buf.getvalue()).decode('ascii'),'text/plain':'<matplotlib figure>'}))
        plt.close('all')
    plt.show=capture_show
    try:
        for kind,source in cells:
            if kind=='md':nb.cells.append(nbformat.v4.new_markdown_cell(source));continue
            count+=1;cell=nbformat.v4.new_code_cell(source,execution_count=count);buffer=io.StringIO();figure_outputs.clear()
            with contextlib.redirect_stdout(buffer):exec(compile(source,f'notebook_cell_{count}','exec'),namespace)
            cell.outputs=[]
            if buffer.getvalue():cell.outputs.append(nbformat.v4.new_output('stream',name='stdout',text=buffer.getvalue()))
            cell.outputs.extend(figure_outputs);nb.cells.append(cell)
    finally:plt.show=original_show
    nbformat.validate(nb)
    nbformat.write(nb,ROOT/'output/Kian_ML_Analysis.ipynb')
    print(f'Executed and validated {count} code cells.')

if __name__=='__main__':main()
