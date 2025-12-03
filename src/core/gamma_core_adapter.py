"""
Gamma Core Adapter.

Provides compatibility layer between Gamma and gamma-core,
allowing Gamma to use shared infrastructure while maintaining
backward compatibility with existing code.
"""

import sys
sys.path.insert(0, '/home/clocksmith/deco/gamma-core')

from gamma_core.engine import ModelEngine as CoreModelEngine, EngineConfig as CoreEngineConfig
from gamma_core.game import DifficultyLevel as CoreDifficultyLevel, GameSession as CoreGameSession
from gamma_core.ui import color_text, print_header, print_separator, wrap_print, UIConfig

# Re-export gamma-core components with Gamma naming
ModelEngineBase = CoreModelEngine
EngineConfigBase = CoreEngineConfig
DifficultyLevel = CoreDifficultyLevel
GameSession = CoreGameSession

# UI exports
__all__ = [
    "ModelEngineBase",
    "EngineConfigBase",
    "DifficultyLevel",
    "GameSession",
    "color_text",
    "print_header",
    "print_separator",
    "wrap_print",
    "UIConfig",
]
