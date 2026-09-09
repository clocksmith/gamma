"""Synthetic adapter validation using caller-supplied, bounded executables."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import fx2_weight_adaptive_neighbor_model_v1 as runner
import fx2_weight_marginal_fixtures_v1 as reference


class AdaptiveAuditTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=os.environ['FX2_ADAPTIVE_TEST_TMP'])
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.extractor = Path(os.environ['FX2_ADAPTIVE_EXTRACTOR']).resolve()
        self.probe = Path(os.environ['FX2_ADAPTIVE_PROBE']).resolve()
        self.bounds = dict(elapsed_seconds=30, phase_elapsed_seconds=10,
                           cpu_seconds_per_phase=10, address_space_bytes=536870912,
                           per_file_bytes=33554432, scratch_bytes=33554432)

    def run_model(self, tensors, expected):
        model = self.root / 'source.model'
        model.write_bytes(reference.encode_reference(tensors))
        return runner.audit(model, self.root / 'result', self.extractor, self.probe, expected, self.bounds)

    def test_mixed_and_empty_tensors(self):
        tensors = [reference.tensor('weights', 0, [2, 3], 1, [-7, 0, 7, 1, -2, 4]),
                   reference.tensor('raw', 0, [2], 0, [255, 0]),
                   reference.tensor('empty', 0, [0, 4], 1, [])]
        result = self.run_model(tensors, dict(tensors=3, int4_tensors=2, int4_symbols=6))
        self.assertEqual(result['phase_count'], 25)
        self.assertEqual(result['totals']['P'], result['totals']['K'])
        self.assertTrue(result['all_independent_inverses'])
        self.assertTrue(result['all_deterministic_repeats'])
        self.assertEqual(Path(result['rows'][0]['original']['path']).read_bytes(), bytes([0,7,14,8,5,11]))
        for row in result['rows']:
            for arm in ('A','D'):
                self.assertEqual(row['arms'][arm]['count_table_bytes'], 0)
        archive = Path(result['rows'][0]['arms']['D']['archive']['path'])
        sealed = archive.read_bytes()
        attempt = subprocess.run([str(self.probe), 'D', result['rows'][0]['original']['path'],
                                  str(archive), '3'], capture_output=True, timeout=10)
        self.assertNotEqual(attempt.returncode, 0)
        self.assertEqual(archive.read_bytes(), sealed)

    def test_empty_model(self):
        result = self.run_model([], dict(tensors=0,int4_tensors=0,int4_symbols=0))
        self.assertEqual(result['totals'], dict(P=0,K=0,A=0,D=0))

    def test_mismatch_does_not_publish_success(self):
        with self.assertRaisesRegex(ValueError, 'population differs'):
            self.run_model([], dict(tensors=1))
        self.assertTrue((self.root/'result/commands.jsonl').exists())
        self.assertFalse((self.root/'result/receipt.json').exists())


if __name__ == '__main__':
    unittest.main()
