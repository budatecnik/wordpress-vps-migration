#!/usr/bin/env python3
"""Render reviewed examples into a private directory; never install them."""
import argparse
import os
from pathlib import Path
import re

from project_config import load_inventory

ROOT = Path(__file__).resolve().parents[1]


def render(text, values):
    needed = set(re.findall(r'@@([A-Z_]+)@@', text))
    missing = needed - values.keys()
    if missing:
        raise ValueError('Missing template values: ' + ', '.join(sorted(missing)))
    return re.sub(r'@@([A-Z_]+)@@', lambda match: values[match[1]], text)


def site_values(site, public_bind_address='203.0.113.10'):
    return {'DOMAIN': site['domain'], 'SITE_USER': site['system_user'],
            'DOCUMENT_ROOT': site['document_root'], 'PHP_SOCKET': site['php_socket'],
            'PUBLIC_BIND_ADDRESS': public_bind_address}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', required=True)
    p.add_argument('--site', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    data = load_inventory(args.config)
    values = site_values(data['sites'][args.site], data['public_bind_address'])
    out = Path(args.output).absolute()
    if out.exists() and (out.is_symlink() or any(out.iterdir())):
        p.error('Output must be a new or empty directory; no existing files will be overwritten')
    if out == Path('/') or any(str(out) == prefix or str(out).startswith(prefix + '/') for prefix in ['/etc', '/srv', '/var/www']):
        p.error('Render into a private review directory, not a system or application directory')
    if any(parent.is_symlink() for parent in [out, *out.parents]):
        p.error('Output path must not traverse symlinks')
    os.umask(0o077)
    out.mkdir(parents=True, mode=0o700, exist_ok=True)
    out.chmod(0o700)
    for template in sorted((ROOT / 'templates').rglob('*.in')):
        relative = template.relative_to(ROOT / 'templates')
        target = out / str(relative)[:-3]
        target.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        target.write_text(render(template.read_text(), values))
        target.chmod(0o600)
    print('Templates rendered for review only; no service configuration changed.')


if __name__ == '__main__':
    main()
