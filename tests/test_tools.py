import contextlib
import copy
import io
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import check_site
import check_smtp
import export_wordpress_db as export_db
import file_manifest
import migrate_files
import project_config
import publication
import render_templates


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'config/inventory.example.json').read_text())

    def load(self, data):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'inventory.json'
            p.write_text(json.dumps(data))
            return project_config.load_inventory(p)

    def test_example_has_two_distinct_sites_and_private_download_collection(self):
        data = self.load(self.data)
        self.assertEqual(set(data['sites']), {'embrylab', 'capadoccia'})
        self.assertIn('downloads', data['sites']['embrylab']['sources'])

    def test_rejects_live_webroot_as_copy_workspace(self):
        self.data['migration_root'] = '/srv/www/embrylab/public/copy'
        with self.assertRaises(ValueError):
            self.load(self.data)

    def test_rejects_config_directive_injection(self):
        self.data['sites']['embrylab']['domain'] = 'example.invalid; include /etc/private;'
        with self.assertRaises(ValueError):
            self.load(self.data)

    def test_rejects_path_traversal(self):
        self.data['sites']['embrylab']['sources']['wordpress'] = '/home/user/../private'
        with self.assertRaises(ValueError):
            self.load(self.data)

    def test_rejects_shared_php_socket(self):
        self.data['sites']['capadoccia']['php_socket'] = self.data['sites']['embrylab']['php_socket']
        with self.assertRaises(ValueError):
            self.load(self.data)

    def test_rejects_boolean_ssh_port(self):
        self.data['source']['port'] = True
        with self.assertRaises(ValueError):
            self.load(self.data)

    def test_example_cannot_access_real_hosting(self):
        with self.assertRaises(ValueError):
            project_config.require_real_source(self.data, self.data['sites']['embrylab'])


class CopyTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'config/inventory.example.json').read_text())

    def test_copy_never_has_delete_flag(self):
        for _, _, cmd in migrate_files.commands(self.data, 'embrylab', 'copy'):
            self.assertNotIn('--delete', cmd)
            self.assertIn('--safe-links', cmd)
            self.assertIn('StrictHostKeyChecking=yes', cmd[cmd.index('-e') + 1])

    def test_checksum_verification_cannot_delete_files(self):
        for _, _, cmd in migrate_files.commands(self.data, 'embrylab', 'verify'):
            self.assertIn('--delete', cmd)
            self.assertIn('--dry-run', cmd)
            self.assertIn('-rcl', cmd)

    def test_default_plan_never_runs_processes_or_creates_workspace(self):
        with tempfile.TemporaryDirectory() as d:
            self.data['migration_root'] = str(Path(d) / 'untouched')
            config = Path(d) / 'inventory.json'
            config.write_text(json.dumps(self.data))
            with mock.patch('migrate_files.subprocess.run', side_effect=AssertionError('No process should run')):
                with contextlib.redirect_stdout(io.StringIO()):
                    result = migrate_files.main(['--config', str(config), '--site', 'embrylab'])
            self.assertEqual(result, 0)
            self.assertFalse(Path(self.data['migration_root']).exists())

    def test_copy_requires_explicit_apply(self):
        with tempfile.TemporaryDirectory() as d:
            config = Path(d) / 'inventory.json'
            config.write_text(json.dumps(self.data))
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                migrate_files.main(['--config', str(config), '--site', 'embrylab', '--mode', 'copy'])
            self.assertEqual(error.exception.code, 2)

    def test_workspace_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'real'
            target.mkdir()
            link = Path(d) / 'link'
            link.symlink_to(target, target_is_directory=True)
            with self.assertRaises(ValueError):
                migrate_files.private_directory(link / 'child')
            self.assertFalse((target / 'child').exists())

    def test_existing_public_permissions_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / 'public'
            root.mkdir(mode=0o755)
            root.chmod(0o755)
            with self.assertRaises(ValueError):
                migrate_files.private_directory(root)


