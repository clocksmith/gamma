"""Exercise transfer publication and owned scratch cleanup without a codec."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


PROJECT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT / 'tools/fx2_weight_native_transfer250k_q0_v1.py'
spec = importlib.util.spec_from_file_location('fx2_transfer_failure_fixture', SOURCE)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def require(condition, message):
    if not condition:
        raise ValueError(message)


class FakeFailure(ValueError):
    category = 'fixture_failure'


class FakeGate:
    def __init__(self, root):
        self.result = root / 'results/fixture'
        self.work = self.result / 'work'
        (self.work / 'native').mkdir(parents=True)
        self.root = root
        self.reference = {'path': 'fixture-contract.json', 'sha256': 'fixture'}
        self.commands = []
        self.children_closed = True
        self.closure_calls = 0
        self.hash_requests = []
        self.unstable_artifact = None
        self.trace_calls = []

    def closure(self):
        self.closure_calls += 1
        if not self.children_closed:
            raise ValueError('fixture child still present')

    def verify(self):
        return None

    def write(self, name, value):
        path = self.result / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def artifact(self, path):
        self.hash_requests.append(path)
        if path == self.work / 'native/ppm.temp':
            raise AssertionError('sparse transient must never be content-hashed')
        if path == self.unstable_artifact:
            raise ValueError('artifact changed while being fingerprinted')
        data = path.read_bytes()
        return {'path': str(path.relative_to(self.root)), 'bytes': len(data),
                'sha256': hashlib.sha256(data).hexdigest()}

    def compare_trace(self, reference, target, expected):
        self.trace_calls.append((reference, target, expected))
        return {'delegated': True}


class NativeTransferFailurePaths(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='gamma-fx2-failure-fixture-')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        self.gate = FakeGate(self.root)
        self.temp = self.gate.work / 'native/ppm.temp'
        patches = (mock.patch.object(runner, 'ROOT', self.root),
                   mock.patch.object(runner, 'require', require, create=True))
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def sparse_temp(self):
        with self.temp.open('wb') as handle:
            handle.truncate(8 * 1024 * 1024)
        return self.temp.lstat()

    def test_absent_temp_is_the_positive_no_residual_control(self):
        record = runner.cleanup_native_transient(self.gate, True)
        self.assertEqual(record['status'], 'absent')
        self.assertTrue(record['cleanup_complete'])
        self.assertTrue(record['no_residual_before_cleanup'])
        self.assertFalse(record['removed'])
        self.assertFalse(record['content_hashed'])

    def test_sparse_temp_removed_after_fresh_child_closure(self):
        before = self.sparse_temp()
        record = runner.cleanup_native_transient(self.gate, True)
        self.assertEqual(self.gate.closure_calls, 1)
        self.assertFalse(self.temp.exists())
        self.assertEqual(record['status'], 'removed')
        self.assertTrue(record['cleanup_complete'])
        self.assertFalse(record['no_residual_before_cleanup'])
        self.assertEqual(record['before']['inode'], before.st_ino)
        self.assertEqual(record['before']['device'], before.st_dev)
        self.assertEqual(record['before']['logical_bytes'], before.st_size)
        self.assertEqual(record['before']['allocated_bytes'], before.st_blocks * 512)
        self.assertFalse(record['content_hashed'])
        self.assertEqual(self.gate.hash_requests, [])

    def test_unclosed_children_preserve_temp_and_prevent_hashing(self):
        self.sparse_temp()
        self.gate.children_closed = False
        record = runner.cleanup_native_transient(self.gate, False)
        self.assertEqual(record['status'], 'retained_children_not_closed')
        self.assertTrue(self.temp.exists())
        artifacts, diagnostics = runner.index_artifacts(self.gate, self.temp)
        self.assertNotIn(self.temp, self.gate.hash_requests)
        self.assertFalse(diagnostics['complete'])
        self.assertTrue(any(row['operation'] == 'mandatory-evidence-index' for row in diagnostics['errors']))
        self.assertFalse(any(row['path'].endswith('ppm.temp') for row in artifacts))

    def test_changed_child_closure_prevents_removal_despite_prior_flag(self):
        self.sparse_temp()
        self.gate.children_closed = False
        record = runner.cleanup_native_transient(self.gate, True)
        self.assertEqual(record['status'], 'cleanup_failed')
        self.assertTrue(self.temp.exists())
        self.assertFalse(record['removed'])
        self.assertFalse(record['cleanup_complete'])

    def test_symlink_target_is_untouched(self):
        target = self.root / 'not-owned-by-cleanup'
        target.write_bytes(b'preserve this target')
        self.temp.symlink_to(target)
        record = runner.cleanup_native_transient(self.gate, True)
        self.assertEqual(record['status'], 'cleanup_failed')
        self.assertTrue(self.temp.is_symlink())
        self.assertEqual(target.read_bytes(), b'preserve this target')
        self.assertFalse(record['removed'])

    def test_removal_error_preserves_explicit_failure_and_hash_exclusion(self):
        self.sparse_temp()
        with mock.patch.object(Path, 'unlink', side_effect=PermissionError('fixture removal denied')):
            record = runner.cleanup_native_transient(self.gate, True)
        self.assertEqual(record['status'], 'cleanup_failed')
        self.assertTrue(record['residual_present'])
        self.assertTrue(record['missing_diagnostics'])
        self.assertFalse(record['cleanup_complete'])
        self.assertTrue(self.temp.exists())
        runner.index_artifacts(self.gate, self.temp)
        self.assertNotIn(self.temp, self.gate.hash_requests)

    def test_trace_completeness_reports_missing_truncated_and_extra_data(self):
        reference = self.gate.work / 'reference.trace'
        target = self.gate.work / 'target.trace'
        for name, reference_size, target_size in (('missing', None, 56), ('truncated', 56, 55), ('oversized', 56, 57)):
            with self.subTest(name=name):
                reference.unlink(missing_ok=True)
                if reference_size is not None:
                    reference.write_bytes(bytes(reference_size))
                target.write_bytes(bytes(target_size))
                with self.assertRaisesRegex(ValueError, 'coder trace'):
                    runner.compare_trace(self.gate, reference, target, 56)
                diagnostic = json.loads((self.gate.result / 'first-divergence.json').read_text())
                self.assertEqual(diagnostic['kind'], 'trace-completeness')
                self.assertEqual(diagnostic['expected_bytes'], 56)
                self.assertEqual(diagnostic['expected_records'], 2)
                self.assertEqual(diagnostic['reference']['observed_bytes'], reference_size)
                self.assertEqual(diagnostic['target']['observed_complete_records'], target_size // 28)
                self.assertEqual(diagnostic['target']['observed_partial_record_bytes'], target_size % 28)
        self.assertEqual(self.gate.trace_calls, [])

    def test_complete_traces_reach_existing_exact_comparison(self):
        reference = self.gate.work / 'reference.trace'
        target = self.gate.work / 'target.trace'
        reference.write_bytes(bytes(56))
        target.write_bytes(bytes(56))
        self.assertEqual(runner.compare_trace(self.gate, reference, target, 56), {'delegated': True})
        self.assertEqual(self.gate.trace_calls, [(reference, target, 56)])

    def test_failed_stage_survives_unclosed_child_and_unstable_artifact(self):
        self.sparse_temp()
        self.gate.children_closed = False
        archive = self.gate.result / 'opening/P/archive.bin'
        archive.parent.mkdir(parents=True)
        archive.write_bytes(b'unstable codec output')
        self.gate.unstable_artifact = archive
        with mock.patch.object(runner, 'load_helpers'), \
             mock.patch.object(runner, 'validate_consumed_inputs'), \
             mock.patch.object(runner, 'NativeGate', return_value=self.gate, create=True), \
             mock.patch.object(runner, 'GateFailure', FakeFailure, create=True), \
             mock.patch.object(runner, 'execute', side_effect=ValueError('codec did not close')), \
             mock.patch.object(runner.sys, 'argv', [str(SOURCE)]):
            self.assertEqual(runner.main(), 1)
        stage = json.loads((self.gate.result / 'stage-decision.json').read_text())
        self.assertEqual(stage['status'], 'execution_failed')
        self.assertEqual(stage['artifact_index_status'], 'incomplete')
        self.assertFalse(stage['child_closure_ok'])
        self.assertTrue(self.temp.exists())
        self.assertNotIn(self.temp, self.gate.hash_requests)
        relative_archive = str(archive.relative_to(self.root))
        self.assertTrue(any(row['path'] == relative_archive and row['operation'] == 'fingerprint-artifact'
                            for row in stage['artifact_index_errors']))
        self.assertEqual(stage['artifact_index_exclusions'][0]['path'], str(self.temp.relative_to(self.root)))
        self.assertEqual(stage['artifact_index_exclusions'][0]['status'], 'retained_children_not_closed')


if __name__ == '__main__':
    unittest.main()
