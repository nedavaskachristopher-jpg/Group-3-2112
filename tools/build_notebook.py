"""Build and execute a standard-library-only cached-result review notebook."""

import contextlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def notebook(root=ROOT, execute=True):
    sections = [
        ('markdown', '# Revised ML review\n\nThis notebook reads public cached evidence only. It does not train, predict or reopen final labels. Scores are not calibrated probabilities. The original training notebook is preserved at tag `legacy-ml-2026-10-25`.'),
        ('code', "from pathlib import Path\nimport sys, json\nROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'review.py').is_file())\nsys.path.insert(0, str(ROOT))\nfrom review import cached_results\nfrom tools.verify_handover import verify\nprint('Public evidence located')"),
        ('code', "checks = verify(ROOT)\nprint('Frozen files unchanged:', checks['frozen_source_and_references_unchanged'])\nprint('Exact numerical claims:', checks['exact_claims_checked'])"),
        ('code', "result = cached_results(ROOT)\npopulation = result['population']\nprint('Cell-days:', population['rows'], '| positive targets:', population['positives'])\nfor name, row in result['policies'].items():\n    print(name, '| recall:', round(row['recall']*100, 2), '| precision:', round(row['precision']*100, 2), '| false alerts:', row['false_positives'], '| misses:', row['false_negatives'])"),
        ('code', "contract = json.loads((ROOT / 'docs/technical/model_contract.json').read_text())\nprint('Ordered inputs:', len(contract['ordered_inputs']))\nprint('Validated probability:', contract['output_score']['validated_probability'])\nfor key, value in result['model_ap'].items():\n    print(key, 'AP:', round(value, 6))"),
        ('markdown', '## Frozen score map\n\n![Cached first-date score map](../report/figures/frozen_score_map.png)\n\nThe date is fixed as the first frozen feature day; colours come from saved scores, not a new prediction pass. This is an illustration, not evidence of reliable warnings. See the map provenance JSON and final report.'),
        ('markdown', '## Interpretation\n\nThe 80%/90% names are development recall targets. Neither transferred to the final population. The logistic comparison ranked better than XGBoost. Both studies use the same 2019-20 source panel, so this is not independent-season replication. Further tuning needs new independent evaluation data. Member understanding, source checks and final report approval remain human review tasks.'),
    ]
    cells, namespace, count = [], {'__name__': 'cached_review'}, 0
    for kind, source in sections:
        cell = {'cell_type': kind, 'id': f'review-{len(cells)+1}', 'metadata': {}, 'source': source.splitlines(keepends=True)}
        if kind == 'code':
            count += 1
            output = io.StringIO()
            if execute:
                with contextlib.redirect_stdout(output):
                    exec(compile(source, f'review_cell_{count}', 'exec'), namespace)
            cell.update(execution_count=count if execute else None,
                        outputs=[{'output_type': 'stream', 'name': 'stdout', 'text': output.getvalue().splitlines(keepends=True)}] if execute else [])
        cells.append(cell)
    return {'cells': cells, 'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
            'language_info': {'name': 'python', 'version': '3.12'}}, 'nbformat': 4, 'nbformat_minor': 5}


def main():
    from tools.build_handover import refresh_manifest
    path = ROOT / 'notebooks/ML_Review.ipynb'
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(notebook(execute=False), indent=2) + '\n', encoding='utf-8')
    refresh_manifest()
    path.write_text(json.dumps(notebook(), indent=2) + '\n', encoding='utf-8')
    refresh_manifest()
    print('Built executed cached-result review notebook; no fitting or prediction')


if __name__ == '__main__':
    main()
