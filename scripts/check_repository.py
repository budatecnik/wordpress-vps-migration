#!/usr/bin/env python3
"""Offline syntax and publication-boundary validation. No server changes."""
import ast
import json
from pathlib import Path
import shutil
import subprocess
import sys

from project_config import load_inventory
from publication import audit, public_files
from render_templates import render, site_values

ROOT = Path(__file__).resolve().parents[1]


def main():
    findings = audit(ROOT)
    for relative, line, reason in findings:
        print(f'{relative}:{line}: {reason}')
    if findings:
        return 1
    config = load_inventory(ROOT / 'config/inventory.example.json')
    for p in public_files(ROOT):
        if p.suffix == '.py':
            ast.parse(p.read_text(), filename=str(p))
        if p.suffix == '.json':
            json.loads(p.read_text())
        if p.suffix == '.sh' or p.name.endswith('.sh.in'):
            subprocess.run(['bash', '-n', str(p)], check=True)
        if p.suffix == '.php' or p.name.endswith('.php.in'):
            if shutil.which('php'):
                subprocess.run(['php', '-l', str(p)], check=True, stdout=subprocess.DEVNULL)
    for site in config['sites'].values():
        values = site_values(site, config['public_bind_address'])
        for template in (ROOT / 'templates').rglob('*.in'):
            text = render(template.read_text(), values)
            if '@@' in text:
                raise ValueError('Unresolved template placeholder')
    print(f'Validated {len(public_files(ROOT))} public files: Python, JSON, shell, templates and leak checks.')
    if not shutil.which('php'):
        print('PHP lint skipped locally: PHP CLI is not installed. This is not a PHP runtime test.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print('Repository check failed: ' + type(error).__name__, file=sys.stderr)
        raise SystemExit(1)
