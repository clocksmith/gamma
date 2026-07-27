#!/usr/bin/env python3
"""Verify an NNCP hierarchical branch-frequency trace."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct


HEADER = struct.Struct("<8sQQ")
ROW = struct.Struct("<QQQHHB")
BRANCH = struct.Struct("<HB")
MAGIC = b"NNQBR1\0\0"
PROBABILITY_TOTAL = 32768


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def expected_bits(symbol: int, vocabulary: int) -> list[int]:
    if vocabulary < 2 or symbol < 0 or symbol >= vocabulary:
        raise ValueError("invalid symbol or vocabulary")
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
        raise AssertionError("split path did not terminate at symbol")
    return bits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--trace-on-archive", type=Path)
    parser.add_argument("--trace-off-archive", type=Path)
    args = parser.parse_args()

    raw = args.trace.read_bytes()
    if len(raw) < HEADER.size:
        raise ValueError("truncated trace header")
    magic, symbol_count, branch_count = HEADER.unpack_from(raw)
    if magic != MAGIC:
        raise ValueError("invalid trace magic")
    offset = HEADER.size
    observed_branches = 0
    previous_after: int | None = None
    vocabularies: set[int] = set()
    min_probability = PROBABILITY_TOTAL
    max_probability = 0
    for index in range(symbol_count):
        if offset + ROW.size > len(raw):
            raise ValueError("truncated symbol row")
        execution, before, after, symbol, vocabulary, count = ROW.unpack_from(
            raw, offset
        )
        offset += ROW.size
        if execution != index:
            raise ValueError("nonconsecutive execution index")
        if previous_after is not None and before != previous_after:
            raise ValueError("coder bit counts are discontinuous")
        if after < before:
            raise ValueError("coder bit count decreased")
        expected = expected_bits(symbol, vocabulary)
        if count != len(expected):
            raise ValueError("branch count does not match split path")
        for expected_bit in expected:
            if offset + BRANCH.size > len(raw):
                raise ValueError("truncated branch row")
            probability, bit = BRANCH.unpack_from(raw, offset)
            offset += BRANCH.size
            if bit != expected_bit:
                raise ValueError("branch bit does not match symbol path")
            if not 1 <= probability < PROBABILITY_TOTAL:
                raise ValueError("branch probability is out of range")
            min_probability = min(min_probability, probability)
            max_probability = max(max_probability, probability)
        observed_branches += count
        previous_after = after
        vocabularies.add(vocabulary)
    if offset != len(raw):
        raise ValueError("trailing trace bytes")
    if observed_branches != branch_count:
        raise ValueError("header branch count mismatch")

    archive_identity: bool | None = None
    archives: dict[str, object] = {}
    if args.trace_on_archive is not None or args.trace_off_archive is not None:
        if args.trace_on_archive is None or args.trace_off_archive is None:
            raise ValueError("both archive paths are required")
        on = args.trace_on_archive.read_bytes()
        off = args.trace_off_archive.read_bytes()
        archive_identity = on == off
        archives = {
            "trace_off_bytes": len(off),
            "trace_off_sha256": sha256(off),
            "trace_on_bytes": len(on),
            "trace_on_sha256": sha256(on),
        }
        if not archive_identity:
            raise ValueError("trace-on and trace-off archives differ")

    receipt = {
        "archive_identity": archive_identity,
        "archives": archives,
        "branch_count": branch_count,
        "coder_counts_continuous": True,
        "maximum_probability": max_probability,
        "minimum_probability": min_probability if branch_count else None,
        "probability_total": PROBABILITY_TOTAL,
        "schema": "nncp_branch_frequency_trace_receipt_v1",
        "score_credit_bytes": 0,
        "split_paths_valid": True,
        "symbol_count": symbol_count,
        "trace_bytes": len(raw),
        "trace_sha256": sha256(raw),
        "vocabularies": sorted(vocabularies),
    }
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
