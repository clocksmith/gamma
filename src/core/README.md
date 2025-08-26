# Core Logic

This directory is the heart of the GAMMA application. It contains the primary game logic, user interface components, and the central abstractions that allow the rest of the system to function in a modular way.

## Key Components:

- **`engine_interface.py`**: Defines the `LLMEngine` abstract base class. This is the most important file for ensuring modularity, as it provides a strict "contract" that all machine learning backends in the `engines/` directory must adhere to.

- **`config.py`**: Contains default configurations for the game, such as model names, sampling parameters, and color settings.

- **`ui.py`**: Manages all command-line input and output, including printing headers, heatmaps, probability tables, and handling user choices.

- **`game_logic.py`**: Implements the rules of the classic game mode, such as generating choices for the player and processing their guesses.

- **Game Mode Modules (`tutorial_mode.py`, `comparison_mode.py`, `mind_meld_mode.py`)**: Each of these files encapsulates the logic for a specific game mode, which is called from the main `game.py` entry point.
