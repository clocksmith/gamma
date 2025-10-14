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
