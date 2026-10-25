"""Assemble a review-ready group draft around unchanged aggregate-derived ML sections."""

import json
from pathlib import Path

from tools.build_handover import REFERENCES, build_pages, markdown_table, read_evidence, tex_text

ROOT = Path(__file__).resolve().parents[1]


def group_content(root=ROOT):
    evidence = read_evidence(root)
    frozen, partition = evidence['freeze'], evidence['partitions']
    p = lambda text: {'type': 'paragraph', 'text': text}
    h = lambda text: {'type': 'heading', 'text': text}
    table = lambda headers, rows, widths: {'type': 'table', 'headers': headers, 'rows': rows, 'widths': widths}
    introduction = {'title': 'Project scope and research question', 'blocks': [
        p('Integration draft for Group 3. Author details, source-owner verification and member approval remain pending. This document is AI-assisted review material, not a declaration that every member completed or endorsed its contents.'),
        h('Executive overview'),
        p('We investigated whether weather, terrain and observed current fire could support next-day satellite-detection research in Blue Mountains National Park. A revised reproducible ML workflow was completed, but its frozen final evaluation did not establish reliable warnings or calibrated fire probabilities. The contribution is a documented comparison and an explanation of its limitations.'),
        h('Research question and objectives'),
        p('For each retained native weather-grid cell and completed UTC day, can learned scores identify eligible satellite fire detection on the next day better than prevalence and persistence references, and can a development-selected reminder policy transfer to later dates? The objectives were to audit the data interface, compare matched models, assess temporal stability and score reliability, freeze decisions and report one final evaluation transparently.'),
        h('Related work'),
        p('XGBoost provides a method for modelling nonlinear feature relationships [1], while AP summarises ranking without conflating it with threshold accuracy [2]. The supplied Australian environmental-analytics paper motivates multi-source bushfire research [5]. Its task, sampling and reported metrics are not a direct benchmark for our cell-day next-day evaluation. Seb must confirm and extend the literature interpretation before submission.'),
        h('Changes from the original plan'),
        p('The available data cover one season, so an independent later-season test was not possible. Fuel/vegetation inputs, Random Forest, new SHAP analysis, live inputs and operational deployment were not delivered. The revised method restricted inputs to those supported by the audit and used chronological rather than interleaved evaluation as its main evidence. These scope changes are recorded, not hidden by high within-season scores.'),
        h('Version and evidence boundary'),
        p('The previous group study and revised study identify the same extended source table and overlapping 2019-20 dates/cells. A protected one-time release under a revised protocol is not a previously unknown dataset or independent-season replication. The legacy version remains preserved; the revised source commit, freeze and release are linked in the repository integration records.'),
    ]}
    data = {'title': 'Data lineage, unit and limitations', 'blocks': [
        table(['Source panel item', 'Recorded value'], [
            ['Rows and columns', f"{partition['source_rows']:,} rows; {partition['source_columns']} columns"],
            ['Source and retained cells', f"{partition['source_grid_cells']} source; {partition['retained_grid_cells']} retained"],
            ['Feature-date coverage', evidence['protocol']['feature_date_start'] + ' to ' + evidence['protocol']['feature_date_end']],
            ['Current model inputs', f"{len(frozen['models']['logistic_16']['columns'])} core; {len(frozen['models']['xgboost_17']['columns'])} with same-day detection"],
            ['Park-overlap rule', f"At least {frozen['minimum_park_area_fraction']:.0%}"],
        ], [0.40, 0.60]),
        h('Supplied source lineage'),
        table(['Dataset', 'Role recorded in the supplied preparation'], [
            ['NASA FIRMS VIIRS', 'Eligible next-day detection target and same-day fire flag'],
            ['ERA5-Land', 'Retrospective hourly weather aggregated to daily summaries'],
            ['Geoscience Australia SRTM', 'Park-portion elevation, slope and aspect summaries'],
            ['NPWS estate and fire history', 'Park boundary/overlap and partial prescribed-burn exclusion'],
        ], [0.32, 0.68]),
        p('The original source register, provenance, prepared tables, spatial files, preparation scripts and limited raw subset are retained with their attribution. Their bytes are checked against the group baseline. The public subset omits most original raw GIS/fire/weather inputs; the complete acquisition and spatial-label pipeline was not independently rerun during integration.'),
        h('Data interface and uncertainty'),
        p('Data sources are joined by grid and UTC date. Weather represents the whole grid cell, whereas terrain and labels concern its park portion. Non-detection is not verified absence of fire, and known prescribed burns are only partially excluded. Zero-positive final months remain reported; adequate observation coverage requires data-owner confirmation.'),
        p('Available columns are not automatically approved predictors. Long rainfall windows have incomplete early history and the initial dry-spell state lacks prior observations. These candidates were excluded; the core three-day window has a two-day fitting warm-up. Inputs describe completed days and retrospective archives, so actual publication latency and issue-time availability have not been validated [6].'),
        p('Penelope is the current data contact identified for this revision. Jin\'s earlier data PR remains historically attributed. Source versions, licences, geometry, coverage and target construction still require the data owner\'s recorded review; no full acquisition or personal verification is claimed on either member\'s behalf.'),
    ]}
    map_page = {'title': 'Cached spatial illustration and use limits', 'blocks': [
        {'type': 'image', 'path': 'figures/frozen_score_map.png', 'height': 345,
         'caption': 'Figure 3  First frozen feature day (1 January 2020), using original saved XGBoost 17 scores. Native grid cells extend outside the park. Colours are uncalibrated model scores, not ignition probabilities or official warnings.'},
        p('The date was fixed as the first frozen feature date without inspecting outcomes. The drawing uses the receipt-matching prediction cache and supplied static geometry, not a new model prediction pass. Its provenance records the original score-cache hash. No observed outcomes are used to select the date or colour the cells.'),
        p('The map illustrates the output unit and park geometry. It does not demonstrate reliable spatial warning performance, generalisation to unseen locations or continuous fire fronts. The old model\'s SHAP and illustrative map remain historical and are not relabelled as revised-model evidence.'),
        h('Decision consequences'),
        p('Emergency services and land managers could face wasted review effort from false alerts, while misses or low scores could create false reassurance. Residents and councils could misinterpret percentage formatting as a validated probability. Any future use affecting communities or land-management choices would need appropriate consultation and governance; no such consultation or stakeholder endorsement is claimed.'),
    ]}
    review = {'title': 'Group integration and assistance appendix', 'blocks': [
        p('Engineering artifacts are available for review. Automated acceptance is recorded separately in the repository and does not establish personal understanding, peer approval or final submission readiness. The official deadline, confirmed author details and final group approval must be supplied by the group.'),
        table(['Contact', 'Required final review'], [
            ['Kian', 'Explain and inspect the ML code, metrics, freeze and adverse findings'],
            ['Chris', 'Confirm official requirements, authors and complete report consistency'],
            ['Penelope', 'Confirm source rights, timing, labels, geometry and observation coverage'],
            ['Seb', 'Check primary literature and stakeholder/ethical interpretation'],
        ], [0.20, 0.80]),
        h('Substantive AI assistance'),
        p('Codex assisted with modelling code, explanations, experimental checks, integration, figures and report prose under Kian\'s direction. The following prompts are condensed English translations, not a verbatim transcript. Preserve the conversation and record real member changes/checks in the linked contribution and AI-use records.'),
        table(['Prompt summary', 'Output and recorded verification'], [
            ['Reserve a final test; explain each ML step', 'Chronological protocol, data guards and baseline comparisons; synthetic checks'],
            ['Compare models, temporal stability and probabilities', 'Matched models and development-only checks; calibration not adopted'],
            ['Freeze both policies and evaluate once', 'Committed freeze, completed receipt and unchanged adverse final result'],
            ['Integrate in five stages with detailed English commits', 'Baseline tag, migration inventory, guarded applications and clean-clone acceptance record'],
        ], [0.42, 0.58]),
        p('Tool-assisted checks are not independent scientific replication or student sign-off. No final outcomes were used to retune this integration. New modelling requires independent evaluation data, while the submitted report must retain the failed probability/warning objectives and the limitations of the supplied evidence.'),
    ]}
    pages = [introduction, data, *build_pages(evidence), map_page, review]
    return {'project': 'Blue Mountains Bushfire Prediction', 'title': 'Group 3 Research Report - Integration Draft',
            'pages': pages, 'references': REFERENCES,
            'status': 'AI-assisted integration draft; member and source-owner review pending',
            'source_ml_commit': '1b3d7dd170583333327c887f95132bb5913e7ccd'}


