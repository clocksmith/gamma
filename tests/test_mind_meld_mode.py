"""
Test Mind Meld Mode

Tests Mind Meld Mode class:
- MindMeldMode initialization
- Model validation
- Game loop execution
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import Mock, MagicMock, patch
import argparse

from src.mind_meld.mode import MindMeldMode


class TestMindMeldMode(unittest.TestCase):
    """Test MindMeldMode class."""

    def setUp(self):
        """Set up test models and args."""
        self.model1 = Mock()
        self.model1.model_name = "test-model-1"
        self.model1.__class__.__name__ = "MockEngine1"

        self.model2 = Mock()
        self.model2.model_name = "test-model-2"
        self.model2.__class__.__name__ = "MockEngine2"

        self.args = argparse.Namespace(
            temperature=0.7,
            top_k=50,
            top_p=0.95,
            verbose=False
        )

    @patch('src.mind_meld.mode.MeldEngine')
    def test_initialization(self, mock_meld_engine):
        """Should initialize with models and args."""
        models = [self.model1, self.model2]

        mode = MindMeldMode(models, self.args)

        self.assertEqual(mode.models, models)
        self.assertEqual(mode.args, self.args)
        mock_meld_engine.assert_called_once_with(models, self.args)

    @patch('src.mind_meld.mode.MeldEngine')
    def test_meld_engine_creation(self, mock_meld_engine):
        """Should create MeldEngine instance."""
        mock_instance = Mock()
        mock_meld_engine.return_value = mock_instance
        models = [self.model1, self.model2]

        mode = MindMeldMode(models, self.args)

        self.assertEqual(mode.meld_engine, mock_instance)

    @patch('src.mind_meld.mode.ui.print_header')
    @patch('src.mind_meld.mode.ui.wrap_print')
    @patch('src.mind_meld.mode.MeldEngine')
    def test_run_with_two_models(self, mock_meld_engine, mock_wrap_print, mock_print_header):
        """Should run game loop with two models."""
        mock_instance = Mock()
        mock_meld_engine.return_value = mock_instance
        models = [self.model1, self.model2]

        mode = MindMeldMode(models, self.args)
        mode.run()

        mock_print_header.assert_called_once()
        mock_instance.run_game_loop.assert_called_once()

    @patch('src.mind_meld.mode.ui.print_header')
    @patch('src.mind_meld.mode.ui.wrap_print')
    @patch('src.mind_meld.mode.MeldEngine')
    def test_run_with_one_model(self, mock_meld_engine, mock_wrap_print, mock_print_header):
        """Should show error with only one model."""
        mock_instance = Mock()
        mock_meld_engine.return_value = mock_instance
        models = [self.model1]

        mode = MindMeldMode(models, self.args)
        mode.run()

        # Should print error
        mock_print_header.assert_called_once()
        # Should NOT run game loop
        mock_instance.run_game_loop.assert_not_called()

    @patch('src.mind_meld.mode.ui.print_header')
    @patch('src.mind_meld.mode.ui.wrap_print')
    @patch('src.mind_meld.mode.MeldEngine')
    def test_run_prints_model_info(self, mock_meld_engine, mock_wrap_print, mock_print_header):
        """Should print model information."""
        mock_instance = Mock()
        mock_meld_engine.return_value = mock_instance
        models = [self.model1, self.model2]

        mode = MindMeldMode(models, self.args)
        mode.run()

        # Should print models loaded and each model info
        self.assertGreater(mock_wrap_print.call_count, 2)

    @patch('src.mind_meld.mode.ui.print_header')
    @patch('src.mind_meld.mode.ui.wrap_print')
    @patch('src.mind_meld.mode.MeldEngine')
    def test_run_with_three_models(self, mock_meld_engine, mock_wrap_print, mock_print_header):
        """Should run with more than two models."""
        mock_instance = Mock()
        mock_meld_engine.return_value = mock_instance
        model3 = Mock()
        model3.model_name = "test-model-3"
        model3.__class__.__name__ = "MockEngine3"
        models = [self.model1, self.model2, model3]

        mode = MindMeldMode(models, self.args)
        mode.run()

        mock_instance.run_game_loop.assert_called_once()

    @patch('src.mind_meld.mode.MeldEngine')
    def test_models_attribute(self, mock_meld_engine):
        """Should store models attribute."""
        models = [self.model1, self.model2]

        mode = MindMeldMode(models, self.args)

        self.assertIsInstance(mode.models, list)
        self.assertEqual(len(mode.models), 2)

    @patch('src.mind_meld.mode.MeldEngine')
    def test_args_attribute(self, mock_meld_engine):
        """Should store args attribute."""
        models = [self.model1, self.model2]

        mode = MindMeldMode(models, self.args)

        self.assertEqual(mode.args, self.args)
        self.assertEqual(mode.args.temperature, 0.7)


def run_tests():
    """Run all mind meld mode tests."""
    print("=" * 80)
    print("Testing Mind Meld Mode")
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
