import json
from pathlib import Path
import shutil
import struct
import subprocess

import pytest


TOOLS = Path(__file__).resolve().parents[1] / "tools"


@pytest.mark.skipif(shutil.which("g++") is None, reason="g++ unavailable")
def test_router_is_deterministic_and_causal(tmp_path: Path) -> None:
    rows = 64 * 8
    p1 = tmp_path / "input.p1"
    store = tmp_path / "input.wrt.store"
    regime = tmp_path / "regime.bin"
    binary = tmp_path / "screen"
    output_a = tmp_path / "a.json"
    output_b = tmp_path / "b.json"
    truth = bytes((index * 41 + 7) & 0xFF for index in range(rows // 8))
    probabilities = b"".join(
        struct.pack("<H", 16000 + ((row * 1297) % 32000))
        for row in range(rows)
    )
    p1.write_bytes(b"CMX21P1\0" + struct.pack("<Q", rows) + probabilities)
    store.write_bytes(b"WRTV1" + truth)
    regime.write_bytes(bytes((row // 64) & 0xFF for row in range(rows)))

    subprocess.run(
        [
            "g++",
            "-std=c++17",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            str(TOOLS / "wrt_phase_residual_native.cpp"),
            str(TOOLS / "wrt_phase_strength_router_screen.cpp"),
            "-o",
            str(binary),
        ],
        check=True,
    )
    command = [
        str(binary),
        "--p1",
        str(p1),
        "--wrt-store",
        str(store),
        "--regime",
        str(regime),
        "--output",
    ]
    subprocess.run(command + [str(output_a)], check=True)
    subprocess.run(command + [str(output_b)], check=True)
    assert output_a.read_bytes() == output_b.read_bytes()
    receipt = json.loads(output_a.read_text())
    assert receipt["causality"] == {
        "prediction_precedes_truth": True,
        "regret_updates_after_truth": True,
        "payload_bytes": 0,
    }
    assert receipt["variants"][-1]["variant_id"] == "shell_regime_after_phase"
