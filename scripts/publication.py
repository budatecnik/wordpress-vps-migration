"""Explicit public-file boundary and targeted leak checks for this portfolio."""
import ipaddress
from pathlib import Path
import re
import subprocess

ROOT_FILES = {'README.md', 'AGENTS.md', 'CONTRIBUTING.md', 'SECURITY.md', 'Makefile',
              '.gitignore', '.gitattributes', '.editorconfig'}
ROOT_DIRS = {'.github', 'config', 'docs', 'scripts', 'templates', 'tests'}
TEXT_SUFFIXES = {'.py', '.sh', '.php', '.md', '.json', '.yml', '.yaml', '.in'}
NETWORKS = [ipaddress.ip_network(value) for value in [
    '127.0.0.0/8', '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16',
    '192.0.2.0/24', '198.51.100.0/24', '203.0.113.0/24',
]]
PATTERNS = [
    ('private-key', re.compile(r'-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----')),
    ('github-token', re.compile(r'\bgh[pousr]_[A-Za-z0-9]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{40,}\b')),
    ('cloud-access-key', re.compile(r'\b(?:AKIA|ASIA)[0-9A-Z]{16}\b')),
    ('personal-email', re.compile(r'[A-Za-z0-9._%+-]+@(?:gmail|outlook|hotmail|yahoo)\.[A-Za-z]{2,}', re.I)),
    ('disabled-ssh-host-check', re.compile(r'StrictHostKeyChecking\s*=\s*(?:no|off)\b')),
    ('credential-in-url', re.compile(r'https?://[^\s/:]+:[^\s/@]+@')),
]


def allowed_path(relative):
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts or not p.parts:
        return False
    if len(p.parts) == 1:
        return p.name in ROOT_FILES
    if p.parts[0] not in ROOT_DIRS or '__pycache__' in p.parts:
        return False
    if p.name == 'config.local.json' or p.name.startswith('.env'):
        return False
    return p.suffix in TEXT_SUFFIXES


def public_files(root):
    root = Path(root)
    files = [root / name for name in ROOT_FILES if (root / name).exists()]
    for name in ROOT_DIRS:
        directory = root / name
        if directory.exists():
            files += [p for p in directory.rglob('*')
                      if (p.is_file() or p.is_symlink()) and '__pycache__' not in p.parts
                      and p.suffix not in {'.pyc', '.pyo'}
                      and p.name != 'config.local.json']
    return sorted(files)


def inspect_text(text):
    findings = []
    for number, line in enumerate(text.splitlines(), 1):
        for reason, pattern in PATTERNS:
            if pattern.search(line):
                findings.append((number, reason))
        for value in re.findall(r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])', line):
            try:
                address = ipaddress.ip_address(value)
            except ValueError:
                continue
            if value != '0.0.0.0' and not any(address in net for net in NETWORKS):
                findings.append((number, 'non-example-public-ip'))
    return findings


def audit(root):
    root = Path(root)
    findings = []
    for p in public_files(root):
        relative = p.relative_to(root).as_posix()
        if p.is_symlink() or not allowed_path(relative):
            findings.append((relative, 0, 'not-publication-eligible'))
            continue
        if p.stat().st_size > 1024 * 1024:
            findings.append((relative, 0, 'unexpected-large-file'))
            continue
        try:
            text = p.read_text(encoding='utf-8')
        except UnicodeError:
            findings.append((relative, 0, 'non-text-file'))
            continue
        findings.extend((relative, line, reason) for line, reason in inspect_text(text))
    git = subprocess.run(['git', 'ls-files', '-z'], cwd=root, capture_output=True)
    if git.returncode == 0:
        for name in git.stdout.decode().split('\0'):
            if name and not allowed_path(name):
                findings.append((name, 0, 'tracked-file-outside-public-boundary'))
    return findings
