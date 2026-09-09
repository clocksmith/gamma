"""Synthetic model adapter tests; caller supplies bounded, prebuilt executables."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


audit = load('neighbor_model_audit', 'tools/fx2_weight_neighbor_model_audit_v1.py')
reference = load('neighbor_model_reference', 'tools/fx2_weight_marginal_fixtures_v1.py')


class ModelAuditTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=os.environ['FX2_NEIGHBOR_TEST_TMP'])
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.extractor = Path(os.environ['FX2_NEIGHBOR_EXTRACTOR']).resolve()
        self.probe = Path(os.environ['FX2_NEIGHBOR_PROBE']).resolve()
        self.bounds = dict(elapsed_seconds=30, phase_elapsed_seconds=10,
                           cpu_seconds_per_phase=10, address_space_bytes=536870912,
                           per_file_bytes=33554432, scratch_bytes=33554432)

    def run_model(self, tensors, expected, name='result'):
        model = self.root / (name + '.model')
        model.write_bytes(reference.encode_reference(tensors))
        return audit.audit(model, self.root / name, self.extractor, self.probe, expected, self.bounds)

    def test_mixed_model_fresh_processes(self):
        tensors = [reference.tensor('weights', 0, [2, 3], 1, [-7, 0, 7, 1, -2, 4]),
                   reference.tensor('raw', 0, [2], 0, [255, 0]),
                   reference.tensor('empty', 0, [0, 4], 1, [])]
        result = self.run_model(tensors, dict(tensors=3, int4_tensors=2, int4_symbols=6))
        self.assertEqual(result['phase_count'], 19)
        self.assertTrue(result['all_independent_inverses'])
        self.assertTrue(result['parent_bookkeeping_identity'])
        self.assertEqual(result['totals']['P'], result['totals']['K'])
        raw = Path(result['rows'][0]['original']['path']).read_bytes()
        self.assertEqual(raw, bytes([0, 7, 14, 8, 5, 11]))
        self.assertIsNone(result['complete_package_bytes'])

    def test_empty_model(self):
        result = self.run_model([], dict(tensors=0, int4_tensors=0, int4_symbols=0))
        self.assertEqual(result['totals'], dict(P=0, K=0, D=0))
        self.assertEqual(result['phase_count'], 1)

    def test_population_mismatch_retains_failure_without_receipt(self):
        with self.assertRaisesRegex(ValueError, 'population differs'):
            self.run_model([], dict(tensors=1, int4_tensors=0, int4_symbols=0))
        self.assertTrue((self.root / 'result' / 'commands.jsonl').exists())
        self.assertFalse((self.root / 'result' / 'receipt.json').exists())


if __name__ == '__main__':
    unittest.main()
