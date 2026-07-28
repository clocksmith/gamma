#!/usr/bin/env python3
"""Verify an NNCP native consumed-branch and derived-tree trace."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct


HEADER = struct.Struct("<8sQQQ")
ROW = struct.Struct("<QQQQQHHBB")
BRANCH = struct.Struct("<HB")
U16 = struct.Struct("<H")
MAGIC = b"NNNTR2\0\0"
PROBABILITY_TOTAL = 32768


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def expected_bits(symbol: int, vocabulary: int) -> list[int]:
    start, active = 0, vocabulary
    bits: list[int] = []
    while active > 1:
        left = active >> 1
        bit = int(symbol >= start + left)
        bits.append(bit)
        if bit:
            start += left
            active -= left
        else:
            active = left
    if start != symbol:
        raise ValueError("split path does not terminate at symbol")
    return bits


def tree_path(
    values: list[int], symbol: int, vocabulary: int
) -> list[int]:
    path: list[int] = []
    base = 0
    start = 0
    active = vocabulary
    while active > 1:
        probability = values[base]
        path.append(probability)
        left = active >> 1
        right = active - left
        if symbol < start + left:
            base += 1
            active = left
        else:
            base += 1 + max(left - 1, 0)
            start += left
            active = right
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--trace-on-archive", required=True, type=Path)
    parser.add_argument("--trace-off-archive", required=True, type=Path)
    parser.add_argument("--decoded", required=True, type=Path)
    parser.add_argument("--expected-raw", required=True, type=Path)
    parser.add_argument("--environment", required=True, type=Path)
    parser.add_argument("--symbol-map-receipt", type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()

    raw = args.trace.read_bytes()
    if len(raw) < HEADER.size:
        raise ValueError("truncated trace")
    magic, rows, branches, trees = HEADER.unpack_from(raw)
    if magic != MAGIC:
        raise ValueError("trace magic mismatch")

    offset = HEADER.size
    observed_branches = 0
    observed_trees = 0
    prior_bits: int | None = None
    prior_bytes: int | None = None
    for index in range(rows):
        if offset + ROW.size > len(raw):
            raise ValueError("truncated symbol row")
        (
            execution,
            before_bits,
            after_bits,
            before_bytes,
            after_bytes,
            symbol,
            vocabulary,
            branch_count,
            has_tree,
        ) = ROW.unpack_from(raw, offset)
        offset += ROW.size
        if execution != index:
            raise ValueError("nonconsecutive execution ordinal")
        if vocabulary < 2 or symbol >= vocabulary:
            raise ValueError("invalid symbol domain")
        if after_bits < before_bits or after_bytes < before_bytes:
            raise ValueError("coder count decreased")
        if prior_bits is not None and before_bits != prior_bits:
            raise ValueError("coder bit-count discontinuity")
        if prior_bytes is not None and before_bytes != prior_bytes:
            raise ValueError("emitted-byte discontinuity")

        bits = expected_bits(symbol, vocabulary)
        if len(bits) != branch_count:
            raise ValueError("branch count mismatch")
        probabilities: list[int] = []
        for expected in bits:
            if offset + BRANCH.size > len(raw):
                raise ValueError("truncated consumed branch")
            probability, bit = BRANCH.unpack_from(raw, offset)
            offset += BRANCH.size
            if bit != expected:
                raise ValueError("consumed path mismatch")
            if not 1 <= probability < PROBABILITY_TOTAL:
                raise ValueError("consumed probability out of range")
            probabilities.append(probability)
        observed_branches += branch_count

        if has_tree:
            if offset + U16.size > len(raw):
                raise ValueError("truncated tree count")
            (tree_count,) = U16.unpack_from(raw, offset)
            offset += U16.size
            if tree_count != vocabulary - 1:
                raise ValueError("derived tree size mismatch")
            byte_count = tree_count * U16.size
            if offset + byte_count > len(raw):
                raise ValueError("truncated derived tree")
            values = list(
                struct.unpack_from(f"<{tree_count}H", raw, offset)
            )
            offset += byte_count
            if any(not 1 <= value < PROBABILITY_TOTAL for value in values):
                raise ValueError("derived probability out of range")
            if tree_path(values, symbol, vocabulary) != probabilities:
                raise ValueError("derived tree disagrees with consumed path")
            observed_trees += 1
        elif has_tree != 0:
            raise ValueError("invalid tree flag")
        prior_bits = after_bits
        prior_bytes = after_bytes

    if offset != len(raw):
        raise ValueError("trailing trace bytes")
    if observed_branches != branches or observed_trees != trees:
        raise ValueError("trace header totals disagree")
    if args.trace_on_archive.read_bytes() != args.trace_off_archive.read_bytes():
        raise ValueError("trace changed native archive")
    if args.decoded.read_bytes() != args.expected_raw.read_bytes():
        raise ValueError("decoded output differs from expected raw input")

    environment = json.loads(args.environment.read_text())
    if environment.get("execution_status") != "NVIDIA_READY":
        raise ValueError("environment is not a bound NVIDIA execution")

    receipt = {
        "archive_identity": True,
        "decoded_identity": True,
        "derived_tree_rows": trees,
        "environment": environment,
        "exact_consumed_integer_probabilities": True,
        "probability_total": PROBABILITY_TOTAL,
        "schema": "nncp_native_trace_cert_v1",
        "score_credit_bytes": 0,
        "symbol_map_receipt": (
            {
                "path": str(args.symbol_map_receipt),
                "sha256": sha256(args.symbol_map_receipt),
            }
            if args.symbol_map_receipt
            else None
        ),
        "symbol_rows": rows,
        "trace": {
            "bytes": args.trace.stat().st_size,
            "sha256": sha256(args.trace),
        },
        "trace_off_archive": {
            "bytes": args.trace_off_archive.stat().st_size,
            "sha256": sha256(args.trace_off_archive),
        },
        "trace_on_archive": {
            "bytes": args.trace_on_archive.stat().st_size,
            "sha256": sha256(args.trace_on_archive),
        },
        "visited_branches": branches,
    }
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
