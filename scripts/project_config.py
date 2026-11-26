"""Validate non-secret inventory used by planning and template tools."""
import json
import ipaddress
from pathlib import Path, PurePosixPath
import re

NAME = re.compile(r'[a-z][a-z0-9_-]{0,31}\Z')
HOST = re.compile(r'[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?\Z')
SAFE_PATH = re.compile(r'/[A-Za-z0-9_./-]+\Z')


def absolute_path(value):
    if not isinstance(value, str) or not SAFE_PATH.fullmatch(value):
        raise ValueError('Expected an absolute path without shell or config metacharacters')
    p = PurePosixPath(value)
    if '..' in p.parts or str(p) != value or value == '/':
        raise ValueError('Path must be normalized and must not be the filesystem root')
    return value


def hostname(value):
    if not isinstance(value, str) or not HOST.fullmatch(value) or '..' in value:
        raise ValueError('Invalid ASCII hostname')
    if any(not label or label.startswith('-') or label.endswith('-') or len(label) > 63
           for label in value.split('.')):
        raise ValueError('Invalid hostname label')
    return value


def load_inventory(path):
    data = json.loads(Path(path).read_text())
    if ipaddress.ip_address(data['public_bind_address']).version != 4:
        raise ValueError('These frontend examples require an explicit IPv4 bind address')
    root = absolute_path(data['migration_root'])
    forbidden = ['/etc', '/proc', '/sys', '/dev', '/var/www', '/srv/www', '/srv/embrylab-editor-staging']
    if root in ['/home', '/srv', '/var', '/tmp'] or any(root == p or root.startswith(p + '/') for p in forbidden):
        raise ValueError('Migration workspace must be separate from system files and live webroots')
    source = data['source']
    hostname(source['host'])
    if not NAME.fullmatch(source['user']):
        raise ValueError('Invalid SSH user')
    if type(source['port']) is not int or not 1 <= source['port'] <= 65535:
        raise ValueError('Invalid SSH port')
    key = source['identity_file']
    if not isinstance(key, str) or not key or '\n' in key or '\r' in key or '\x00' in key:
        raise ValueError('Invalid identity-file path')
    if not data['sites']:
        raise ValueError('At least one site is required')
    domains, users, roots, sockets = set(), set(), set(), set()
    for name, site in data['sites'].items():
        if not NAME.fullmatch(name) or not NAME.fullmatch(site['system_user']):
            raise ValueError('Invalid site or system-user name')
        hostname(site['domain'])
        absolute_path(site['document_root'])
        absolute_path(site['php_socket'])
        if not site['document_root'].startswith('/srv/www/') or not site['document_root'].endswith('/public'):
            raise ValueError('Example document roots must use /srv/www/SITE/public')
        if not site['php_socket'].startswith('/run/php/') or not site['php_socket'].endswith('.sock'):
            raise ValueError('Expected a per-site PHP socket')
        for value, seen in [(site['domain'], domains), (site['system_user'], users),
                            (site['document_root'], roots), (site['php_socket'], sockets)]:
            if value in seen:
                raise ValueError('Sites must have distinct domains, users, roots and sockets')
            seen.add(value)
        if not site['sources']:
            raise ValueError('Each site needs at least one source collection')
        for collection, source_path in site['sources'].items():
            if not NAME.fullmatch(collection):
                raise ValueError('Invalid collection name')
            absolute_path(source_path)
    return data


def require_real_source(data, site):
    if data['source']['host'].endswith('.invalid') or any('SOURCE_USER' in p for p in site['sources'].values()):
        raise ValueError('Replace example source parameters before accessing the hosting')
    key = Path(data['source']['identity_file']).expanduser()
    if not key.is_file():
        raise ValueError('SSH identity file does not exist')
    if key.stat().st_mode & 0o077:
        raise ValueError('SSH identity file must not be accessible to group or other users')
