from __future__ import annotations

import argparse
import importlib.util
import struct
import sys
from pathlib import Path

import numpy as np


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "projects/enwiki9/tools/cmix_aux_logit_blend_screen.py"
)
SPEC = importlib.util.spec_from_file_location("cmix_aux_logit_blend_screen", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def fixture_args(tmp_path: Path) -> argparse.Namespace:
    rows = 800
    truth = np.tile(np.asarray([0, 1], dtype=np.uint8), rows // 2)
    base = np.full(rows, 32768, dtype="<u2")
    endpoint = np.where(truth != 0, 57344, 8192).astype("<u2")
    pair = tmp_path / "pair.bin"
    pair.write_bytes(
        MODULE.PAIR_MAGIC
        + struct.pack("<Q", rows)
        + np.column_stack((base, endpoint)).astype("<u2").tobytes()
    )
    base_p1 = tmp_path / "base.p1"
    base_p1.write_bytes(b"CMX21P1\0" + struct.pack("<Q", rows) + base.tobytes())
    wrt_store = tmp_path / "input.store"
    wrt_store.write_bytes(b"WRT1\0" + np.packbits(truth, bitorder="big").tobytes())
    _, base_payload, _ = MODULE.exact_replay(truth, base, base)
    archive = tmp_path / "archive.comp"
    archive.write_bytes(bytes([0, 0, 0, 0, 100]) + base_payload)
    return argparse.Namespace(
        pair_trace=pair,
        endpoint_p1=None,
        base_p1=base_p1,
        base_archive=archive,
        candidate_reference_archive=None,
        wrt_store=wrt_store,
        raw_scope_bytes=100,
        output=tmp_path / "receipt.json",
        candidate_payload=tmp_path / "candidate.payload",
        candidate_p1=tmp_path / "candidate.p1",
        dev_start_ppm=600_000,
        holdout_start_ppm=800_000,
        weights=(100_000, 250_000, 500_000),
        chunk_rows=73,
        holdout_blocks=4,
        max_regressing_blocks=0,
        max_largest_regression_bytes=0,
        max_total_regression_bytes=0,
        required_incremental_bytes_per_1m=1.0,
        mix_mode="native_q16",
    )


def test_same_state_endpoint_passes_all_identity_and_holdout_gates(tmp_path: Path) -> None:
    receipt = MODULE.run(fixture_args(tmp_path))

    assert receipt["scope"]["selection_reads_holdout"] is False
    assert receipt["identity"]["pair_base_equals_frozen_base_p1"] is True
    assert receipt["identity"]["archive_payload_identity"] is True
    assert receipt["exact_replay"]["full"]["saved_bytes"] > 0
    assert receipt["exact_replay"]["holdout"]["saved_bytes"] > 0
    assert receipt["guardrails"]["regret_budget_pass"] is True
    assert receipt["verdict"] == (
        "causal_endpoint_pass_requires_native_fixed_point_integration"
    )


def test_pair_base_mismatch_fails_closed(tmp_path: Path) -> None:
    args = fixture_args(tmp_path)
    pair = bytearray(args.pair_trace.read_bytes())
    pair[MODULE.PAIR_HEADER_BYTES] ^= 1
    args.pair_trace.write_bytes(pair)

    receipt = MODULE.run(args)

    assert receipt["identity"]["pair_base_equals_frozen_base_p1"] is False
    assert receipt["verdict"] == "retire_same_state_auxiliary_endpoint"


def test_standalone_endpoint_trace_uses_frozen_base(tmp_path: Path) -> None:
    args = fixture_args(tmp_path)
    pair = np.memmap(
        args.pair_trace,
        dtype="<u2",
        mode="r",
        offset=MODULE.PAIR_HEADER_BYTES,
        shape=(800, 2),
    )
    endpoint = tmp_path / "endpoint.p1"
    endpoint.write_bytes(
        MODULE.ENDPOINT_MAGIC
        + struct.pack("<Q", 800)
        + np.asarray(pair[:, 1], dtype="<u2").tobytes()
    )
    args.pair_trace = None
    args.endpoint_p1 = endpoint

    receipt = MODULE.run(args)

    assert receipt["identity"]["trace_kind"] == "independent_causal_endpoint"
    assert receipt["identity"]["pair_base_equals_frozen_base_p1"] is True
    assert receipt["inputs"]["pair_trace"] is None
    assert receipt["inputs"]["endpoint_p1"]["bytes"] == endpoint.stat().st_size
    assert receipt["exact_replay"]["full"]["saved_bytes"] > 0


def test_standalone_endpoint_accepts_generic_p1_header(tmp_path: Path) -> None:
    args = fixture_args(tmp_path)
    pair = np.memmap(
        args.pair_trace,
        dtype="<u2",
        mode="r",
        offset=MODULE.PAIR_HEADER_BYTES,
        shape=(800, 2),
    )
    endpoint = tmp_path / "generic.p1"
    endpoint.write_bytes(
        b"CMX21P1\0"
        + struct.pack("<Q", 800)
        + np.asarray(pair[:, 1], dtype="<u2").tobytes()
    )
    args.pair_trace = None
    args.endpoint_p1 = endpoint

    receipt = MODULE.run(args)

    assert receipt["identity"]["trace_kind"] == "independent_causal_endpoint"
    assert receipt["exact_replay"]["full"]["saved_bytes"] > 0


def test_native_q16_blend_is_symmetric_and_bounded() -> None:
    base = np.asarray([1, 8192, 32768, 57344, 65535], dtype=np.uint16)
    endpoint = np.asarray([65535, 57344, 32768, 8192, 1], dtype=np.uint16)

    mixed = MODULE.mix_native_q16(base, endpoint, 500_000)

    assert mixed.tolist() == [32768, 32768, 32768, 32768, 32768]
    assert np.all((mixed >= 1) & (mixed <= 65535))


def test_candidate_reference_mismatch_fails_closed(tmp_path: Path) -> None:
    args = fixture_args(tmp_path)
    reference = tmp_path / "candidate-reference.comp"
    reference.write_bytes(bytes([0, 0, 0, 0, 100]) + b"not-the-candidate")
    args.candidate_reference_archive = reference

    receipt = MODULE.run(args)

    assert receipt["identity"]["candidate_payload_equals_native_reference"] is False
    assert receipt["verdict"] == "retire_same_state_auxiliary_endpoint"
