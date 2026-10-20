import json
from pathlib import Path
import stat
import tempfile
import unittest
import zipfile

from algsolve.web_delivery import SEMANTICS, checked_zip, import_delivery, sha, verify_files


def fixture():
    expected = {'batch_id': 'W002-B03', 'problems': [
        {'id': n, 'key': f'lc:fixture-{n}', 'entry': {'class': 'Solution', 'method': 'solve'},
         'params': [['value', 'int']]} for n in range(1, 26)]}
    rows = [{'id': n, 'signature': 'solve(value)', 'source': f'{n:04d}.js',
             'semantics': f'{n:04d}-semantics.json'} for n in range(1, 26)]
    files = {'assignment.json': json.dumps({'batch': 'W002-B03', 'assigned': rows}).encode(),
             'validation-report.json': b'{}', 'validation-examples.json': b'[]'}
    for row in rows:
        files[row['source']] = b'function solve(value) { return value; }\n'
        files[row['semantics']] = json.dumps({key: 'fixture' for key in SEMANTICS}).encode()
    files['SHA256SUMS'] = ''.join(f'{sha(data)}  {name}\n' for name, data in files.items()).encode()
    return expected, files


class WebDeliveryTests(unittest.TestCase):
    def test_listing_schema_keeps_original_names_and_checksum_coverage(self):
        expected, files = fixture()
        listing = json.loads(files['assignment.json'])
        rows = listing.pop('assigned')
        for row in rows:
            row['signature'] = 'function ' + row['signature']
            row['source_file'] = row.pop('source')
            row['semantics_file'] = row.pop('semantics')
        files['assignment.json'] = json.dumps({'schema': 'gamma-js-assignment-listing/v1',
            'batch_id': listing['batch'], 'problems': rows}).encode()
        del files['validation-report.json'], files['validation-examples.json'], files['SHA256SUMS']
        files.update({'VALIDATION.md': b'Authored checks only', 'validation-results.json': b'{}'})
        files['SHA256SUMS'] = ''.join(f'{sha(data)}  {name}\n' for name, data in files.items()).encode()
        self.assertEqual(len(verify_files(files, expected)), 25)
        files['SHA256SUMS'] = files['SHA256SUMS'].split(b'\n', 1)[1]
        with self.assertRaisesRegex(ValueError, 'coverage'):
            verify_files(files, expected)

    def test_hash_ids_and_unqualified_interface_diagnostic(self):
        expected, files = fixture()
        rows = verify_files(files, expected)
        self.assertEqual(len(rows), 25)
        self.assertTrue(all(r['contract_issues'] for r in rows))
        files['0001.js'] += b'changed'
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            verify_files(files, expected)

    def test_wrong_ids_missing_files_and_extra_files_rejected(self):
        expected, files = fixture()
        wrong = json.loads(files['assignment.json'])
        wrong['assigned'][0]['id'] = 999
        files['assignment.json'] = json.dumps(wrong).encode()
        with self.assertRaisesRegex(ValueError, 'IDs'):
            verify_files(files, expected)
        for change in ('missing', 'extra'):
            expected, files = fixture()
            if change == 'missing':
                del files['0001-semantics.json']
            else:
                files['run.sh'] = b'ignored code'
            with self.assertRaisesRegex(ValueError, 'missing/extra'):
                verify_files(files, expected)

    def test_paths_links_and_duplicate_names_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.zip'
            for name in ('../escape', '/absolute', 'nested/file.js', 'C:\\bad.js'):
                with zipfile.ZipFile(path, 'w') as archive:
                    archive.writestr(name, b'x')
                with self.assertRaisesRegex(ValueError, 'unsafe'):
                    checked_zip(path)
            with zipfile.ZipFile(path, 'w') as archive:
                link = zipfile.ZipInfo('link.js')
                link.create_system = 3
                link.external_attr = (stat.S_IFLNK | 0o777) << 16
                archive.writestr(link, b'/etc/passwd')
            with self.assertRaisesRegex(ValueError, 'nonregular'):
                checked_zip(path)
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('One.js', b'a')
                archive.writestr('one.js', b'b')
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                checked_zip(path)

    def test_exact_wrapper_supported_without_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'wrapped.zip'
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('gamma-js-W002-B01/0001.js', b'unchanged')
            self.assertEqual(checked_zip(path, 'gamma-js-W002-B01'), {'0001.js': b'unchanged'})
            with self.assertRaisesRegex(ValueError, 'unsafe'):
                checked_zip(path, 'wrong-batch')
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('gamma-js-W002-B01/../escape', b'x')
            with self.assertRaisesRegex(ValueError, 'unsafe'):
                checked_zip(path, 'gamma-js-W002-B01')

    def test_import_preserves_bytes_and_rejects_reimport(self):
        expected, files = fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            authority, folder = root / 'authority', root / 'download'
            authority.mkdir(); folder.mkdir()
            packet = json.dumps(expected).encode()
            (authority / 'W002-B03.json').write_bytes(packet)
            manifest = json.dumps({'batches': [{'batch_id': 'W002-B03', 'json_sha256': sha(packet),
                                               'ids': list(range(1, 26))}]}).encode()
            (authority / 'manifest.json').write_bytes(manifest)
            (authority / 'manifest.sha256').write_text(sha(manifest))
            zip_path = root / 'original.zip'
            with zipfile.ZipFile(zip_path, 'w') as archive:
                for name, content in files.items():
                    archive.writestr(name, content)
                    (folder / name).write_bytes(content)
            receipt = import_delivery(zip_path, folder, authority, root, 'W002-B03')
            self.assertEqual(receipt['status'], 'imported-unqualified')
            self.assertFalse(receipt['qualified'])
            self.assertEqual((root / receipt['rows'][0]['source']).read_bytes(), files['0001.js'])
            with self.assertRaises(FileExistsError):
                import_delivery(zip_path, folder, authority, root, 'W002-B03')
            # A new, tampered delivery is retained as failed evidence; the imported
            # original bytes are never replaced by either a repair or this attempt.
            with zipfile.ZipFile(zip_path, 'w') as archive:
                for name, content in files.items():
                    archive.writestr(name, content + (b'changed' if name == '0001.js' else b''))
            rejected = import_delivery(zip_path, folder, authority, root, 'W002-B03')
            self.assertEqual(rejected['status'], 'rejected')
            retained = root / 'runs/web-deliveries/W002-B03' / rejected['zip_sha256']
            self.assertEqual((retained / 'original.zip').read_bytes(), zip_path.read_bytes())
            self.assertTrue((retained / 'receipt.json').exists())
            self.assertEqual((root / receipt['rows'][0]['source']).read_bytes(), files['0001.js'])


if __name__ == '__main__':
    unittest.main()