class DatabaseTests(unittest.TestCase):
    def test_single_quoted_php_escapes(self):
        self.assertEqual(export_db.literal("'a\\'b\\\\c'"), "a'b\\c")

    def test_dynamic_double_quoted_php_is_rejected(self):
        with self.assertRaises(ValueError):
            export_db.literal('"$VARIABLE"')

    def test_literal_configuration_is_parsed_without_executing_php(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'sample.php'
            p.write_text("<?php\ndefine('DB_NAME', 'sample');\ndefine('DB_USER', 'sample');\n"
                         "define('DB_PASSWORD', 'EXAMPLE_ONLY');\ndefine('DB_HOST', 'localhost:3307');\n")
            data = export_db.settings(p)
            self.assertEqual(data['DB_NAME'], 'sample')
            self.assertIn('port=3307', export_db.client_text(data))

    def test_duplicate_db_definition_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'sample.php'
            p.write_text("define('DB_NAME','one');\ndefine('DB_NAME','two');\n")
            with self.assertRaises(ValueError):
                export_db.settings(p)

    def test_newline_cannot_inject_a_client_option(self):
        with self.assertRaises(ValueError):
            export_db.option('EXAMPLE_ONLY\nuser=other')

    def test_mariadb_client_does_not_receive_mysql_specific_flags(self):
        cmd = export_db.command('dump', 'mariadb', '/tmp/example.cnf', 'sample')
        self.assertEqual(cmd[0], 'mariadb-dump')
        self.assertNotIn('--column-statistics=0', cmd)
        self.assertNotIn('--set-gtid-purged=OFF', cmd)

    def test_database_name_cannot_be_an_option(self):
        with self.assertRaises(ValueError):
            export_db.command('dump', 'mysql', '/tmp/example.cnf', '--help')

    def test_temporary_credential_file_is_private_and_removed(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'sample.php'
            p.write_text("define('DB_NAME','sample');\ndefine('DB_USER','sample');\n"
                         "define('DB_PASSWORD','EXAMPLE_ONLY');\ndefine('DB_HOST','localhost');\n")
            seen = []
            def client(cmd):
                defaults = Path(cmd[1].split('=', 1)[1])
                seen.append(defaults)
                self.assertEqual(defaults.stat().st_mode & 0o777, 0o600)
                self.assertIn('EXAMPLE_ONLY', defaults.read_text())
                self.assertNotIn('EXAMPLE_ONLY', ' '.join(cmd))
                return types.SimpleNamespace(returncode=0)
            with mock.patch('export_wordpress_db.subprocess.run', side_effect=client):
                self.assertEqual(export_db.main(['inspect', str(p)]), 0)
            self.assertEqual(len(seen), 1)
            self.assertFalse(seen[0].exists())


class ManifestTests(unittest.TestCase):
    def test_same_size_content_change_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'design.bin'
            p.write_bytes(b'first')
            before = file_manifest.inventory(d)
            p.write_bytes(b'other')
            after = file_manifest.inventory(d)
            self.assertEqual(file_manifest.differences(before, after)['changed'], 1)

    def test_missing_and_extra_files_are_detected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'one'
            p.write_text('one')
            before = file_manifest.inventory(d)
            p.unlink()
            (Path(d) / 'two').write_text('two')
            self.assertEqual(file_manifest.differences(before, file_manifest.inventory(d)),
                             {'missing': 1, 'extra': 1, 'changed': 0})

    def test_symlink_cannot_include_an_external_file(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / 'tree'
            root.mkdir()
            external = Path(d) / 'outside'
            external.write_text('synthetic')
            (root / 'link').symlink_to(external)
            with self.assertRaises(ValueError):
                file_manifest.inventory(root)


class TemplateAndNetworkTests(unittest.TestCase):
    def test_render_keeps_nginx_variables_and_resolves_project_placeholders(self):
        data = project_config.load_inventory(ROOT / 'config/inventory.example.json')
        site = data['sites']['embrylab']
        text = (ROOT / 'templates/nginx/public-http.conf.in').read_text()
        rendered = render_templates.render(text, render_templates.site_values(site))
        self.assertIn('$request_uri', rendered)
        self.assertNotIn('@@', rendered)
        self.assertIn(site['domain'], rendered)

    def test_missing_template_value_is_an_error(self):
        with self.assertRaises(ValueError):
            render_templates.render('@@DOMAIN@@', {})

    def test_external_and_downgrade_redirects_are_rejected(self):
        for url in ['http://example.invalid/', 'https://elsewhere.invalid/',
                    'https://example.invalid:444/', 'https://user@example.invalid/']:
            self.assertFalse(check_site.allowed_redirect('example.invalid', url))
        self.assertTrue(check_site.allowed_redirect('example.invalid', 'https://www.example.invalid/'))

    def test_ipv4_smtp_probe_does_not_fall_back_to_ipv6(self):
        address = ('192.0.2.20', 25)
        with mock.patch('check_smtp.socket.getaddrinfo', return_value=[(socket.AF_INET, socket.SOCK_STREAM, 0, '', address)]) as lookup:
            with mock.patch('check_smtp.socket.socket') as factory:
                factory.return_value.__enter__.return_value.recv.return_value = b'220 synthetic SMTP\r\n'
                self.assertTrue(check_smtp.probe('mail.example.invalid', family=4)['ok'])
                lookup.assert_called_once_with('mail.example.invalid', 25, socket.AF_INET, socket.SOCK_STREAM)
                factory.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)


class PublicationTests(unittest.TestCase):
    def test_operational_folder_and_dumps_cannot_be_published(self):
        for path in ['ops/script.py', '.git/config', 'config/config.local.json',
                     'docs/database.sql', 'private/credentials.json', 'scripts/key.pem']:
            self.assertFalse(publication.allowed_path(path))

    def test_private_key_marker_is_detected(self):
        synthetic = '-----BEGIN ' + 'PRIVATE KEY-----'
        self.assertTrue(any(reason == 'private-key' for _, reason in publication.inspect_text(synthetic)))

    def test_real_public_ip_is_rejected_but_documentation_range_is_allowed(self):
        public = '.'.join(['8'] * 4)
        self.assertTrue(publication.inspect_text(public))
        self.assertFalse(publication.inspect_text('203.0.113.10 and 127.0.0.1'))

    def test_package_file_list_never_includes_original_ops(self):
        self.assertTrue(publication.public_files(ROOT))
        self.assertTrue(all('ops' != p.relative_to(ROOT).parts[0] for p in publication.public_files(ROOT)))


if __name__ == '__main__':
    unittest.main()
