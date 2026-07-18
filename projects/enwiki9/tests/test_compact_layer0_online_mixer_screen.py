from __future__ import annotations

from pathlib import Path
import struct
import subprocess

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "projects/enwiki9/tools/compact_layer0_online_mixer_screen.cpp"


def write_inputs(directory: Path, rows: int = 800) -> tuple[Path, Path, Path, Path]:
    truth = np.asarray([(index * 17 + index // 11) & 1 for index in range(rows)], dtype=np.uint8)
    base = np.full(rows, 32768, dtype="<u2")
    endpoints = np.full((rows, 26), 32768, dtype="<u2")
    endpoints[:, 0] = np.where(truth, 45000, 20536).astype("<u2")

    layer = directory / "layer0.p1pack"
    layer.write_bytes(b"CML0P1V1" + struct.pack("<Q", rows) + endpoints.tobytes())
    base_path = directory / "base.p1"
    base_path.write_bytes(b"CMX21P1\0" + struct.pack("<Q", rows) + base.tobytes())
    pair = directory / "pair.bin"
    pair_values = np.column_stack((base, endpoints[:, 0])).astype("<u2")
    pair.write_bytes(b"CMXAUX1\0" + struct.pack("<Q", rows) + pair_values.tobytes())
    store = directory / "store.bin"
    store.write_bytes(b"abcde" + np.packbits(truth, bitorder="big").tobytes())
    return layer, pair, base_path, store


def test_online_screen_is_deterministic_and_holdout_blind(tmp_path: Path) -> None:
    binary = tmp_path / "screen"
    subprocess.run(
        ["g++", "-std=c++17", "-O2", str(SOURCE), "-o", str(binary)],
        check=True,
    )
    layer, pair, base, store = write_inputs(tmp_path)
    output_p1 = tmp_path / "candidate.p1"
    output_json = tmp_path / "receipt.json"
    subprocess.run(
        [
            str(binary),
            "--layer0-trace",
            str(layer),
            "--pair-trace",
            str(pair),
            "--base-p1",
            str(base),
            "--wrt-store",
            str(store),
            "--output-p1",
            str(output_p1),
            "--output-json",
            str(output_json),
        ],
        check=True,
    )

    import json

    receipt = json.loads(output_json.read_text())
    assert receipt["scope"]["selection_reads_holdout"] is False
    assert receipt["deterministic_probability_replay"] is True
    assert output_p1.stat().st_size == 16 + 2 * 800
    assert receipt["selection"]["dev_gain_qbits"] > 0
