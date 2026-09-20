"""Synthetic causal-selection and WRT-coordinate checks; no corpus access."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_native_selection_and_emission_boundaries(tmp_path):
    binary = tmp_path / 'coverage'
    subprocess.run([
        'g++', '-std=c++17', '-O1', '-Wall', '-Wextra',
        '-Wno-misleading-indentation', '-Werror', '-fsanitize=undefined',
        '-fno-sanitize-recover=all', '-I', str(ROOT / 'lib'),
        str(ROOT / 'tests/donor_coverage_fixture_v1.cpp'), '-o', str(binary),
    ], check=True, timeout=60)
    subprocess.run([str(binary)], check=True, timeout=20)
