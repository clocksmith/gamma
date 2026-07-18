#!/usr/bin/env python3
"""Build a minimal CMNEST1 trace from a CMX21P1 stream and WRT truth."""

from __future__ import annotations

import argparse
import os
import pathlib
import struct

import numpy as np


P1_MAGIC = b"CMX21P1\0"
FX2_P1_MAGIC = b"FX2P1V1\0"
P1_MAGICS = (P1_MAGIC, FX2_P1_MAGIC)
P1_HEADER_BYTES = 16
TRACE_MAGIC = b"CMNEST1\0"
TRACE_HEADER = struct.Struct("<8sIIIIIQ")
TRACE_VERSION = 1
TRACE_ENDPOINTS = 1
TRACE_LAYER0_ENDPOINTS = 0
TRACE_ROW_BYTES = 1 + 2 * TRACE_ENDPOINTS
WRT_HEADER = b"\x80\x00\x00\x00\x00"


def read_p1_rows(path: pathlib.Path) -> int:
    with path.open("rb") as source:
        header = source.read(P1_HEADER_BYTES)
    if len(header) != P1_HEADER_BYTES or header[:8] not in P1_MAGICS:
        raise ValueError("invalid CMX21P1/FX2P1V1 header")
    rows = int.from_bytes(header[8:16], "little")
    if rows <= 0 or path.stat().st_size != P1_HEADER_BYTES + 2 * rows:
        raise ValueError("CMX21P1 size does not match its row count")
    return rows


def validate_store(path: pathlib.Path, rows: int) -> None:
    if rows % 8:
        raise ValueError("probability row count is not byte aligned")
    if path.stat().st_size != len(WRT_HEADER) + rows // 8:
        raise ValueError("WRT store size does not match probability rows")
    with path.open("rb") as source:
        if source.read(len(WRT_HEADER)) != WRT_HEADER:
            raise ValueError("invalid WRT store header")


def build_trace(
    p1_path: pathlib.Path, store_path: pathlib.Path, output: pathlib.Path
) -> dict[str, int | str]:
    rows = read_p1_rows(p1_path)
    validate_store(store_path, rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    expected_bytes = TRACE_HEADER.size + rows * TRACE_ROW_BYTES
    with output.open("wb") as target:
        target.write(
            TRACE_HEADER.pack(
                TRACE_MAGIC,
                TRACE_VERSION,
                TRACE_HEADER.size,
                TRACE_ROW_BYTES,
                TRACE_ENDPOINTS,
                TRACE_LAYER0_ENDPOINTS,
                rows,
            )
        )
        target.truncate(expected_bytes)

    p1 = np.memmap(
        p1_path, mode="r", dtype="<u2", offset=P1_HEADER_BYTES, shape=(rows,)
    )
    store = np.memmap(
        store_path, mode="r", dtype="u1", offset=len(WRT_HEADER), shape=(rows // 8,)
    )
    row_dtype = np.dtype([("bit", "u1"), ("p", "<u2", (TRACE_ENDPOINTS,))])
    trace = np.memmap(
        output,
        mode="r+",
        dtype=row_dtype,
        offset=TRACE_HEADER.size,
        shape=(rows,),
    )
    trace["bit"] = np.unpackbits(store, bitorder="big")
    trace["p"][:, 0] = p1
    trace.flush()
    del trace
    os.sync()
    if output.stat().st_size != expected_bytes:
        raise RuntimeError("minimal matched trace has an unexpected size")
    return {
        "output": str(output.resolve()),
        "rows": rows,
        "row_bytes": TRACE_ROW_BYTES,
        "endpoint_count": TRACE_ENDPOINTS,
        "bytes": expected_bytes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p1", type=pathlib.Path, required=True)
    parser.add_argument("--store", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    print(build_trace(args.p1, args.store, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
