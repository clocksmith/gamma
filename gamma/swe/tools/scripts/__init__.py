"""
Standalone tool scripts for FunctionGemma ring.

Each tool is a simple Python module with an execute() function.
Tools can be:
1. Built-in (shipped with the agent)
2. Synthesized by conductor at runtime
3. Evolved via LoRA fine-tuning
"""

from pathlib import Path
from typing import Any, Callable, Dict
import importlib.util


def load_tools(tools_dir: Path = None) -> Dict[str, Callable]:
    """Load all tools from directory."""
    if tools_dir is None:
        tools_dir = Path(__file__).parent

    tools = {}

    for py_file in tools_dir.glob("*.py"):
        if py_file.name.startswith("_"):
            continue

        tool_name = py_file.stem
        try:
            spec = importlib.util.spec_from_file_location(tool_name, py_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "execute"):
                tools[tool_name] = module.execute
        except Exception:
            continue

    return tools


def save_tool(name: str, code: str, tools_dir: Path = None) -> bool:
    """Save a synthesized tool to disk."""
    if tools_dir is None:
        tools_dir = Path(__file__).parent

    try:
        tool_path = tools_dir / f"{name}.py"
        tool_path.write_text(code)
        return True
    except Exception:
        return False
