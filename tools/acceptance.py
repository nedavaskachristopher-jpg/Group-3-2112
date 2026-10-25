"""Run clean-checkout acceptance without private artifacts or real-data modelling."""

import argparse
import ast
import hashlib
import importlib.metadata
import json
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def tracked_hashes(root=ROOT):
    names = subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z']).decode().split('\0')
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names if name}


def command(arguments, root=ROOT, json_output=False):
    result = subprocess.run([sys.executable, *arguments], cwd=root, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"Acceptance command failed: python {' '.join(arguments)}\n{result.stderr[-3000:]}")
    return json.loads(result.stdout) if json_output else result.stdout + result.stderr


def accept(root=ROOT, pdf=False):
    before = tracked_hashes(root)
    status = subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain']).decode()
    results = command(['-S', 'review.py', 'results', '--json'], root, True)
    verified = command(['-S', 'review.py', 'verify'], root, True)
    public = command(['-S', '-m', 'tools.check_repository'], root, True)
    integration = command(['-S', '-m', 'tools.check_integration'], root, True)
    tests = command(['review.py', 'test'], root)
    counts = [int(value) for value in re.findall(r'Ran (\d+) tests?', tests)]
    if counts != [48, 20] or 'FAILED' in tests:
        raise ValueError(f'Unexpected suite completion: {counts}')
    command(['-S', 'src/verify_results.py'], root)
    checked_syntax = 0
    for name in before:
        if name.endswith('.py'):
            ast.parse((root / name).read_text(encoding='utf-8-sig'), filename=name)
            checked_syntax += 1
    group = json.loads((root / 'report/group_report_content.json').read_text())
    ml = json.loads((root / 'report/report_content.json').read_text())
    if group['pages'][2:6] != ml['pages']:
        raise ValueError('Group report scientific blocks differ from the ML contribution')
    pages = None
    if pdf:
        from pypdf import PdfReader
        pages = {name: len(PdfReader(root / name).pages) for name in ['report/group_report.pdf', 'report/ml_contribution.pdf']}
        if list(pages.values()) != [8, 4]:
            raise ValueError(f'Unexpected PDF pagination: {pages}')
    frozen = json.loads((root / 'research/reports/final_freeze.json').read_text())
    versions = {'python': platform.python_version(), **{name: importlib.metadata.version(name) for name in frozen['software_versions'] if name != 'python'}}
    if versions != frozen['software_versions']:
        raise ValueError('Acceptance runtime differs from the recorded research environment')
    if before != tracked_hashes(root) or status != subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain']).decode():
        raise ValueError('Acceptance commands rewrote public artifacts')
    return {'accepted': True, 'checked_at_utc': datetime.now(timezone.utc).isoformat(),
            'checked_commit': subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD']).decode().strip(),
            'tracked_files_unchanged': len(before), 'synthetic_tests_passed': sum(counts),
            'python_sources_parsed': checked_syntax, 'runtime_matches_freeze': versions,
            'public_verification': verified, 'public_content': public, 'integration': integration,
            'pdf_pages_checked': pages, 'cached_result_only': results['cached_result_only'],
            'evaluation_runs': results['evaluation_runs'], 'private_artifacts_required': False,
            'real_data_fitting': False, 'new_final_prediction': False, 'human_review_completed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', action='store_true', help='Also inspect PDFs; requires optional report dependencies')
    args = parser.parse_args()
    print(json.dumps(accept(pdf=args.pdf), indent=2))


if __name__ == '__main__':
    main()
