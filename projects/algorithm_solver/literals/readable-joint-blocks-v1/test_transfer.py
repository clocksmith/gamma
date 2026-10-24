"""Invented-only transfer controls. No real corpus source/case is opened."""
import copy
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import transfer


class TransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.root = Path(cls.directory.name)
        cls.work = cls.root / 'work'
        cls.work.mkdir()
        rows, metadata = [], []
        for pid in range(1, 401):
            for kind, name in (
                ('source', f'style150/submitted/{pid}.js'),
                ('cases', f'population500/{pid}-tests.json'),
                ('baseline', f'population500-baseline/qualification/baselines/{pid}.json'),
            ):
                data = transfer.packed({'invented': True, 'kind': kind, 'id': pid})
                path = cls.work / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                rows.append({'id': pid, 'kind': kind, 'path': name, 'sha256': transfer.sha(data)})
            metadata.append({'id': pid, 'entry': 'solve', 'transport': 'standard',
                             'tests_sha256': rows[-2]['sha256']})
        for width in (128, 256):
            name = f'roles/run-v1/dictionaries/L-R-{width}.json'
            data = transfer.packed(['invented', str(width)])
            path = cls.work / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            rows.append({'kind': 'dictionary', 'width': width, 'path': name, 'sha256': transfer.sha(data)})
        # Excluded rows in approved metadata must never cause a payload read.
        original = transfer.packed({'rows': metadata + [{'id': 999, 'private': 'DO-NOT-EXPORT'}]})
        (cls.work / 'population500/manifest.json').write_bytes(original)
        (cls.work / 'population500/999-tests.json').write_text('DO-NOT-OPEN')
        cls.spec = {'schema': 'gamma.dot.development400-transfer.v1',
                    'partition': {'dev_fit': list(range(1, 301)), 'dev_val': list(range(301, 401))},
                    'population_metadata': {'path': 'population500/manifest.json', 'sha256': transfer.sha(original)},
                    'files': rows}
        cls.manifest = cls.root / 'manifest.json'
        cls.manifest.write_bytes(transfer.packed(cls.spec))
        cls.archive = cls.root / 'clean.tar'
        cls.export_receipt = transfer.export_inputs(cls.work, cls.archive, cls.manifest)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=self.root)
        self.addCleanup(self.temporary.cleanup)
        self.temp = Path(self.temporary.name)

    def mutate_archive(self, *, extra=None, change=None):
        destination = self.temp / 'changed.tar'
        with tarfile.open(self.archive) as source, tarfile.open(destination, 'w') as target:
            for member in source:
                data = source.extractfile(member).read()
                if change:
                    data = change(member.name, data)
                transfer._add(target, member.name, data)
            if extra:
                if isinstance(extra, str):
                    transfer._add(target, extra, b'bad')
                else:
                    target.addfile(extra)
        return destination, transfer.sha(destination.read_bytes())

    def test_round_trip_exact_payload_and_filtered_metadata(self):
        target = self.temp / 'imported'
        result = transfer.import_inputs(self.archive, target, self.export_receipt['sha256'], self.manifest)
        self.assertEqual(result['payload_files_verified'], 1202)
        self.assertFalse(result['candidate_execution'])
        for row in self.spec['files']:
            self.assertEqual(transfer.sha((target / row['path']).read_bytes()), row['sha256'])
        subset = transfer.parse((target / transfer.SUBSET).read_bytes())
        self.assertEqual(len(subset['rows']), 400)
        self.assertNotIn(b'DO-NOT-EXPORT', self.archive.read_bytes())
        self.assertFalse((target / 'population500/manifest.json').exists())
        self.assertFalse((target / 'population500/999-tests.json').exists())

    def test_export_opens_only_allowlisted_payloads_and_approved_metadata(self):
        allowed = {r['path'] for r in self.spec['files']} | {'population500/manifest.json'}
        real = transfer.read_relative
        seen = []
        def observed(root, name, *args):
            if Path(root) == self.work:
                self.assertIn(name, allowed)
                seen.append(name)
            return real(root, name, *args)
        with patch.object(transfer, 'read_relative', side_effect=observed):
            transfer.export_inputs(self.work, self.temp / 'export.tar', self.manifest)
        self.assertEqual(set(seen), allowed)

    def test_same_inputs_produce_identical_archive(self):
        receipt = transfer.export_inputs(self.work, self.temp / 'export.tar', self.manifest)
        self.assertEqual(receipt['sha256'], self.export_receipt['sha256'])

    def test_total_limit_includes_receipt_symmetrically(self):
        with tarfile.open(self.archive) as archive:
            total_member_bytes = sum(member.size for member in archive)
        with patch.object(transfer, 'MAX_TOTAL', total_member_bytes):
            exported = transfer.export_inputs(self.work, self.temp / 'exact.tar', self.manifest)
            imported = transfer.import_inputs(self.temp / 'exact.tar', self.temp / 'exact',
                                              exported['sha256'], self.manifest)
        self.assertEqual(imported['payload_files_verified'], 1202)
        with patch.object(transfer, 'MAX_TOTAL', total_member_bytes - 1):
            with self.assertRaisesRegex(ValueError, 'payload exceeds total limit'):
                transfer.export_inputs(self.work, self.temp / 'over.tar', self.manifest)
            with self.assertRaisesRegex(ValueError, 'archive payload too large'):
                transfer.import_inputs(self.archive, self.temp / 'over',
                                       self.export_receipt['sha256'], self.manifest)
        self.assertFalse((self.temp / 'over.tar').exists())
        self.assertFalse((self.temp / 'over').exists())

    def test_generated_metadata_obeys_per_file_import_limit(self):
        with tarfile.open(self.archive) as archive:
            largest = max(archive, key=lambda member: member.size)
        self.assertEqual(largest.name, transfer.SUBSET)
        with patch.object(transfer, 'MAX_FILE', largest.size):
            exported = transfer.export_inputs(self.work, self.temp / 'exact-file.tar', self.manifest)
            imported = transfer.import_inputs(self.temp / 'exact-file.tar', self.temp / 'exact-file',
                                              exported['sha256'], self.manifest)
        self.assertEqual(imported['payload_files_verified'], 1202)
        with patch.object(transfer, 'MAX_FILE', largest.size - 1):
            with self.assertRaisesRegex(ValueError, 'generated metadata or receipt exceeds file limit'):
                transfer.export_inputs(self.work, self.temp / 'over-file.tar', self.manifest)
        self.assertFalse((self.temp / 'over-file.tar').exists())

    def test_rejects_wrong_archive_hash_before_destination_creation(self):
        target = self.temp / 'output'
        with self.assertRaisesRegex(ValueError, 'archive hash'):
            transfer.import_inputs(self.archive, target, '0' * 64, self.manifest)
        self.assertFalse(target.exists())

    def test_rejects_changed_payload_even_with_matching_archive_hash(self):
        name = self.spec['files'][0]['path']
        archive, digest = self.mutate_archive(change=lambda n, raw: b'changed' if n == name else raw)
        with self.assertRaisesRegex(ValueError, 'payload hash'):
            transfer.import_inputs(archive, self.temp / 'output', digest, self.manifest)

    def test_rejects_extra_protected_member(self):
        archive, digest = self.mutate_archive(extra='population500/999-tests.json')
        with self.assertRaisesRegex(ValueError, 'extra or duplicate'):
            transfer.import_inputs(archive, self.temp / 'output', digest, self.manifest)

    def test_rejects_duplicate_member(self):
        archive, digest = self.mutate_archive(extra=self.spec['files'][0]['path'])
        with self.assertRaisesRegex(ValueError, 'extra or duplicate'):
            transfer.import_inputs(archive, self.temp / 'output', digest, self.manifest)

    def test_rejects_traversal(self):
        archive, digest = self.mutate_archive(extra='../escape')
        with self.assertRaisesRegex(ValueError, 'unsafe relative'):
            transfer.import_inputs(archive, self.temp / 'output', digest, self.manifest)
        self.assertFalse((self.temp / 'escape').exists())

    def test_rejects_archive_symlink(self):
        member = tarfile.TarInfo('outside')
        member.type = tarfile.SYMTYPE
        member.linkname = '/tmp'
        archive, digest = self.mutate_archive(extra=member)
        with self.assertRaises(ValueError):
            transfer.import_inputs(archive, self.temp / 'output', digest, self.manifest)

    def test_rejects_source_final_and_parent_symlinks(self):
        actual = self.temp / 'actual'
        actual.mkdir()
        (actual / 'file').write_bytes(b'invented')
        (self.temp / 'alias').symlink_to(actual, target_is_directory=True)
        (self.temp / 'link').symlink_to(actual / 'file')
        for path in ('link', 'alias/file'):
            with self.assertRaises(OSError):
                transfer.read_relative(self.temp, path)

    def test_rejects_destination_parent_symlink(self):
        actual = self.temp / 'actual'
        actual.mkdir()
        (self.temp / 'alias').symlink_to(actual, target_is_directory=True)
        with self.assertRaises(OSError):
            transfer.import_inputs(self.archive, self.temp / 'alias/output', self.export_receipt['sha256'], self.manifest)
        self.assertFalse((actual / 'output').exists())

    def test_no_overwrite(self):
        target = self.temp / 'existing'
        target.mkdir()
        with self.assertRaisesRegex(ValueError, 'destination exists'):
            transfer.import_inputs(self.archive, target, self.export_receipt['sha256'], self.manifest)
        with self.assertRaisesRegex(ValueError, 'archive destination exists'):
            transfer.export_inputs(self.work, self.archive, self.manifest)

    def test_manifest_rejects_outside_identity_and_wrong_partition(self):
        for change in ('file', 'partition'):
            spec = copy.deepcopy(self.spec)
            if change == 'file':
                spec['files'][0]['id'] = 999
            else:
                spec['partition']['dev_val'][0] = 1
            path = self.temp / (change + '.json')
            path.write_bytes(transfer.packed(spec))
            with self.assertRaises(ValueError):
                transfer.load_manifest(path)

    def test_filtered_metadata_hash_mismatch(self):
        archive, digest = self.mutate_archive(change=lambda n, raw: raw + b' ' if n == transfer.SUBSET else raw)
        with self.assertRaisesRegex(ValueError, 'receipt mismatch'):
            transfer.import_inputs(archive, self.temp / 'output', digest, self.manifest)

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate JSON'):
            transfer.parse(b'{"id": 1, "id": 2}')

    def test_default_policy_uses_only_two_pinned_repository_contracts(self):
        real = transfer.read_relative
        seen = []
        def observed(root, name, *args):
            self.assertEqual(Path(root), transfer.REPO_ROOT)
            self.assertIn(name, transfer.CONTRACT_PINS)
            seen.append(name)
            return real(root, name, *args)
        with patch.object(transfer, 'read_relative', side_effect=observed):
            spec, digest = transfer.load_manifest()
        self.assertEqual(seen, list(transfer.CONTRACT_PINS))
        self.assertEqual(len(spec['files']), 1202)
        self.assertEqual(len(spec['partition']['dev_fit']), 300)
        self.assertEqual(len(spec['partition']['dev_val']), 100)
        self.assertEqual(digest, transfer.sha((json.dumps(spec, indent=2) + '\n').encode()))

    def test_contract_drift_fails_before_parsing_or_private_reads(self):
        with patch.object(transfer, 'read_relative', return_value=b'not JSON') as read:
            with self.assertRaisesRegex(ValueError, 'pinned repository contract hash mismatch'):
                transfer.derive_manifest(self.temp)
        self.assertEqual(read.call_count, 1)
        self.assertEqual(read.call_args.args, (self.temp, transfer.SOURCE_CONTRACT))

    def test_missing_pinned_contract_fails_without_network_fallback(self):
        with self.assertRaises(FileNotFoundError):
            transfer.derive_manifest(self.temp)

    def test_policy_is_identical_from_another_matching_checkout(self):
        for name in transfer.CONTRACT_PINS:
            target = self.temp / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(transfer.read_relative(transfer.REPO_ROOT, name))
        self.assertEqual(transfer.derive_manifest(self.temp), transfer.derive_manifest())
        source = self.temp / transfer.SOURCE_CONTRACT
        source.write_bytes(source.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'pinned repository contract hash mismatch'):
            transfer.derive_manifest(self.temp)

    def test_rejects_hidden_nonzero_archive_trailer(self):
        archive = self.temp / 'trailer.tar'
        raw = self.archive.read_bytes() + b'unlisted private payload'
        archive.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, 'nonzero archive trailer'):
            transfer.import_inputs(archive, self.temp / 'output', transfer.sha(raw), self.manifest)


if __name__ == '__main__':
    unittest.main()
