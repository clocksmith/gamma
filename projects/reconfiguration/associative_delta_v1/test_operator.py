import unittest
import numpy as np

from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

spec = spec_from_file_location("delta_operator", Path(__file__).with_name("delta.py"))
op = module_from_spec(spec)
spec.loader.exec_module(op)


class DeltaTests(unittest.TestCase):
    def test_orthogonal_keys(self):
        base = np.zeros((2, 2))
        keys = np.eye(2)
        values = np.array([[2.0, 3.0], [4.0, 5.0]])
        left, right = op.derive(base, keys, values, rate=1, epsilon=1e-12)
        np.testing.assert_allclose(
            op.apply(base, left, right, keys), values, atol=1e-10
        )
        np.testing.assert_array_equal(base, np.zeros((2, 2)))

    def test_factor_dense_equivalence(self):
        rng = np.random.default_rng(4)
        base, keys, values, query = (
            rng.normal(size=(2, 3)),
            rng.normal(size=(5, 3)),
            rng.normal(size=(5, 2)),
            rng.normal(size=(7, 3)),
        )
        left, right = op.derive(base, keys, values)
        dense = base.copy()
        for k, v in zip(keys, values, strict=True):
            dense += 0.5 * np.outer(v - dense @ k, k) / (k @ k + 1e-9)
        np.testing.assert_allclose(
            op.apply(base, left, right, query), query @ dense.T, atol=1e-12
        )

    def test_empty_zero_rate_zero_key(self):
        base = np.ones((2, 3))
        for keys, values, rate in [
            (np.empty((0, 3)), np.empty((0, 2)), 0.5),
            (np.ones((2, 3)), np.ones((2, 2)), 0),
            (np.zeros((2, 3)), np.ones((2, 2)), 0.5),
        ]:
            left, right = op.derive(base, keys, values, rate)
            np.testing.assert_array_equal(
                op.apply(base, left, right, np.eye(3)), base.T
            )

    def test_invalid(self):
        for keys, values, rate in [
            (np.ones((2, 4)), np.ones((2, 2)), 0.5),
            (np.full((2, 3), np.nan), np.ones((2, 2)), 0.5),
            (np.ones((2, 3)), np.ones((2, 2)), 2),
        ]:
            with self.assertRaises(ValueError):
                op.derive(np.ones((2, 3)), keys, values, rate)


if __name__ == "__main__":
    unittest.main()
