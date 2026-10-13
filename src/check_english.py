"""Enforce ASCII artifact paths and reject Chinese characters in project text.

This check supports the team's English-only upload requirement. It does not
replace human review of grammar or determine the language of binary figures.
"""
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {'.py', '.md', '.txt', '.json', '.csv', '.ipynb', '.yml',
                 '.yaml', '.bib', '.tex', '.geojson'}
TEXT_NAMES = {'.gitignore', '.gitattributes'}
CJK = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0003134f]')


def main():
    paths = subprocess.run(
        ['git', '-C', str(ROOT), 'ls-files', '--cached', '--others',
         '--exclude-standard', '-z'],
        capture_output=True, check=True,
    ).stdout.decode('utf-8').split('\0')
    violations = []
    checked = 0
    for relative in sorted(set(path for path in paths if path)):
        file = ROOT / relative
        if not relative.isascii():
            violations.append(f'Non-ASCII file path: {relative}')
        if not file.is_file() or (file.suffix not in TEXT_SUFFIXES and file.name not in TEXT_NAMES):
            continue
        checked += 1
        text = file.read_text(encoding='utf-8-sig')
        if CJK.search(text):
            violations.append(f'Chinese characters found in: {relative}')
    if violations:
        raise SystemExit('\n'.join(violations))
    print(f'English upload check passed: {checked} text files scanned; all artifact paths are ASCII.')


if __name__ == '__main__':
    main()
