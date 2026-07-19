from __future__ import annotations

import json
from pathlib import Path
import struct
import subprocess

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "projects/enwiki9/tools/endpoint_diagonal_reservoir_screen.cpp"


def write_inputs(directory: Path, rows: int = 800) -> tuple[Path, Path]:
    truth = np.asarray(
        [((index // 8) * 29 + index // 31) & 1 for index in range(rows)],
        dtype=np.uint8,
    )
    base = np.full(rows, 32768, dtype="<u2")
    p1 = directory / "base.p1"
    p1.write_bytes(b"CMX21P1\0" + struct.pack("<Q", rows) + base.tobytes())
    store = directory / "store.bin"
    store.write_bytes(b"abcde" + np.packbits(truth, bitorder="big").tobytes())
    return p1, store


def test_diagonal_reservoir_is_deterministic_and_holdout_blind(tmp_path: Path) -> None:
    binary = tmp_path / "screen"
    subprocess.run(
        ["g++", "-std=c++17", "-O2", str(SOURCE), "-o", str(binary)],
        check=True,
    )
    p1, store = write_inputs(tmp_path)
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    command = [str(binary), "--p1", str(p1), "--wrt-store", str(store)]
    subprocess.run(command + ["--output", str(first)], check=True)
    subprocess.run(command + ["--output", str(second)], check=True)

    assert first.read_bytes() == second.read_bytes()
    receipt = json.loads(first.read_text())
    assert receipt["selection_reads_holdout"] is False
    assert receipt["rows"] == 800
    assert len(receipt["variants"]) == 35
    assert all(row["state_bytes"] < 20000 for row in receipt["variants"])
    zero_rate = [
        row for row in receipt["variants"] if row["update_shift"] == 44
    ]
    assert all(row["max_absolute_weight"] == 0 for row in zero_rate)
    assert all(row["exact_saved_bytes"] == 0 for row in zero_rate)


def test_diagonal_reservoir_reads_selected_pair_endpoint(tmp_path: Path) -> None:
    binary = tmp_path / "screen"
    subprocess.run(
        ["g++", "-std=c++17", "-O2", str(SOURCE), "-o", str(binary)],
        check=True,
    )
    p1, store = write_inputs(tmp_path)
    raw = p1.read_bytes()
    rows = struct.unpack_from("<Q", raw, 8)[0]
    base = np.frombuffer(raw, dtype="<u2", offset=16).copy()
    pair = tmp_path / "pair.bin"
    endpoints = np.column_stack((np.full(rows, 16384, dtype="<u2"), base))
    pair.write_bytes(b"CMXAUX1\0" + struct.pack("<Q", rows) + endpoints.tobytes())
    output = tmp_path / "pair.json"
    subprocess.run(
        [
            str(binary),
            "--pair-trace",
            str(pair),
            "--pair-endpoint",
            "1",
            "--wrt-store",
            str(store),
            "--output",
            str(output),
        ],
        check=True,
    )
    receipt = json.loads(output.read_text())
    assert receipt["base_trace_kind"] == "same_execution_pair_endpoint"
    assert receipt["pair_endpoint"] == 1
