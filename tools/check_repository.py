"""Check upload language, private artifacts and common embedded credentials."""

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = {'.py', '.md', '.txt', '.json', '.csv', '.ipynb', '.yml', '.yaml', '.bib', '.tex', '.geojson'}


def check(root=ROOT):
    names = subprocess.check_output(['git', '-C', str(root), 'ls-files', '--cached', '--others', '--exclude-standard', '-z']).decode().split('\0')
    failures, checked = [], 0
    secret = re.compile(r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-proj-[A-Za-z0-9_-]{30,}')
    for name in sorted(set(filter(None, names))):
        path = root / name
        if not path.is_file():
            continue
        if not name.isascii() or re.search(r'(^|/)(\.local_data|\.venv|__pycache__)(/|$)', name) or path.suffix in {'.ubj', '.joblib', '.pkl'}:
            failures.append(f'Invalid public artifact path: {name}')
        if path.suffix not in TEXT and path.name not in {'.gitignore', '.gitattributes'}:
            continue
        checked += 1
        text = path.read_text(encoding='utf-8-sig')
        if re.search('[\u3400-\u9fff]', text):
            failures.append(f'Non-English authored text: {name}')
        if secret.search(text) or re.search(r'C:[/\\]Users[/\\]Admin', text):
            failures.append(f'Credential/private-path pattern: {name}')
    if failures:
        raise ValueError('\n'.join(failures))
    return {'public_text_files_checked': checked, 'english_and_private_boundary_checks': True}


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
