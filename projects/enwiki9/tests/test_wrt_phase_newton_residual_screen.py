import json
from pathlib import Path
import shutil
import struct
import subprocess

import pytest


TOOLS = Path(__file__).resolve().parents[1] / "tools"


@pytest.mark.skipif(shutil.which("g++") is None, reason="g++ unavailable")
def test_newton_screen_is_deterministic_and_causal(tmp_path: Path) -> None:
    rows = 128 * 8
    p1 = tmp_path / "input.p1"
    store = tmp_path / "input.wrt.store"
    binary = tmp_path / "screen"
    output_a = tmp_path / "a.json"
    output_b = tmp_path / "b.json"
    truth = bytes((index * 41 + 7) & 0xFF for index in range(rows // 8))
    probabilities = b"".join(
        struct.pack("<H", 12000 + ((row * 1297) % 40000))
        for row in range(rows)
    )
    p1.write_bytes(b"CMX21P1\0" + struct.pack("<Q", rows) + probabilities)
    store.write_bytes(b"WRTV1" + truth)

    subprocess.run(
        [
            "g++",
            "-std=c++17",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            str(TOOLS / "wrt_phase_residual_native.cpp"),
            str(TOOLS / "wrt_phase_newton_residual_screen.cpp"),
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
        "--output",
    ]
    subprocess.run(command + [str(output_a)], check=True)
    subprocess.run(command + [str(output_b)], check=True)
    assert output_a.read_bytes() == output_b.read_bytes()
    receipt = json.loads(output_a.read_text())
    assert receipt["causality"] == {
        "prediction_precedes_truth": True,
        "statistics_update_after_truth": True,
        "payload_bytes": 0,
    }
    assert [
        variant["prior_observations"] for variant in receipt["variants"][:3]
    ] == [
        64,
        256,
        1024,
    ]
    assert receipt["selected_newton_variant"].startswith("newton_prior")
    assert [variant["variant_id"] for variant in receipt["variants"][-2:]] == [
        "frozen_phase_control",
        "equal_correction_blend",
    ]
