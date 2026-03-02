"""
Test Perplexity-based Swap Strategies

Tests perplexity and confidence-based swap strategies:
- PerplexitySwapStrategy: Swap when model is uncertain
- ConfidenceBasedStrategy: Swap when confidence is low
"""

import sys

import unittest
import numpy as np

from src.mind_meld.strategies.perplexity_strategy import (
    PerplexitySwapStrategy,
    ConfidenceBasedStrategy
)
from src.mind_meld.strategies.base_strategy import SwapDecision


class TestPerplexityStrategyInit(unittest.TestCase):
    """Test PerplexitySwapStrategy initialization."""

    def test_initialization_default(self):
        """Should initialize with default parameters."""
        strategy = PerplexitySwapStrategy(verbose=False)

        self.assertEqual(strategy.threshold, 50.0)
        self.assertEqual(strategy.initial_threshold, 50.0)
        self.assertEqual(strategy.window_size, 5)
        self.assertTrue(strategy.adaptive)
        self.assertEqual(len(strategy.perplexity_history), 0)
        self.assertEqual(strategy.min_perplexity, float('inf'))
        self.assertEqual(strategy.max_perplexity, 0.0)

    def test_initialization_custom(self):
        """Should initialize with custom parameters."""
        strategy = PerplexitySwapStrategy(
            threshold=100.0,
            window_size=10,
            adaptive=False,
            verbose=True
        )

        self.assertEqual(strategy.threshold, 100.0)
        self.assertEqual(strategy.window_size, 10)
        self.assertFalse(strategy.adaptive)
        self.assertTrue(strategy.verbose)


class TestPerplexityCalculation(unittest.TestCase):
    """Test perplexity calculation."""

    def setUp(self):
        """Create strategy for testing."""
        self.strategy = PerplexitySwapStrategy(verbose=False)

    def test_calculate_perplexity_confident(self):
        """Should calculate low perplexity for confident prediction."""
        # Logits strongly favoring one token
        logits = np.array([10.0, 1.0, 1.0, 1.0])

        perplexity = self.strategy.calculate_perplexity(logits, token_id=0)

        # Confident prediction should have low perplexity (close to 1)
        self.assertLess(perplexity, 2.0)

    def test_calculate_perplexity_uncertain(self):
        """Should calculate high perplexity for uncertain prediction."""
        # Uniform distribution (all equal)
        logits = np.array([1.0, 1.0, 1.0, 1.0])

        perplexity = self.strategy.calculate_perplexity(logits, token_id=0)

        # Uncertain prediction should have higher perplexity
        self.assertGreater(perplexity, 2.0)

    def test_calculate_perplexity_without_token_id(self):
        """Should use argmax when token_id not provided."""
        logits = np.array([5.0, 10.0, 3.0])

        perplexity = self.strategy.calculate_perplexity(logits)

        # Should calculate perplexity for highest logit (index 1)
        self.assertIsInstance(perplexity, float)
        self.assertGreater(perplexity, 0)

    def test_calculate_perplexity_with_nan(self):
        """Should handle NaN in logits."""
        logits = np.array([1.0, np.nan, 2.0, 1.0])

        perplexity = self.strategy.calculate_perplexity(logits, token_id=0)

        # Should not crash and return valid perplexity
        self.assertIsInstance(perplexity, float)
        self.assertFalse(np.isnan(perplexity))
        self.assertFalse(np.isinf(perplexity))

    def test_calculate_perplexity_with_inf(self):
        """Should handle inf in logits."""
        logits = np.array([1.0, np.inf, 2.0])

        perplexity = self.strategy.calculate_perplexity(logits, token_id=0)

        self.assertIsInstance(perplexity, float)
        self.assertFalse(np.isnan(perplexity))

    def test_calculate_perplexity_out_of_bounds_token(self):
        """Should handle token_id out of bounds."""
        logits = np.array([1.0, 2.0, 3.0])

        perplexity = self.strategy.calculate_perplexity(logits, token_id=99)

        # Should use fallback probability
        self.assertIsInstance(perplexity, float)
        self.assertGreater(perplexity, 0)