def export(content, root=ROOT):
    folder = root / 'report'
    (folder / 'group_report_content.json').write_text(json.dumps(content, indent=2) + '\n')
    markdown = ['# ' + content['project'], '', content['title'], '', content['status'], '']
    tex = []
    for index, page in enumerate(content['pages']):
        if index:
            tex += [r'\clearpage']
        markdown += ['## ' + page['title'], '']
        tex += [r'\section*{' + tex_text(page['title']) + '}']
        for block in page['blocks']:
            if block['type'] in {'paragraph', 'heading'}:
                markdown += [('### ' if block['type'] == 'heading' else '') + block['text'], '']
                tex += [r'\subsection*{' + tex_text(block['text']) + '}' if block['type'] == 'heading' else tex_text(block['text']), '']
            elif block['type'] == 'table':
                markdown += [markdown_table(block['headers'], block['rows']), '']
                widths = [f'p{{{width * 0.86:.3f}\\linewidth}}' for width in block['widths']]
                tex += [r'\begin{center}\small\setlength{\tabcolsep}{3pt}', r'\begin{tabular}{' + ''.join(widths) + '}', r'\hline',
                        ' & '.join(tex_text(str(x)) for x in block['headers']) + r' \\ \hline']
                tex += [' & '.join(tex_text(str(x)) for x in row) + r' \\' for row in block['rows']]
                tex += [r'\hline\end{tabular}\end{center}', '']
            else:
                markdown += [f"![{block['caption']}]({block['path']})", '', block['caption'], '']
                tex += [r'\begin{center}\includegraphics[width=0.82\linewidth]{report/' + block['path'] + '}',
                        r'\par\small ' + tex_text(block['caption']) + r'\end{center}']
    markdown += ['## References', '']
    for i, ref in enumerate(content['references'], 1):
        markdown += [f"{i}. {ref['author'].replace('{', '').replace('}', '')}. {ref['title']}. {ref['year']}. [Source]({ref['url']})"]
    markdown += ['', '## Evidence and review records', '',
                 '[Final aggregate](../research/reports/final_holdout.json) | [Freeze](../research/reports/final_freeze.json) | [Integration](../docs/integration/README.md) | [Contributions](../team/CONTRIBUTIONS.md) | [AI record](ai_use_appendix.md)', '']
    (folder / 'group_report.md').write_text('\n'.join(markdown), encoding='utf-8')
    (folder / 'group_sections.tex').write_text('\n'.join(tex).rstrip() + '\n', encoding='utf-8')
    (folder / 'group_report.tex').write_text(r'''\documentclass[10pt,a4paper]{article}
\usepackage[margin=1.7cm]{geometry}
\usepackage[T1]{fontenc}
\usepackage{graphicx,hyperref,array}
\begin{document}
\begin{center}\Large Blue Mountains Bushfire Prediction\\
\normalsize Group 3 - Integration Draft\\
Author details and member approval pending\end{center}
\input{report/group_sections.tex}
\bibliographystyle{plain}
\bibliography{report/ml_references}
\end{document}
''', encoding='utf-8')


def main():
    content = group_content()
    export(content)
    print(json.dumps({'group_draft_pages_designed': len(content['pages']), 'model_fitting': False,
                      'source': 'Existing public aggregate evidence only'}))


if __name__ == '__main__':
    main()
