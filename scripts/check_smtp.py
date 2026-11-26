#!/usr/bin/env python3
"""Check a chosen SMTP address family; connect/read greeting, never send mail."""
import argparse
import json
import socket

from project_config import hostname


def probe(host, family=4, timeout=8):
    hostname(host)
    address_family = socket.AF_INET if family == 4 else socket.AF_INET6
    addresses = socket.getaddrinfo(host, 25, address_family, socket.SOCK_STREAM)
    last_error = 'NoAddress'
    for _, _, _, _, address in addresses[:2]:
        try:
            with socket.socket(address_family, socket.SOCK_STREAM) as connection:
                connection.settimeout(timeout)
                connection.connect(address)
                banner = connection.recv(512)
                if not banner.startswith(b'220'):
                    return {'host': host, 'family': family, 'ok': False, 'error_type': 'UnexpectedGreeting'}
                return {'host': host, 'family': family, 'ok': True, 'smtp_greeting': '220'}
        except OSError as error:
            last_error = type(error).__name__
    return {'host': host, 'family': family, 'ok': False, 'error_type': last_error}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host', required=True)
    p.add_argument('--family', type=int, choices=[4, 6], default=4)
    args = p.parse_args()
    try:
        result = probe(args.host, args.family)
    except Exception as error:
        result = {'host': args.host, 'family': args.family, 'ok': False, 'error_type': type(error).__name__}
    print(json.dumps(result))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
