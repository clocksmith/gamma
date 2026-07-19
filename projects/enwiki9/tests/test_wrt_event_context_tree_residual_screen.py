import json
from pathlib import Path
import shutil
import struct
import subprocess

import pytest


TOOLS = Path(__file__).resolve().parents[1] / "tools"
SOURCE = TOOLS / "wrt_event_context_tree_residual_screen.cpp"


@pytest.mark.skipif(shutil.which("g++") is None, reason="g++ unavailable")
def test_screen_is_causal_and_deterministic(tmp_path: Path) -> None:
    rows = 64 * 8
    p1 = tmp_path / "input.p1"
    store = tmp_path / "input.wrt.store"
    binary = tmp_path / "screen"
    output_a = tmp_path / "a.json"
    output_b = tmp_path / "b.json"

    probabilities = bytearray()
    truth = bytes((index * 37 + 11) & 0xFF for index in range(rows // 8))
    for row in range(rows):
        probability = 22000 + ((row * 977) % 24000)
        probabilities.extend(struct.pack("<H", probability))
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
            str(SOURCE),
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
        "event_history_completed_only": True,
        "payload_bytes": 0,
    }
    assert [row["variant_id"] for row in receipt["variants"]] == [
        "phase_prefix_control",
        "nested_completed_event_context",
        "adaptive_phase_prefix_d6",
        "adaptive_phase_prefix_d8",
        "adaptive_phase_prefix_d10",
    ]


@pytest.mark.skipif(shutil.which("g++") is None, reason="g++ unavailable")
def test_screen_builds_with_warnings_as_errors() -> None:
    subprocess.run(
        [
            "g++",
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-fsyntax-only",
            str(SOURCE),
        ],
        check=True,
    )
