"""Bounded adapter checks using synthetic bytes and stubbed native calls."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('smg_fixture_adapter', ROOT / 'tools/fx2_weight_sign_magnitude_fixture50051_q0_v1.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def selected_line(arm):
    return ('Gamma weight loader selected=' + ('S' if arm == 'D' else 'A') +
            ' tensors=434 histogram_tensors=111 histogram_symbols=5868864 '
            'side_information_bytes=0 canonical=1\n')


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'results')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_native_routing_and_exact_activation(self):
        base = runner.load_source(runner.BASE, {runner.BASE: dict(sha256=runner.PINNED[runner.BASE])},
                                  '_smg_test_fixture_spine')
        base.require = runner.require
        codec_type = runner.codec_class(base)
        native = self.root / 'native'
        native.mkdir()
        for name in ('cmix', 'cmix.P'):
            (native / name).write_bytes(b'synthetic executable placeholder')
        calls = []
        gate = types.SimpleNamespace(result=self.root, binaries={},
                    spec={'runtime': {name: dict(sha256=name) for name in ('cmix', 'cmix.P')}},
                    verify=lambda: None)
        def run(name, command, cap, env, work):
            arm = name.split('-')[1]
            (self.root / (name + '.stderr')).write_text(selected_line(arm))
            calls.append((arm, command, cap, env, work))
        gate.run = run
        for arm in ('P', 'K', 'D'):
            codec_type(gate, native, arm).invoke('encode', ['-c', 'dictionary', 'raw', 'archive'])
        for arm, command, cap, env, work in calls:
            self.assertEqual(Path(command[0]).name, 'cmix.P' if arm == 'P' else 'cmix')
            self.assertEqual(command[-2:], ['--transformer', 'models/model.D' if arm == 'D' else 'models/model.P'])
            self.assertEqual('GAMMA_FX2_WEIGHT_BOOKKEEPING' in env, arm != 'P')
            self.assertEqual(cap, 120)
            self.assertEqual(work, native)
        self.assertEqual(len(calls), 3)

    def test_wrong_or_duplicate_activation_rejected(self):
        gate = types.SimpleNamespace(result=self.root)
        path = self.root / 'phase.stderr'
        for bad in (selected_line('P'), selected_line('D') * 2, ''):
            path.write_text(bad)
            with self.assertRaisesRegex(ValueError, 'loader activation'):
                runner.activation(gate, 'phase', 'D')

    def test_absolute_receipt_reference_and_tamper(self):
        data = b'synthetic receipt'
        row = dict(path='input', bytes=len(data), sha256=runner.digest(data))
        gate = types.SimpleNamespace(inputs={'input': row}, buffers={'input': data})
        self.assertEqual(runner.bound_ref(gate, dict(row, path=str(ROOT / 'input'))), data)
        gate.buffers['input'] = b'changed'
        with self.assertRaisesRegex(ValueError, 'identity differs'):
            runner.bound_ref(gate, row)

    def test_changed_source_rejected_before_execution(self):
        path = self.root / 'source.py'
        path.write_text('raise AssertionError("must never execute")\n')
        with patch.object(runner, 'ROOT', self.root):
            with self.assertRaisesRegex(ValueError, 'Python source changed'):
                runner.load_source('source.py', {'source.py': dict(sha256='0' * 64)}, '_never_execute')

    def evidence(self):
        accounting = dict(model_delta_per_copy=-416, binary_delta_per_copy=0,
                          raw_source_delta=1638, runtime_pair_delta=-832,
                          source_compressor_plus_decoder_delta=806, option_delta_bytes=0)
        tensor = dict(exact_byte_comparison=True, tensor_count=434, payload_bytes=39588806,
                      reference_digest_hex='exact', target_digest_hex='exact')
        production = dict(status='passed', accounting=accounting, tensor_reports=[tensor] * 3)
        inner = dict(accounting, status='passed', all_production_outputs_exact=True,
                     old_dispatch_negative_reproduced=True)
        zipped = dict(status='passed', zip_delta_bytes=-40, decoder_binary_delta_bytes=0,
                      decoder_model_delta_bytes=-416, source_zip_plus_decoder_delta_bytes=-456,
                      inherited_runtime_pair_delta_bytes=-832, option_delta_bytes=0)
        return production, inner, zipped

    def test_zip_economics_preserve_raw_source_failure(self):
        result = runner.economics(*self.evidence())
        self.assertEqual(result['source_zip_plus_decoder_delta'], -456)
        self.assertEqual(result['source_compressor_plus_decoder_delta'], 806)
        self.assertEqual(result['runtime_pair_delta'], -832)

    def test_measured_zip_budget_enforced(self):
        measured = runner.economics(*self.evidence())
        self.assertEqual(runner.check_budget(measured, dict(maximumAddedPackageBytes=376)),
                         dict(compressed_source_increment_bytes=376, gross_runtime_saving_bytes=832,
                              net_zip_and_decoder_saving_bytes=456))
        with self.assertRaisesRegex(ValueError, 'exceeds budget'):
            runner.check_budget(measured, dict(maximumAddedPackageBytes=375))

    def test_missing_control_or_changed_cost_rejected(self):
        for role, key, value in ((1, 'old_dispatch_negative_reproduced', False),
                                 (2, 'source_zip_plus_decoder_delta_bytes', -872),
                                 (2, 'decoder_model_delta_bytes', -832)):
            evidence = self.evidence()
            evidence[role][key] = value
            with self.assertRaises(ValueError):
                runner.economics(*evidence)

    def test_driver_labels_parent_package_and_restores_callback(self):
        written = {}
        gate = types.SimpleNamespace(work=self.root, economics={},
                    spec=dict(production_terminal='production', zip_terminal='zip', zip_result='result'),
                    write=lambda name, value: written.__setitem__(name, copy.deepcopy(value)),
                    artifact=lambda path: dict(path=str(path), bytes=1, sha256='bound'))
        original = lambda *args, **kwargs: dict(arm=None, roundtrip_ok=True)
        driver = types.SimpleNamespace(run=original)
        def execute(gate, support):
            for arm in ('P', 'K', 'D'):
                package = dict(counted_files=[dict(path=str(self.root / 'native/cmix'), bytes=1)])
                driver.run(module=types.SimpleNamespace(arm=arm),
                           package_inventory=([(str(self.root / 'native/cmix'), 1)], package))
            return dict(archive_saved_bytes=0)
        result = runner.execute_fixture(execute, driver, gate, None)
        self.assertIs(driver.run, original)
        self.assertFalse(result['full_hidden_predictor_state_verified'])
        for arm in ('P', 'K', 'D'):
            self.assertEqual(written['fixture/' + arm + '/result.json']['arm'], arm)
            name = Path(written[arm + '-package.json']['counted_files'][0]['path']).name
            self.assertEqual(name, 'cmix.P' if arm == 'P' else 'cmix')
        def fail(*args):
            raise ValueError('synthetic driver failure')
        with self.assertRaisesRegex(ValueError, 'synthetic driver failure'):
            runner.execute_fixture(fail, driver, gate, None)
        self.assertIs(driver.run, original)


if __name__ == '__main__':
    unittest.main()
