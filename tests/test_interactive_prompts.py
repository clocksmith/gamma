"""
Test Interactive Prompts

Tests interactive user input handling:
- get_user_input: Input validation and processing
- confirm_or_modify_config: Configuration modification
- select_engine_interactively: Engine selection
- select_model_interactively: Model selection
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import patch, MagicMock, Mock
import argparse

from src.core.menu import interactive_prompts


class TestGetUserInput(unittest.TestCase):
    """Test get_user_input function."""

    @patch('builtins.input')
    def test_simple_input(self, mock_input):
        """Should return user input."""
        mock_input.return_value = "test input"

        result = interactive_prompts.get_user_input("Enter something")

        self.assertEqual(result, "test input")

    @patch('builtins.input')
    def test_valid_choice_selection(self, mock_input):
        """Should validate against valid_choices."""
        mock_input.return_value = "yes"

        result = interactive_prompts.get_user_input(
            "Choose",
            valid_choices=["yes", "no"]
        )

        self.assertEqual(result, "yes")

    @patch('builtins.input')
    def test_invalid_then_valid_choice(self, mock_input):
        """Should re-prompt on invalid choice."""
        mock_input.side_effect = ["invalid", "yes"]

        result = interactive_prompts.get_user_input(
            "Choose",
            valid_choices=["yes", "no"]
        )

        self.assertEqual(result, "yes")
        self.assertEqual(mock_input.call_count, 2)

    @patch('builtins.input')
    def test_quit_shortcut(self, mock_input):
        """Should return quit shortcut."""
        mock_input.return_value = "q"

        result = interactive_prompts.get_user_input(
            "Enter something",
            allow_quit=True
        )

        self.assertEqual(result, "q")

    @patch('builtins.input')
    def test_empty_input_with_default(self, mock_input):
        """Should return default on empty input."""
        mock_input.return_value = ""

        result = interactive_prompts.get_user_input(
            "Enter something",
            allow_empty=True,
            default_val_on_empty="default"
        )

        self.assertEqual(result, "default")

    @patch('builtins.input')
    def test_empty_input_without_default(self, mock_input):
        """Should return empty string when allowed."""
        mock_input.return_value = ""

        result = interactive_prompts.get_user_input(
            "Enter something",
            allow_empty=True
        )

        self.assertEqual(result, "")

    @patch('builtins.input')
    def test_empty_input_not_allowed(self, mock_input):
        """Should re-prompt when empty not allowed."""
        mock_input.side_effect = ["", "valid input"]

        result = interactive_prompts.get_user_input(
            "Enter something",
            allow_empty=False
        )

        self.assertEqual(result, "valid input")
        self.assertEqual(mock_input.call_count, 2)

    @patch('builtins.input')
    def test_case_insensitive_choice_matching(self, mock_input):
        """Should match choices case-insensitively."""
        mock_input.return_value = "YES"

        result = interactive_prompts.get_user_input(
            "Choose",
            valid_choices=["yes", "no"]
        )

        # Should return the original case from valid_choices
        self.assertEqual(result, "yes")

    @patch('builtins.input')
    def test_eoferror_exits(self, mock_input):
        """Should exit on EOFError."""
        mock_input.side_effect = EOFError()

        with self.assertRaises(SystemExit):
            interactive_prompts.get_user_input("Enter something")

    @patch('builtins.input')
    def test_keyboard_interrupt_exits(self, mock_input):
        """Should exit on KeyboardInterrupt."""
        mock_input.side_effect = KeyboardInterrupt()

        with self.assertRaises(SystemExit):
            interactive_prompts.get_user_input("Enter something")

    @patch('builtins.input')
    def test_strips_whitespace(self, mock_input):
        """Should strip leading/trailing whitespace."""
        mock_input.return_value = "  test input  "

        result = interactive_prompts.get_user_input("Enter something")

        self.assertEqual(result, "test input")


class TestConfirmOrModifyConfig(unittest.TestCase):
    """Test confirm_or_modify_config function."""

    def setUp(self):
        """Create mock args."""
        self.args = argparse.Namespace(
            engine="pytorch",
            model="test-model",
            steps=10,
            temperature=0.7,
            top_k=50,
            top_p=0.95,
            num_choices=4,
            permutation_length=3,
            focus_words=False,
            player_choice_mode=False,
            show_attention=False,
            verbose=False
        )

    # Note: confirm_or_modify_config is complex and requires mocking display_current_config
    # which is imported inside the function. Skipping detailed tests for this function
    # as it would require complex import mocking.


class TestSelectEngineInteractively(unittest.TestCase):
    """Test select_engine_interactively function."""

    @patch('src.core.menu.interactive_prompts.get_user_input')
    def test_select_first_engine(self, mock_input):
        """Should return first engine."""
        mock_input.return_value = "1"

        result = interactive_prompts.select_engine_interactively("pytorch")

        self.assertEqual(result, "pytorch")

    @patch('src.core.menu.interactive_prompts.get_user_input')
    def test_select_second_engine(self, mock_input):
        """Should return second engine."""
        mock_input.return_value = "2"

        result = interactive_prompts.select_engine_interactively("pytorch")

        self.assertEqual(result, "llamacpp")

    @patch('src.core.menu.interactive_prompts.get_user_input')
    def test_quit_selection(self, mock_input):
        """Should return None on quit."""
        mock_input.return_value = "q"

        result = interactive_prompts.select_engine_interactively("pytorch")

        self.assertIsNone(result)

    @patch('src.core.menu.interactive_prompts.get_user_input')
    def test_default_engine_shown(self, mock_input):
        """Should show default engine in list."""
        mock_input.return_value = "1"

        # Just verify it runs without error when default is in list
        result = interactive_prompts.select_engine_interactively("jax")

        self.assertIsNotNone(result)


class TestSelectModelInteractively(unittest.TestCase):
    """Test select_model_interactively function."""

    @patch('src.core.models.model_catalog.ModelSelector.select_model')
    def test_select_model(self, mock_select):
        """Should delegate to ModelSelector."""
        mock_select.return_value = "model-name"

        result = interactive_prompts.select_model_interactively("pytorch")

        self.assertEqual(result, "model-name")
        mock_select.assert_called_once()

    @patch('src.core.models.model_catalog.ModelSelector.select_model')
    def test_select_model_with_default(self, mock_select):
        """Should pass through default model."""
        mock_select.return_value = "new-model"

        result = interactive_prompts.select_model_interactively(
            "pytorch",
            current_default_model="old-model"
        )

        self.assertEqual(result, "new-model")


def run_tests():
    """Run all interactive prompts tests."""
    print("=" * 80)
    print("Testing Interactive Prompts")
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