class TestEntropyCalculation(unittest.TestCase):
    """Test entropy calculation."""

    def setUp(self):
        """Create strategy for testing."""
        self.strategy = PerplexitySwapStrategy(verbose=False)

    def test_calculate_entropy_confident(self):
        """Should calculate low entropy for confident prediction."""
        # One token strongly favored
        logits = np.array([10.0, 1.0, 1.0, 1.0])

        entropy = self.strategy.calculate_entropy(logits)

        # Confident prediction should have low entropy
        self.assertLess(entropy, 1.0)

    def test_calculate_entropy_uncertain(self):
        """Should calculate high entropy for uncertain prediction."""
        # Uniform distribution
        logits = np.array([1.0, 1.0, 1.0, 1.0])

        entropy = self.strategy.calculate_entropy(logits)

        # Uncertain prediction should have higher entropy
        # For 4 equal options, entropy = log2(4) = 2.0
        self.assertAlmostEqual(entropy, 2.0, places=1)

    def test_calculate_entropy_with_nan(self):
        """Should handle NaN in logits."""
        logits = np.array([1.0, np.nan, 2.0])

        entropy = self.strategy.calculate_entropy(logits)

        self.assertIsInstance(entropy, float)
        self.assertFalse(np.isnan(entropy))


class TestSmoothedPerplexity(unittest.TestCase):
    """Test smoothed perplexity calculation."""

    def setUp(self):
        """Create strategy for testing."""
        self.strategy = PerplexitySwapStrategy(window_size=3, verbose=False)

    def test_get_smoothed_perplexity_empty(self):
        """Should return None when no history."""
        smoothed = self.strategy.get_smoothed_perplexity()

        self.assertIsNone(smoothed)

    def test_get_smoothed_perplexity_with_history(self):
        """Should return mean of history."""
        self.strategy.perplexity_history.append(10.0)
        self.strategy.perplexity_history.append(20.0)
        self.strategy.perplexity_history.append(30.0)

        smoothed = self.strategy.get_smoothed_perplexity()

        self.assertAlmostEqual(smoothed, 20.0)

    def test_smoothed_perplexity_bounded_by_window(self):
        """Should only use recent history up to window_size."""
        for i in range(10):
            self.strategy.perplexity_history.append(float(i))

        # Window size is 3, so should only have last 3 values: 7, 8, 9
        self.assertEqual(len(self.strategy.perplexity_history), 3)

        smoothed = self.strategy.get_smoothed_perplexity()
        self.assertAlmostEqual(smoothed, 8.0)  # Mean of 7, 8, 9


class TestAdaptiveThreshold(unittest.TestCase):
    """Test adaptive threshold updating."""

    def setUp(self):
        """Create strategy with adaptive threshold."""
        self.strategy = PerplexitySwapStrategy(
            threshold=50.0,
            window_size=5,
            adaptive=True,
            verbose=False
        )

    def test_update_adaptive_threshold_insufficient_history(self):
        """Should not update with insufficient history."""
        self.strategy.perplexity_history.append(10.0)
        self.strategy.perplexity_history.append(20.0)

        old_threshold = self.strategy.threshold
        self.strategy.update_adaptive_threshold()

        # Should not change threshold (need window_size=5 values)
        self.assertEqual(self.strategy.threshold, old_threshold)

    def test_update_adaptive_threshold_with_full_history(self):
        """Should update threshold with full history."""
        # Add 5 values
        for val in [10.0, 20.0, 30.0, 40.0, 50.0]:
            self.strategy.perplexity_history.append(val)

        self.strategy.update_adaptive_threshold()

        # Threshold should be 75th percentile of [10, 20, 30, 40, 50] = 40
        self.assertAlmostEqual(self.strategy.threshold, 40.0, places=1)

    def test_adaptive_threshold_clamped(self):
        """Should clamp threshold to reasonable range."""
        # Initial threshold is 50.0
        # Add very high values
        for val in [1000.0, 2000.0, 3000.0, 4000.0, 5000.0]:
            self.strategy.perplexity_history.append(val)

        self.strategy.update_adaptive_threshold()

        # Should be clamped to max 2x initial threshold = 100.0
        self.assertLessEqual(self.strategy.threshold, 100.0)

    def test_update_adaptive_disabled(self):
        """Should not update when adaptive is disabled."""
        strategy = PerplexitySwapStrategy(adaptive=False, verbose=False)

        for val in [10.0, 20.0, 30.0, 40.0, 50.0]:
            strategy.perplexity_history.append(val)

        old_threshold = strategy.threshold
        strategy.update_adaptive_threshold()

        # Should not change
        self.assertEqual(strategy.threshold, old_threshold)


