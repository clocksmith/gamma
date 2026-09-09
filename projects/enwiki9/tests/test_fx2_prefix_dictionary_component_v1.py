"""Runner checks with a synthetic dictionary and simulated native commands."""
import hashlib
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import fx2_prefix_dictionary_component_v1 as runner


class FakeGate:
    def __init__(self, root, raw, encoded):
        self.work = root / 'work'
        self.result = root / 'result'
        (self.work / 'native').mkdir(parents=True)
        self.result.mkdir()
        (self.work / 'dictionary.bin').write_bytes(raw)
        self.raw, self.encoded = raw, encoded
        self.commands, self.records = [], {}
        self.fail = False
        self.corrupt_restore = False

    def closure(self):
        pass

    def artifact(self, path):
        data = path.read_bytes()
        return dict(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())

    def write(self, name, record):
        self.records[name] = record

    def run(self, name, command, cap, work=None, accepted=(0,)):
        self.commands.append((name, command, cap, work))
        (self.work / 'native/ppm.temp').write_bytes(b'transient')
        if self.fail:
            raise ValueError('simulated process failure')
        if Path(command[0]).name == 'cmix':
            operation, source, target = command[1:]
            data = Path(source).read_bytes()
            if operation == '-c':
                Path(target).write_bytes(b'archive:' + data)
            elif operation == '-d':
                assert data.startswith(b'archive:')
                Path(target).write_bytes(data[8:])
            else:
                raise AssertionError('unexpected auxiliary arguments')
        else:
            source, target = map(Path, command[1:])
            if source.read_bytes() != self.encoded:
                assert accepted == (3,)
                return
            if target.exists():
                assert accepted == (4,)
                return
            assert accepted == (0,)
            assert source.read_bytes() == self.encoded
            target.write_bytes(self.raw[:-1] if self.corrupt_restore else self.raw)


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.raw = b'oak\noakford\npine\n'
        self.encoded = b'BPD1\1 oak\n#ford\n pine\n'
        for name, value in [('RAW_BYTES', len(self.raw)), ('RAW_SHA256', hashlib.sha256(self.raw).hexdigest()),
                            ('PREFIX_BYTES', len(self.encoded)), ('PREFIX_SHA256', hashlib.sha256(self.encoded).hexdigest())]:
            patch = mock.patch.object(runner, name, value)
            patch.start()
            self.addCleanup(patch.stop)
        self.g = FakeGate(Path(self.temp.name), self.raw, self.encoded)
        self.prefix_sources = []

        def encode(raw):
            self.assertEqual(raw, self.raw)
            self.prefix_sources.append(raw)
            return self.encoded, {'synthetic': True}

        self.encoder = encode

        def clean(g, closed):
            self.assertTrue(closed)
            transient = g.work / 'native/ppm.temp'
            present = transient.exists()
            if present:
                transient.unlink()
            return dict(cleanup_complete=True, content_hashed=False, removed=present)

        self.support = types.SimpleNamespace(cleanup_native_transient=clean)

    def codec(self, arm):
        return runner.Codec(self.g, arm, self.encoder, self.g.work / 'restore-dictionary', self.support)

    def test_all_arms_use_plain_auxiliary_mode_and_independent_repeat(self):
        archives = {}
        for arm in ('P', 'K', 'D'):
            codec = self.codec(arm)
            archives[arm] = codec.compress(self.raw)
            self.assertEqual(codec.decompress(archives[arm]), self.raw)
            self.assertEqual(codec.compress(self.raw), archives[arm])
            self.assertEqual([row['phase'] for row in codec.phases], ['encode', 'decode', 'repeat'])
        self.assertEqual(archives['P'], archives['K'])
        self.assertEqual(archives['D'], b'archive:' + self.encoded)
        self.assertEqual(len(self.prefix_sources), 4)
        self.assertTrue(self.g.records['K-encode-restore-rejections.json']['existing_output_preserved'])
        self.assertTrue(self.g.records['K-encode-restore-rejections.json']['complete_record_truncation_rejected'])
        auxiliary = [row for row in self.g.commands if Path(row[1][0]).name == 'cmix']
        self.assertEqual(len(auxiliary), 9)
        for _, command, cap, work in auxiliary:
            self.assertEqual(len(command), 4)
            self.assertIn(command[1], ('-c', '-d'))
            self.assertEqual(cap, 360)
            self.assertEqual(work, self.g.work / 'native')
        p_repeat = next(row for row in auxiliary if row[0] == 'P-repeat')
        self.assertTrue(p_repeat[1][2].endswith('P-decode.raw'))
        self.assertFalse((self.g.work / 'native/ppm.temp').exists())
        self.assertTrue(all(not record['content_hashed'] for name, record in self.g.records.items()
                            if name.endswith('-cleanup.json')))

    def test_repeat_rejects_changed_independently_decoded_source(self):
        codec = self.codec('D')
        archive = codec.compress(self.raw)
        codec.decompress(archive)
        codec.restored.write_bytes(b'x' * len(self.raw))
        with self.assertRaisesRegex(ValueError, 'physical source'):
            codec.compress(self.raw)

    def test_record_boundary_truncation_rejected_before_native_inverse(self):
        codec = self.codec('D')
        archive = codec.compress(self.raw)
        before = len(self.g.commands)
        with self.assertRaisesRegex(ValueError, 'prefix input'):
            codec.decompress(archive[:-6])
        self.assertEqual(len(self.g.commands), before + 1)

    def test_native_inverse_success_still_requires_external_raw_sha(self):
        codec = self.codec('K')
        self.g.corrupt_restore = True
        with self.assertRaisesRegex(ValueError, 'restored dictionary'):
            codec.compress(self.raw)
        self.assertFalse(any(Path(row[1][0]).name == 'cmix' for row in self.g.commands))

    def test_process_failure_cleans_transient_and_propagates(self):
        self.g.fail = True
        with self.assertRaisesRegex(ValueError, 'simulated process failure'):
            self.codec('P').compress(self.raw)
        self.assertFalse((self.g.work / 'native/ppm.temp').exists())
        self.assertTrue(self.g.records['P-encode-cleanup.json']['removed'])

    def test_component_accounting_charges_two_helpers_and_both_sources(self):
        result = runner.economics(100096, 99000, 900, 700)
        self.assertEqual(result['archive_saving_bytes_per_copy'], 1096)
        self.assertEqual(result['diagnostic_net_bytes'], -308)
        self.assertIsNone(result['complete_package_bytes'])
        self.assertEqual(result['objective_credit_bytes'], 0)


if __name__ == '__main__':
    unittest.main()
