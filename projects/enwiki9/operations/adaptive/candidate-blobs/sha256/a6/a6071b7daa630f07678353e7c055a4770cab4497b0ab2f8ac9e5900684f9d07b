"""Native synthetic metadata-memory tests; never access corpus data."""
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_native_title_memory_under_undefined_behavior_sanitizer(tmp_path):
    compiler = shutil.which("g++")
    if not compiler:
        pytest.skip("C++ compiler is not provisioned")
    binary = tmp_path / "fixture"
    subprocess.run([compiler, "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror",
                    "-fsanitize=undefined", "-fno-sanitize-recover=all", "-I", str(ROOT / "lib"),
                    str(ROOT / "tests/fx2_title_memory_v1_fixture.cpp"), "-o", str(binary)],
                   check=True, timeout=45)
    result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=5)
    assert "matched causal donors" in result.stdout
