"""Adapter that imports shared gamma-core modules with a fixed contract."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _resolve_gamma_core_src() -> Path:
    """
    Resolve the gamma-core source directory.

    Contract:
    - Default: <repo>/gamma-core/src (vendored checkout)
    - Override: GAMMA_CORE_SRC_PATH (absolute or relative path to gamma-core/src)
    """
    override = os.environ.get("GAMMA_CORE_SRC_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return (Path(__file__).resolve().parents[2] / "gamma-core" / "src").resolve()


def _ensure_gamma_core_path() -> Path:
    src_path = _resolve_gamma_core_src()
    if not src_path.exists() or not src_path.is_dir():
        raise ModuleNotFoundError(
            "gamma-core source directory is missing. Expected: "
            f"{src_path}. Set GAMMA_CORE_SRC_PATH to a valid gamma-core/src path."
        )
    src_path_str = str(src_path)
    if src_path_str not in sys.path:
        sys.path.insert(0, src_path_str)
    return src_path


def _import_gamma_core():
    """
    Import gamma-core symbols from vendored src modules.

    gamma-core currently exports top-level modules: engine, game, ui.
    """
    _ensure_gamma_core_path()
    try:
        from engine import ModelEngine as CoreModelEngine, EngineConfig as CoreEngineConfig
        from game import DifficultyLevel as CoreDifficultyLevel, GameSession as CoreGameSession
        from ui import color_text, print_header, print_separator, wrap_print, UIConfig
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "gamma-core modules are not importable from the configured source path. "
            "Ensure gamma-core/src contains engine/, game/, and ui/ packages."
        ) from exc

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
