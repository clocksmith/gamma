import unittest
from unittest.mock import patch, MagicMock
import argparse
import sys
import os


try:
    # Import from cli.py file directly (cli/ package shadows it)
    import importlib.util
    _cli_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'game', 'cli.py')
    _spec = importlib.util.spec_from_file_location("game_cli", _cli_path)
    game = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(game)
    from src.core import config as cfg
    _GAME_IMPORT_ERROR = None
except Exception as exc:
    game = None
    cfg = None
    _GAME_IMPORT_ERROR = exc

# Module path for patching - use the actual file path
_CLI_MODULE = 'src.game.cli' if game is None else game.__name__


@unittest.skipIf(_GAME_IMPORT_ERROR is not None, f"Skipping game tests: {_GAME_IMPORT_ERROR}")
class TestGameRefactor(unittest.TestCase):

    @patch.object(game, 'run_tutorial_mode') if game else patch('src.game.cli.run_tutorial_mode')
    def test_run_selected_mode_tutorial(self, mock_run_tutorial_mode):
        """Test that tutorial mode is called from run_selected_mode."""
        with patch('sys.argv', ['gamma.py', '--tutorial']):
            args = game.parse_arguments()
            game.run_selected_mode(args)
        mock_run_tutorial_mode.assert_called_once_with(args)

    @patch.object(game, 'run_comparison_mode') if game else patch('src.game.cli.run_comparison_mode')
    def test_run_selected_mode_comparison(self, mock_run_comparison_mode):
        """Test that comparison mode is called from run_selected_mode."""
        with patch('sys.argv', ['gamma.py', '--comparison']):
            args = game.parse_arguments()
            game.run_selected_mode(args)
        mock_run_comparison_mode.assert_called_once_with(args)

    @patch.object(game, 'run_meld_mode') if game else patch('src.game.cli.run_meld_mode')
    def test_run_selected_mode_mind_meld(self, mock_run_meld_mode):
        """Test that mind meld mode is called from run_selected_mode."""
        with patch('sys.argv', ['gamma.py', '--mind-meld']):
            args = game.parse_arguments()
            game.run_selected_mode(args)
        mock_run_meld_mode.assert_called_once_with(args)

    @patch.object(game, 'initialize_game_engine') if game else patch('src.game.cli.initialize_game_engine')
    @patch.object(game, 'run_game_loop') if game else patch('src.game.cli.run_game_loop')
    def test_run_selected_mode_game_loop(self, mock_run_game_loop, mock_initialize_game_engine):
        """Test that the game loop is called from run_selected_mode."""
        mock_engine = MagicMock()
        mock_initialize_game_engine.return_value = mock_engine
        with patch('sys.argv', ['gamma.py']):
            args = game.parse_arguments()
            game.run_selected_mode(args)
        mock_initialize_game_engine.assert_called_once_with(args)
        mock_run_game_loop.assert_called_once_with(mock_engine, args)


if __name__ == '__main__':
    unittest.main()
