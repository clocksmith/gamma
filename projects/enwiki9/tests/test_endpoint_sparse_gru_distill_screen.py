from __future__ import annotations

import json
from pathlib import Path
import struct
import subprocess

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
TOOL = ROOT / "projects/enwiki9/tools/endpoint_sparse_gru_distill_screen.py"
PYTHON = ROOT / ".venv/bin/python"


def test_sparse_gru_screen_preserves_holdout_boundary(tmp_path: Path) -> None:
    byte_count = 320
    values = np.asarray(
        [((index * 29) ^ (index >> 2)) & 255 for index in range(byte_count)],
        dtype=np.uint8,
    )
    truth = np.unpackbits(values, bitorder="big")
    base = np.full(len(truth), 32768, dtype="<u2")
    teacher = np.where(truth, 45000, 20536).astype("<u2")
    endpoints = np.column_stack((teacher, base))
    pair = tmp_path / "pair.bin"
    pair.write_bytes(
        b"CMXAUX1\0" + struct.pack("<Q", len(truth)) + endpoints.tobytes()
    )
    store = tmp_path / "store.bin"
    store.write_bytes(b"store" + values.tobytes())
    output = tmp_path / "receipt.json"
    subprocess.run(
        [
            str(PYTHON),
            str(TOOL),
            "--pair-trace",
            str(pair),
            "--wrt-store",
            str(store),
            "--output",
            str(output),
            "--source-scope-bytes",
            str(byte_count),
            "--cells",
            "4",
            "--embedding-dims",
            "2",
            "--epochs",
            "1",
            "--sequence-bytes",
            "16",
            "--warmup-bytes",
            "4",
            "--batch-size",
            "4",
        ],
        check=True,
    )
    receipt = json.loads(output.read_text())
    assert receipt["selection"]["holdout_reads_during_selection"] is False
    assert [row["split"] for row in receipt["splits"]] == [
        "train",
        "development",
        "holdout",
        "all",
    ]
    assert receipt["model"]["parameter_count"] > 0
    assert receipt["promotion_authorized"] is False
    assert receipt["exact_full_scope_replay"]["baseline_payload_bytes"] > 0
