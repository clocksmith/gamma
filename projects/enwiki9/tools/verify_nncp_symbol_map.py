#!/usr/bin/env python3
"""Verify an observation-only NNCP symbol-to-raw interval trace."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


MAGIC = b"NNSMAP1\0"
HEADER_BYTES = 16
ROW_DTYPE = np.dtype(
    [("raw_start", "<u8"), ("raw_end", "<u8"), ("symbol", "<u2")]
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def page_boundaries(raw: bytes) -> tuple[list[int], list[int]]:
    starts: list[int] = []
    ends: list[int] = []
    cursor = 0
    while True:
        start = raw.find(b"<page>", cursor)
        if start < 0:
            break
        close = raw.find(b"</page>", start + 6)
        if close < 0:
            break
        end = close + len(b"</page>")
        starts.append(start)
        ends.append(end)
        cursor = end
    return starts, ends


def run(args: argparse.Namespace) -> dict[str, Any]:
    raw = args.raw_input.read_bytes()
    restored = args.restored.read_bytes()
    if restored != raw:
        raise ValueError("NNCP preprocessor roundtrip differs from raw input")
    if args.preprocessed.stat().st_size % 2:
        raise ValueError("preprocessed symbol file is not 16-bit aligned")
    expected_rows = args.preprocessed.stat().st_size // 2
    with args.symbol_map.open("rb") as source:
        header = source.read(HEADER_BYTES)
    if len(header) != HEADER_BYTES or header[:8] != MAGIC:
        raise ValueError("invalid NNCP symbol map header")
    rows = int.from_bytes(header[8:16], "little")
    if rows != expected_rows:
        raise ValueError("symbol map row count differs from preprocessed symbols")
    if args.symbol_map.stat().st_size != HEADER_BYTES + rows * ROW_DTYPE.itemsize:
        raise ValueError("symbol map size differs from its declared row count")

    trace = np.memmap(
        args.symbol_map,
        mode="r",
        dtype=ROW_DTYPE,
        offset=HEADER_BYTES,
        shape=(rows,),
    )
    symbols = np.memmap(
        args.preprocessed, mode="r", dtype=">u2", shape=(rows,)
    )
    if not np.array_equal(trace["symbol"], symbols):
        raise ValueError("symbol map values differ from preprocessed input")
    if int(trace["raw_start"][0]) != 0:
        raise ValueError("first symbol does not begin at raw offset zero")
    if int(trace["raw_end"][-1]) != len(raw):
        raise ValueError("last symbol does not end at raw file length")
    if np.any(trace["raw_end"] < trace["raw_start"]):
        raise ValueError("symbol map contains a reversed raw interval")
    if not np.array_equal(trace["raw_start"][1:], trace["raw_end"][:-1]):
        raise ValueError("symbol map contains a raw gap or overlap")

    starts, ends = page_boundaries(raw)
    start_values = set(map(int, trace["raw_start"]))
    end_values = set(map(int, trace["raw_end"]))
    exact_page_starts = sum(value in start_values for value in starts)
    exact_page_ends = sum(value in end_values for value in ends)
    lengths = trace["raw_end"] - trace["raw_start"]
    receipt = {
        "schema": "nncp_symbol_raw_map_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "official_source_observation_patch_exact_roundtrip",
        "artifacts": {
            "official_source_tar": artifact(args.source_tar),
            "observation_patch": artifact(args.patch),
            "instrumented_binary": artifact(args.binary),
            "raw_input": artifact(args.raw_input),
            "dictionary": artifact(args.dictionary),
            "preprocessed_symbols": artifact(args.preprocessed),
            "symbol_map": artifact(args.symbol_map),
            "restored_raw": artifact(args.restored),
        },
        "proof": {
            "preprocessor_roundtrip_identity": True,
            "symbol_rows": rows,
            "symbol_width_bytes": 2,
            "map_row_bytes": ROW_DTYPE.itemsize,
            "map_symbols_equal_preprocessed_symbols": True,
            "raw_intervals_total_order": True,
            "raw_intervals_gapless": True,
            "raw_intervals_nonoverlapping": True,
            "raw_interval_coverage_bytes": len(raw),
            "zero_output_symbols": int(np.count_nonzero(lengths == 0)),
            "one_byte_symbols": int(np.count_nonzero(lengths == 1)),
            "multi_byte_symbols": int(np.count_nonzero(lengths > 1)),
            "maximum_raw_bytes_per_symbol": int(lengths.max()),
            "complete_pages": len(starts),
            "page_starts_on_symbol_boundaries": exact_page_starts,
            "page_ends_on_symbol_boundaries": exact_page_ends,
            "all_complete_page_boundaries_exact": (
                exact_page_starts == len(starts)
                and exact_page_ends == len(ends)
            ),
        },
        "claim_boundary": (
            "This receipt proves only deterministic alignment of official NNCP "
            "preprocessor symbols to raw intervals. It contains no teacher "
            "probabilities, no Gamma residual, no student, and zero score credit."
        ),
    }
    return receipt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-tar", type=Path, required=True)
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--raw-input", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--preprocessed", type=Path, required=True)
    parser.add_argument("--symbol-map", type=Path, required=True)
    parser.add_argument("--restored", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    receipt = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
