"""
Gamma Core Adapter.

Provides compatibility layer between Gamma and gamma-core,
allowing Gamma to use shared infrastructure while maintaining
backward compatibility with existing code.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _add_gamma_core_search_paths() -> None:
    """
    Add optional gamma-core search paths if the package is not already installed.

    Search order:
    1) GAMMA_CORE_PATH env var (explicit override)
    2) local repo sibling: <repo>/gamma-core
    """
    candidates: list[Path] = []
    env_path = os.environ.get("GAMMA_CORE_PATH", "").strip()
    if env_path:
        candidates.append(Path(env_path).expanduser())
    candidates.append(Path(__file__).resolve().parents[2] / "gamma-core")

    expanded: list[Path] = []
    for candidate in candidates:
        expanded.append(candidate)
        expanded.append(candidate / "src")

    for candidate in expanded:
        if not candidate.exists() or not candidate.is_dir():
            continue
        candidate_str = str(candidate)
        if candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)


def _import_gamma_core():
    def _from_gamma_core_package():
        from gamma_core.engine import ModelEngine as CoreModelEngine, EngineConfig as CoreEngineConfig
        from gamma_core.game import DifficultyLevel as CoreDifficultyLevel, GameSession as CoreGameSession
        from gamma_core.ui import color_text, print_header, print_separator, wrap_print, UIConfig
        return (
            CoreModelEngine,
            CoreEngineConfig,
            CoreDifficultyLevel,
            CoreGameSession,
            color_text,
            print_header,
            print_separator,
            wrap_print,
            UIConfig,
        )

    def _from_gamma_core_src_layout():
        from engine import ModelEngine as CoreModelEngine, EngineConfig as CoreEngineConfig
        from game import DifficultyLevel as CoreDifficultyLevel, GameSession as CoreGameSession
        from ui import color_text, print_header, print_separator, wrap_print, UIConfig
        return (
            CoreModelEngine,
            CoreEngineConfig,
            CoreDifficultyLevel,
            CoreGameSession,
            color_text,
            print_header,
            print_separator,
            wrap_print,
            UIConfig,
        )

    try:
        return _from_gamma_core_package()
    except ModuleNotFoundError:
        try:
            return _from_gamma_core_src_layout()
        except ModuleNotFoundError as first_exc:
            _add_gamma_core_search_paths()
            try:
                return _from_gamma_core_package()
            except ModuleNotFoundError:
                try:
                    return _from_gamma_core_src_layout()
                except ModuleNotFoundError as exc:
                    raise ModuleNotFoundError(
                        "gamma_core is not importable. Install with `pip install -r requirements-core.txt` "
                        "or set GAMMA_CORE_PATH to a local gamma-core checkout."
                    ) from (exc or first_exc)
    except Exception as first_exc:
        _add_gamma_core_search_paths()
        try:
            return _from_gamma_core_package()
        except Exception:
            try:
                return _from_gamma_core_src_layout()
            except Exception as exc:
                raise ModuleNotFoundError(
                    "gamma_core is not importable. Install with `pip install -r requirements-core.txt` "
                    "or set GAMMA_CORE_PATH to a local gamma-core checkout."
                ) from (exc or first_exc)


(
    CoreModelEngine,
    CoreEngineConfig,
    CoreDifficultyLevel,
    CoreGameSession,
    color_text,
    print_header,
    print_separator,
    wrap_print,
    UIConfig,
) = _import_gamma_core()

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
