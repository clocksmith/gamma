"""Synthetic orchestration failures; no compiler, trained model or corpus use."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import fx2_weight_sign_magnitude_production_v1 as gate


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'results')
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / 'run'
        self.plan = dict(bounds=dict(elapsed_seconds=60, scratch_bytes=1048576),
                         tensor_comparator=dict(path='unused'),
                         models={k: dict(path='unused') for k in ('original', 'parent', 'adaptive')})
        self.good = dict(exact_byte_comparison=True, tensor_count=434, payload_bytes=39588806,
                         reference_digest_hex='same', target_digest_hex='same')

    def test_wrong_tensor_blocks_production(self):
        wrong = dict(self.good, payload_bytes=0)
        with patch.object(gate, 'phase', return_value=json.dumps(wrong)), \
                patch.object(gate.production, 'run') as production:
            with self.assertRaisesRegex(ValueError, 'tensor comparison differs'):
                gate.run(self.plan, {}, self.output)
            production.assert_not_called()
        self.assertFalse((self.output / 'receipt.json').exists())

    def test_production_failure_restores_adapter_and_has_no_success_receipt(self):
        previous = gate.production.patch
        with patch.object(gate, 'phase', return_value=json.dumps(self.good)), \
                patch.object(gate.production, 'run', side_effect=ValueError('native divergence')):
            with self.assertRaisesRegex(ValueError, 'native divergence'):
                gate.run(self.plan, {}, self.output)
        self.assertIs(gate.production.patch, previous)
        self.assertFalse((self.output / 'receipt.json').exists())

    def test_occupied_output_preserved(self):
        self.output.mkdir()
        sealed = self.output / 'sealed'
        sealed.write_bytes(b'keep')
        with self.assertRaises(FileExistsError):
            gate.run(self.plan, {}, self.output)
        self.assertEqual(sealed.read_bytes(), b'keep')


if __name__ == '__main__':
    unittest.main()
