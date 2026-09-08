import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('forge_gate', ROOT / 'tools/forge_compact_fixture50051_q0_v1.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
namespace = {}
exec(compile((ROOT / 'lib/fx2_native_gate_v1.py').read_bytes(), 'native-helper', 'exec'), namespace)
runner.require, runner.GateFailure = namespace['require'], namespace['GateFailure']


class FakeGate:
    def __init__(self, result, failure=None):
        self.result, self.work = result, result / 'work'
        self.buffers = {runner.UPSTREAM + 'src/probe.cpp': b'source', runner.UPSTREAM + 'dictionary/english.dic': b'dict', runner.UPSTREAM + 'prof_input/input': b'fixture'}
        self.binaries, self.commands, self.failure = {}, [], failure

    def copy(self, source, target):
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as f:
            f.write(self.buffers[source])

    def artifact(self, path):
        b = path.read_bytes()
        return {'path': str(path), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}

    def write(self, name, obj):
        (self.result / name).write_text(json.dumps(obj))

    def run(self, name, argv, cap, work):
        self.commands.append((name, argv, cap))
        if self.failure == name:
            raise runner.GateFailure('budget_exhausted', name)
        if name == 'compile-native':
            (work / 'cmix').write_bytes(b'binary')
        elif name == 'disassemble':
            (self.result / (name + '.stdout')).write_text('vrcpps' if self.failure == 'reciprocal' else 'mov')
        elif name == 'dynamic-dependencies':
            (self.result / (name + '.stdout')).write_text('NEEDED libc.so.6\n')
        elif name == 'encode':
            assert (work / 'input').read_bytes() == b'fixture'
            (work / 'archive').write_bytes(b'archive')
        elif name == 'decode':
            assert not (work / 'input').exists()
            (work / 'restored').write_bytes(b'wrong' if self.failure == 'inverse' else b'fixture')
        elif name == 'reencode':
            (work / 'repeat').write_bytes(b'wrong' if self.failure == 'repeat' else b'archive')


class ForgeGateTests(unittest.TestCase):
    def run_case(self, failure=None):
        with tempfile.TemporaryDirectory() as d:
            gate = FakeGate(Path(d), failure)
            audit = {'source_tree': [{'path': p} for p in gate.buffers] + [{'path': runner.UPSTREAM + 'cmix.before_upx'}]}
            result = runner.execute(gate, audit)
            self.assertTrue(result['exact_inverse'] and result['exact_repeat'])
            self.assertEqual([c[0] for c in gate.commands], ['compile-native', 'disassemble', 'dynamic-dependencies', 'encode', 'decode', 'reencode'])
            self.assertNotIn(runner.UPSTREAM + 'cmix.before_upx', runner.build_paths(audit))
            self.assertFalse(result['larger_gate_authorized'])

    def test_exact_sequence_and_no_shipped_executable(self):
        self.run_case()

    def test_bad_inverse_stops_before_repeat(self):
        with self.assertRaisesRegex(ValueError, 'inverse'):
            self.run_case('inverse')

    def test_bad_repeat_rejected(self):
        with self.assertRaisesRegex(ValueError, 'repeat'):
            self.run_case('repeat')

    def test_approximate_reciprocal_rejected(self):
        with self.assertRaisesRegex(ValueError, 'reciprocal'):
            self.run_case('reciprocal')

    def test_execution_stop_not_compression_rejection(self):
        with self.assertRaises(runner.GateFailure) as caught:
            self.run_case('encode')
        self.assertEqual(caught.exception.category, 'budget_exhausted')


if __name__ == '__main__':
    unittest.main()