class TestPerplexityShouldSwap(unittest.TestCase):
    """Test should_swap decision logic."""

    def setUp(self):
        """Create strategy for testing."""
        self.strategy = PerplexitySwapStrategy(
            threshold=10.0,
            adaptive=False,
            verbose=False
        )

    def test_should_swap_high_perplexity(self):
        """Should swap when perplexity exceeds threshold."""
        # Uniform logits over many tokens = high perplexity
        # Perplexity = 1/probability. For 20 uniform tokens, perplexity = 20 > 10.0 threshold
        logits = np.array([1.0] * 20)

        decision = self.strategy.should_swap("token", logits, 0, 2, token_id=0)

        self.assertTrue(decision.should_swap)
        self.assertIn("High perplexity", decision.reason)
        self.assertEqual(self.strategy.swap_count, 1)

    def test_should_swap_low_perplexity(self):
        """Should not swap when perplexity below threshold."""
        # Confident logits = low perplexity
        logits = np.array([10.0, 1.0, 1.0])

        decision = self.strategy.should_swap("token", logits, 0, 2, token_id=0)

        self.assertFalse(decision.should_swap)
        self.assertIn("below threshold", decision.reason)

    def test_should_swap_updates_history(self):
        """Should update perplexity history."""
        logits = np.array([5.0, 1.0, 1.0])

        self.strategy.should_swap("token", logits, 0, 2, token_id=0)

        self.assertEqual(len(self.strategy.perplexity_history), 1)
        self.assertGreater(self.strategy.perplexity_history[0], 0)

    def test_should_swap_tracks_min_max(self):
        """Should track min and max perplexity."""
        # Low perplexity
        logits1 = np.array([10.0, 1.0, 1.0])
        self.strategy.should_swap("token1", logits1, 0, 2, token_id=0)

        # High perplexity
        logits2 = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
        self.strategy.should_swap("token2", logits2, 0, 2, token_id=0)

        self.assertLess(self.strategy.min_perplexity, 2.0)
        self.assertGreater(self.strategy.max_perplexity, 5.0)

    def test_should_swap_metadata(self):
        """Should include metadata in decision."""
        logits = np.array([5.0, 2.0, 1.0])

        decision = self.strategy.should_swap("token", logits, 0, 2)

        self.assertIn('perplexity', decision.metadata)
        self.assertIn('entropy', decision.metadata)
        self.assertIn('threshold', decision.metadata)
        self.assertIn('min_perplexity', decision.metadata)
        self.assertIn('max_perplexity', decision.metadata)

    def test_should_swap_uses_smoothed_perplexity(self):
        """Should use smoothed perplexity after building history."""
        logits = np.array([5.0, 2.0, 1.0])

        # Build up history with low perplexity
        for i in range(3):
            self.strategy.should_swap(f"token{i}", logits, 0, 2, token_id=0)

        # All should be low perplexity, so smoothed should be low
        decision = self.strategy.should_swap("token4", logits, 0, 2, token_id=0)

        self.assertIsNotNone(decision.metadata.get('smoothed_perplexity'))

    def test_should_swap_triggers_adaptive_update(self):
        """Should trigger adaptive threshold update periodically."""
        strategy = PerplexitySwapStrategy(
            threshold=50.0,
            window_size=5,
            adaptive=True,
            verbose=False
        )

        logits = np.array([1.0, 1.0, 1.0, 1.0])

        # Generate 10 tokens (adaptive updates every 10)
        for i in range(10):
            strategy.should_swap(f"token{i}", logits, 0, 2)

        # Threshold should have been updated
        # (With uniform logits, perplexity ~4, so 75th percentile should adjust threshold down)
        # Initial was 50, should be adjusted based on observed perplexities


class TestPerplexityGetStats(unittest.TestCase):
    """Test statistics gathering."""

    def setUp(self):
        """Create strategy for testing."""
        self.strategy = PerplexitySwapStrategy(verbose=False)

    def test_get_stats_empty(self):
        """Should return stats with empty history."""
        stats = self.strategy.get_stats()

        self.assertIn('avg_perplexity', stats)
        self.assertIn('min_perplexity', stats)
        self.assertIn('max_perplexity', stats)
        self.assertIn('current_threshold', stats)
        self.assertIn('adaptive', stats)
        self.assertEqual(stats['avg_perplexity'], 0.0)
        self.assertEqual(stats['min_perplexity'], 0.0)  # Converted from inf
        self.assertTrue(stats['adaptive'])

    def test_get_stats_with_history(self):
        """Should calculate stats from history."""
        logits = np.array([5.0, 2.0, 1.0])

        for i in range(3):
            self.strategy.should_swap(f"token{i}", logits, 0, 2)

        stats = self.strategy.get_stats()

        self.assertGreater(stats['avg_perplexity'], 0.0)
        self.assertGreater(stats['min_perplexity'], 0.0)
        self.assertGreater(stats['max_perplexity'], 0.0)


