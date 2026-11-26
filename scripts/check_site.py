#!/usr/bin/env python3
"""Read-only HTTPS, redirect and protected-file checks; never ignore TLS errors."""
import argparse
import json
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request

from project_config import hostname


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def allowed_redirect(domain, url):
    p = urllib.parse.urlsplit(url)
    return (p.scheme == 'https' and p.hostname in {domain, 'www.' + domain}
            and p.port in {None, 443} and not p.username and not p.password)


def fetch(domain, scheme='https', path='/'):
    opener = urllib.request.build_opener(NoRedirect())
    url = f'{scheme}://{domain}{path}'
    for _ in range(6):
        request = urllib.request.Request(url, headers={'User-Agent': 'wordpress-vps-migration-check/1'})
        try:
            response = opener.open(request, timeout=20)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            if response.code in {301, 302, 303, 307, 308}:
                target = urllib.parse.urljoin(url, response.headers.get('Location', ''))
                if not allowed_redirect(domain, target):
                    raise ValueError('External or insecure redirect rejected')
                url = target
                continue
            return response.code, url, response.read(1024 * 1024)
    raise ValueError('Redirect loop')


def check(domain):
    hostname(domain)
    with socket.create_connection((domain, 443), timeout=15) as connection:
        with ssl.create_default_context().wrap_socket(connection, server_hostname=domain) as tls:
            cert = tls.getpeercert()
            result = {'domain': domain, 'tls_valid': True, 'expires': cert['notAfter']}
    for scheme in ['http', 'https']:
        code, url, body = fetch(domain, scheme)
        if code != 200 or not url.startswith('https://'):
            raise ValueError('Expected a successful HTTPS homepage')
        if any(marker.lower() in body.lower() for marker in [b'Error establishing a database connection', b'There has been a critical error']):
            raise ValueError('WordPress error response')
        result[scheme] = {'status': code, 'final_url': url}
    for path in ['/wp-config.php', '/.user.ini', '/wp-content/uploads/migration-probe.php']:
        if fetch(domain, path=path)[0] not in {403, 404}:
            raise ValueError('A protected path was not rejected')
    result['protected_paths_rejected'] = True
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('domain', nargs='+')
    args = p.parse_args()
    failed = False
    for domain in args.domain:
        try:
            print(json.dumps(check(domain)))
        except Exception as error:
            failed = True
            print(json.dumps({'domain': domain, 'ok': False, 'error_type': type(error).__name__}))
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
