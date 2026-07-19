from __future__ import annotations

import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "projects/enwiki9/tools/lstm_gate_runtime_probe.cpp"


def test_runtime_probe_preserves_step_arithmetic(tmp_path: Path) -> None:
    binary = tmp_path / "lstm-gate-runtime-probe"
    subprocess.run(
        [
            "g++",
            "-std=c++17",
            "-O2",
            "-fopenmp",
            str(SOURCE),
            "-o",
            str(binary),
        ],
        check=True,
    )
    completed = subprocess.run(
        [str(binary), "17", "29", "3", "2"],
        check=True,
        capture_output=True,
        text=True,
    )
    receipt = json.loads(completed.stdout)

    assert receipt["schema"] == "lstm_gate_runtime_probe_v1"
    assert receipt["persistent_step_identity"] is True
    assert receipt["serial_step_identity"] is True
    assert receipt["current_checksum"] == receipt["persistent_checksum"]
    assert receipt["current_checksum"] == receipt["serial_checksum"]
