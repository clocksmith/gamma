"""Synthetic CPU tests; no corpus access, installs, or scientific score claims.

Run with an explicitly selected existing torch/numpy interpreter. The native
container fixture is optional in generic CI, mandatory in the local preflight.
"""
import importlib
from pathlib import Path
import tempfile
import unittest

from gamma_enwiki9.adapters.fx2_training_reference import materialize, load_package, load_model
from gamma_enwiki9.adapters.fx2_weight_training import combined_objective, export_entries, quantized_weight_rate_bits
from gamma_enwiki9.adapters.fx2_training_capture import validate_rows, expected_rows, training_windows, source_members, adapt

try:
    import numpy as np
    import torch
except ImportError:
    torch = None

PROJECT = Path(__file__).resolve().parents[1]
UPSTREAM = PROJECT / "external/fx2-cmix-transformer-v1"


class AccountingTests(unittest.TestCase):
    def test_full_population_normalization_is_explicit(self):
        self.assertEqual(combined_objective(2, 80, model_copies=2, represented_symbols=100), 3.6)
        for count, population in ((0, 100), (3, 100), (2, 0), (1, float("inf"))):
            with self.assertRaises(ValueError):
                combined_objective(2, 80, model_copies=count, represented_symbols=population)


class CaptureTests(unittest.TestCase):
    def test_pairs_exclude_resets_and_eof(self):
        rows = bytes([2, 1, 3, 0, 4, 2, 5, 1, 6, 0, 7, 0])
        self.assertEqual(validate_rows(rows, 6 * 410)["eligible_next_token_rows"], 4)
        self.assertEqual(training_windows(rows, [1], 2), [3])

    def test_bad_alignment_or_resets_fail(self):
        for rows, size in ((b"\1", 410), (b"\1\0", 410),
                           (b"\1\1\2\1", 820), (b"\1\2\2\0", 820),
                           (b"\1\1", 409), (b"\xff\1", 410)):
            with self.assertRaises(ValueError):
                validate_rows(rows, size)
        with self.assertRaises(ValueError):
            expected_rows(bytes(20), 250000)

    @unittest.skipUnless((PROJECT / "results/fx2_expert_release250k_v3/P-source.zip").is_file(), "retained native fixture unavailable")
    def test_native_source_transform_is_unique_and_preserves_parent(self):
        members = source_members(PROJECT / "results/fx2_expert_release250k_v3/P-source.zip")
        copy = dict(members)
        changed, identities = adapt(members)
        self.assertEqual(members, copy)
        self.assertEqual(len(identities), 3)
        self.assertEqual({name for name in members if members[name] != changed[name]},
                         {"src/predictor.h", "src/predictor.cpp", "src/runner.cpp"})
        with self.assertRaises(ValueError):
            adapt(changed)


@unittest.skipUnless(torch is not None and (UPSTREAM / "models/6m-q4-fp32.tch").is_file(),
                     "requires provisioned torch/numpy and original FX2 assets")
class ReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.temp = tempfile.TemporaryDirectory(prefix="fx2-reference-test-")
        cls.workspace = Path(cls.temp.name) / "reference"
        cls.manifest = materialize(UPSTREAM, cls.workspace)
        cls.package = load_package(cls.workspace)
        cls.model = load_model(cls.package, UPSTREAM / "models/6m-q4-fp32.tch")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_preimage_failure_does_not_create_output(self):
        root = Path(self.temp.name) / "changed"
        (root / "pysrc").mkdir(parents=True)
        (root / "pysrc/model.py").write_text("not upstream")
        destination = Path(self.temp.name) / "must-not-exist"
        with self.assertRaisesRegex(ValueError, "preimage"):
            materialize(root, destination)
        self.assertFalse(destination.exists())

    def test_owned_workspace_is_not_replaced(self):
        with self.assertRaises(FileExistsError):
            materialize(UPSTREAM, self.workspace)

    def test_full_checkpoint_and_all_layer_gradients(self):
        model = self.model
        self.assertEqual(sum(p.numel() for p in model.parameters()), 5923228)
        model.zero_grad(set_to_none=True)
        tokens = torch.arange(8).reshape(1, 8)
        priors = torch.full((1, 8, 205), 1 / 205)
        logits = model.compute_logits(tokens, priors, torch.tensor([[0, 8]], dtype=torch.int32))
        loss = torch.nn.functional.cross_entropy(logits.reshape(-1, 205), (tokens + 1).reshape(-1))
        loss.backward()
        grads = {n: p.grad for n, p in model.named_parameters() if p.grad is not None}
        self.assertEqual(len(grads), 429)
        self.assertTrue(all(torch.isfinite(g).all() for g in grads.values()))
        for layer in range(12):
            self.assertTrue(any(g.abs().sum() > 0 for n, g in grads.items() if n.startswith(f"blocks.{layer}.")))

    def test_future_tokens_and_priors_cannot_change_prefix(self):
        tokens = torch.arange(8).reshape(1, 8)
        priors = torch.full((1, 8, 205), 1 / 205)
        bounds = torch.tensor([[0, 8]], dtype=torch.int32)
        with torch.no_grad():
            left = self.model.compute_logits(tokens, priors, bounds)
            tokens[:, 4:] += 50
            priors[:, 4:, :] = torch.nn.functional.one_hot(tokens[:, 4:], 205).float()
            right = self.model.compute_logits(tokens, priors, bounds)
        self.assertTrue(torch.equal(left[:, :4], right[:, :4]))
        self.assertFalse(torch.equal(left[:, 4:], right[:, 4:]))

    def test_rate_rounds_signed_half_even_before_symbol_offset(self):
        model = torch.nn.Module()
        model.layer = torch.nn.Module()
        model.layer.weight = torch.nn.Parameter(torch.tensor([[0., .5, 1.5]]))
        model.layer.quantize_weight = torch.nn.Module()
        model.layer.quantize_weight.scale = torch.nn.Parameter(torch.ones(1))
        rate = quantized_weight_rate_bits(model)
        expected = -(2 * np.log2(2.5 / 10.5) + np.log2(1.5 / 10.5))
        self.assertAlmostEqual(rate.item(), expected, places=5)
        rate.backward()
        self.assertTrue(torch.isfinite(model.layer.weight.grad).all())
        self.assertGreater(model.layer.weight.grad.abs().sum().item(), 0)

    def test_all_native_tensors_survive_cpu_export(self):
        packed = importlib.import_module(self.package + ".weights_compress")
        template = packed.read_tensor_file_v2(str(UPSTREAM / "models/6m-q4-fp32.tfwc2"))
        entries = export_entries(self.model, template, self.package)
        self.assertEqual(len(entries), 434)
        for key, kind, value in entries:
            self.assertEqual(kind, template[key][0], key)
            self.assertTrue(np.array_equal(value, template[key][1]), key)
        # Changing a trainable tensor must change the actual native payload.
        with torch.no_grad():
            old = self.model.skip_connection_weights.value.clone()
            self.model.skip_connection_weights.value.add_(.125)
        try:
            child = dict((key, value) for key, _, value in export_entries(self.model, template, self.package))
            self.assertFalse(np.array_equal(child["skip_connection_weights.value"], template["skip_connection_weights.value"][1]))
        finally:
            with torch.no_grad():
                self.model.skip_connection_weights.value.copy_(old)


if __name__ == "__main__":
    unittest.main()
