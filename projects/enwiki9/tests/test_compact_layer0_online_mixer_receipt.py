from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct

import numpy as np

from projects.enwiki9.tools.compact_layer0_online_mixer_receipt import run
from projects.enwiki9.tools.fx2_attribution_external_base_screen import exact_replay


def test_receipt_seals_exact_identity_and_economics(tmp_path: Path) -> None:
    rows = 800
    truth = np.asarray([(index * 7) & 1 for index in range(rows)], dtype=np.uint8)
    base = np.full(rows, 32768, dtype="<u2")
    candidate = np.where(truth, 40000, 25536).astype("<u2")
    base_path = tmp_path / "base.p1"
    candidate_path = tmp_path / "candidate.p1"
    base_path.write_bytes(b"CMX21P1\0" + struct.pack("<Q", rows) + base.tobytes())
    candidate_path.write_bytes(
        b"CMX21P1\0" + struct.pack("<Q", rows) + candidate.tobytes()
    )
    store = tmp_path / "store.bin"
    store.write_bytes(b"abcde" + np.packbits(truth, bitorder="big").tobytes())
    exact, base_payload, _ = exact_replay(truth, base, candidate)
    archive = tmp_path / "archive.bin"
    archive.write_bytes(b"\0" * 5 + base_payload)
    source = tmp_path / "screen.cpp"
    binary = tmp_path / "screen.bin"
    source.write_text("source\n")
    binary.write_bytes(b"binary")
    train_end = 480
    dev_end = 640

    from projects.enwiki9.tools.compact_layer0_online_mixer_receipt import qbit_gain

    screen = tmp_path / "screen.json"
    screen.write_text(
        json.dumps(
            {
                "schema": "compact_layer0_online_mixer_screen_v1",
                "scope": {
                    "rows": rows,
                    "train_end_row": train_end,
                    "dev_end_row": dev_end,
                    "selection_reads_holdout": False,
                },
                "selection": {"name": "synthetic"},
                "causality": {"prediction_precedes_current_truth": True},
                "deterministic_probability_replay": True,
                "qbit_replay": {
                    "train_gain_qbits": qbit_gain(
                        truth[:train_end], base[:train_end], candidate[:train_end]
                    ),
                    "dev_gain_qbits": qbit_gain(
                        truth[train_end:dev_end],
                        base[train_end:dev_end],
                        candidate[train_end:dev_end],
                    ),
                    "holdout_gain_qbits": qbit_gain(
                        truth[dev_end:], base[dev_end:], candidate[dev_end:]
                    ),
                },
            }
        )
    )
    output_payload = tmp_path / "payload.bin"
    args = argparse.Namespace(
        screen_json=screen,
        screen_source=source,
        screen_binary=binary,
        base_p1=base_path,
        candidate_p1=candidate_path,
        pair_trace=None,
        base_archive=archive,
        wrt_store=store,
        raw_scope_bytes=100,
        output=tmp_path / "receipt.json",
        candidate_payload=output_payload,
        instrumented_archive=None,
        reference_native_archive=None,
        instrumented_pair_trace=None,
        reference_pair_trace=None,
        holdout_blocks=4,
        remaining_debt_bytes_per_1m=0.0,
        provisional_code_bytes=0,
        max_regressing_blocks=0,
        max_largest_regression_bytes=0,
        max_total_regression_bytes=0,
    )

    receipt = run(args)

    assert receipt["identity"]["all_required_identities_pass"] is True
    assert receipt["economics"]["full_and_holdout_clear_required_rate"] is True
    assert receipt["verdict"] == "compact_layer0_online_mixer_pass_requires_native_integration"
    assert receipt["exact_replay"]["full"] == exact
