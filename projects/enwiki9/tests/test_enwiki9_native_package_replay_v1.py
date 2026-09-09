"""Synthetic orchestration tests; no native codec or corpus execution."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import enwiki9_native_package_replay_v1 as native
import research_contracts


def sha(data):
    return hashlib.sha256(data).hexdigest()


class FakeGate:
    def __init__(self, root):
        self.root = root
        self.candidate = 'native_package_unit_v1'
        self.result = root / 'result'
        self.result.mkdir()
        self.caps = dict(cpus=[2], memory_bytes=9999998976, scratch_bytes=16000000000,
                         swap_bytes=0, wall_seconds=900)
        self.buffers = {}
        self.binaries = {}
        self.commands = []
        self.bad_binary = False
        self.bad_trace = False
        self.bad_inverse = False
        self.tamper_source = False

    def bind(self):
        self.buffers = {str(p.relative_to(self.root)): p.read_bytes()
                        for p in self.root.rglob('*') if p.is_file()}

    def verify(self):
        for path, raw in self.buffers.items():
            if (self.root / path).read_bytes() != raw:
                raise ValueError('frozen input changed')

    def closure(self):
        pass

    def artifact(self, path):
        return dict(path=str(path.relative_to(self.root)), bytes=path.stat().st_size,
                    sha256=sha(path.read_bytes()))

    def write(self, path, data):
        (self.result / path).write_text(json.dumps(data))

    def compare_trace(self, reference, target, size):
        if target.stat().st_size != size or target.read_bytes() != reference.read_bytes():
            raise ValueError('trace differs')
        return {'exact_byte_comparison': True}

    def run(self, name, command, cap):
        self.commands.append((name, command, cap))
        work = Path(command[command.index('--bind') + 1])
        if name.endswith('-build'):
            (work / 'package/codec').write_bytes(b'wrong' if self.bad_binary else b'binary')
            return
        if self.tamper_source:
            (work / 'package/codec.c').write_bytes(b'changed')
        (work / 'codec.trace').write_bytes(b'X' * 28 if self.bad_trace else b'T' * 28)
        if name == 'package-decode':
            (work / 'restored.enwik9').write_bytes(b'wrong' if self.bad_inverse else b'exact input')
        else:
            (work / 'archive.bin').write_bytes(b'archive')


class NativePackageReplayTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix='gamma-native-package-unit-')
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.gate = FakeGate(self.root)
        package = self.root / 'package'
        package.mkdir()
        (package / 'codec.c').write_bytes(b'source')
        (self.root / 'input').write_bytes(b'exact input')
        (self.root / 'reference.trace').write_bytes(b'T' * 28)
        files = [dict(path='codec.c', bytes=6, sha256=sha(b'source'), role='source')]
        self.manifest = dict(
            schema='gamma.enwiki9.dependency-closure.v1', objective=research_contracts.objective_binding(),
            candidateId=self.gate.candidate, candidateTreeSha256=research_contracts.candidate_tree_digest(files),
            candidateTreeDigestAlgorithm='sha256-canonical-counted-files-v1', candidateRoot='package',
            entryPoint='codec.c', platform='linux-x86-64',
            commands=dict(build=['/usr/bin/gcc', '{entry_point}', '-o', '{package}/codec'],
                          compress=['{package}/codec', 'c', '{corpus}', '{archive}'],
                          decompress=['{package}/codec', 'd', '{archive}', '{restored}']),
            countedFiles=files, requiredOptions=[], requiredOptionBytes=0, totalPackageBytes=6,
            dependencies=[], complete=False, missing=['Synthetic declaration remains incomplete'],
            generatedUtc='2026-09-09T00:00:00+00:00')
        def record(path, data):
            return dict(path=path, bytes=len(data), sha256=sha(data))
        self.spec = dict(resource_budget=self.gate.caps, build_phase_seconds=180, codec_phase_seconds=120,
                         corpus=record('input', b'exact input'), trace=record('reference.trace', b'T' * 28),
                         binary=record('codec', b'binary'), archive=record('unused', b'archive'))
        self.bind()

    def bind(self):
        (self.root / 'manifest.json').write_text(json.dumps(self.manifest))
        (self.root / 'spec.json').write_text(json.dumps(self.spec))
        self.gate.bind()

    def run_replay(self):
        return native.run(self.gate, 'manifest.json', 'spec.json')

    def test_three_builds_without_decode_source_mount_and_without_release_credit(self):
        result = self.run_replay()
        self.assertEqual(result['independent_builds'], 3)
        self.assertTrue(result['exact_inverse'] and result['exact_repeat'])
        self.assertFalse(result['qualification_authority'])
        self.assertFalse(result['license_audit']['approved'])
        self.assertIsNone(result['full_corpus_score_bytes'])
        self.assertIsNone(result['complete_package_bytes'])
        self.assertEqual(result['objective_credit_bytes'], 0)
        self.assertEqual(len(self.gate.commands), 6)
        works = []
        for name, command, cap in self.gate.commands:
            self.assertIn('--unshare-all', command)
            self.assertIn('/work/tmp', command)
            self.assertEqual(cap, 180 if name.endswith('-build') else 120)
            if name.endswith('-build') or name == 'package-decode':
                self.assertNotIn('/input/enwik9', command)
                self.assertNotIn(str(self.root / 'input'), command)
            if name.endswith('-build'):
                works.append(command[command.index('--bind') + 1])
        self.assertEqual(len(set(works)), 3)

    def test_wrong_rebuild_rejected_before_encoding(self):
        self.gate.bad_binary = True
        with self.assertRaisesRegex(ValueError, 'artifact identity differs'):
            self.run_replay()
        self.assertEqual(len(self.gate.commands), 1)

    def test_trace_mismatch_is_not_a_size_pass(self):
        self.gate.bad_trace = True
        with self.assertRaisesRegex(ValueError, 'trace differs'):
            self.run_replay()
        self.assertFalse((self.gate.result / 'package-replay.json').exists())

    def test_bad_inverse_rejected(self):
        self.gate.bad_inverse = True
        with self.assertRaisesRegex(ValueError, 'artifact identity differs'):
            self.run_replay()

    def test_execution_cannot_modify_supplied_source(self):
        self.gate.tamper_source = True
        with self.assertRaisesRegex(ValueError, 'artifact identity differs'):
            self.run_replay()

    def test_missing_package_member_rejected_before_build(self):
        (self.root / 'package/codec.c').unlink()
        with self.assertRaises(ValueError):
            self.run_replay()
        self.assertEqual(self.gate.commands, [])

    def test_unbound_package_member_rejected(self):
        del self.gate.buffers['package/codec.c']
        with self.assertRaisesRegex(ValueError, 'unbound package input'):
            self.run_replay()

    def test_forbidden_decode_corpus_placeholder(self):
        self.manifest['commands']['decompress'].append('{corpus}')
        self.bind()
        with self.assertRaisesRegex(ValueError, 'access.*corpus'):
            self.run_replay()

    def test_cached_binary_cannot_substitute_for_rebuild(self):
        self.spec['binary']['path'] = 'codec.c'
        self.bind()
        with self.assertRaisesRegex(ValueError, 'must be independently built'):
            self.run_replay()

    def test_budget_and_population_must_be_bounded(self):
        self.spec['corpus']['bytes'] = 1000001
        self.bind()
        with self.assertRaisesRegex(ValueError, 'exceeds scope'):
            self.run_replay()
        self.spec['corpus']['bytes'] = len(b'exact input')
        self.spec['resource_budget'] = {**self.gate.caps, 'memory_bytes': 10000000001}
        self.bind()
        with self.assertRaisesRegex(ValueError, 'budget differs'):
            self.run_replay()

    def test_existing_replay_is_not_overwritten(self):
        self.run_replay()
        with self.assertRaises(FileExistsError):
            self.run_replay()


if __name__ == '__main__':
    unittest.main()
