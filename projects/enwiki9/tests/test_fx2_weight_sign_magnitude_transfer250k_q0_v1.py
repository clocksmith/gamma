"""Synthetic transfer orchestration checks; native calls are stubbed."""
import copy
import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('smg_transfer', ROOT / 'tools/fx2_weight_sign_magnitude_transfer250k_q0_v1.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class TransferTests(unittest.TestCase):
    def test_population_and_reflection_tampering_rejected(self):
        inputs = json.loads((ROOT / runner.SPEC).read_text())
        paths = [inputs[key] for key in ('parent_terminal', 'transfer_terminal', 'transfer_reflection')]
        buffers = {path: (ROOT / path).read_bytes() for path in paths}
        documents = {path: json.loads(raw) for path, raw in buffers.items()}
        calls = []
        helper = types.SimpleNamespace(
            document=lambda gate, path: documents[path],
            digest=lambda raw: hashlib.sha256(raw).hexdigest(),
            bound_ref=lambda gate, row: calls.append(row))
        gate = types.SimpleNamespace(spec=copy.deepcopy(inputs), buffers=buffers,
                    economics=documents[inputs['parent_terminal']]['package_economics'])
        runner.validate_populations(helper, gate)
        self.assertEqual(len(calls), 8)
        for key, value in (('offset', 1), ('modeled', 151211)):
            gate.spec = copy.deepcopy(inputs)
            gate.spec['populations'][0][key] = value
            with self.assertRaisesRegex(ValueError, 'populations'):
                runner.validate_populations(helper, gate)
        gate.spec = copy.deepcopy(inputs)
        gate.spec['populations'][0]['trace']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'coordinates'):
            runner.validate_populations(helper, gate)
        gate.spec = copy.deepcopy(inputs)
        documents[inputs['transfer_reflection']]['evidence'] = []
        with self.assertRaisesRegex(ValueError, 'omits terminal'):
            runner.validate_populations(helper, gate)

    def test_population_paths_parent_binary_and_once_only_cost(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'results') as tmp:
            root = Path(tmp)
            written, calls = {}, []
            gate = types.SimpleNamespace(work=root, economics={},
                spec=dict(production_terminal='production', zip_terminal='zip', parent_terminal='fixture'),
                write=lambda path, obj: written.__setitem__(path, copy.deepcopy(obj)),
                artifact=lambda path: dict(path=str(path), bytes=496136, sha256='bound'))
            def original(*args, **kwargs):
                calls.append(kwargs)
                self.assertNotIn('arm', kwargs, 'driver arm dispatch must remain disabled')
                return dict(arm=None, compressed_size=1)
            driver = types.SimpleNamespace(run=original)
            def execute(gate, support):
                for name in ('opening', 'distant'):
                    for arm in 'PKD':
                        path = str(root / 'native/cmix')
                        package = dict(counted_files=[dict(path=path, bytes=496136)])
                        codec = types.SimpleNamespace(arm=arm, population=dict(name=name))
                        driver.run(module=codec, package_inventory=([(path, 496136)], package))
                return dict(archive_saved_bytes=0, all_populations_complete=True)
            result = runner.execute_transfer(execute, driver, gate, None)
            self.assertIs(driver.run, original)
            self.assertEqual(len(calls), 6)
            self.assertEqual(result['source_zip_plus_decoder_delta'], -456)
            self.assertFalse(result['full_hidden_predictor_state_verified'])
            self.assertEqual(result['raw_source_plus_decoder_delta'], 806)
            for name in ('opening', 'distant'):
                for arm in 'PKD':
                    self.assertEqual(written[name + '/' + arm + '/result.json']['arm'], name + '-' + arm)
                    p = written[name + '-' + arm + '-package.json']['counted_files'][0]['path']
                    self.assertEqual(Path(p).name, 'cmix.P' if arm == 'P' else 'cmix')
            self.assertFalse(any(p.startswith('fixture/') for p in written))

    def test_failure_restores_shared_driver(self):
        original = lambda: None
        driver = types.SimpleNamespace(run=original)
        def fail(*args):
            raise ValueError('synthetic failure')
        with self.assertRaisesRegex(ValueError, 'synthetic failure'):
            runner.execute_transfer(fail, driver, object(), None)
        self.assertIs(driver.run, original)

    def test_incomplete_population_or_claimed_archive_gain_rejected(self):
        original = lambda: None
        for result in (dict(archive_saved_bytes=1, all_populations_complete=True),
                       dict(archive_saved_bytes=0, all_populations_complete=False)):
            driver = types.SimpleNamespace(run=original)
            with self.assertRaisesRegex(ValueError, 'invariant failed'):
                runner.execute_transfer(lambda *_: result, driver, object(), None)
            self.assertIs(driver.run, original)


if __name__ == '__main__':
    unittest.main()
