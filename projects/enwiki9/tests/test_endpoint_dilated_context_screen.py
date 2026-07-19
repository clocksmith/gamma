from __future__ import annotations

import json
from pathlib import Path
import struct
import subprocess

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
TOOL = ROOT / "projects/enwiki9/tools/endpoint_dilated_context_screen.py"
PYTHON = ROOT / ".venv/bin/python"


def test_dilated_context_screen_is_holdout_blind(tmp_path: Path) -> None:
    byte_count = 320
    values = np.asarray(
        [((index * 17) ^ (index >> 3)) & 255 for index in range(byte_count)],
        dtype=np.uint8,
    )
    truth = np.unpackbits(values, bitorder="big")
    base = np.full(len(truth), 32768, dtype="<u2")
    pair_values = np.column_stack((base, base))
    pair = tmp_path / "pair.bin"
    pair.write_bytes(
        b"CMXAUX1\0" + struct.pack("<Q", len(truth)) + pair_values.tobytes()
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
            "--embedding-dims",
            "2",
            "--hidden-dims",
            "4",
            "--epochs",
            "1",
            "--batch-size",
            "32",
        ],
        check=True,
    )
    receipt = json.loads(output.read_text())
    assert receipt["selection"]["holdout_reads_during_selection"] is False
    assert receipt["selection"]["lags"] == [1, 2, 4, 8, 16, 32, 64]
    assert receipt["selection"]["selected_epoch"] == 1
    assert receipt["promotion_authorized"] is False
    assert receipt["model"]["parameter_count"] > 0
