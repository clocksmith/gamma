"""
GAMMA CLI Module - Split architecture for better maintainability.

This module contains:
- commands.py: Click/argparse command definitions
- controller.py: Game state machine and flow control
- renderer.py: Rich terminal output and formatting
"""

from src.game.cli.commands import parse_arguments, CLI_OVERRIDE_FLAGS
from src.game.cli.controller import GameController, run_game_loop
from src.game.cli.renderer import (
    display_final_score_and_message,
    display_round_info,
)

# Import main from the legacy cli.py file
# (Python prefers cli/ package over cli.py, so we use importlib)
import importlib.util
import os as _os
_cli_path = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), 'cli.py')
_spec = importlib.util.spec_from_file_location("_cli_legacy", _cli_path)
_cli_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cli_module)
main = _cli_module.main

__all__ = [
    'main',
    'parse_arguments',
    'CLI_OVERRIDE_FLAGS',
    'GameController',
    'run_game_loop',
    'display_final_score_and_message',
    'display_round_info',
]
