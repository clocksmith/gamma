import importlib.util
from pathlib import Path
import unittest

import numpy as np


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "janus_paid_residual_mdl_oracle.py"
)
SPEC = importlib.util.spec_from_file_location("janus_oracle", MODULE_PATH)
JANUS = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(JANUS)


class JanusOracleTest(unittest.TestCase):
    def test_range_roundtrip_and_tail_fallback(self):
        short_probabilities = np.array(
            [32768, 40000, 12000, 65535, 1, 50000, 27000, 33000],
            dtype=np.uint16,
        )
        short_truth = np.array([0, 1, 0, 1, 0, 1, 1, 0], dtype=np.uint8)
        probabilities = np.tile(short_probabilities, 32)
        truth = np.tile(short_truth, 32)
        candidate = probabilities.copy()
        candidate[:4] = np.array([20000, 50000, 10000, 60000])
        self.assertTrue(np.array_equal(candidate[4:], probabilities[4:]))
        payload = JANUS.range_encode(candidate, truth)
        decoded = JANUS.range_decode(payload, candidate)
        self.assertTrue(np.array_equal(decoded, truth))

    def test_canonical_model_serialization(self):
        tensors_a = {
            "z": np.array([1, -2], dtype=np.int8),
            "a": np.array([[3]], dtype=np.int8),
        }
        tensors_b = {"a": tensors_a["a"], "z": tensors_a["z"]}
        scales = {"a": np.float32(0.25), "z": np.float32(0.5)}
        self.assertEqual(
            JANUS.serialize_jmdl1(tensors_a, scales),
            JANUS.serialize_jmdl1(tensors_b, scales),
        )

    def test_shift_null_moves_residual_not_base_probability(self):
        base = np.array(
            [10000, 20000, 30000, 40000, 50000, 60000, 15000, 25000]
            * 4,
            dtype=np.uint16,
        )
        base_logits = JANUS.probability_logits(base)
        residual = np.full(base.shape, 0.5, dtype=np.float64)
        candidate = JANUS.quantized_probabilities(base_logits, residual)
        shifted = JANUS.shift_residual_probabilities(base, candidate, 4, 1)
        self.assertTrue(np.array_equal(shifted, candidate))

    def test_paid_total_selection(self):
        result = JANUS.select_projected_winner(
            baseline_bytes=1000,
            j1_bytes=999,
            j2_bytes=990,
            j1_package=100,
            j2_package=1000,
            raw_bytes=1_000_000,
        )
        self.assertEqual(result["winner"], "J2")
        result = JANUS.select_projected_winner(
            baseline_bytes=1000,
            j1_bytes=999,
            j2_bytes=999,
            j1_package=100,
            j2_package=1000,
            raw_bytes=1_000_000,
        )
        self.assertEqual(result["winner"], "J1")

    def test_valid_negative_exit_contract_is_zero(self):
        self.assertEqual(JANUS.result_exit_code("AUTHORIZED_10M"), 0)
        self.assertEqual(JANUS.result_exit_code("REJECT"), 0)
        self.assertNotEqual(JANUS.result_exit_code("INVALID"), 0)


if __name__ == "__main__":
    unittest.main()
