#!/usr/bin/env python3
"""Create/verify private SHA-256 manifests. No file contents are displayed."""
import argparse
import hashlib
import json
import os
from pathlib import Path


def inventory(root):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Expected a real directory, not a symlink')
    result = {}
    for p in sorted(root.rglob('*')):
        if p.is_symlink():
            raise ValueError('Resolve and inventory symlinks separately')
        if p.is_dir():
            continue
        if not p.is_file():
            raise ValueError('Only regular files and directories are supported')
        digest = hashlib.sha256()
        with p.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
        result[p.relative_to(root).as_posix()] = {'size': p.stat().st_size, 'sha256': digest.hexdigest()}
    return result


def differences(expected, actual):
    return {'missing': len(expected.keys() - actual.keys()),
            'extra': len(actual.keys() - expected.keys()),
            'changed': sum(expected[k] != actual[k] for k in expected.keys() & actual.keys())}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['create', 'verify'])
    p.add_argument('directory')
    p.add_argument('--output')
    p.add_argument('--manifest')
    args = p.parse_args()
    root = Path(args.directory).resolve()
    if args.mode == 'create':
        if not args.output:
            p.error('create requires --output')
        out = Path(args.output).absolute()
        if out.resolve().is_relative_to(root):
            p.error('Manifest must be outside the inventoried tree')
        data = inventory(args.directory)
        fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as handle:
            json.dump({'version': 1, 'files': data}, handle, indent=2, ensure_ascii=False)
            handle.write('\n')
        print(f'Private manifest created: {len(data)} files.')
    else:
        if not args.manifest:
            p.error('verify requires --manifest')
        manifest = json.loads(Path(args.manifest).read_text())
        if manifest.get('version') != 1:
            raise ValueError('Unsupported manifest version')
        result = differences(manifest['files'], inventory(args.directory))
        print(json.dumps(result, sort_keys=True))
        return 2 if any(result.values()) else 0
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
