"""Guardrails that keep docs and runtime CLI surface in sync."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
README_PATH = REPO_ROOT / "README.md"
DOCS_README_PATH = REPO_ROOT / "docs" / "README.md"
WEB_README_PATH = REPO_ROOT / "web" / "README.md"
GAMMA_PY = REPO_ROOT / "gamma.py"

REQUIRED_README_SNIPPETS = (
    "python gamma.py help codegen",
    "python gamma.py help benchmark",
    "python gamma.py game --comparison --help",
    "docs/ARCHITECTURE.md",
)

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
def test_readme_contains_cli_entrypoints() -> None:
    text = README_PATH.read_text(encoding="utf-8")
    missing = [snippet for snippet in REQUIRED_README_SNIPPETS if snippet not in text]
    assert not missing, f"README missing required CLI snippets: {missing}"


@pytest.mark.docs
def test_docs_index_mentions_architecture_map() -> None:
    text = DOCS_README_PATH.read_text(encoding="utf-8")
    assert "Architecture Map" in text
    assert "ARCHITECTURE.md" in text


@pytest.mark.docs
def test_web_readme_retains_static_contract() -> None:
    text = WEB_README_PATH.read_text(encoding="utf-8")
    assert "Build" in text and "None" in text
    assert "firebase deploy" in text
    assert "web/dist/" in text


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
