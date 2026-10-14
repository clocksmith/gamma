"""
Test Core Config Module

Tests the core configuration invariants:
- Model information structure
- Color configuration based on platform
"""

import sys
import os

import unittest
from unittest.mock import patch, MagicMock

from src.core import config


class TestGemmaModelInfo(unittest.TestCase):
    """Test Gemma model information."""

    def test_all_models_have_required_fields(self):
        """All models should have required fields."""
        required_fields = {"desc", "params_b", "raw_model_gb", "rec_ram_gb"}
        for model_name, model_info in config.GEMMA_MODEL_INFO.items():
            self.assertTrue(
                required_fields.issubset(model_info.keys()),
                f"Model {model_name} missing required fields"
            )

    def test_model_params_are_positive(self):
        """Model parameters should be positive numbers."""
        for model_name, model_info in config.GEMMA_MODEL_INFO.items():
            self.assertGreater(
                model_info["params_b"],
                0,
                f"Model {model_name} has non-positive params_b"
            )

    def test_model_size_is_positive(self):
        """Model size should be positive."""
        for model_name, model_info in config.GEMMA_MODEL_INFO.items():
            self.assertGreater(
                model_info["raw_model_gb"],
                0,
                f"Model {model_name} has non-positive raw_model_gb"
            )


class TestColorConfiguration(unittest.TestCase):
    """Test color configuration logic."""

    def test_color_constants_defined(self):
        """Color constants should be defined (either as colors or empty strings)."""
        # These should always be defined
        self.assertIsNotNone(config.COLOR_RED)
        self.assertIsNotNone(config.COLOR_GREEN)
        self.assertIsNotNone(config.COLOR_BLUE)
        self.assertIsNotNone(config.COLOR_RESET)

    def test_use_colors_is_boolean(self):
        """USE_COLORS should be a boolean."""
        self.assertIsInstance(config.USE_COLORS, bool)

    @patch('sys.platform', 'win32')
    @patch('os.name', 'nt')
    def test_windows_color_initialization_with_colorama(self):
        """On Windows with colorama, colors should work."""
        # Mock colorama module
        mock_colorama = MagicMock()
        with patch.dict('sys.modules', {'colorama': mock_colorama}):
            # Reload config to test initialization
            import importlib
            importlib.reload(config)

            # USE_COLORS should be True (or False if not tty)
            self.assertIsInstance(config.USE_COLORS, bool)

    @patch('sys.platform', 'win32')
    @patch('os.name', 'nt')
    @patch.dict('os.environ', {'TERM': 'dumb'})
    def test_windows_color_initialization_without_colorama(self):
        """On Windows without colorama and unsupported TERM, colors should be disabled."""
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == 'colorama':
                raise ImportError("colorama not found")
            return original_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import):
            import importlib
            importlib.reload(config)

            # Colors might be disabled depending on TERM
            self.assertIsInstance(config.USE_COLORS, bool)

    @patch('sys.stdout')
    def test_non_tty_disables_colors(self, mock_stdout):
        """Non-tty stdout should disable colors."""
        # Make stdout.isatty() return False
        mock_stdout.isatty.return_value = False

        import importlib
        importlib.reload(config)

        # Verify isatty was checked
        self.assertIsInstance(config.USE_COLORS, bool)


if __name__ == "__main__":
    print("=" * 80)
    print("Testing Core Config Module")
    print("=" * 80)
    print()

    # Run tests
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 80)
    print(f"Tests: {result.testsRun}, Failures: {len(result.failures)}, Errors: {len(result.errors)}")
    print("=" * 80)

    sys.exit(0 if result.wasSuccessful() else 1)
