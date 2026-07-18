#!/usr/bin/env python3
"""Validate a native endpoint428 paired trace and emit its hybrid FX2PT01 view."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
from typing import Any

import numpy as np


PAIR_MAGIC = b"CMXPAIR1"
PAIR_HEADER = struct.Struct("<8sIIIIQ")
PAIR_VERSION = 1
PAIR_HEADER_BYTES = PAIR_HEADER.size
PAIR_ROW_BYTES = 7
PAIR_FIELD_MASK = 7
PAIR_DTYPE = np.dtype(
    [
        ("compact_base_p1", "<u2"),
        ("endpoint428_p1", "<u2"),
        ("hybrid_p1", "<u2"),
        ("bit", "u1"),
    ]
)
P1_MAGICS = (b"CMX21P1\0", b"FX2P1V1\0")
P1_HEADER_BYTES = 16
FX2PT_MAGIC = b"FX2PT01\n"
FX2PT_DTYPE = np.dtype([("p1", "<u2"), ("bit", "u1")])
TOTAL = 1 << 16
MAX_CODE = (1 << 32) - 1


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def read_pair_rows(path: Path) -> int:
    with path.open("rb") as source:
        header = source.read(PAIR_HEADER_BYTES)
    if len(header) != PAIR_HEADER_BYTES:
        raise ValueError("truncated endpoint428 paired-trace header")
    magic, version, header_bytes, row_bytes, field_mask, rows = PAIR_HEADER.unpack(
        header
    )
    if (
        magic != PAIR_MAGIC
        or version != PAIR_VERSION
        or header_bytes != PAIR_HEADER_BYTES
        or row_bytes != PAIR_ROW_BYTES
        or field_mask != PAIR_FIELD_MASK
    ):
        raise ValueError("invalid endpoint428 paired-trace contract")
    if rows <= 0 or rows % 8:
        raise ValueError("paired-trace rows must be positive and WRT-byte aligned")
    if path.stat().st_size != PAIR_HEADER_BYTES + rows * PAIR_ROW_BYTES:
        raise ValueError("paired-trace size does not match its row count")
    return rows


def read_p1_rows(path: Path) -> int:
    with path.open("rb") as source:
        header = source.read(P1_HEADER_BYTES)
    if len(header) != P1_HEADER_BYTES or header[:8] not in P1_MAGICS:
        raise ValueError("invalid final-P1 header")
    rows = int.from_bytes(header[8:16], "little")
    if rows <= 0 or path.stat().st_size != P1_HEADER_BYTES + rows * 2:
        raise ValueError("final-P1 size does not match its row count")
    return rows


def archive_payload_bytes(path: Path) -> tuple[int, int]:
    with path.open("rb") as source:
        header = source.read(5)
    if len(header) != 5:
        raise ValueError("truncated endpoint428 archive")
    wrt_bytes = header[0] & 0x7F
    for value in header[1:]:
        wrt_bytes = (wrt_bytes << 8) | value
    header_bytes = 5 if wrt_bytes < 10_000 else 37
    payload_bytes = path.stat().st_size - header_bytes
    if payload_bytes <= 0:
        raise ValueError("endpoint428 archive has no arithmetic payload")
    return payload_bytes, wrt_bytes


class RangeCounter:
    def __init__(self) -> None:
        self.x1 = 0
        self.x2 = MAX_CODE
        self.bytes = 0

    def encode(self, bit: int, p1: int) -> None:
        delta = self.x2 - self.x1
        midpoint = self.x1 + (delta >> 16) * p1 + (
            (delta & 0xFFFF) * p1 >> 16
        )
        if bit:
            self.x2 = midpoint
        else:
            self.x1 = midpoint + 1
        while ((self.x1 ^ self.x2) & 0xFF000000) == 0:
            self.bytes += 1
            self.x1 = (self.x1 << 8) & MAX_CODE
            self.x2 = ((self.x2 << 8) & MAX_CODE) + 255

    def finish(self) -> None:
        while ((self.x1 ^ self.x2) & 0xFF000000) == 0:
            self.bytes += 1
            self.x1 = (self.x1 << 8) & MAX_CODE
            self.x2 = ((self.x2 << 8) & MAX_CODE) + 255
        self.bytes += 1


def materialize(
    paired_path: Path,
    output_path: Path,
    *,
    final_p1_path: Path | None = None,
    archive_path: Path | None = None,
    trace_off_archive_path: Path | None = None,
    input_path: Path | None = None,
    restored_path: Path | None = None,
    binary_path: Path | None = None,
    state_origin: str,
    scope_bytes: int,
    chunk_rows: int = 1 << 20,
) -> dict[str, Any]:
    rows = read_pair_rows(paired_path)
    if chunk_rows <= 0:
        raise ValueError("chunk rows must be positive")
    aligned_chunk_rows = max(8, chunk_rows - chunk_rows % 8)
    if scope_bytes <= 0:
        raise ValueError("scope bytes must be positive")
    if (input_path is None) != (restored_path is None):
        raise ValueError("input and restored paths must be supplied together")

    paired = np.memmap(
        paired_path,
        mode="r",
        dtype=PAIR_DTYPE,
        offset=PAIR_HEADER_BYTES,
        shape=(rows,),
    )
    final_p1 = None
    final_rows_match: bool | None = None
    if final_p1_path is not None:
        final_rows = read_p1_rows(final_p1_path)
        final_rows_match = final_rows == rows
        if final_rows_match:
            final_p1 = np.memmap(
                final_p1_path,
                mode="r",
                dtype="<u2",
                offset=P1_HEADER_BYTES,
                shape=(rows,),
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.unlink(missing_ok=True)
    expected_output_bytes = len(FX2PT_MAGIC) + rows * FX2PT_DTYPE.itemsize
    with temporary.open("wb") as target:
        target.write(FX2PT_MAGIC)
        target.truncate(expected_output_bytes)
    output = np.memmap(
        temporary,
        mode="r+",
        dtype=FX2PT_DTYPE,
        offset=len(FX2PT_MAGIC),
        shape=(rows,),
    )

    probabilities_valid = True
    truth_valid = True
    hybrid_equals_final_p1: bool | None = None if final_p1 is None else True
    wrt_digest = hashlib.sha256()
    range_counter = RangeCounter() if archive_path is not None else None
    for start in range(0, rows, aligned_chunk_rows):
        end = min(rows, start + aligned_chunk_rows)
        part = paired[start:end]
        for field in ("compact_base_p1", "endpoint428_p1", "hybrid_p1"):
            values = part[field]
            probabilities_valid &= bool(np.all((values > 0) & (values < TOTAL)))
        bits = part["bit"]
        truth_valid &= bool(np.all(bits <= 1))
        output["p1"][start:end] = part["hybrid_p1"]
        output["bit"][start:end] = bits
        if final_p1 is not None:
            hybrid_equals_final_p1 &= bool(
                np.array_equal(part["hybrid_p1"], final_p1[start:end])
            )
        wrt_digest.update(np.packbits(bits, bitorder="big").tobytes())
        if range_counter is not None:
            for row in part:
                range_counter.encode(int(row["bit"]), int(row["hybrid_p1"]))
    output.flush()
    del output
    if final_p1 is not None:
        del final_p1
    del paired
    with temporary.open("rb") as target:
        os.fsync(target.fileno())
    os.replace(temporary, output_path)
    if output_path.stat().st_size != expected_output_bytes:
        raise RuntimeError("materialized FX2PT01 trace has an unexpected size")

    archive_identity: bool | None = None
    payload_match: bool | None = None
    archive_wrt_match: bool | None = None
    replay_payload_bytes: int | None = None
    archive_payload: int | None = None
    archive_wrt_bytes: int | None = None
    if archive_path is not None:
        assert range_counter is not None
        range_counter.finish()
        replay_payload_bytes = range_counter.bytes
        archive_payload, archive_wrt_bytes = archive_payload_bytes(archive_path)
        payload_match = replay_payload_bytes == archive_payload
        archive_wrt_match = rows // 8 == archive_wrt_bytes
        if trace_off_archive_path is not None:
            archive_identity = (
                archive_path.stat().st_size == trace_off_archive_path.stat().st_size
                and sha256_file(archive_path) == sha256_file(trace_off_archive_path)
            )

    roundtrip_ok: bool | None = None
    if input_path is not None and restored_path is not None:
        roundtrip_ok = (
            input_path.stat().st_size == restored_path.stat().st_size
            and sha256_file(input_path) == sha256_file(restored_path)
        )

    identity_checks = (
        final_rows_match,
        hybrid_equals_final_p1,
        archive_identity,
        payload_match,
        archive_wrt_match,
        roundtrip_ok,
    )
    identity_complete = all(check is True for check in identity_checks)
    accepted = probabilities_valid and truth_valid and identity_complete
    inputs: dict[str, Any] = {"paired_trace": artifact(paired_path)}
    for name, path in (
        ("final_p1", final_p1_path),
        ("archive_trace_on", archive_path),
        ("archive_trace_off", trace_off_archive_path),
        ("input", input_path),
        ("restored", restored_path),
        ("binary", binary_path),
    ):
        if path is not None:
            inputs[name] = artifact(path)
    return {
        "schema": "endpoint428_paired_trace_materialization_v1",
        "evidence_level": "observation_neutral_same_execution_trace",
        "claim_boundary": (
            "This proves trace identity and exact hybrid-payload replay only. "
            "It does not prove a new endpoint gain or an official enwik9 score."
        ),
        "scope_bytes": scope_bytes,
        "state_origin": state_origin,
        "rows": rows,
        "wrt_bytes": rows // 8,
        "record": {
            "bytes": PAIR_ROW_BYTES,
            "fields": [
                "compact_base_p1:uint16le",
                "endpoint428_p1:uint16le",
                "hybrid_p1:uint16le",
                "truth_bit:uint8",
            ],
        },
        "inputs": inputs,
        "output": artifact(output_path),
        "wrt_sha256": wrt_digest.hexdigest(),
        "identity": {
            "probabilities_valid": probabilities_valid,
            "truth_valid": truth_valid,
            "final_rows_match": final_rows_match,
            "hybrid_equals_final_p1": hybrid_equals_final_p1,
            "trace_on_off_archive_identical": archive_identity,
            "hybrid_range_payload_match": payload_match,
            "archive_wrt_length_match": archive_wrt_match,
            "roundtrip_ok": roundtrip_ok,
            "identity_complete": identity_complete,
        },
        "range_replay": {
            "replay_payload_bytes": replay_payload_bytes,
            "archive_payload_bytes": archive_payload,
            "archive_wrt_bytes": archive_wrt_bytes,
        },
        "accepted": accepted,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paired", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--scope-bytes", type=int, required=True)
    parser.add_argument(
        "--state-origin",
        choices=("cold_reset_window", "cumulative_from_corpus_start", "warmup_then_score"),
        required=True,
    )
    parser.add_argument("--final-p1", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--trace-off-archive", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--restored", type=Path, required=True)
    parser.add_argument("--binary", type=Path)
    parser.add_argument("--chunk-rows", type=int, default=1 << 20)
    args = parser.parse_args()
    paths = [
        args.paired,
        args.final_p1,
        args.archive,
        args.trace_off_archive,
        args.input,
        args.restored,
        args.binary,
    ]
    for path in paths:
        if path is not None and not path.is_file():
            raise SystemExit(f"missing input: {path}")
    receipt = materialize(
        args.paired,
        args.output,
        final_p1_path=args.final_p1,
        archive_path=args.archive,
        trace_off_archive_path=args.trace_off_archive,
        input_path=args.input,
        restored_path=args.restored,
        binary_path=args.binary,
        state_origin=args.state_origin,
        scope_bytes=args.scope_bytes,
        chunk_rows=args.chunk_rows,
    )
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.receipt.with_suffix(args.receipt.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, args.receipt)
    print(json.dumps({"accepted": receipt["accepted"], "receipt": str(args.receipt.resolve())}))
    return 0 if receipt["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
