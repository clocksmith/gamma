"""Synthetic trace and runner checks; never execute the native compressor."""
import hashlib
from pathlib import Path
import struct
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import fx2_xml_word_opening250k_q0_v1 as runner


def xml_trace(path, arm, fields, raw_bytes):
    ring = bytearray(4096)
    previous = None
    with path.open('wb') as output:
        for index in range(len(fields) + 2):
            terminal = index == len(fields) + 1
            event = b'I' if index == 0 else b'F' if terminal else b'B'
            count = min(index, len(fields))
            current = fields[count - 1] if count else 0
            if terminal:
                state = bytearray(previous)
                state[6] = state[runner.OBSERVER_START + 6] = 1
            else:
                delayed = ring[(count - 1) % 4096] if count else 0
                if count:
                    ring[(count - 1) % 4096] = current
                effective = current if arm == 'D' else delayed if arm == 'S' else 0
                parent = count * 17
                context = parent ^ ((effective * runner.FIELD_MULTIPLIER) & runner.MASK)
                state = bytearray(b'XWC1' + bytes((ord(arm), 1, 0, current, delayed, effective)))
                state += struct.pack('<4Q', count, count % 4096, parent, context)
                state += ring
                state += b'XFO1' + bytes((int(count > 0), 0, 0, 0, 0, 0)) + b'\0' * 3
                state += struct.pack('<3Q', raw_bytes, min(max(count - 1, 0), raw_bytes), count)
                state += bytes((current, 0)) + b'\0' * 27
                state += struct.pack('<Q', context)
            assert len(state) == runner.STATE_BYTES
            output.write(event + struct.pack('<I', len(state)) + state)
            previous = state


