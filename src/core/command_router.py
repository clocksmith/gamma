"""Helpers for routing top-level GAMMA CLI commands."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Callable, List


def run_python_entrypoint(
    script_name: str,
    main_fn: Callable[[], None],
    remaining_args: List[str],
    extra_args: List[str] | None = None,
) -> None:
    """Run a Python entrypoint with a controlled ``sys.argv`` payload."""
    argv = [script_name]
    if extra_args:
        argv.extend(extra_args)
    argv.extend(remaining_args)
    sys.argv = argv
    main_fn()


def run_codegen_command(
    remaining_args: List[str],
    root_dir: str,
    print_command_help: Callable[[str], None],
) -> None:
    """Dispatch the ``gamma.py codegen`` subcommand."""
    if len(remaining_args) == 0 or remaining_args[0] in ["-h", "--help"]:
        print_command_help("codegen")
        sys.exit(0)

    suite_type = remaining_args[0]

    if suite_type == "mind-meld":
        from src.benchmarks.mind_meld_benchmark import main as codegen_mm_main

        run_python_entrypoint(
            "mind_meld_benchmark.py",
            codegen_mm_main,
            remaining_args[1:],
        )
        return

    if suite_type == "language":
        benchmark_dir = _resolve_codegen_benchmark_dir(root_dir)
        print("Running TypeScript vs JavaScript benchmarks (Node.js)...")
        print(f"  Working directory: {benchmark_dir}\n")
        cmd = ["node", "index.js"] + remaining_args[1:]
        try:
            result = subprocess.run(cmd, cwd=benchmark_dir)
            sys.exit(result.returncode)
        except FileNotFoundError:
            print("Error: Node.js not found. Install from https://nodejs.org/")
            sys.exit(1)
        except (OSError, subprocess.SubprocessError) as exc:
            print(f"Error running benchmark: {exc}")
            sys.exit(1)

    if suite_type == "all":
        print("Running all codegen benchmarks...")
        print("\n" + "=" * 70)
        print("1/2 - Mind Meld Benchmarks")
        print("=" * 70)
        from src.benchmarks.mind_meld_benchmark import main as codegen_mm_main

        run_python_entrypoint(
            "mind_meld_benchmark.py",
            codegen_mm_main,
            remaining_args[1:],
        )

        print("\n" + "=" * 70)
        print("2/2 - Language Comparison Benchmarks")
        print("=" * 70)
        benchmark_dir = _resolve_codegen_benchmark_dir(root_dir)
        subprocess.run(["node", "index.js"] + remaining_args[1:], cwd=benchmark_dir)
        return

    print(f"Unknown codegen benchmark type: {suite_type}")
    print("Available types: mind-meld, language, all")
    print_command_help("codegen")
    sys.exit(1)


def _resolve_codegen_benchmark_dir(root_dir: str) -> str:
    benchmark_dir = os.path.join(root_dir, "src", "benchmarks", "codegen")
    if not os.path.exists(benchmark_dir):
        print(f"Error: codegen benchmarks not found at {benchmark_dir}")
        sys.exit(1)
    return benchmark_dir