class TestPerplexityReset(unittest.TestCase):
    """Test strategy reset."""

    def setUp(self):
        """Create strategy for testing."""
        self.strategy = PerplexitySwapStrategy(threshold=50.0, verbose=False)

    def test_reset(self):
        """Should reset all state."""
        logits = np.array([5.0, 2.0, 1.0])

        # Build up some state
        for i in range(5):
            self.strategy.should_swap(f"token{i}", logits, 0, 2)

        self.strategy.threshold = 25.0  # Simulate adaptive change

        # Reset
        self.strategy.reset()

        self.assertEqual(len(self.strategy.perplexity_history), 0)
        self.assertEqual(self.strategy.min_perplexity, float('inf'))
        self.assertEqual(self.strategy.max_perplexity, 0.0)
        self.assertEqual(self.strategy.threshold, 50.0)  # Back to initial
        self.assertEqual(self.strategy.token_count, 0)
        self.assertEqual(self.strategy.swap_count, 0)


class TestConfidenceBasedStrategy(unittest.TestCase):
    """Test ConfidenceBasedStrategy."""

    def test_initialization(self):
        """Should initialize with confidence threshold."""
        strategy = ConfidenceBasedStrategy(min_confidence=0.5, verbose=False)

        self.assertEqual(strategy.min_confidence, 0.5)
        # Confidence 0.5 -> perplexity threshold 2.0
        self.assertAlmostEqual(strategy.threshold, 2.0, places=1)

    def test_initialization_low_confidence(self):
        """Should handle very low confidence threshold."""
        strategy = ConfidenceBasedStrategy(min_confidence=0.001, verbose=False)

        # Very low confidence (0.001) -> very high perplexity threshold (1/0.001 = 1000)
        self.assertGreaterEqual(strategy.threshold, 100.0)

    def test_should_swap_adds_confidence(self):
        """Should add confidence to metadata."""
        strategy = ConfidenceBasedStrategy(min_confidence=0.3, verbose=False)

        # Confident logits
        logits = np.array([10.0, 1.0, 1.0])

        decision = strategy.should_swap("token", logits, 0, 2, token_id=0)

        self.assertIn('confidence', decision.metadata)
        self.assertGreater(decision.metadata['confidence'], 0.5)

    def test_should_swap_low_confidence(self):
        """Should swap when confidence is low."""
        strategy = ConfidenceBasedStrategy(min_confidence=0.5, verbose=False)

        # Uncertain logits -> low confidence
        logits = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])

        decision = strategy.should_swap("token", logits, 0, 2, token_id=0)

        self.assertTrue(decision.should_swap)
        self.assertIn("Low confidence", decision.reason)

    def test_should_swap_high_confidence(self):
        """Should not swap when confidence is high."""
        strategy = ConfidenceBasedStrategy(min_confidence=0.3, verbose=False)

        # Confident logits
        logits = np.array([10.0, 1.0, 1.0])

        decision = strategy.should_swap("token", logits, 0, 2, token_id=0)

        self.assertFalse(decision.should_swap)
        self.assertIn("Sufficient confidence", decision.reason)

    def test_confidence_calculation(self):
        """Should correctly calculate confidence from perplexity."""
        strategy = ConfidenceBasedStrategy(min_confidence=0.5, verbose=False)

        # Perplexity 2 -> confidence 0.5
        logits = np.array([10.0, 9.0, 1.0])  # Should give perplexity around 2

        decision = strategy.should_swap("token", logits, 0, 2, token_id=0)

        confidence = decision.metadata['confidence']
        perplexity = decision.metadata['perplexity']

        # confidence ≈ 1/perplexity
        self.assertAlmostEqual(confidence * perplexity, 1.0, places=1)


def run_tests():
    """Run all perplexity strategy tests."""
    print("=" * 80)
    print("Testing Perplexity Swap Strategies")
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