class FakeGate:
    def __init__(self, root, raw):
        self.work, self.result = root / 'work', root / 'result'
        (self.work / 'native').mkdir(parents=True)
        self.result.mkdir()
        self.buffers = {runner.RAW: raw}
        self.commands, self.records = [], {}
        self.fail = False

    def closure(self):
        pass

    def write(self, name, record):
        self.records[name] = record

    def run(self, name, argv, cap, env=None, work=None):
        self.commands.append(dict(name=name, argv=argv, cap=cap, env=env, work=work))
        (work / 'ppm.temp').write_bytes(b'scratch')
        if self.fail:
            raise ValueError('simulated native failure')
        operation, dictionary, source, target, flag, weights = argv[1:]
        assert dictionary == 'dictionary/english.dic' and flag == '--transformer'
        assert weights == 'models/6m-q4-fp32.tfwc2'
        payload = Path(source).read_bytes()
        Path(target).write_bytes(b'archive:' + payload if operation == '-c' else payload[8:])
        arm = env['GAMMA_FX2_XML_ARM']
        (self.result / (name + '.stderr')).write_bytes(
            b'' if arm == 'P' else b'Gamma XML selected=' + arm.encode() + b'\n')


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def cleanup_support(self):
        def clean(g, closed):
            self.assertTrue(closed)
            path = g.work / 'native/ppm.temp'
            present = path.exists()
            if present:
                path.unlink()
            return dict(cleanup_complete=True, content_hashed=False, removed=present)
        return types.SimpleNamespace(cleanup_native_transient=clean)

    def test_native_phases_and_repeat_use_physical_decoder_output(self):
        g = FakeGate(self.root, b'<title>x</title>')
        for arm in runner.ARMS:
            codec = runner.Codec(g, arm, self.cleanup_support())
            archive = codec.compress(g.buffers[runner.RAW])
            self.assertEqual(codec.decompress(archive), g.buffers[runner.RAW])
            self.assertEqual(codec.compress(g.buffers[runner.RAW]), archive)
        self.assertEqual(len(g.commands), 12)
        for command in g.commands:
            self.assertEqual(command['cap'], 180)
            self.assertEqual(command['work'], g.work / 'native')
            env = command['env']
            self.assertEqual(set(env), {'GAMMA_FX2_XML_ARM', 'GAMMA_FX2_CODER_TRACE'} |
                             (set() if env['GAMMA_FX2_XML_ARM'] == 'P' else
                              {'GAMMA_FX2_XML_TRACE', 'GAMMA_FX2_XML_RAW'}))
            if command['name'].endswith('-repeat'):
                self.assertTrue(command['argv'][3].endswith('-decode.raw'))
        self.assertFalse((g.work / 'native/ppm.temp').exists())

    def test_corrupt_physical_repeat_and_failed_child_rejected(self):
        g = FakeGate(self.root, b'raw')
        codec = runner.Codec(g, 'D', self.cleanup_support())
        archive = codec.compress(b'raw')
        codec.decompress(archive)
        codec.restored.write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError, 'physical decoded'):
            codec.compress(b'raw')
        other = runner.Codec(g, 'S', self.cleanup_support())
        g.fail = True
        with self.assertRaisesRegex(ValueError, 'simulated native failure'):
            other.compress(b'raw')
        self.assertFalse((g.work / 'native/ppm.temp').exists())
        self.assertTrue(g.records['S-encode-cleanup.json']['removed'])

    def test_complete_ring_control_and_shared_observer(self):
        fields = [0] + [1] * 4100 + [0, 2, 2, 0]
        paths = {arm: self.root / (arm + '.xml') for arm in ('K', 'D', 'S')}
        for arm, path in paths.items():
            xml_trace(path, arm, fields, len(fields) - 1)
        result = runner.compare_shared_xml(paths, len(fields), len(fields) - 1)
        self.assertTrue(result['control_adequate'])
        self.assertGreater(result['disagreements'], 0)
        self.assertEqual(sum(map(sum, result['contingency_current_by_delayed'])), len(fields))
        # A future-affecting ring byte outside the cursor must be checked too.
        with paths['D'].open('r+b') as output:
            output.seek(runner.RECORD_BYTES + 5 + runner.RING_START + 37)
            output.write(b'\1')
        with self.assertRaisesRegex(ValueError, 'ring contents'):
            list(runner.xml_records(paths['D'], 'D', len(fields), len(fields) - 1))

    def test_truncation_external_scalar_and_pending_terminal_fail(self):
        path = self.root / 'D.xml'
        fields = [0, 1, 0]
        xml_trace(path, 'D', fields, 2)
        original = path.read_bytes()
        for offset, value in ((runner.RECORD_BYTES + 5 + 4204, 99),
                              (4 * runner.RECORD_BYTES + 5 + runner.OBSERVER_START + 9, 1)):
            damaged = bytearray(original)
            damaged[offset] = value
            path.write_bytes(damaged)
            with self.assertRaises(ValueError):
                list(runner.xml_records(path, 'D', 3, 2))
        path.write_bytes(original[:-1])
        with self.assertRaisesRegex(ValueError, 'length'):
            list(runner.xml_records(path, 'D', 3, 2))

    def test_no_activation_or_nonpositive_control_margin_holds(self):
        paths = {arm: self.root / (arm + '.xml') for arm in ('K', 'D', 'S')}
        for arm, path in paths.items():
            xml_trace(path, arm, [0, 0, 0], 2)
        self.assertFalse(runner.compare_shared_xml(paths, 3, 2)['control_adequate'])
        tied = runner.decision(dict(P=100, K=100, D=99, S=99), True, 10)
        self.assertEqual(tied['scientific_verdict'], 'hold_fixed_realization')
        positive = runner.decision(dict(P=100, K=100, D=98, S=99), True, 10)
        self.assertEqual(positive['diagnostic_local_net_bytes'], -8)
        self.assertFalse(positive['larger_gate_authorized'])
        self.assertIsNone(positive['complete_package_bytes'])

    def test_activation_checks_and_transient_hash_exclusion(self):
        runner.validate_activation(b'other log\n', 'P')
        runner.validate_activation(b'Gamma XML selected=D\n', 'D')
        for text, arm in ((b'', 'D'), (b'Gamma XML selected=D\n', 'P'),
                          (b'Gamma XML selected=D\n' * 2, 'D')):
            with self.assertRaisesRegex(ValueError, 'activation'):
                runner.validate_activation(text, arm)
        gate = object.__new__(runner.NativeGate)
        with self.assertRaisesRegex(ValueError, 'never be hashed'):
            gate.artifact(self.root / 'ppm.temp')

    def test_cache_release_occurs_only_after_verified_closure(self):
        gate = object.__new__(runner.NativeGate)
        gate.work, gate.result, gate.group = self.root / 'work', self.root, self.root
        (gate.work / 'native').mkdir(parents=True)
        (gate.work / 'native/K-encode.xml').write_bytes(b'closed')
        calls = []
        gate.closure = lambda: calls.append('closed')
        gate.write = lambda *args: None
        with mock.patch.object(runner, 'memory_snapshot', return_value={}), \
             mock.patch.object(runner, 'release_closed_file', side_effect=lambda p: calls.append('released') or {}):
            gate.release_observations('test')
        self.assertEqual(calls, ['closed', 'released'])
        gate.closure = mock.Mock(side_effect=ValueError('writer alive'))
        with mock.patch.object(runner, 'release_closed_file') as release:
            with self.assertRaisesRegex(ValueError, 'writer alive'):
                gate.release_observations('blocked')
            release.assert_not_called()


if __name__ == '__main__':
    unittest.main()
