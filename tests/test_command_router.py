"""Regression tests for top-level command routing helpers."""

from __future__ import annotations

import types
from pathlib import Path

import pytest

from src.core import command_router as cr


@pytest.mark.regression
def test_run_python_entrypoint_sets_argv(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_main() -> None:
        import sys
        captured["argv"] = list(sys.argv)

    cr.run_python_entrypoint("gamma.py", fake_main, ["game", "--help"], extra_args=["--verbose"])
    assert captured["argv"] == ["gamma.py", "--verbose", "game", "--help"]


@pytest.mark.regression
def test_run_codegen_help_branch_exits_zero() -> None:
    seen: list[str] = []

    def _print_help(name: str) -> None:
        seen.append(name)

    with pytest.raises(SystemExit) as exc:
        cr.run_codegen_command([], "/tmp/irrelevant", _print_help)

    assert int(exc.value.code) == 0
    assert seen == ["codegen"]


@pytest.mark.regression
def test_run_codegen_unknown_branch_exits_one(capsys: pytest.CaptureFixture[str]) -> None:
    seen: list[str] = []

    def _print_help(name: str) -> None:
        seen.append(name)

    with pytest.raises(SystemExit) as exc:
        cr.run_codegen_command(["does-not-exist"], "/tmp/irrelevant", _print_help)

    out = capsys.readouterr().out
    assert int(exc.value.code) == 1
    assert "Unknown codegen benchmark type" in out
    assert seen == ["codegen"]


@pytest.mark.regression
def test_resolve_codegen_benchmark_dir_missing(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        cr._resolve_codegen_benchmark_dir(str(tmp_path))
    assert int(exc.value.code) == 1


@pytest.mark.regression
def test_run_codegen_language_handles_missing_node(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    benchmark_dir = tmp_path / "tools" / "codegen-bench"
    benchmark_dir.mkdir(parents=True, exist_ok=True)

    def _print_help(_: str) -> None:
        raise AssertionError("help should not be called")

    monkeypatch.setattr(
        cr,
        "subprocess",
        types.SimpleNamespace(run=lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError())),
    )

    with pytest.raises(SystemExit) as exc:
        cr.run_codegen_command(["language", "--foo"], str(tmp_path), _print_help)

    assert int(exc.value.code) == 1
