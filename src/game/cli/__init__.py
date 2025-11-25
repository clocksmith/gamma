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

__all__ = [
    'parse_arguments',
    'CLI_OVERRIDE_FLAGS',
    'GameController',
    'run_game_loop',
    'display_final_score_and_message',
    'display_round_info',
]
