"""
Test Explanations Module

Tests user-facing explanation functions:
- explain_game_concepts: Explains GAMMA core concepts
- explain_attention: Explains attention mechanism
- explain_sampling_filters: Explains temperature, top-k, top-p
- explain_focus_words_mode: Explains focus words mode
- explain_player_choice_mode: Explains player choice mode
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import patch, MagicMock
from io import StringIO

from src.ui import explanations


class MockArgs:
    """Mock arguments object for testing."""
    def __init__(self, temperature=0.7, top_k=50, top_p=0.95,
                 verbose=False, focus_words=False, player_choice_mode=False):
        self.temperature = temperature
        self.top_k = top_k
        self.top_p = top_p
        self.verbose = verbose
        self.focus_words = focus_words
        self.player_choice_mode = player_choice_mode


class TestExplainGameConcepts(unittest.TestCase):
    """Test explain_game_concepts function."""

    def test_explain_game_concepts_basic(self):
        """Should print game concepts explanation."""
        args = MockArgs()

        with patch('sys.stdout', new=StringIO()) as fake_out:
            explanations.explain_game_concepts(args)
            output = fake_out.getvalue()

            # Check key concepts are explained
            self.assertIn("GAMMA", output)
            self.assertIn("Attention", output)
            self.assertIn("Probabilities", output)
            self.assertIn("Sampling Filters", output)
            self.assertIn("Temperature", output)
            self.assertIn("Top-K", output)
            self.assertIn("Top-P", output)

    def test_explain_game_concepts_shows_settings(self):
        """Should display current settings."""
        args = MockArgs(temperature=0.8, top_k=40, top_p=0.9)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            explanations.explain_game_concepts(args)
            output = fake_out.getvalue()

            # Check settings are displayed
            self.assertIn("0.80", output)
            self.assertIn("40", output)
            self.assertIn("0.90", output)

    def test_explain_game_concepts_verbose(self):
        """Should show additional info in verbose mode."""
        args_normal = MockArgs(verbose=False)
        args_verbose = MockArgs(verbose=True)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            explanations.explain_game_concepts(args_normal)
            output_normal = fake_out.getvalue()

        with patch('sys.stdout', new=StringIO()) as fake_out:
            explanations.explain_game_concepts(args_verbose)
            output_verbose = fake_out.getvalue()

            # Verbose should have more content
            self.assertGreater(len(output_verbose), len(output_normal))
            self.assertIn("Token Types", output_verbose)

    def test_explain_game_concepts_includes_goal(self):
        """Should include goal statement."""
        args = MockArgs()

        with patch('sys.stdout', new=StringIO()) as fake_out:
            explanations.explain_game_concepts(args)
            output = fake_out.getvalue()

            self.assertIn("Goal:", output)
            self.assertIn("intuition", output)


class TestExplainAttention(unittest.TestCase):
    """Test explain_attention function."""

    def test_explain_attention_basic(self):
        """Should print attention explanation."""
        args = MockArgs()

        with patch('sys.stdout', new=StringIO()) as fake_out:
            explanations.explain_attention(args)
            output = fake_out.getvalue()

            # Check key concepts
            self.assertIn("Attention", output)
            self.assertIn("heatmap", output)
            self.assertIn("focus", output)
            self.assertIn("normalized", output)

    def test_explain_attention_verbose(self):
        """Should show additional info in verbose mode."""
        args_normal = MockArgs(verbose=False)
        args_verbose = MockArgs(verbose=True)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            explanations.explain_attention(args_normal)
            output_normal = fake_out.getvalue()

        with patch('sys.stdout', new=StringIO()) as fake_out:
            explanations.explain_attention(args_verbose)
            output_verbose = fake_out.getvalue()

            # Verbose should have more content
            self.assertGreater(len(output_verbose), len(output_normal))
            self.assertIn("Why it matters", output_verbose)
            self.assertIn("dependencies", output_verbose)

    def test_explain_attention_mentions_context(self):
        """Should explain context importance."""
        args = MockArgs(verbose=True)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            explanations.explain_attention(args)
            output = fake_out.getvalue()

            self.assertIn("context", output.lower())


class TestExplainSamplingFilters(unittest.TestCase):
    """Test explain_sampling_filters function."""

    def test_explain_sampling_filters_basic(self):
        """Should print sampling filters explanation."""
        args = MockArgs()

        with patch('sys.stdout', new=StringIO()) as fake_out:
            explanations.explain_sampling_filters(args)
            output = fake_out.getvalue()

            # Check all three filters are explained
            self.assertIn("Temperature", output)
            self.assertIn("Top-K", output)
            self.assertIn("Top-P", output)
            self.assertIn("Nucleus", output)

    def test_explain_sampling_filters_shows_settings(self):
        """Should display current settings."""
        args = MockArgs(temperature=0.5, top_k=30, top_p=0.85)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            explanations.explain_sampling_filters(args)
            output = fake_out.getvalue()

            # Check settings are displayed
            self.assertIn("0.50", output)
            self.assertIn("30", output)
            self.assertIn("0.85", output)

    def test_explain_sampling_filters_verbose(self):
        """Should show combined effect in verbose mode."""
        args_normal = MockArgs(verbose=False)
        args_verbose = MockArgs(verbose=True)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            explanations.explain_sampling_filters(args_normal)
            output_normal = fake_out.getvalue()

        with patch('sys.stdout', new=StringIO()) as fake_out:
            explanations.explain_sampling_filters(args_verbose)
            output_verbose = fake_out.getvalue()

            # Verbose should have more content
            self.assertGreater(len(output_verbose), len(output_normal))
            self.assertIn("Combined Effect", output_verbose)

    def test_explain_sampling_filters_explains_temperature(self):
        """Should explain temperature effects."""
        args = MockArgs()

        with patch('sys.stdout', new=StringIO()) as fake_out:
            explanations.explain_sampling_filters(args)
            output = fake_out.getvalue()

            self.assertIn("deterministic", output.lower())
            self.assertIn("random", output.lower())


class TestExplainFocusWordsMode(unittest.TestCase):
    """Test explain_focus_words_mode function."""

    def test_explain_focus_words_mode_disabled(self):
        """Should not print anything when focus_words is False."""
        args = MockArgs(focus_words=False)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            explanations.explain_focus_words_mode(args)
            output = fake_out.getvalue()

            # Should be empty
            self.assertEqual(output.strip(), "")

    def test_explain_focus_words_mode_enabled(self):
        """Should print explanation when focus_words is True."""
        args = MockArgs(focus_words=True)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            explanations.explain_focus_words_mode(args)
            output = fake_out.getvalue()

            # Should have content
            self.assertGreater(len(output), 0)
            self.assertIn("Focus Words", output)

    def test_explain_focus_words_mode_explains_filtering(self):
        """Should explain word token filtering."""
        args = MockArgs(focus_words=True)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            explanations.explain_focus_words_mode(args)
            output = fake_out.getvalue()

            self.assertIn("word tokens", output)
            self.assertIn("punctuation", output)

    def test_explain_focus_words_mode_mentions_config(self):
        """Should mention minimum word token length from config."""
        args = MockArgs(focus_words=True)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            explanations.explain_focus_words_mode(args)
            output = fake_out.getvalue()

            # Should mention the config constant
            self.assertIn("minimum length", output.lower())


class TestExplainPlayerChoiceMode(unittest.TestCase):
    """Test explain_player_choice_mode function."""

    def test_explain_player_choice_mode_disabled(self):
        """Should not print anything when player_choice_mode is False."""
        args = MockArgs(player_choice_mode=False)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            explanations.explain_player_choice_mode(args)
            output = fake_out.getvalue()

            # Should be empty
            self.assertEqual(output.strip(), "")

    def test_explain_player_choice_mode_enabled(self):
        """Should print explanation when player_choice_mode is True."""
        args = MockArgs(player_choice_mode=True)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            explanations.explain_player_choice_mode(args)
            output = fake_out.getvalue()

            # Should have content
            self.assertGreater(len(output), 0)
            self.assertIn("Player Choice", output)

    def test_explain_player_choice_mode_explains_mechanics(self):
        """Should explain correct guess continuation."""
        args = MockArgs(player_choice_mode=True)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            explanations.explain_player_choice_mode(args)
            output = fake_out.getvalue()

            self.assertIn("correct", output.lower())
            self.assertIn("sequence", output)
            self.assertIn("steer", output.lower())

    def test_explain_player_choice_mode_mentions_fallback(self):
        """Should explain fallback to model choice."""
        args = MockArgs(player_choice_mode=True)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            explanations.explain_player_choice_mode(args)
            output = fake_out.getvalue()

            self.assertIn("not a perfect match", output.lower())
            self.assertIn("model's own", output.lower())


def run_tests():
    """Run all explanations tests."""
    print("=" * 80)
    print("Testing Explanations")
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
