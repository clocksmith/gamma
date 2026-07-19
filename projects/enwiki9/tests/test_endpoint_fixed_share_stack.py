from __future__ import annotations

import json
from pathlib import Path
import struct
import subprocess

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "projects/enwiki9/tools/endpoint_fixed_share_stack.cpp"


def write_p1(path: Path, probabilities: np.ndarray) -> None:
    path.write_bytes(
        b"CMX21P1\0"
        + struct.pack("<Q", len(probabilities))
        + probabilities.astype("<u2").tobytes()
    )


def test_fixed_share_stack_is_deterministic_and_holdout_blind(tmp_path: Path) -> None:
    rows = 800
    truth = np.asarray(
        [(index * 17 + index // 11) & 1 for index in range(rows)],
        dtype=np.uint8,
    )
    base = np.full(rows, 32768, dtype=np.uint16)
    alternate = np.where(truth, 45000, 20536).astype(np.uint16)
    base_path = tmp_path / "base.p1"
    alternate_path = tmp_path / "alternate.p1"
    store = tmp_path / "store.bin"
    write_p1(base_path, base)
    write_p1(alternate_path, alternate)
    store.write_bytes(b"abcde" + np.packbits(truth, bitorder="big").tobytes())

    binary = tmp_path / "fixed-share"
    subprocess.run(
        ["g++", "-std=c++17", "-O2", str(SOURCE), "-o", str(binary)],
        check=True,
    )
    output_p1 = tmp_path / "candidate.p1"
    output_json = tmp_path / "screen.json"
    subprocess.run(
        [
            str(binary),
            "--endpoint",
            f"base={base_path}",
            "--endpoint",
            f"alternate={alternate_path}",
            "--wrt-store",
            str(store),
            "--output-p1",
            str(output_p1),
            "--output-json",
            str(output_json),
        ],
        check=True,
    )

    result = json.loads(output_json.read_text())
    assert result["scope"]["selection_reads_holdout"] is False
    assert result["causality"]["prediction_precedes_truth"] is True
    assert result["causality"]["posterior_updates_after_truth"] is True
    assert result["deterministic_probability_replay"] is True
    assert result["qbit_replay"]["holdout_gain_qbits"] > 0
    assert output_p1.stat().st_size == 16 + rows * 2
