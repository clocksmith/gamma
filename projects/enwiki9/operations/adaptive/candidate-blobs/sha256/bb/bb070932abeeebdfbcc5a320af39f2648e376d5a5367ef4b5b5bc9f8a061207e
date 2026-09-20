"""Synthetic tests for the full-model title path and counted container fields."""
import tempfile
import unittest
from pathlib import Path

try:
    import numpy as np
    import torch
except ImportError:
    torch = None

from gamma_enwiki9.adapters.fx2_training_reference import materialize, load_package, load_model
from gamma_enwiki9.adapters.fx2_title_conditioning import conditioning, metadata_entries, validate_features

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / 'external/fx2-cmix-transformer-v1'

@unittest.skipUnless(torch is not None and (UPSTREAM / 'models/6m-q4-fp32.tch').is_file(), 'provisioned CPU torch and checkpoint required')
class TitleTests(unittest.TestCase):
    def test_zero_control_gradients_and_future_feature_causality(self):
        torch.set_num_threads(1)
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / 'reference'
            materialize(UPSTREAM, destination)
            package = load_package(destination)
            base = load_model(package, UPSTREAM / 'models/6m-q4-fp32.tch')
            child = conditioning(base, package)
            tokens = torch.arange(8).reshape(1, 8)
            prior = torch.full((1, 8, 205), 1 / 205)
            bounds = torch.tensor([[0, 8]], dtype=torch.int32)
            features = torch.zeros((1, 8, 205)); features[..., 10] = 3
            with torch.no_grad():
                plain = base.compute_logits(tokens, prior, bounds)
                zero = child.compute_logits(tokens, prior, bounds, features)
            self.assertTrue(torch.equal(plain, zero))
            loss = child.compute_logits(tokens, prior, bounds, features).square().mean()
            loss.backward()
            self.assertTrue(torch.isfinite(child.gain.grad).all())
            self.assertGreater(float(child.gain.grad.abs().sum()), 0)
            with torch.no_grad():
                child.gain.fill_(.1)
                aligned = child.compute_logits(tokens, prior, bounds, features)
                changed = features.clone(); changed[:, 4:, 10] = 0; changed[:, 4:, 20] = 3
                future = child.compute_logits(tokens, prior, bounds, changed)
                self.assertTrue(torch.equal(aligned[:, :4], future[:, :4]))
                self.assertFalse(torch.equal(aligned[:, 4:], future[:, 4:]))
                self.assertFalse(torch.equal(aligned, plain))
            self.assertEqual(len(base.blocks[0]._forward_pre_hooks), 0)

    def test_native_metadata_inventory_and_matched_capacity(self):
        entries = metadata_entries(np.zeros(192), 1)
        self.assertEqual([(n,k,a.shape) for n,k,a in entries],
                         [('gamma.metadata_gain', 2, (192,)), ('gamma.metadata_mode', 3, (1,))])
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'features'
            row = np.zeros((1, 411), dtype=np.uint8)
            row[0, 0] = row[0, 3] = row[0, 210] = 3
            path.write_bytes(row.tobytes())
            self.assertEqual(validate_features(path, 1)[0, 0], 3)
            row[0, 210] = 4; path.write_bytes(row.tobytes())
            with self.assertRaises(ValueError): validate_features(path, 1)

if __name__ == '__main__':
    unittest.main()
