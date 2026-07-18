from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import struct
import sys

import numpy as np


TOOL = Path(__file__).resolve().parents[1] / "tools/compact_layer0_blend_screen.py"
SPEC = importlib.util.spec_from_file_location("compact_layer0_blend_screen", TOOL)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def fixture(tmp_path: Path) -> argparse.Namespace:
    rows = 800
    truth = np.tile(np.asarray([0, 1], dtype=np.uint8), rows // 2)
    base = np.full(rows, 32768, dtype="<u2")
    endpoint0 = np.where(truth != 0, 57344, 8192).astype("<u2")
    endpoint1 = np.where(truth != 0, 40960, 24576).astype("<u2")
    endpoints = np.column_stack((endpoint0, endpoint1)).astype("<u2")
    packed = tmp_path / "layer0.bin"
    packed.write_bytes(
        MODULE.PACKED_MAGIC + struct.pack("<Q", rows) + endpoints.tobytes()
    )
    base_p1 = tmp_path / "base.p1"
    base_p1.write_bytes(b"CMX21P1\0" + struct.pack("<Q", rows) + base.tobytes())
    store = tmp_path / "input.store"
    store.write_bytes(b"WRT1\0" + np.packbits(truth, bitorder="big").tobytes())
    _, payload, _ = MODULE.exact_replay(truth, base, base)
    archive = tmp_path / "archive.comp"
    archive.write_bytes(bytes([0, 0, 0, 0, 100]) + payload)
    pair = tmp_path / "pair.bin"
    pair.write_bytes(b"identity")
    return argparse.Namespace(
        layer0_trace=packed,
        base_p1=base_p1,
        base_archive=archive,
        wrt_store=store,
        raw_scope_bytes=100,
        output=tmp_path / "receipt.json",
        candidate_payload=tmp_path / "candidate.payload",
        candidate_p1=tmp_path / "candidate.p1",
        instrumented_archive=archive,
        reference_native_archive=archive,
        instrumented_pair_trace=pair,
        reference_pair_trace=pair,
        dev_start_ppm=600_000,
        holdout_start_ppm=800_000,
        coefficients=(-250_000, 250_000, 500_000),
        chunk_rows=73,
        holdout_blocks=4,
        remaining_debt_bytes_per_1m=1.0,
        provisional_code_bytes=0,
        max_regressing_blocks=0,
        max_largest_regression_bytes=0,
        max_total_regression_bytes=0,
    )


def test_selects_endpoint_and_coefficient_on_dev_only(tmp_path: Path) -> None:
    receipt = MODULE.run(fixture(tmp_path))

    assert receipt["scope"]["selection_reads_holdout"] is False
    assert receipt["scope"]["endpoint_count"] == 2
    assert receipt["selection"]["selected_endpoint_index"] == 0
    assert receipt["selection"]["selected_coefficient_ppm"] == 500_000
    assert receipt["identity"]["all_required_identities_pass"] is True
    assert receipt["exact_replay"]["full"]["saved_bytes"] > 0
    assert receipt["verdict"] == (
        "compact_layer0_endpoint_pass_requires_native_integration"
    )


def test_identity_mismatch_fails_closed(tmp_path: Path) -> None:
    args = fixture(tmp_path)
    other = tmp_path / "other.comp"
    other.write_bytes(b"different")
    args.reference_native_archive = other

    receipt = MODULE.run(args)

    assert receipt["identity"]["instrumented_archive_byte_identity"] is False
    assert receipt["verdict"] == "retire_compact_layer0_endpoint_universe"


def test_signed_native_mix_can_move_away_from_endpoint() -> None:
    base = np.asarray([32768], dtype=np.uint16)
    endpoint = np.asarray([49152], dtype=np.uint16)

    toward = MODULE.mix_signed_native_q16(base, endpoint, 250_000)[0]
    away = MODULE.mix_signed_native_q16(base, endpoint, -250_000)[0]

    assert toward > base[0]
    assert away < base[0]


def test_positive_signed_mix_matches_existing_native_blend() -> None:
    base = np.asarray([1, 8192, 32768, 57344, 65535], dtype=np.uint16)
    endpoint = np.asarray([65535, 57344, 32768, 8192, 1], dtype=np.uint16)

    expected = MODULE.mix_native_q16(base, endpoint, 225_000)
    observed = MODULE.mix_signed_native_q16(base, endpoint, 225_000)

    assert np.array_equal(observed, expected)


def test_packed_header_rejects_nonintegral_dimensions(tmp_path: Path) -> None:
    path = tmp_path / "bad.bin"
    path.write_bytes(MODULE.PACKED_MAGIC + struct.pack("<Q", 3) + b"12345")

    try:
        MODULE.read_packed_header(path)
    except ValueError as error:
        assert "dimensions" in str(error)
    else:
        raise AssertionError("invalid packed trace was accepted")
