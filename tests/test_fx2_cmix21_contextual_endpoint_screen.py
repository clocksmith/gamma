from __future__ import annotations

import json
import struct
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "projects/enwiki9/tools/fx2_cmix21_contextual_endpoint_screen.py"


def write_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    trace = tmp_path / "trace.bin"
    store = tmp_path / "stream.store"
    receipt = tmp_path / "endpoint.json"
    rows = 800
    bits = []
    stream = bytearray()
    with trace.open("wb") as output:
        output.write(struct.pack("<8sIIIIIQ", b"CMNEST1\0", 1, 36, 13, 6, 1, rows))
        for row in range(rows):
            bit = int(((row * 17 + row // 7) & 3) != 0)
            base = 36000 if bit else 29000
            endpoint = 60000 if bit else 5000
            output.write(struct.pack("<B6H", bit, base, 32768, 32768, 32768, 32768, endpoint))
            bits.append(bit)
    for start in range(0, rows, 8):
        value = 0
        for bit in bits[start : start + 8]:
            value = (value << 1) | bit
        stream.append(value)
    store.write_bytes(b"\x80\x00\x00\x00\x00" + stream)
    receipt.write_text(
        json.dumps(
            {
                "fixed_blend_dev_ranking": [
                    {
                        "endpoint": 5,
                        "endpoint_name": "strong_endpoint",
                        "weight_ppm": 1_000_000,
                    }
                ]
            }
        )
    )
    return trace, store, receipt


def test_contextual_screen_validates_identity_and_scores_holdout(tmp_path: Path) -> None:
    trace, store, receipt = write_inputs(tmp_path)
    output = tmp_path / "screen.json"
    subprocess.run(
        [
            "/usr/bin/python3",
            str(TOOL),
            "--trace",
            str(trace),
            "--store",
            str(store),
            "--endpoint-receipt",
            str(receipt),
            "--output",
            str(output),
            "--raw-scope-bytes",
            "100",
            "--minimum-train-rows",
            "1",
        ],
        check=True,
    )
    result = json.loads(output.read_text())
    assert result["inputs"]["store"]["truth_identity"] is True
    assert result["selected_on_dev"]["holdout_gain_bytes_per_1m_raw"] > 500
    assert result["promotion_authorized"] is False


def test_contextual_screen_rejects_store_truth_drift(tmp_path: Path) -> None:
    trace, store, receipt = write_inputs(tmp_path)
    drifted = bytearray(store.read_bytes())
    drifted[-1] ^= 1
    store.write_bytes(drifted)
    completed = subprocess.run(
        [
            "/usr/bin/python3",
            str(TOOL),
            "--trace",
            str(trace),
            "--store",
            str(store),
            "--endpoint-receipt",
            str(receipt),
            "--output",
            str(tmp_path / "screen.json"),
            "--raw-scope-bytes",
            "100",
        ],
        text=True,
        capture_output=True,
    )
    assert completed.returncode != 0
    assert "truth differs" in completed.stderr
