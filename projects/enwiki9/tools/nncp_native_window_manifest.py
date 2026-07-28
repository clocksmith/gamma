#!/usr/bin/env python3
"""Bind raw headroom windows to exact NNCP symbol ordinals."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


MAGIC = b"NNSMAP1\0"
HEADER_BYTES = 16
ROW_DTYPE = np.dtype(
    [("raw_start", "<u8"), ("raw_end", "<u8"), ("symbol", "<u2")]
)
DEFAULT_WINDOWS = (
    ("opening_1m", 0, 1_000_000, False),
    ("mature_9m_10m", 9_000_000, 10_000_000, True),
    ("mature_49m_50m", 49_000_000, 50_000_000, True),
    ("mature_99m_100m", 99_000_000, 100_000_000, True),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_window(value: str) -> tuple[str, int, int, bool]:
    fields = value.split(":")
    if len(fields) not in (3, 4):
        raise argparse.ArgumentTypeError(
            "window must be ID:START:END[:MATURE]"
        )
    window_id, start_text, end_text = fields[:3]
    if not window_id:
        raise argparse.ArgumentTypeError("window ID must not be empty")
    try:
        start = int(start_text)
        end = int(end_text)
    except ValueError as error:
        raise argparse.ArgumentTypeError("window bounds must be integers") from error
    if start < 0 or end <= start:
        raise argparse.ArgumentTypeError("invalid window interval")
    mature = len(fields) == 4 and fields[3].lower() in ("1", "true", "mature")
    if len(fields) == 4 and not mature:
        raise argparse.ArgumentTypeError("fourth field must be MATURE")
    return window_id, start, end, mature


def exact_cut(trace: np.memmap, raw_offset: int) -> int:
    starts = trace["raw_start"]
    ends = trace["raw_end"]
    crossing = np.flatnonzero((starts < raw_offset) & (ends > raw_offset))
    if crossing.size:
        raise ValueError(
            f"raw boundary {raw_offset} crosses symbol row {int(crossing[0])}"
        )
    # A symbol belongs to the prefix exactly when it begins before the raw cut.
    # This includes zero-output controls preceding an output symbol in the
    # prefix and excludes zero-output controls at the start of the future side.
    return int(np.searchsorted(starts, raw_offset, side="left"))


def artifact_from_receipt(
    receipt: dict[str, Any], name: str
) -> dict[str, Any]:
    artifacts = receipt.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValueError("symbol-map receipt lacks artifacts")
    artifact = artifacts.get(name)
    if not isinstance(artifact, dict):
        raise ValueError(f"symbol-map receipt lacks {name}")
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol-map", required=True, type=Path)
    parser.add_argument("--map-receipt", required=True, type=Path)
    parser.add_argument(
        "--window",
        action="append",
        type=parse_window,
        help="ID:START:END[:MATURE]; defaults to the four frozen windows",
    )
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    receipt = json.loads(args.map_receipt.read_text())
    if receipt.get("schema") != "nncp_symbol_raw_map_receipt_v1":
        raise ValueError("unexpected symbol-map receipt schema")
    proof = receipt.get("proof")
    if not isinstance(proof, dict):
        raise ValueError("symbol-map receipt lacks proof")
    for condition in (
        "preprocessor_roundtrip_identity",
        "map_symbols_equal_preprocessed_symbols",
        "raw_intervals_total_order",
        "raw_intervals_gapless",
        "raw_intervals_nonoverlapping",
    ):
        if proof.get(condition) is not True:
            raise ValueError(f"symbol-map proof did not establish {condition}")

    expected_map = artifact_from_receipt(receipt, "symbol_map")
    map_hash = sha256(args.symbol_map)
    if map_hash != expected_map.get("sha256"):
        raise ValueError("symbol map hash differs from bound receipt")
    if args.symbol_map.stat().st_size != expected_map.get("bytes"):
        raise ValueError("symbol map size differs from bound receipt")

    with args.symbol_map.open("rb") as source:
        header = source.read(HEADER_BYTES)
    if len(header) != HEADER_BYTES or header[:8] != MAGIC:
        raise ValueError("invalid symbol map header")
    rows = int.from_bytes(header[8:16], "little")
    if args.symbol_map.stat().st_size != HEADER_BYTES + rows * ROW_DTYPE.itemsize:
        raise ValueError("symbol map row count is inconsistent")
    trace = np.memmap(
        args.symbol_map,
        mode="r",
        dtype=ROW_DTYPE,
        offset=HEADER_BYTES,
        shape=(rows,),
    )

    windows = args.window or list(DEFAULT_WINDOWS)
    maximum_raw = max(window[2] for window in windows)
    coverage = int(proof.get("raw_interval_coverage_bytes", -1))
    if coverage < maximum_raw:
        raise ValueError(
            "symbol map does not cover every requested mature boundary"
        )

    manifest_windows: list[dict[str, object]] = []
    checkpoint_symbols: set[int] = set()
    full_tree_windows: list[str] = []
    seen_ids: set[str] = set()
    for window_id, raw_start, raw_end, mature in windows:
        if window_id in seen_ids:
            raise ValueError("duplicate window ID")
        seen_ids.add(window_id)
        symbol_start = exact_cut(trace, raw_start)
        symbol_end = exact_cut(trace, raw_end)
        if symbol_end <= symbol_start:
            raise ValueError(f"{window_id}: empty symbol interval")
        if symbol_start:
            checkpoint_symbols.add(symbol_start)
        checkpoint_symbols.add(symbol_end)
        full_tree_windows.append(f"{symbol_start}:{symbol_end}")
        manifest_windows.append(
            {
                "mature": mature,
                "raw_end": raw_end,
                "raw_start": raw_start,
                "symbol_end": symbol_end,
                "symbol_start": symbol_start,
                "window_id": window_id,
            }
        )

    dictionary = artifact_from_receipt(receipt, "dictionary")
    raw_input = artifact_from_receipt(receipt, "raw_input")
    preprocessed = artifact_from_receipt(receipt, "preprocessed_symbols")
    manifest = {
        "checkpoint_argument": ",".join(
            str(value) for value in sorted(checkpoint_symbols)
        ),
        "claim_boundary": (
            "This manifest binds raw windows to exact preprocessed symbol "
            "ordinals. It contains no teacher execution or score credit."
        ),
        "dictionary": dictionary,
        "full_tree_window_argument": ",".join(full_tree_windows),
        "map_receipt": {
            "bytes": args.map_receipt.stat().st_size,
            "path": str(args.map_receipt.resolve()),
            "sha256": sha256(args.map_receipt),
        },
        "preprocessed_symbols": preprocessed,
        "raw_input": raw_input,
        "schema": "nncp_native_trace_window_manifest_v1",
        "score_credit_bytes": 0,
        "symbol_map": {
            "bytes": args.symbol_map.stat().st_size,
            "path": str(args.symbol_map.resolve()),
            "rows": rows,
            "sha256": map_hash,
        },
        "windows": manifest_windows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
