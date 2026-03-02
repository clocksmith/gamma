"""
Test ABE Ensemble

Tests Agreement-Based Ensembling:
- ABECandidate dataclass
- ABEEnsemble initialization and agreement finding
- Text agreement checking
- Best match finding
- Position updates and stalling
- Full ensemble steps
"""

import sys

import unittest
from unittest.mock import Mock, MagicMock
import numpy as np

from src.mind_meld.core.abe_ensemble import ABECandidate, ABEEnsemble


class MockModel:
    """Mock model for testing."""
    def decode(self, token_ids, skip_special_tokens=True):
        # Simple mapping for testing
        token_map = {
            0: "",
            1: "the",
            2: " the",
            3: "cat",
            4: " cat",
            5: "dog",
            6: "hello",
            7: "world",
        }
        if len(token_ids) == 1:
            return token_map.get(token_ids[0], "")
        return ""


class TestABECandidate(unittest.TestCase):
    """Test ABECandidate dataclass."""

    def test_initialization(self):
        """Should initialize with all fields."""
        candidate = ABECandidate(
            model_tokens=[(1, "the"), (2, " the")],
            combined_score=0.8,
            agreed_text="the",
            is_complete=False
        )

        self.assertEqual(len(candidate.model_tokens), 2)
        self.assertEqual(candidate.combined_score, 0.8)
        self.assertEqual(candidate.agreed_text, "the")
        self.assertFalse(candidate.is_complete)


