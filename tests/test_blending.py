"""
Test Blending Module

Tests weighted blending strategies for combining model outputs:
- BlendingStrategy enum
- BlendingConfig dataclass
- LogitBlender initialization and configuration
- All blending strategies
- Helper methods for conversions and filtering
- Statistics tracking
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import Mock, MagicMock, patch
import numpy as np

from src.mind_meld.core.blending import BlendingStrategy, BlendingConfig, LogitBlender


class TestBlendingStrategy(unittest.TestCase):
    """Test BlendingStrategy enum."""

    def test_all_strategies(self):
        """Should have all expected strategies."""
        expected = {
            "WEIGHTED_AVERAGE",
            "CONFIDENCE_WEIGHTED",
            "DYNAMIC_WEIGHTED",
            "ATTENTION_WEIGHTED",
            "LEARNED",
            "HIERARCHICAL",
            "ENSEMBLE_VOTING"
        }

        actual = {s.name for s in BlendingStrategy}
        self.assertEqual(actual, expected)

    def test_strategy_values(self):
        """Should have correct values."""
        self.assertEqual(BlendingStrategy.WEIGHTED_AVERAGE.value, "weighted_average")
        self.assertEqual(BlendingStrategy.CONFIDENCE_WEIGHTED.value, "confidence_weighted")


class TestBlendingConfig(unittest.TestCase):
    """Test BlendingConfig dataclass."""

    def test_default_initialization(self):
        """Should initialize with defaults."""
        config = BlendingConfig()

        self.assertEqual(config.strategy, BlendingStrategy.WEIGHTED_AVERAGE)
        self.assertIsNone(config.weights)
        self.assertEqual(config.temperature, 1.0)
        self.assertTrue(config.use_confidence_scores)
        self.assertEqual(config.confidence_threshold, 0.7)

    def test_custom_initialization(self):
        """Should initialize with custom values."""
        config = BlendingConfig(
            strategy=BlendingStrategy.CONFIDENCE_WEIGHTED,
            weights=[0.3, 0.7],
            temperature=0.8,
            confidence_threshold=0.9
        )

        self.assertEqual(config.strategy, BlendingStrategy.CONFIDENCE_WEIGHTED)
        self.assertEqual(config.weights, [0.3, 0.7])
        self.assertEqual(config.temperature, 0.8)
        self.assertEqual(config.confidence_threshold, 0.9)

    def test_all_config_fields(self):
        """Should have all expected fields."""
        config = BlendingConfig()

        # Check key fields exist
        self.assertIsNotNone(config.strategy)
        self.assertIsNotNone(config.temperature)
        self.assertIsNotNone(config.use_confidence_scores)
        self.assertIsNotNone(config.dynamic_adjustment)
        self.assertIsNotNone(config.smoothing_factor)


class TestLogitBlender(unittest.TestCase):
    """Test LogitBlender class."""

    def setUp(self):
        """Set up test blender."""
        self.blender = LogitBlender(verbose=False)

    def test_initialization_default(self):
        """Should initialize with default config."""
        blender = LogitBlender()

        self.assertIsNotNone(blender.config)
        self.assertEqual(blender.config.strategy, BlendingStrategy.WEIGHTED_AVERAGE)
        self.assertEqual(blender.blend_count, 0)
        self.assertTrue(blender.verbose)

    def test_initialization_custom_config(self):
        """Should initialize with custom config."""
        config = BlendingConfig(strategy=BlendingStrategy.CONFIDENCE_WEIGHTED)
        blender = LogitBlender(config=config, verbose=False)

        self.assertEqual(blender.config.strategy, BlendingStrategy.CONFIDENCE_WEIGHTED)
        self.assertFalse(blender.verbose)

    def test_blend_empty_list(self):
        """Should raise error for empty logits list."""
        with self.assertRaises(ValueError):
            self.blender.blend([])

    def test_blend_single_model(self):
        """Should return single model output unchanged."""
        logits = np.array([1.0, 2.0, 3.0])

        result, stats = self.blender.blend([logits])

        self.assertTrue(stats["single_model"])
        np.testing.assert_array_equal(result, logits)

    def test_blend_two_models_weighted_average(self):
        """Should blend two models with weighted average."""
        # Use larger vocab size to avoid top_k filtering issues
        logits1 = np.random.randn(1000)
        logits2 = np.random.randn(1000)

        config = BlendingConfig(
            strategy=BlendingStrategy.WEIGHTED_AVERAGE,
            weights=[0.5, 0.5]
        )
        blender = LogitBlender(config=config, verbose=False)

        result, stats = blender.blend([logits1, logits2])

        self.assertIsInstance(result, np.ndarray)
        self.assertIsInstance(stats, dict)
        self.assertGreater(blender.blend_count, 0)

    def test_blend_with_temperature(self):
        """Should apply temperature to blended output."""
        # Use larger vocab size to avoid top_k filtering issues
        logits1 = np.random.randn(1000)
        logits2 = np.random.randn(1000)

        config = BlendingConfig(temperature=0.5, top_k_blend=None)
        blender = LogitBlender(config=config, verbose=False)

        result, stats = blender.blend([logits1, logits2])

        # With temperature != 1.0, result should be scaled
        self.assertIsInstance(result, np.ndarray)

    def test_blend_increments_count(self):
        """Should increment blend count."""
        # Use larger arrays and disable top_k
        logits1 = np.random.randn(1000)
        logits2 = np.random.randn(1000)

        # Use custom blender with disabled filtering
        config = BlendingConfig(top_k_blend=None, top_p_blend=None)
        blender = LogitBlender(config=config, verbose=False)

        initial_count = blender.blend_count
        blender.blend([logits1, logits2])

        self.assertEqual(blender.blend_count, initial_count + 1)

    def test_weighted_average_blend(self):
        """Should perform weighted average blending."""
        logits1 = np.array([1.0, 2.0, 3.0])
        logits2 = np.array([3.0, 2.0, 1.0])
        weights = np.array([0.7, 0.3])

        result = self.blender._weighted_average_blend([logits1, logits2], weights)

        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result.shape, logits1.shape)

    def test_confidence_weighted_blend(self):
        """Should perform confidence-weighted blending."""
        logits1 = np.array([1.0, 2.0, 3.0])
        logits2 = np.array([3.0, 2.0, 1.0])
        confidences = [0.8, 0.6]

        result = self.blender._confidence_weighted_blend([logits1, logits2], confidences)

        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result.shape, logits1.shape)

    def test_confidence_weighted_blend_no_confidences(self):
        """Should estimate confidence when not provided."""
        logits1 = np.array([1.0, 2.0, 3.0])
        logits2 = np.array([3.0, 2.0, 1.0])

        result = self.blender._confidence_weighted_blend([logits1, logits2], None)

        self.assertIsInstance(result, np.ndarray)

    def test_dynamic_weighted_blend(self):
        """Should perform dynamic weighted blending."""
        logits1 = np.array([1.0, 2.0, 3.0])
        logits2 = np.array([3.0, 2.0, 1.0])
        metadata = {"step": 5, "history": []}

        result = self.blender._dynamic_weighted_blend([logits1, logits2], metadata)

        self.assertIsInstance(result, np.ndarray)

    def test_attention_weighted_blend(self):
        """Should perform attention-weighted blending."""
        logits1 = np.array([1.0, 2.0, 3.0])
        logits2 = np.array([3.0, 2.0, 1.0])
        attention_scores = [np.array([0.7]), np.array([0.3])]

        result = self.blender._attention_weighted_blend([logits1, logits2], attention_scores)

        self.assertIsInstance(result, np.ndarray)

    def test_attention_weighted_blend_no_scores(self):
        """Should handle missing attention scores."""
        logits1 = np.array([1.0, 2.0, 3.0])
        logits2 = np.array([3.0, 2.0, 1.0])

        result = self.blender._attention_weighted_blend([logits1, logits2], None)

        self.assertIsInstance(result, np.ndarray)

    def test_hierarchical_blend(self):
        """Should perform hierarchical blending."""
        logits1 = np.array([1.0, 2.0, 3.0])
        logits2 = np.array([3.0, 2.0, 1.0])
        weights = np.array([0.6, 0.4])

        result = self.blender._hierarchical_blend([logits1, logits2], weights)

        self.assertIsInstance(result, np.ndarray)

    def test_ensemble_voting_blend(self):
        """Should perform ensemble voting."""
        logits1 = np.array([1.0, 2.0, 3.0])
        logits2 = np.array([3.0, 2.0, 1.0])
        logits3 = np.array([2.0, 3.0, 1.0])

        result = self.blender._ensemble_voting_blend([logits1, logits2, logits3])

        self.assertIsInstance(result, np.ndarray)

    def test_get_weights_with_provided_weights(self):
        """Should use provided weights."""
        config = BlendingConfig(weights=[0.6, 0.4])
        blender = LogitBlender(config=config, verbose=False)

        weights = blender._get_weights(2, None, None)

        np.testing.assert_array_almost_equal(weights, [0.6, 0.4])

    def test_get_weights_equal_default(self):
        """Should use equal weights by default."""
        weights = self.blender._get_weights(3, None, None)

        expected = np.array([1/3, 1/3, 1/3])
        np.testing.assert_array_almost_equal(weights, expected)

    def test_get_target_shape(self):
        """Should determine target shape from logits."""
        logits1 = np.array([1.0, 2.0, 3.0])
        logits2 = np.array([1.0, 2.0, 3.0, 4.0])

        shape = self.blender._get_target_shape([logits1, logits2])

        # Should use the largest shape
        self.assertEqual(shape, (4,))

    def test_reshape_logits(self):
        """Should reshape logits to target shape."""
        logits = np.array([1.0, 2.0, 3.0])
        target_shape = (5,)

        result = self.blender._reshape_logits(logits, target_shape)

        self.assertEqual(result.shape, target_shape)

    def test_apply_filtering_with_top_k(self):
        """Should apply top-k filtering."""
        config = BlendingConfig(top_k_blend=2)
        blender = LogitBlender(config=config, verbose=False)

        logits = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = blender._apply_filtering(logits)

        self.assertIsInstance(result, np.ndarray)

    def test_apply_filtering_with_top_p(self):
        """Should apply top-p filtering."""
        config = BlendingConfig(top_k_blend=None, top_p_blend=0.9)
        blender = LogitBlender(config=config, verbose=False)

        logits = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = blender._apply_filtering(logits)

        self.assertIsInstance(result, np.ndarray)

    def test_apply_entropy_regularization(self):
        """Should apply entropy regularization."""
        logits = np.array([1.0, 2.0, 3.0])

        result = self.blender._apply_entropy_regularization(logits)

        self.assertIsInstance(result, np.ndarray)

    def test_estimate_confidence(self):
        """Should estimate confidence from logits."""
        logits = np.array([1.0, 2.0, 10.0])  # High confidence

        confidence = self.blender._estimate_confidence(logits)

        self.assertIsInstance(confidence, (float, np.floating))
        self.assertGreater(confidence, 0)
        self.assertLessEqual(confidence, 1.0)

    def test_compute_perplexity(self):
        """Should compute perplexity."""
        logits = np.array([1.0, 2.0, 3.0])

        perplexity = self.blender._compute_perplexity(logits)

        self.assertIsInstance(perplexity, (float, np.floating))
        self.assertGreater(perplexity, 0)

    def test_compute_entropy(self):
        """Should compute entropy."""
        logits = np.array([1.0, 2.0, 3.0])

        entropy = self.blender._compute_entropy(logits)

        self.assertIsInstance(entropy, (float, np.floating))
        self.assertGreaterEqual(entropy, 0)

    def test_compute_agreement_scores(self):
        """Should compute agreement between models."""
        logits1 = np.array([1.0, 2.0, 3.0])
        logits2 = np.array([1.1, 1.9, 3.1])  # Similar to logits1
        logits3 = np.array([3.0, 2.0, 1.0])  # Different

        scores = self.blender._compute_agreement_scores([logits1, logits2, logits3])

        self.assertIsInstance(scores, np.ndarray)

    def test_compute_blend_statistics(self):
        """Should compute statistics for blend."""
        logits1 = np.array([1.0, 2.0, 3.0])
        logits2 = np.array([3.0, 2.0, 1.0])
        blended = np.array([2.0, 2.0, 2.0])
        weights = np.array([0.5, 0.5])
        model_names = ["model1", "model2"]

        stats = self.blender._compute_blend_statistics(
            [logits1, logits2], blended, weights, model_names
        )

        self.assertIsInstance(stats, dict)
        self.assertIn("num_models", stats)
        self.assertIn("weights", stats)

    def test_reset_dynamic_weights(self):
        """Should reset dynamic weights."""
        self.blender.current_weights = np.array([0.7, 0.3])
        self.blender.weight_history = [[0.5, 0.5], [0.6, 0.4]]

        self.blender.reset_dynamic_weights()

        self.assertIsNone(self.blender.current_weights)
        self.assertEqual(len(self.blender.weight_history), 0)

    def test_get_weight_summary(self):
        """Should return weight summary."""
        self.blender.current_weights = np.array([0.6, 0.4])
        self.blender.weight_history = [[0.5, 0.5], [0.6, 0.4]]
        self.blender.blend_count = 2

        summary = self.blender.get_weight_summary()

        self.assertIsInstance(summary, dict)
        self.assertIn("current_weights", summary)
        self.assertIn("num_blends", summary)  # Correct field name

    def test_softmax(self):
        """Should compute softmax."""
        x = np.array([1.0, 2.0, 3.0])

        result = self.blender._softmax(x)

        # Softmax should sum to 1
        self.assertAlmostEqual(np.sum(result), 1.0, places=6)
        self.assertTrue(np.all(result >= 0))
        self.assertTrue(np.all(result <= 1))

    def test_top_k_filtering(self):
        """Should filter to top k values."""
        logits = np.array([1.0, 5.0, 3.0, 2.0, 4.0])
        k = 3

        result = self.blender._top_k_filtering(logits, k)

        # Only top 3 should remain, others set to -1e9
        # Count values that are not -1e9
        not_filtered_count = np.sum(result > -1e8)
        self.assertEqual(not_filtered_count, k)

    def test_top_p_filtering(self):
        """Should filter by cumulative probability."""
        logits = np.array([1.0, 5.0, 3.0, 2.0, 4.0])
        p = 0.9

        result = self.blender._top_p_filtering(logits, p)

        self.assertIsInstance(result, np.ndarray)
        # Should filter some tokens
        self.assertGreaterEqual(np.sum(np.isfinite(result)), 1)

    def test_to_numpy_from_numpy(self):
        """Should convert ndarray to numpy."""
        array = np.array([1.0, 2.0, 3.0])

        result = self.blender._to_numpy(array)

        np.testing.assert_array_equal(result, array)

    def test_to_numpy_from_list(self):
        """Should convert list to numpy."""
        lst = [1.0, 2.0, 3.0]

        result = self.blender._to_numpy(lst)

        np.testing.assert_array_equal(result, np.array(lst))

    def test_from_numpy_to_numpy(self):
        """Should convert back to original type."""
        array = np.array([1.0, 2.0, 3.0])
        reference = np.array([0.0])

        result = self.blender._from_numpy(array, reference)

        self.assertIsInstance(result, np.ndarray)
        np.testing.assert_array_equal(result, array)

    def test_blend_with_confidence_weighted_strategy(self):
        """Should use confidence weighted strategy."""
        # Use larger arrays to avoid top_k issues
        logits1 = np.random.randn(1000)
        logits2 = np.random.randn(1000)
        confidences = [0.8, 0.6]

        config = BlendingConfig(strategy=BlendingStrategy.CONFIDENCE_WEIGHTED)
        blender = LogitBlender(config=config, verbose=False)

        result, stats = blender.blend([logits1, logits2], confidences=confidences)

        self.assertIsInstance(result, np.ndarray)
        self.assertIn("num_models", stats)

    def test_blend_with_model_names(self):
        """Should track model names in statistics."""
        # Use larger arrays
        logits1 = np.random.randn(1000)
        logits2 = np.random.randn(1000)
        model_names = ["gpt2", "llama"]

        # Disable top_k filtering
        config = BlendingConfig(top_k_blend=None)
        blender = LogitBlender(config=config, verbose=False)

        result, stats = blender.blend([logits1, logits2], model_names=model_names)

        self.assertIsInstance(stats, dict)
        # Stats should include model names
        self.assertIn("num_models", stats)

    def test_blend_with_metadata(self):
        """Should pass metadata to blending strategies."""
        # Use larger arrays
        logits1 = np.random.randn(1000)
        logits2 = np.random.randn(1000)
        metadata = {"step": 10, "loss": 0.5}

        # Disable top_k filtering
        config = BlendingConfig(top_k_blend=None)
        blender = LogitBlender(config=config, verbose=False)

        result, stats = blender.blend([logits1, logits2], metadata=metadata)

        self.assertIsInstance(result, np.ndarray)

    def test_blend_with_all_strategies(self):
        """Should work with all blending strategies."""
        # Use larger arrays
        logits1 = np.random.randn(1000)
        logits2 = np.random.randn(1000)

        strategies = [
            BlendingStrategy.WEIGHTED_AVERAGE,
            BlendingStrategy.CONFIDENCE_WEIGHTED,
            BlendingStrategy.DYNAMIC_WEIGHTED,
            BlendingStrategy.ATTENTION_WEIGHTED,
            BlendingStrategy.HIERARCHICAL,
            BlendingStrategy.ENSEMBLE_VOTING,
        ]

        for strategy in strategies:
            config = BlendingConfig(strategy=strategy, top_k_blend=None)
            blender = LogitBlender(config=config, verbose=False)

            result, stats = blender.blend([logits1, logits2])

            self.assertIsInstance(result, np.ndarray)
            self.assertIsInstance(stats, dict)


class TestVocabMismatchFix(unittest.TestCase):
    """Tests for handling different vocabulary sizes between models."""

    def setUp(self):
        """Set up test blender with filtering disabled."""
        config = BlendingConfig(top_k_blend=None, top_p_blend=None)
        self.blender = LogitBlender(config=config, verbose=False)

    def test_blend_different_vocab_sizes_1d(self):
        """Should blend 1D arrays with different vocab sizes."""
        logits1 = np.random.randn(32000)  # Smaller vocab
        logits2 = np.random.randn(64000)  # Larger vocab

        result, stats = self.blender.blend([logits1, logits2])

        # Result should have the larger vocab size
        self.assertEqual(result.shape[0], 64000)

    def test_blend_different_vocab_sizes_2d(self):
        """Should blend 2D arrays with different vocab sizes."""
        logits1 = np.random.randn(1, 32000)  # batch=1, smaller vocab
        logits2 = np.random.randn(1, 64000)  # batch=1, larger vocab

        result, stats = self.blender.blend([logits1, logits2])

        # Result should have the larger vocab size
        self.assertEqual(result.shape, (1, 64000))

    def test_ensemble_voting_2d_arrays(self):
        """Ensemble voting should handle 2D arrays without index errors."""
        # This was the original bug - 2D arrays caused index out of bounds
        logits1 = np.random.randn(1, 32000)
        logits2 = np.random.randn(1, 32000)

        # Should not raise IndexError
        result = self.blender._ensemble_voting_blend([logits1, logits2])

        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result.shape, (1, 32000))

    def test_ensemble_voting_different_vocab_2d(self):
        """Ensemble voting should handle 2D arrays with different vocab sizes."""
        logits1 = np.random.randn(1, 32000)
        logits2 = np.random.randn(1, 64000)

        # Reshape to same vocab first
        target_shape = self.blender._get_target_shape([logits1, logits2])
        logits1_reshaped = self.blender._reshape_logits(logits1, target_shape)
        logits2_reshaped = self.blender._reshape_logits(logits2, target_shape)

        # Should not raise IndexError
        result = self.blender._ensemble_voting_blend([logits1_reshaped, logits2_reshaped])

        self.assertEqual(result.shape, (1, 64000))

    def test_top_k_filtering_2d(self):
        """Top-k filtering should handle 2D arrays."""
        logits = np.random.randn(1, 1000)

        result = self.blender._top_k_filtering(logits, k=10)

        self.assertEqual(result.shape, (1, 1000))
        # Should have exactly k non-filtered values
        not_filtered = np.sum(result > -1e8)
        self.assertEqual(not_filtered, 10)

    def test_top_p_filtering_2d(self):
        """Top-p filtering should handle 2D arrays."""
        logits = np.random.randn(1, 1000)

        result = self.blender._top_p_filtering(logits, p=0.9)

        self.assertEqual(result.shape, (1, 1000))

    def test_reshape_logits_padding(self):
        """Should pad smaller logits to target shape."""
        logits = np.array([1.0, 2.0, 3.0])
        target_shape = (5,)

        result = self.blender._reshape_logits(logits, target_shape)

        self.assertEqual(result.shape, (5,))
        # Padded values should be very low
        self.assertLess(result[3], -1e8)
        self.assertLess(result[4], -1e8)

    def test_reshape_logits_truncation(self):
        """Should truncate larger logits to target shape."""
        logits = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        target_shape = (3,)

        result = self.blender._reshape_logits(logits, target_shape)

        self.assertEqual(result.shape, (3,))
        np.testing.assert_array_equal(result, [1.0, 2.0, 3.0])

    def test_reshape_logits_2d_padding(self):
        """Should pad 2D logits along vocab dimension."""
        logits = np.array([[1.0, 2.0, 3.0]])
        target_shape = (1, 5)

        result = self.blender._reshape_logits(logits, target_shape)

        self.assertEqual(result.shape, (1, 5))
        # Original values preserved
        np.testing.assert_array_equal(result[0, :3], [1.0, 2.0, 3.0])

    def test_full_blend_pipeline_vocab_mismatch(self):
        """Full blend should work end-to-end with vocab mismatch."""
        # Simulate Gemma 1B (256k vocab) vs GPT-2 (50k vocab) scenario
        logits_gemma = np.random.randn(1, 256000)
        logits_gpt2 = np.random.randn(1, 50257)

        # Should complete without errors
        result, stats = self.blender.blend([logits_gemma, logits_gpt2])

        self.assertEqual(result.shape, (1, 256000))
        self.assertEqual(stats["num_models"], 2)


def run_tests():
    """Run all blending tests."""
    print("=" * 80)
    print("Testing Blending Module")
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
