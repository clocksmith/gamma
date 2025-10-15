"""
Test Mind Meld Swap Strategies

Tests that newly exposed strategies can be imported and instantiated:
- ConfidenceBasedStrategy
- SyntacticRoleStrategy
- PerplexitySwapStrategy
- SemanticSimilarityStrategy
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest

from src.mind_meld.strategies import (
    ConfidenceBasedStrategy,
    SyntacticRoleStrategy,
    PerplexitySwapStrategy,
    SemanticSimilarityStrategy,
    SwapStrategyBase
)
from src.mind_meld.strategies.base_strategy import (
    SwapDecision,
    FixedIntervalStrategy,
    PatternBasedStrategy,
    RoundRobinStrategy,
    RandomStrategy
)
import numpy as np


class TestSwapDecision(unittest.TestCase):
    """Test SwapDecision data class."""

    def test_swap_decision_creation(self):
        """Should create SwapDecision with all fields."""
        decision = SwapDecision(
            should_swap=True,
            reason='test reason',
            confidence=0.9,
            metadata={'key': 'value'}
        )

        self.assertTrue(decision.should_swap)
        self.assertEqual(decision.reason, 'test reason')
        self.assertEqual(decision.confidence, 0.9)
        self.assertEqual(decision.metadata, {'key': 'value'})

    def test_swap_decision_default_metadata(self):
        """Should initialize metadata as empty dict by default."""
        decision = SwapDecision(should_swap=False, reason='no swap')

        self.assertIsNotNone(decision.metadata)
        self.assertIsInstance(decision.metadata, dict)
        self.assertEqual(len(decision.metadata), 0)


class TestFixedIntervalStrategy(unittest.TestCase):
    """Test FixedIntervalStrategy."""

    def test_fixed_interval_initialization(self):
        """Should initialize with interval parameter."""
        strategy = FixedIntervalStrategy(interval=5, verbose=False)
        self.assertEqual(strategy.interval, 5)
        self.assertEqual(strategy.counter, 0)

    def test_fixed_interval_swaps_at_interval(self):
        """Should swap at fixed intervals."""
        strategy = FixedIntervalStrategy(interval=3, verbose=False)

        logits = np.array([0.1, 0.9])

        # First token - no swap
        decision1 = strategy.should_swap('token1', logits, 0, 2)
        self.assertFalse(decision1.should_swap)

        # Second token - no swap
        decision2 = strategy.should_swap('token2', logits, 0, 2)
        self.assertFalse(decision2.should_swap)

        # Third token - should swap
        decision3 = strategy.should_swap('token3', logits, 0, 2)
        self.assertTrue(decision3.should_swap)
        self.assertIn('interval', decision3.reason.lower())
        self.assertEqual(strategy.swap_count, 1)

    def test_fixed_interval_resets_counter(self):
        """Should reset counter after swap."""
        strategy = FixedIntervalStrategy(interval=2, verbose=False)
        logits = np.array([0.1, 0.9])

        strategy.should_swap('token1', logits, 0, 2)
        strategy.should_swap('token2', logits, 0, 2)  # Swaps, resets counter

        self.assertEqual(strategy.counter, 0)

    def test_fixed_interval_reset(self):
        """Should reset strategy state."""
        strategy = FixedIntervalStrategy(interval=2, verbose=False)
        logits = np.array([0.1, 0.9])

        strategy.should_swap('token1', logits, 0, 2)
        strategy.swap_count = 5
        strategy.token_count = 10

        strategy.reset()

        self.assertEqual(strategy.counter, 0)
        self.assertEqual(strategy.swap_count, 0)
        self.assertEqual(strategy.token_count, 0)

    def test_fixed_interval_verbose_logging(self):
        """Should log when verbose is enabled."""
        strategy = FixedIntervalStrategy(interval=1, verbose=True)
        logits = np.array([0.1, 0.9])

        # This should log, but we can't easily capture output - just verify it doesn't crash
        decision = strategy.should_swap('token1', logits, 0, 2)
        self.assertTrue(decision.should_swap)


class TestPatternBasedStrategy(unittest.TestCase):
    """Test PatternBasedStrategy."""

    def test_pattern_initialization(self):
        """Should initialize with default patterns."""
        strategy = PatternBasedStrategy(verbose=False)
        self.assertIsNotNone(strategy.patterns)
        self.assertIn('.', strategy.patterns)
        self.assertIn('!', strategy.patterns)

    def test_pattern_custom_patterns(self):
        """Should accept custom patterns."""
        custom_patterns = ['###', '***']
        strategy = PatternBasedStrategy(patterns=custom_patterns, verbose=False)
        self.assertEqual(strategy.patterns, custom_patterns)

    def test_pattern_detects_punctuation(self):
        """Should detect punctuation patterns."""
        strategy = PatternBasedStrategy(verbose=False)
        logits = np.array([0.1, 0.9])

        # Token with period
        decision = strategy.should_swap('word.', logits, 0, 2)
        self.assertTrue(decision.should_swap)
        self.assertIn('pattern', decision.reason.lower())
        self.assertIn('.', decision.metadata['pattern'])

    def test_pattern_no_match(self):
        """Should not swap when no pattern matches."""
        strategy = PatternBasedStrategy(patterns=['###'], verbose=False)
        logits = np.array([0.1, 0.9])

        decision = strategy.should_swap('normalword', logits, 0, 2)
        self.assertFalse(decision.should_swap)

    def test_pattern_multiple_patterns(self):
        """Should detect any matching pattern."""
        strategy = PatternBasedStrategy(patterns=['.', '!', '?'], verbose=False)
        logits = np.array([0.1, 0.9])

        decision1 = strategy.should_swap('sentence!', logits, 0, 2)
        self.assertTrue(decision1.should_swap)

        decision2 = strategy.should_swap('question?', logits, 0, 2)
        self.assertTrue(decision2.should_swap)


class TestRoundRobinStrategy(unittest.TestCase):
    """Test RoundRobinStrategy."""

    def test_round_robin_always_swaps(self):
        """Should swap on every token."""
        strategy = RoundRobinStrategy(verbose=False)
        logits = np.array([0.1, 0.9])

        for i in range(5):
            decision = strategy.should_swap(f'token{i}', logits, 0, 2)
            self.assertTrue(decision.should_swap)
            self.assertIn('round-robin', decision.reason.lower())

        self.assertEqual(strategy.swap_count, 5)


class TestRandomStrategy(unittest.TestCase):
    """Test RandomStrategy."""

    def test_random_initialization(self):
        """Should initialize with probability parameter."""
        strategy = RandomStrategy(probability=0.5, verbose=False)
        self.assertEqual(strategy.probability, 0.5)

    def test_random_swaps_probabilistically(self):
        """Should swap based on probability."""
        # Use deterministic seed for testing
        np.random.seed(42)

        strategy = RandomStrategy(probability=1.0, verbose=False)  # Always swap
        logits = np.array([0.1, 0.9])

        decision = strategy.should_swap('token', logits, 0, 2)
        self.assertTrue(decision.should_swap)
        self.assertIn('random', decision.reason.lower())

    def test_random_no_swap_when_threshold_not_met(self):
        """Should not swap when random value exceeds probability."""
        np.random.seed(42)

        strategy = RandomStrategy(probability=0.0, verbose=False)  # Never swap
        logits = np.array([0.1, 0.9])

        decision = strategy.should_swap('token', logits, 0, 2)
        self.assertFalse(decision.should_swap)


class TestSwapStrategyBase(unittest.TestCase):
    """Test base strategy methods."""

    def test_reset_clears_state(self):
        """Should clear all strategy state."""
        strategy = FixedIntervalStrategy(interval=2)
        strategy.swap_count = 10
        strategy.token_count = 20
        strategy.history = [{'token': 'test'}]

        strategy.reset()

        self.assertEqual(strategy.swap_count, 0)
        self.assertEqual(strategy.token_count, 0)
        self.assertEqual(len(strategy.history), 0)

    def test_update_history(self):
        """Should update generation history."""
        strategy = FixedIntervalStrategy(interval=5)

        strategy.update_history('token1', {'confidence': 0.9})
        strategy.update_history('token2', {'confidence': 0.8})

        self.assertEqual(len(strategy.history), 2)
        self.assertEqual(strategy.token_count, 2)
        self.assertEqual(strategy.history[0]['token'], 'token1')
        self.assertEqual(strategy.history[1]['token'], 'token2')

    def test_update_history_bounds_size(self):
        """Should keep history bounded."""
        strategy = FixedIntervalStrategy(interval=5)

        # Add 150 tokens
        for i in range(150):
            strategy.update_history(f'token{i}', {'idx': i})

        # Should only keep last 100
        self.assertEqual(len(strategy.history), 100)
        self.assertEqual(strategy.history[0]['metadata']['idx'], 50)
        self.assertEqual(strategy.history[-1]['metadata']['idx'], 149)

    def test_get_stats(self):
        """Should return strategy statistics."""
        strategy = FixedIntervalStrategy(interval=2)
        logits = np.array([0.1, 0.9])

        # Generate some swaps
        for i in range(6):
            strategy.should_swap(f'token{i}', logits, 0, 2)
            strategy.update_history(f'token{i}', {'idx': i})

        stats = strategy.get_stats()

        self.assertIn('swap_count', stats)
        self.assertIn('token_count', stats)
        self.assertIn('swap_rate', stats)
        self.assertEqual(stats['token_count'], 6)
        self.assertEqual(stats['swap_count'], 3)  # Swaps at positions 2, 4, 6
        self.assertEqual(stats['swap_rate'], 3 / 6)

    def test_log_with_verbose_disabled(self):
        """Should not log when verbose is False."""
        strategy = FixedIntervalStrategy(interval=1, verbose=False)
        # _log is called internally - just verify it doesn't crash
        logits = np.array([0.1, 0.9])
        strategy.should_swap('token', logits, 0, 2)

    def test_base_should_swap_abstract_method(self):
        """Base class should_swap should be callable (abstract with pass)."""
        # Create a minimal concrete strategy for testing
        strategy = FixedIntervalStrategy(interval=1)
        logits = np.array([0.1, 0.9])

        # Call the base class method directly to cover the pass statement
        result = SwapStrategyBase.should_swap(strategy, 'token', logits, 0, 2)

        # Since it's just 'pass', it returns None
        self.assertIsNone(result)


class TestConfidenceBasedStrategy(unittest.TestCase):
    """Test confidence-based swapping strategy."""

    def test_instantiation(self):
        """Strategy should be instantiatable with min_confidence."""
        strategy = ConfidenceBasedStrategy(min_confidence=0.7)
        self.assertIsNotNone(strategy)
        self.assertTrue(hasattr(strategy, 'should_swap'))

    def test_default_parameters(self):
        """Strategy should work with default parameters."""
        strategy = ConfidenceBasedStrategy()
        self.assertIsNotNone(strategy)

    def test_custom_threshold(self):
        """Should accept custom confidence threshold."""
        strategy = ConfidenceBasedStrategy(min_confidence=0.9)
        self.assertIsNotNone(strategy)
        # Confidence translates to perplexity threshold
        self.assertTrue(hasattr(strategy, 'threshold'))


class TestSyntacticRoleStrategy(unittest.TestCase):
    """Test syntactic role-based swapping strategy."""

    def test_instantiation(self):
        """Strategy should be instantiatable with role_mapping."""
        strategy = SyntacticRoleStrategy(role_mapping={'NOUN': 1, 'VERB': 0})
        self.assertIsNotNone(strategy)
        self.assertTrue(hasattr(strategy, 'should_swap'))

    def test_default_role_mapping(self):
        """Strategy should have default role mapping."""
        strategy = SyntacticRoleStrategy()
        self.assertIsNotNone(strategy)
        self.assertTrue(hasattr(strategy, 'role_mapping'))
        self.assertIsInstance(strategy.role_mapping, dict)

    def test_custom_role_mapping(self):
        """Should accept custom role mapping."""
        custom_mapping = {'ADJ': 0, 'NOUN': 1, 'VERB': 0, 'PUNCT': 1}
        strategy = SyntacticRoleStrategy(role_mapping=custom_mapping)
        self.assertEqual(strategy.role_mapping, custom_mapping)


class TestPerplexitySwapStrategy(unittest.TestCase):
    """Test perplexity-based swapping strategy."""

    def test_instantiation(self):
        """Strategy should be instantiatable with threshold."""
        strategy = PerplexitySwapStrategy(threshold=10.0)
        self.assertIsNotNone(strategy)
        self.assertTrue(hasattr(strategy, 'should_swap'))

    def test_default_threshold(self):
        """Strategy should work with default threshold."""
        strategy = PerplexitySwapStrategy()
        self.assertIsNotNone(strategy)
        self.assertTrue(hasattr(strategy, 'threshold'))

    def test_custom_threshold(self):
        """Should accept custom perplexity threshold."""
        strategy = PerplexitySwapStrategy(threshold=5.0)
        self.assertEqual(strategy.threshold, 5.0)


class TestSemanticSimilarityStrategy(unittest.TestCase):
    """Test semantic similarity-based swapping strategy."""

    def test_instantiation(self):
        """Strategy should be instantiatable."""
        strategy = SemanticSimilarityStrategy()
        self.assertIsNotNone(strategy)
        self.assertTrue(hasattr(strategy, 'should_swap'))

    def test_window_size_configurable(self):
        """Should accept custom window size."""
        strategy = SemanticSimilarityStrategy(window_size=10)
        self.assertIsNotNone(strategy)
        self.assertEqual(strategy.window_size, 10)

    def test_default_window_size(self):
        """Strategy should have default window size."""
        strategy = SemanticSimilarityStrategy()
        self.assertTrue(hasattr(strategy, 'window_size'))
        self.assertGreater(strategy.window_size, 0)


class TestStrategyImports(unittest.TestCase):
    """Test that all strategies are properly exported."""

    def test_all_strategies_importable(self):
        """All strategies should be importable from strategies module."""
        from src.mind_meld.strategies import (
            SwapStrategyBase,
            ConfidenceBasedStrategy,
            SyntacticRoleStrategy,
            PerplexitySwapStrategy,
            SemanticSimilarityStrategy
        )

        # Check they're all classes
        self.assertTrue(callable(ConfidenceBasedStrategy))
        self.assertTrue(callable(SyntacticRoleStrategy))
        self.assertTrue(callable(PerplexitySwapStrategy))
        self.assertTrue(callable(SemanticSimilarityStrategy))

    def test_strategies_have_should_swap(self):
        """All strategies should implement should_swap method."""
        from src.mind_meld.strategies import (
            ConfidenceBasedStrategy,
            SyntacticRoleStrategy
        )

        confidence = ConfidenceBasedStrategy(min_confidence=0.7)
        syntactic = SyntacticRoleStrategy(role_mapping={'NOUN': 1})

        self.assertTrue(hasattr(confidence, 'should_swap'))
        self.assertTrue(hasattr(syntactic, 'should_swap'))
        self.assertTrue(callable(confidence.should_swap))
        self.assertTrue(callable(syntactic.should_swap))


def run_tests():
    """Run all strategy tests."""
    print("=" * 80)
    print("Testing Mind Meld Swap Strategies")
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
