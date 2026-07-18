#!/usr/bin/env python3
"""Convert an exact P1 stream and matching WRT store to FX2PT01 records."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np


P1_MAGICS = (b"CMX21P1\0", b"FX2P1V1\0")
P1_HEADER_BYTES = 16
WRT_HEADER = b"\x80\x00\x00\x00\x00"
TRACE_MAGIC = b"FX2PT01\n"
TRACE_DTYPE = np.dtype([("p1", "<u2"), ("bit", "u1")])


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


def read_p1_rows(path: Path) -> tuple[bytes, int]:
    with path.open("rb") as source:
        header = source.read(P1_HEADER_BYTES)
    if len(header) != P1_HEADER_BYTES or header[:8] not in P1_MAGICS:
        raise ValueError("invalid CMX21P1/FX2P1V1 header")
    rows = int.from_bytes(header[8:16], "little")
    if rows <= 0 or path.stat().st_size != P1_HEADER_BYTES + 2 * rows:
        raise ValueError("P1 file size does not match its declared rows")
    if rows % 8:
        raise ValueError("P1 rows are not WRT-byte aligned")
    return header[:8], rows


def validate_store(path: Path, rows: int) -> None:
    if path.stat().st_size != len(WRT_HEADER) + rows // 8:
        raise ValueError("WRT store size does not match P1 rows")
    with path.open("rb") as source:
        if source.read(len(WRT_HEADER)) != WRT_HEADER:
            raise ValueError("invalid WRT store header")


def build_trace(
    p1_path: Path,
    store_path: Path,
    output: Path,
    *,
    chunk_bytes: int = 1 << 20,
) -> dict[str, Any]:
    magic, rows = read_p1_rows(p1_path)
    validate_store(store_path, rows)
    if chunk_bytes <= 0:
        raise ValueError("chunk size must be positive")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.unlink(missing_ok=True)
    expected_bytes = len(TRACE_MAGIC) + rows * TRACE_DTYPE.itemsize
    with temporary.open("wb") as target:
        target.write(TRACE_MAGIC)
        target.truncate(expected_bytes)

    p1 = np.memmap(
        p1_path,
        mode="r",
        dtype="<u2",
        offset=P1_HEADER_BYTES,
        shape=(rows,),
    )
    store = np.memmap(
        store_path,
        mode="r",
        dtype="u1",
        offset=len(WRT_HEADER),
        shape=(rows // 8,),
    )
    trace = np.memmap(
        temporary,
        mode="r+",
        dtype=TRACE_DTYPE,
        offset=len(TRACE_MAGIC),
        shape=(rows,),
    )
    for byte_start in range(0, len(store), chunk_bytes):
        byte_end = min(len(store), byte_start + chunk_bytes)
        row_start = byte_start * 8
        row_end = byte_end * 8
        trace["p1"][row_start:row_end] = p1[row_start:row_end]
        trace["bit"][row_start:row_end] = np.unpackbits(
            store[byte_start:byte_end], bitorder="big"
        )
    trace.flush()
    del trace
    del store
    del p1
    with temporary.open("rb") as source:
        os.fsync(source.fileno())
    os.replace(temporary, output)
    if output.stat().st_size != expected_bytes:
        raise RuntimeError("compact trace has an unexpected size")
    return {
        "schema": "p1_wrt_to_fx2pt_trace_v1",
        "evidence_level": "deterministic_trace_materialization",
        "inputs": {
            "p1": artifact(p1_path),
            "p1_magic": magic.decode("ascii", errors="replace"),
            "wrt_store": artifact(store_path),
        },
        "output": artifact(output),
        "rows": rows,
        "wrt_bytes": rows // 8,
        "record_bytes": TRACE_DTYPE.itemsize,
        "truth_bit_order": "MSB-first within each WRT byte",
        "identity": {
            "row_count_match": True,
            "wrt_store_header_match": True,
            "probabilities_copied_without_rescaling": True,
        },
        "claim_boundary": (
            "This receipt proves deterministic trace materialization only. It does "
            "not prove an endpoint gain or change a constructive archive."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p1", type=Path, required=True)
    parser.add_argument("--wrt-store", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--chunk-bytes", type=int, default=1 << 20)
    args = parser.parse_args()
    for path in (args.p1, args.wrt_store):
        if not path.is_file():
            raise SystemExit(f"missing input: {path}")
    receipt = build_trace(
        args.p1,
        args.wrt_store,
        args.output,
        chunk_bytes=args.chunk_bytes,
    )
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.receipt.with_suffix(args.receipt.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, args.receipt)
    print(
        json.dumps(
            {
                "rows": receipt["rows"],
                "wrt_bytes": receipt["wrt_bytes"],
                "output": receipt["output"]["path"],
                "receipt": str(args.receipt.resolve()),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
