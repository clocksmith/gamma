"""Top-level command router for ``gamma.py``."""

from __future__ import annotations

from typing import Callable, Sequence

from src.core.command_router import run_codegen_command, run_python_entrypoint


TOP_LEVEL_COMMANDS: tuple[str, ...] = (
    "game",
    "mind-meld",
    "comparison",
    "benchmark",
    "codegen",
    "list",
    "select",
    "help",
)


def route_command(
    command: str,
    remaining_args: Sequence[str],
    root_dir: str,
    print_command_help: Callable[[str], None],
) -> None:
    """Dispatch a top-level command to its concrete implementation."""
    if command == "game":
        from src.game.cli import main as game_main

        run_python_entrypoint("gamma.py", game_main, list(remaining_args))
        return

    if command == "mind-meld":
        from tools.run_mind_meld_cli import main as mind_meld_main

        run_python_entrypoint("run_mind_meld_cli.py", mind_meld_main, list(remaining_args))
        return

    if command == "comparison":
        from src.game.cli import main as game_main

        run_python_entrypoint("gamma.py", game_main, list(remaining_args), extra_args=["--comparison"])
        return

    if command == "benchmark":
        from tools.benchmark_model_speed import main as benchmark_main

        run_python_entrypoint("benchmark_model_speed.py", benchmark_main, list(remaining_args))
        return

    if command == "codegen":
        run_codegen_command(list(remaining_args), root_dir, print_command_help)
        return

    if command == "list":
        from tools.list_models import main as list_main

        run_python_entrypoint("list_models.py", list_main, list(remaining_args))
        return

    if command == "select":
        from tools.engine_selector import main as selector_main

        run_python_entrypoint("engine_selector.py", selector_main, list(remaining_args))
        return

