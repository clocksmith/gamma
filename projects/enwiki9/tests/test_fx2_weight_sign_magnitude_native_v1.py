"""Reuse native loader fixtures with the separately materialized sign format."""
import os
import sys
from unittest.mock import patch
import unittest
import test_fx2_weight_adaptive_loader_v1 as base
import fx2_weight_sign_magnitude_loader_v1 as adapter


class SignMagnitudeNativeTests(base.LoaderTests):
    def test_adaptive_parent_compatibility(self):
        tensors = [base.reference.tensor('adaptive', 0, [15], 1, list(range(-7, 8)))]
        raw, _ = self.fixture('adaptive', tensors)
        original = raw.parent / 'P'
        adaptive = raw.parent / 'ADM'
        self.call([os.environ['FX2_LOADER_ADAPTIVE_CODEC'], 'D', original, adaptive])
        self.assertEqual(adaptive.read_bytes()[:8], b'GFX2ADM1')
        old = self.call([self.old, raw, adaptive])
        new = self.call([self.new, raw, adaptive])
        self.assertEqual(old.stdout, new.stdout)

    def test_source_identity_rejected(self):
        with self.assertRaisesRegex(ValueError, 'parent differs'):
            adapter.patch(b'changed')

    def test_source_output_exclusive(self):
        target = self.root / 'sealed'
        target.write_bytes(b'keep')
        with patch.object(sys, 'argv', ['loader', '--source', os.environ['FX2_LOADER_SOURCE'],
                                       '--output', str(target)]):
            with self.assertRaises(FileExistsError):
                adapter.main()
        self.assertEqual(target.read_bytes(), b'keep')

    def test_mixed_sign_rescale(self):
        values = [-7, 0, 7, -1, 2, -3, 4] * 20000
        self.fixture('mixed', [base.reference.tensor('mixed', 0, [len(values)], 1, values),
                               base.reference.tensor('reset', 0, [15], 1, list(range(-7, 8)))])


if __name__ == '__main__':
    unittest.main()
