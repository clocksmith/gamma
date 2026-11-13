"""Exercise development entrypoints without importing model or archive dependencies."""

from __future__ import annotations

import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def clean_environment():
    env = os.environ.copy()
    for key in ("GAMMA_ALL_TESTS", "PYTEST_ADDOPTS", "PYTHON_BIN", "PYTEST_EXTRA_ARGS"):
        env.pop(key, None)
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    return env


@pytest.mark.parametrize("selection", ["bare", "file", "node", "marker", "all", "other-marker"])
def test_archive_collection_is_opt_in_before_import(tmp_path, selection):
    tests = tmp_path / "tests"
    tests.mkdir()
    shutil.copyfile(ROOT / "tests/conftest.py", tests / "conftest.py")
    archive_names = runpy.run_path(str(ROOT / "tests/conftest.py"))["ENWIKI9_ARCHIVED_TEST_FILES"]
    archived = tests / sorted(archive_names)[0]
    imported = tmp_path / "archive-imported"
    archived.write_text(
        "from pathlib import Path\nimport pytest\n"
        f"Path({str(imported)!r}).touch()\n"
        "@pytest.mark.regression\ndef test_archived(): pass\n"
    )
    (tests / "test_active.py").write_text("def test_active(): pass\n")
    (tmp_path / "pytest.ini").write_text(
        "[pytest]\nmarkers =\n    enwiki9: archive\n    regression: regression\n"
    )
    env = clean_environment()
    args = ["tests"]
    if selection == "file":
        args = [str(archived)]
    elif selection == "node":
        args = [str(archived) + "::test_archived"]
    elif selection == "marker":
        args += ["-m", "enwiki9"]
    elif selection == "other-marker":
        args += ["-m", "regression"]
    elif selection == "all":
        env["GAMMA_ALL_TESTS"] = "1"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", *args],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert imported.exists() == (selection != "bare")
    assert ("::test_archived" in result.stdout) == (selection != "bare")
    assert ("::test_active" in result.stdout) == (selection in {"bare", "all"})


def fake_python(path, label, *, has_pytest=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "#!/bin/bash\n"
        f'if [[ "$*" == "-m pytest --version" ]]; then exit {0 if has_pytest else 1}; fi\n'
        f"printf '%s\\n' {label!r}\n"
        "printf '<%s>' \"$@\"\n"
    )
    path.chmod(0o755)


@pytest.mark.parametrize("selection", ["explicit", "local", "missing-pytest"])
@pytest.mark.parametrize("targets", [[], ["tests/a test.py::test_one"]])
def test_runner_keeps_the_selected_environment(tmp_path, selection, targets):
    shutil.copyfile(ROOT / "run_tests.sh", tmp_path / "run_tests.sh")
    fake_python(tmp_path / ".venv/bin/python", "local", has_pytest=selection != "missing-pytest")
    fake_python(tmp_path / "bin/python3", "fallback")
    env = clean_environment()
    env["PATH"] = str(tmp_path / "bin") + os.pathsep + env["PATH"]
    if selection == "explicit":
        custom = tmp_path / "custom python"
        fake_python(custom, "explicit")
        env["PYTHON_BIN"] = str(custom)
    result = subprocess.run(
        ["bash", "run_tests.sh", *targets],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=10,
    )
    if selection == "missing-pytest":
        assert result.returncode == 1
        assert "pytest is not available for .venv/bin/python" in result.stdout
        assert "fallback" not in result.stdout
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        assert f"\n{selection}\n" in result.stdout
        if targets:
            assert "<tests/a test.py::test_one>" in result.stdout
        else:
            assert "<tests/test_engine_interface.py><tests/test_engine_factory.py><tests/test_game.py><tests/test_ui_components.py>" in result.stdout
