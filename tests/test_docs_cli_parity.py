"""Guardrails that keep the runtime CLI help surface working."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
GAMMA_PY = REPO_ROOT / "gamma.py"

DOCUMENTED_TOP_LEVEL_COMMANDS = (
    "game",
    "comparison",
    "mind-meld",
    "benchmark",
    "codegen",
    "list",
    "select",
    "help",
)

HELP_SUBCOMMANDS_TO_CHECK = (
    "game",
    "comparison",
    "mind-meld",
    "benchmark",
    "codegen",
    "list",
    "select",
)


def _run_gamma(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GAMMA_PY), *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.docs
def test_web_dist_directory_not_checked_in() -> None:
    assert not (REPO_ROOT / "web" / "dist").exists()


@pytest.mark.docs
def test_top_level_help_includes_documented_commands() -> None:
    result = _run_gamma("--help")
    assert result.returncode == 0, result.stderr
    output = result.stdout
    for command in DOCUMENTED_TOP_LEVEL_COMMANDS:
        assert command in output, f"Missing '{command}' in top-level --help output"


@pytest.mark.docs
def test_help_router_handles_documented_subcommands() -> None:
    failures: list[str] = []
    for command in HELP_SUBCOMMANDS_TO_CHECK:
        result = _run_gamma("help", command)
        if result.returncode != 0:
            failures.append(f"help {command}: {result.stderr.strip()}")
    assert not failures, " ; ".join(failures)
