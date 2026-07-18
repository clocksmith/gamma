from __future__ import annotations

import argparse
import importlib.util
import struct
import sys
from pathlib import Path

import numpy as np


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "projects/enwiki9/tools/fx2_attribution_external_base_screen.py"
)
SPEC = importlib.util.spec_from_file_location(
    "fx2_attribution_external_base_screen", MODULE_PATH
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def write_fixture(tmp_path: Path) -> argparse.Namespace:
    rows = 800
    raw_count = sum(MODULE.EXPECTED_GROUP_COUNTS)
    layer0_count = 23
    words_per_row = 4 + raw_count + layer0_count
    row_bytes = 2 * words_per_row
    truth = np.tile(np.asarray([0, 1], dtype=np.uint8), rows // 2)
    base = np.full(rows, 32768, dtype="<u2")

    trace_rows = np.full((rows, words_per_row), 32768, dtype="<u2")
    trace_rows[:, 3] = 0
    ppmd_raw_index = sum(MODULE.EXPECTED_GROUP_COUNTS[:6])
    ppmd_column = 4 + ppmd_raw_index
    trace_rows[:, ppmd_column] = np.where(truth != 0, 57344, 8192)

    header = bytearray(MODULE.ATTRIBUTION_HEADER_BYTES)
    header[:8] = MODULE.ATTRIBUTION_MAGIC
    struct.pack_into("<Q", header, 8, rows)
    struct.pack_into(
        "<4I",
        header,
        16,
        MODULE.ATTRIBUTION_HEADER_BYTES,
        row_bytes,
        raw_count,
        layer0_count,
    )
    struct.pack_into("<8H", header, 32, *MODULE.EXPECTED_GROUP_COUNTS)
    struct.pack_into("<I", header, 48, 0x0F)
    attribution = tmp_path / "attribution.bin"
    attribution.write_bytes(bytes(header) + trace_rows.tobytes())

    base_p1 = tmp_path / "base.p1"
    base_p1.write_bytes(b"CMX21P1\0" + struct.pack("<Q", rows) + base.tobytes())
    wrt_store = tmp_path / "input.store"
    wrt_store.write_bytes(b"WRT1\0" + np.packbits(truth, bitorder="big").tobytes())

    _, base_payload, _ = MODULE.exact_replay(truth, base, base)
    base_archive = tmp_path / "archive.comp"
    base_archive.write_bytes(bytes([0, 0, 0, 0, 100]) + base_payload)
    output = tmp_path / "screen.json"
    return argparse.Namespace(
        attribution_trace=attribution,
        trace_inspection_receipt=None,
        base_p1=base_p1,
        base_archive=base_archive,
        base_archive_header_bytes=5,
        wrt_store=wrt_store,
        raw_scope_bytes=100,
        output=output,
        candidate_payload=tmp_path / "candidate.payload",
        dev_start_ppm=600_000,
        holdout_start_ppm=800_000,
        chunk_rows=73,
        shortlist=16,
        top_exact=4,
        force_endpoint_name=None,
        holdout_blocks=4,
        weights=(125_000, 250_000, 500_000),
        mix_space="probability",
        required_incremental_bytes_per_1m=1.0,
        discovery_headroom_bytes_per_1m=2.0,
    )


def test_screen_selects_paying_ppmd_endpoint_and_proves_base_identity(tmp_path: Path) -> None:
    args = write_fixture(tmp_path)

    receipt = MODULE.run(args)

    assert receipt["scope"]["selection_reads_holdout"] is False
    assert receipt["selected"]["endpoint_name"] == "raw_ppmd_0"
    assert receipt["selected"]["dependency_class"] == "ppmd_only"
    assert receipt["exact_replay"]["base_archive_payload_identity"] is True
    assert receipt["exact_replay"]["full"]["saved_bytes"] > 0
    assert receipt["exact_replay"]["holdout"]["saved_bytes"] > 0
    assert receipt["exact_replay"]["holdout_block_audit"]["regressing_blocks"] == 0
    assert receipt["verdict"] == (
        "component_candidate_requires_dependency_rss_and_native_replay"
    )


def test_screen_fails_closed_on_base_archive_mismatch(tmp_path: Path) -> None:
    args = write_fixture(tmp_path)
    archive = bytearray(args.base_archive.read_bytes())
    archive[-1] ^= 1
    args.base_archive.write_bytes(archive)

    receipt = MODULE.run(args)

    assert receipt["exact_replay"]["base_archive_payload_identity"] is False
    assert receipt["verdict"] == "retire_measured_fx2_component_universe_over_external_base"


def test_forced_endpoint_freezes_identity_but_selects_weight_on_dev(tmp_path: Path) -> None:
    args = write_fixture(tmp_path)
    args.force_endpoint_name = "fx2_final"

    receipt = MODULE.run(args)

    assert receipt["scope"]["forced_endpoint_name"] == "fx2_final"
    assert receipt["selected"]["endpoint_name"] == "fx2_final"
    assert receipt["evidence_level"].startswith("development_weight_selected")


def test_logit_mix_is_bounded() -> None:
    base = np.asarray([1, 32768, 65535], dtype=np.uint16)
    endpoint = np.asarray([65535, 32768, 1], dtype=np.uint16)

    mixed = MODULE.mix_endpoint(base, endpoint, 250_000, "logit")

    assert mixed.dtype == np.uint16
    assert np.all(mixed >= 1)
    assert np.all(mixed <= 65535)
