#!/usr/bin/env python3
"""Extract base and final FX2PT01 streams from a DPLRTRC1 teacher trace."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np


INPUT_MAGIC = b"DPLRTRC1"
OUTPUT_MAGIC = b"FX2PT01\n"
HEADER = struct.Struct("<8s4I")
INPUT_DTYPE = np.dtype(
    [
        ("base", "<u2"),
        ("side", "<u2"),
        ("main", "<u2"),
        ("final", "<u2"),
        ("bit", "u1"),
    ]
)
OUTPUT_DTYPE = np.dtype([("p1", "<u2"), ("bit", "u1")])


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_stream(path: Path, rows: np.memmap, field: str, chunk_rows: int) -> None:
    with path.open("wb") as target:
        target.write(OUTPUT_MAGIC)
        for start in range(0, len(rows), chunk_rows):
            part = rows[start : start + chunk_rows]
            output = np.empty(len(part), dtype=OUTPUT_DTYPE)
            output["p1"] = part[field]
            output["bit"] = part["bit"]
            target.write(output.tobytes())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--chunk-rows", type=int, default=1 << 20)
    args = parser.parse_args()

    with args.input.open("rb") as source:
        header = source.read(HEADER.size)
    if len(header) != HEADER.size:
        raise ValueError("truncated DPLRTRC1 header")
    magic, version, header_bytes, row_bytes, flags = HEADER.unpack(header)
    if magic != INPUT_MAGIC or version != 1:
        raise ValueError("unsupported DPLR teacher trace")
    if header_bytes < HEADER.size or row_bytes != INPUT_DTYPE.itemsize:
        raise ValueError("unexpected DPLR teacher trace layout")
    payload = args.input.stat().st_size - header_bytes
    if payload < 0 or payload % row_bytes:
        raise ValueError("invalid DPLR teacher trace length")
    row_count = payload // row_bytes
    rows = np.memmap(
        args.input,
        mode="r",
        dtype=INPUT_DTYPE,
        offset=header_bytes,
        shape=(row_count,),
    )
    if np.any(rows["bit"] > 1):
        raise ValueError("truth bit outside {0,1}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {}
    for field in ("base", "final"):
        path = args.output_dir / f"{field}.fx2pt"
        write_stream(path, rows, field, args.chunk_rows)
        outputs[field] = {
            "path": str(path.resolve()),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    receipt = {
        "schema": "extract_dplr_gain_traces_v1",
        "input": {
            "path": str(args.input.resolve()),
            "bytes": args.input.stat().st_size,
            "sha256": sha256_file(args.input),
            "flags": flags,
        },
        "rows": row_count,
        "outputs": outputs,
    }
    receipt_path = args.output_dir / "receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"receipt": str(receipt_path.resolve()), "rows": row_count}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
