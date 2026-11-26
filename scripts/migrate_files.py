#!/usr/bin/env python3
"""Plan/copy hosting files into a private workspace; verification never deletes."""
import argparse
import os
from pathlib import Path
import shlex
import subprocess
import sys

from project_config import load_inventory, require_real_source


def commands(data, site_name, mode):
    source, site = data['source'], data['sites'][site_name]
    ssh = ['ssh', '-i', str(Path(source['identity_file']).expanduser()), '-p', str(source['port']),
           '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
           '-o', 'ConnectTimeout=15', '-o', 'ServerAliveInterval=30']
    for collection, source_path in site['sources'].items():
        target = Path(data['migration_root']) / site_name / collection
        if mode == 'verify':
            flags = ['-rcl', '--dry-run', '--delete', '--itemize-changes', '--out-format=%i %n%L']
        else:
            flags = ['-a', '--no-owner', '--no-group', '--safe-links', '--partial',
                     '--partial-dir=.rsync-partial', '--stats']
        remote = f"{source['user']}@{source['host']}:{shlex.quote(source_path + '/')}"
        yield collection, target, ['rsync', *flags, '-e', shlex.join(ssh), '--', remote, str(target) + '/']


def private_directory(path):
    for parent in [path, *path.parents]:
        if parent.is_symlink():
            raise ValueError('Symlinks are not allowed in the workspace path')
    path.mkdir(parents=True, mode=0o700, exist_ok=True)
    if path.stat().st_mode & 0o077:
        raise ValueError('Migration directory must have private permissions (0700)')


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', required=True)
    p.add_argument('--site', required=True)
    p.add_argument('--mode', choices=['plan', 'copy', 'verify'], default='plan')
    p.add_argument('--apply', action='store_true')
    args = p.parse_args(argv)
    data = load_inventory(args.config)
    if args.site not in data['sites']:
        p.error('Unknown site')
    if args.mode == 'copy' and not args.apply:
        p.error('Copy mode requires --apply')
    if args.apply and args.mode != 'copy':
        p.error('--apply is valid only for copy mode')
    jobs = list(commands(data, args.site, 'verify' if args.mode == 'verify' else 'copy'))
    if args.mode == 'plan':
        print('PLAN ONLY: no SSH connection and no filesystem changes.')
        for collection, _, command in jobs:
            print(collection + ': ' + shlex.join(command))
        return 0
    require_real_source(data, data['sites'][args.site])
    if args.mode == 'copy':
        os.umask(0o077)
        private_directory(Path(data['migration_root']))
        private_directory(Path(data['migration_root']) / args.site)
    differences = 0
    for collection, target, command in jobs:
        if args.mode == 'copy':
            private_directory(target)
            subprocess.run(command, check=True)
            print(collection + ': copy completed; verify content before restoring.')
        else:
            if not target.is_dir() or target.is_symlink():
                raise ValueError('Verification target is missing or is a symlink')
            # The only command using --delete also contains --dry-run.
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            count = len([line for line in result.stdout.splitlines() if line])
            differences += count
            print(f'{collection}: {count} differences; no files modified.')
    return 2 if differences else 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError):
        print('Migration operation failed. Check configuration, permissions and SSH access privately.', file=sys.stderr)
        raise SystemExit(1)
