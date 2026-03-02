"""
Test Sampling Utils

Tests centralized sampling logic for all engines:
- temperature_scale: Scale logits by temperature
- top_k_filter: Filter to top k tokens
- top_p_filter: Nucleus sampling
- softmax: Convert logits to probabilities
"""

import sys

import unittest
import numpy as np

from src.engines.sampling_utils import temperature_scale, top_k_filter, top_p_filter, softmax


class TestTemperatureScale(unittest.TestCase):
    """Test temperature_scale function."""

    def test_temperature_one(self):
        """Should return unchanged logits for temperature=1.0."""
        logits = np.array([1.0, 2.0, 3.0])

        result = temperature_scale(logits, 1.0)

        np.testing.assert_array_equal(result, logits)

    def test_temperature_higher(self):
        """Should scale down logits for temperature>1.0."""
        logits = np.array([2.0, 4.0, 6.0])

        result = temperature_scale(logits, 2.0)

        expected = np.array([1.0, 2.0, 3.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_temperature_lower(self):
        """Should scale up logits for temperature<1.0."""
        logits = np.array([1.0, 2.0, 3.0])

        result = temperature_scale(logits, 0.5)

        expected = np.array([2.0, 4.0, 6.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_temperature_zero(self):
        """Should return unchanged for temperature=0."""
        logits = np.array([1.0, 2.0, 3.0])

        result = temperature_scale(logits, 0.0)

        np.testing.assert_array_equal(result, logits)

    def test_temperature_negative(self):
        """Should return unchanged for negative temperature."""
        logits = np.array([1.0, 2.0, 3.0])

        result = temperature_scale(logits, -0.5)

        np.testing.assert_array_equal(result, logits)

    def test_temperature_very_small(self):
        """Should handle very small temperature (clamped to 1e-6)."""
        logits = np.array([1.0, 2.0, 3.0])

        result = temperature_scale(logits, 1e-10)

        # Should be scaled by 1e-6 (minimum)
        self.assertIsInstance(result, np.ndarray)


class TestTopKFilter(unittest.TestCase):
    """Test top_k_filter function."""

    def test_top_k_basic(self):
        """Should keep only top k tokens."""
        logits = np.array([1.0, 5.0, 3.0, 2.0, 4.0])
        k = 3

        result = top_k_filter(logits, k)

        # Top 3 are: 5.0, 4.0, 3.0
        # Others should be -inf
        self.assertTrue(np.isfinite(result[1]))  # 5.0
        self.assertTrue(np.isfinite(result[4]))  # 4.0
        self.assertTrue(np.isfinite(result[2]))  # 3.0
        self.assertTrue(np.isneginf(result[0]))  # 1.0
        self.assertTrue(np.isneginf(result[3]))  # 2.0

    def test_top_k_zero(self):
        """Should return unchanged for k=0."""
        logits = np.array([1.0, 2.0, 3.0])

        result = top_k_filter(logits, 0)

        np.testing.assert_array_equal(result, logits)

    def test_top_k_negative(self):
        """Should return unchanged for negative k."""
        logits = np.array([1.0, 2.0, 3.0])

        result = top_k_filter(logits, -5)

        np.testing.assert_array_equal(result, logits)

    def test_top_k_larger_than_vocab(self):
        """Should return unchanged if k >= vocab size."""
        logits = np.array([1.0, 2.0, 3.0])

        result = top_k_filter(logits, 10)

        np.testing.assert_array_equal(result, logits)

    def test_top_k_equal_to_vocab(self):
        """Should return unchanged if k == vocab size."""
        logits = np.array([1.0, 2.0, 3.0])

        result = top_k_filter(logits, 3)

        np.testing.assert_array_equal(result, logits)

    def test_top_k_one(self):
        """Should keep only the top token."""
        logits = np.array([1.0, 5.0, 3.0])
        k = 1

        result = top_k_filter(logits, k)

        # Only 5.0 should remain
        self.assertTrue(np.isfinite(result[1]))
        self.assertTrue(np.isneginf(result[0]))
        self.assertTrue(np.isneginf(result[2]))

    def test_top_k_multidimensional(self):
        """Should work with multidimensional arrays."""
        logits = np.array([[1.0, 5.0, 3.0], [2.0, 1.0, 4.0]])
        k = 2

        result = top_k_filter(logits, k)

        # First row: keep 5.0 and 3.0
        self.assertTrue(np.isfinite(result[0, 1]))
        self.assertTrue(np.isfinite(result[0, 2]))
        self.assertTrue(np.isneginf(result[0, 0]))

        # Second row: keep 4.0 and 2.0
        self.assertTrue(np.isfinite(result[1, 2]))
        self.assertTrue(np.isfinite(result[1, 0]))
        self.assertTrue(np.isneginf(result[1, 1]))


class TestTopPFilter(unittest.TestCase):
    """Test top_p_filter function."""

    def test_top_p_basic(self):
        """Should filter by cumulative probability."""
        logits = np.array([1.0, 5.0, 3.0, 2.0, 4.0])
        p = 0.8

        result = top_p_filter(logits, p)

        # Should have some finite and some -inf values
        finite_count = np.sum(np.isfinite(result))
        self.assertGreater(finite_count, 0)
        self.assertLess(finite_count, len(logits))

    def test_top_p_zero(self):
        """Should return unchanged for p=0."""
        logits = np.array([1.0, 2.0, 3.0])

        result = top_p_filter(logits, 0.0)

        np.testing.assert_array_equal(result, logits)

    def test_top_p_one(self):
        """Should return unchanged for p=1.0."""
        logits = np.array([1.0, 2.0, 3.0])

        result = top_p_filter(logits, 1.0)

        np.testing.assert_array_equal(result, logits)

    def test_top_p_negative(self):
        """Should return unchanged for negative p."""
        logits = np.array([1.0, 2.0, 3.0])

        result = top_p_filter(logits, -0.5)

        np.testing.assert_array_equal(result, logits)

    def test_top_p_above_one(self):
        """Should return unchanged for p>1.0."""
        logits = np.array([1.0, 2.0, 3.0])

        result = top_p_filter(logits, 1.5)

        np.testing.assert_array_equal(result, logits)

    def test_top_p_min_tokens(self):
        """Should respect min_tokens parameter."""
        logits = np.array([1.0, 5.0, 3.0, 2.0, 4.0])
        p = 0.1  # Very restrictive
        min_tokens = 3

        result = top_p_filter(logits, p, min_tokens=min_tokens)

        # Should keep at least min_tokens
        finite_count = np.sum(np.isfinite(result))
        self.assertGreaterEqual(finite_count, min_tokens)

    def test_top_p_min_tokens_zero(self):
        """Should work with min_tokens=0."""
        logits = np.array([1.0, 5.0, 3.0])
        p = 0.5

        result = top_p_filter(logits, p, min_tokens=0)

        self.assertIsInstance(result, np.ndarray)

    def test_top_p_multidimensional(self):
        """Should work with multidimensional arrays."""
        logits = np.array([[1.0, 5.0, 3.0], [2.0, 1.0, 4.0]])
        p = 0.8

        result = top_p_filter(logits, p)

        self.assertEqual(result.shape, logits.shape)


class TestSoftmax(unittest.TestCase):
    """Test softmax function."""

    def test_softmax_basic(self):
        """Should convert logits to probabilities."""
        x = np.array([1.0, 2.0, 3.0])

        result = softmax(x)

        # Should sum to 1
        self.assertAlmostEqual(np.sum(result), 1.0, places=6)

        # All values should be between 0 and 1
        self.assertTrue(np.all(result >= 0))
        self.assertTrue(np.all(result <= 1))

        # Higher logit should have higher probability
        self.assertGreater(result[2], result[1])
        self.assertGreater(result[1], result[0])

    def test_softmax_equal_logits(self):
        """Should give equal probabilities for equal logits."""
        x = np.array([2.0, 2.0, 2.0])

        result = softmax(x)

        expected = np.array([1/3, 1/3, 1/3])
        np.testing.assert_array_almost_equal(result, expected)

    def test_softmax_large_values(self):
        """Should handle large values without overflow."""
        x = np.array([100.0, 200.0, 300.0])

        result = softmax(x)

        # Should sum to 1
        self.assertAlmostEqual(np.sum(result), 1.0, places=6)

        # Should not have NaN or inf
        self.assertTrue(np.all(np.isfinite(result)))

    def test_softmax_negative_values(self):
        """Should handle negative values."""
        x = np.array([-3.0, -2.0, -1.0])

        result = softmax(x)

        # Should sum to 1
        self.assertAlmostEqual(np.sum(result), 1.0, places=6)

        # Higher (less negative) should have higher probability
        self.assertGreater(result[2], result[1])
        self.assertGreater(result[1], result[0])

    def test_softmax_single_value(self):
        """Should work with single value."""
        x = np.array([5.0])

        result = softmax(x)

        # Should be 1.0
        np.testing.assert_array_almost_equal(result, [1.0])

    def test_softmax_multidimensional(self):
        """Should work with multidimensional arrays."""
        x = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])

        result = softmax(x)

        # Each row should sum to 1
        row_sums = np.sum(result, axis=-1)
        np.testing.assert_array_almost_equal(row_sums, [1.0, 1.0])

    def test_softmax_zero_values(self):
        """Should handle all zeros."""
        x = np.array([0.0, 0.0, 0.0])

        result = softmax(x)

        # Should be equal probabilities
        expected = np.array([1/3, 1/3, 1/3])
        np.testing.assert_array_almost_equal(result, expected)


def run_tests():
    """Run all sampling utils tests."""
    print("=" * 80)
    print("Testing Sampling Utils")
    print("=" * 80)
    print()

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 80)
    print(f"Tests: {result.testsRun}, Failures: {len(result.failures)}, Errors: {len(result.errors)}")
    print("=" * 80)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
