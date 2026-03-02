"""Shared bootstrap for CLI tools that need repo-root imports."""

from __future__ import annotations

from pathlib import Path
import sys


def ensure_project_root_on_path() -> str:
    """Insert repository root into ``sys.path`` once and return it."""
    root = Path(__file__).resolve().parent.parent
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root_str


def ensure_src_on_path() -> str:
    """Insert repository ``src`` directory into ``sys.path`` once and return it."""
    root = Path(ensure_project_root_on_path())
    src = root / "src"
    src_str = str(src)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)
    return src_str


def ensure_tools_on_path() -> str:
    """Insert repository ``tools`` directory into ``sys.path`` once and return it."""
    root = Path(ensure_project_root_on_path())
    tools = root / "tools"
    tools_str = str(tools)
    if tools_str not in sys.path:
        sys.path.insert(0, tools_str)
    return tools_str
