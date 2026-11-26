#!/usr/bin/env python3
"""Inspect/export a database without executing PHP or printing credentials."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def literal(raw):
    value = raw[1:-1]
    if raw[0] == "'":
        return re.sub(r"\\([\\'])", r"\1", value)
    if '\\' in value or '$' in value:
        raise ValueError('Non-literal double-quoted PHP value')
    return value


def settings(path):
    content = Path(path).read_text()
    result = {}
    for key in ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST']:
        pattern = (r"^\s*define\s*\(\s*['\"]" + key
                   + r"['\"]\s*,\s*('(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\")\s*\)\s*;")
        matches = re.findall(pattern, content, re.MULTILINE)
        if len(matches) != 1:
            raise ValueError('Expected exactly one literal definition')
        result[key] = literal(matches[0])
    return result


def option(value):
    if any(c in value for c in ['\x00', '\r', '\n']):
        raise ValueError('Unsupported control character')
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'


def client_text(values):
    host = values['DB_HOST']
    extra = ''
    if ':' in host:
        host, suffix = host.split(':', 1)
        if suffix.isdigit() and 1 <= int(suffix) <= 65535:
            extra = 'port=' + suffix + '\n'
        elif suffix.startswith('/'):
            extra = 'socket=' + option(suffix) + '\n'
        else:
            raise ValueError('Unsupported DB_HOST syntax; IPv6 needs manual adaptation')
    return ('[client]\nuser=' + option(values['DB_USER']) + '\npassword='
            + option(values['DB_PASSWORD']) + '\nhost=' + option(host) + '\n' + extra)


def command(mode, flavor, defaults_path, database):
    if not database or database.startswith('-'):
        raise ValueError('Unsupported database name')
    defaults = '--defaults-extra-file=' + defaults_path
    if mode == 'inspect':
        query = ("SELECT COALESCE(ENGINE,'VIEW'),COUNT(*) FROM information_schema.TABLES "
                 "WHERE TABLE_SCHEMA=DATABASE() GROUP BY ENGINE; "
                 "SELECT 'ROUTINES',COUNT(*) FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA=DATABASE(); "
                 "SELECT 'EVENTS',COUNT(*) FROM information_schema.EVENTS WHERE EVENT_SCHEMA=DATABASE();")
        return ['mysql' if flavor == 'mysql' else 'mariadb', defaults,
                '--batch', '--skip-column-names', database, '-e', query]
    args = ['mysqldump' if flavor == 'mysql' else 'mariadb-dump', defaults,
            '--single-transaction', '--quick', '--skip-lock-tables', '--no-tablespaces',
            '--hex-blob', '--routines', '--events', '--triggers']
    if flavor == 'mysql':
        args += ['--set-gtid-purged=OFF', '--column-statistics=0']
    return args + [database]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['inspect', 'dump'])
    parser.add_argument('config')
    parser.add_argument('--flavor', choices=['mysql', 'mariadb'], default='mysql')
    args = parser.parse_args(argv)
    values = settings(args.config)
    fd, path = tempfile.mkstemp(prefix='wp-migration-client-', suffix='.cnf')
    try:
        with os.fdopen(fd, 'w') as handle:
            handle.write(client_text(values))
        return subprocess.run(command(args.mode, args.flavor, path, values['DB_NAME'])).returncode
    finally:
        os.unlink(path)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        # Exception text can contain configuration values; never include it.
        print('Database operation failed: ' + type(error).__name__, file=sys.stderr)
        raise SystemExit(1)
