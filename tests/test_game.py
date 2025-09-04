import unittest
from unittest.mock import patch, MagicMock
import argparse
import sys

# Add the project root to the Python path
sys.path.insert(0, '.')

import game
from src.core import config as cfg

class TestGame(unittest.TestCase):

    def test_parse_arguments_defaults(self):
        """Test that arguments are parsed with correct default values."""
        with patch('sys.argv', ['game.py']):
            args = game.parse_arguments()
            self.assertEqual(args.engine, 'pytorch')
            self.assertIsNone(args.model)
            self.assertEqual(args.steps, cfg.DEFAULT_MAX_DECODE_STEPS)
            self.assertFalse(args.tutorial)

    @patch('game.get_engine')
    def test_initialize_game_engine_success(self, mock_get_engine):
        """Test that the game engine can be initialized successfully."""
        # Mock the engine and its load method
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine

        args = argparse.Namespace(engine='pytorch', model='test-model')
        
        # Add other necessary args from the parser defaults
        for key, value in vars(game.parse_arguments()).items():
            if not hasattr(args, key):
                setattr(args, key, value)

        engine = game.initialize_game_engine(args)

        mock_get_engine.assert_called_once_with('pytorch', 'test-model', vars(args))
        mock_engine.load.assert_called_once()
        self.assertIsNotNone(engine)

    @patch('game.initialize_game_engine')
    @patch('src.core.tutorial_mode.TutorialMode')
    def test_run_tutorial_mode(self, mock_tutorial_mode, mock_initialize_engine):
        """Test that tutorial mode runs without crashing."""
        mock_engine = MagicMock()
        mock_initialize_engine.return_value = mock_engine
        mock_tutorial_instance = MagicMock()
        mock_tutorial_mode.return_value = mock_tutorial_instance

        args = argparse.Namespace(model='test-model', verbose=False)
        game.run_tutorial_mode(args)

        mock_initialize_engine.assert_called_once_with(args)
        mock_tutorial_mode.assert_called_once_with(mock_engine, False)
        mock_tutorial_instance.run_tutorial.assert_called_once()

    @patch('src.core.comparison_mode.ComparisonMode')
    def test_run_comparison_mode(self, mock_comparison_mode):
        """Test that comparison mode runs without crashing."""
        mock_comparison_instance = MagicMock()
        mock_comparison_instance.load_models.return_value = True
        mock_comparison_mode.return_value = mock_comparison_instance

        args = argparse.Namespace(comparison_models=['pytorch:model1', 'pytorch:model2'], verbose=False)
        game.run_comparison_mode(args)

        mock_comparison_mode.assert_called_once()
        mock_comparison_instance.load_models.assert_called_once()
        mock_comparison_instance.run_comparison.assert_called_once()

if __name__ == '__main__':
    unittest.main()