class TestABEEnsemble(unittest.TestCase):
    """Test ABEEnsemble class."""

    def setUp(self):
        """Set up test models."""
        self.model1 = MockModel()
        self.model2 = MockModel()
        self.models = [self.model1, self.model2]

    def test_initialization(self):
        """Should initialize with models."""
        ensemble = ABEEnsemble(self.models)

        self.assertEqual(len(ensemble.models), 2)
        self.assertEqual(len(ensemble.model_positions), 2)
        self.assertEqual(ensemble.model_positions, [0, 0])
        self.assertEqual(len(ensemble.stalled_models), 0)

    def test_initialization_verbose(self):
        """Should initialize with verbose mode."""
        ensemble = ABEEnsemble(self.models, verbose=True)

        self.assertTrue(ensemble.verbose)

    def test_check_agreement_exact_match(self):
        """Should detect exact match."""
        ensemble = ABEEnsemble(self.models)

        result = ensemble._check_agreement("the", "the")

        self.assertEqual(result, "the")

    def test_check_agreement_prefix(self):
        """Should detect when one is prefix of other."""
        ensemble = ABEEnsemble(self.models)

        # "the" is prefix of "there"
        result = ensemble._check_agreement("there", "the")
        self.assertEqual(result, "the")

        result = ensemble._check_agreement("the", "there")
        self.assertEqual(result, "the")

    def test_check_agreement_no_match(self):
        """Should return None when no agreement."""
        ensemble = ABEEnsemble(self.models)

        result = ensemble._check_agreement("cat", "dog")

        self.assertIsNone(result)

    def test_check_agreement_empty_text(self):
        """Should return None for empty text."""
        ensemble = ABEEnsemble(self.models)

        result = ensemble._check_agreement("", "the")
        self.assertIsNone(result)

        result = ensemble._check_agreement("the", "")
        self.assertIsNone(result)

    def test_check_agreement_with_whitespace(self):
        """Should handle whitespace in agreement check."""
        ensemble = ABEEnsemble(self.models)

        # " the" and "the" should agree after lstrip
        result = ensemble._check_agreement(" the", "the")
        self.assertEqual(result, "the")

    def test_find_best_match_found(self):
        """Should find best matching token."""
        ensemble = ABEEnsemble(self.models)

        token_list = [
            (1, "the", 0.5),
            (3, "cat", 0.3),
            (5, "dog", 0.2),
        ]

        result = ensemble._find_best_match("the", token_list)

        self.assertIsNotNone(result)
        self.assertEqual(result[0], 1)
        self.assertEqual(result[1], "the")

    def test_find_best_match_not_found(self):
        """Should return None when no match."""
        ensemble = ABEEnsemble(self.models)

        token_list = [
            (3, "cat", 0.3),
            (5, "dog", 0.2),
        ]

        result = ensemble._find_best_match("the", token_list)

        self.assertIsNone(result)

    def test_update_positions(self):
        """Should update model positions."""
        ensemble = ABEEnsemble(self.models)

        candidate = ABECandidate(
            model_tokens=[(1, "the"), (2, " the")],
            combined_score=0.8,
            agreed_text="the",
            is_complete=True
        )

        ensemble.update_positions(candidate)

        # Both models generated tokens with length 3/4
        self.assertEqual(ensemble.model_positions[0], 3)
        self.assertEqual(ensemble.model_positions[1], 4)

    def test_update_positions_with_stalling(self):
        """Should mark stalled models."""
        ensemble = ABEEnsemble(self.models)

        candidate = ABECandidate(
            model_tokens=[(1, "the"), (2, " the ")],  # Different lengths
            combined_score=0.8,
            agreed_text="the",
            is_complete=False
        )

        ensemble.update_positions(candidate)

        # First model generated shorter token
        self.assertIn(0, ensemble.stalled_models)

    def test_find_agreement_with_agreement(self):
        """Should find agreement between models."""
        ensemble = ABEEnsemble(self.models)

        # Create probability distributions
        probs1 = np.array([0.0, 0.7, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0])  # Prefers token 1 ("the")
        probs2 = np.array([0.0, 0.1, 0.6, 0.2, 0.1, 0.0, 0.0, 0.0])  # Prefers token 2 (" the")

        candidate = ensemble.find_agreement([probs1, probs2], temperature=1.0, top_k=5)

        self.assertIsNotNone(candidate)
        self.assertIsInstance(candidate, ABECandidate)
        self.assertGreater(candidate.combined_score, 0)

    def test_find_agreement_no_agreement(self):
        """Should fallback when no agreement found."""
        ensemble = ABEEnsemble(self.models)

        # Completely different preferences
        probs1 = np.array([0.0, 0.0, 0.0, 0.9, 0.1, 0.0, 0.0, 0.0])  # Prefers "cat"
        probs2 = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.9, 0.1, 0.0])  # Prefers "dog"

        candidate = ensemble.find_agreement([probs1, probs2], temperature=1.0, top_k=3)

        self.assertIsNotNone(candidate)
        # Should use first model's top token as fallback
        self.assertIsInstance(candidate, ABECandidate)

    def test_find_agreement_with_temperature(self):
        """Should apply temperature to probabilities."""
        ensemble = ABEEnsemble(self.models)

        probs1 = np.array([0.0, 0.7, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0])
        probs2 = np.array([0.0, 0.1, 0.6, 0.2, 0.1, 0.0, 0.0, 0.0])

        # Higher temperature should flatten distribution
        candidate = ensemble.find_agreement([probs1, probs2], temperature=2.0, top_k=5)

        self.assertIsNotNone(candidate)

    def test_ensemble_step(self):
        """Should perform full ensemble step."""
        ensemble = ABEEnsemble(self.models)

        probs1 = np.array([0.0, 0.7, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0])
        probs2 = np.array([0.0, 0.1, 0.6, 0.2, 0.1, 0.0, 0.0, 0.0])

        agreed_text, token_ids = ensemble.ensemble_step([probs1, probs2])

        self.assertIsInstance(agreed_text, str)
        self.assertIsInstance(token_ids, list)
        self.assertEqual(len(token_ids), 2)

    def test_ensemble_step_updates_positions(self):
        """Should update positions after ensemble step."""
        ensemble = ABEEnsemble(self.models)

        probs1 = np.array([0.0, 0.7, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0])
        probs2 = np.array([0.0, 0.1, 0.6, 0.2, 0.1, 0.0, 0.0, 0.0])

        initial_positions = ensemble.model_positions.copy()

        ensemble.ensemble_step([probs1, probs2])

        # Positions should have changed
        self.assertNotEqual(ensemble.model_positions, initial_positions)


def run_tests():
    """Run all ABE ensemble tests."""
    print("=" * 80)
    print("Testing ABE Ensemble")
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
