#!/usr/bin/env python3
"""Certify predicates removed from the immutable B2 FCF/BPDQ closure."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath


FILTERS = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME}]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    packed = args.payload.read_bytes()
    raw = lzma.decompress(packed, format=lzma.FORMAT_RAW, filters=FILTERS)
    if raw[:4] != b"FCF1" or len(raw) < 6:
        raise ValueError("invalid FCF header")
    count = int.from_bytes(raw[4:6], "big")
    cursor = 6
    seen: set[str] = set()
    dictionary: bytes | None = None
    minimum_name_bytes: int | None = None
    maximum_name_bytes = 0
    for _ in range(count):
        if cursor + 6 > len(raw):
            raise ValueError("truncated FCF record")
        name_size = int.from_bytes(raw[cursor : cursor + 2], "big")
        data_size = int.from_bytes(raw[cursor + 2 : cursor + 6], "big")
        cursor += 6
        name_end = cursor + name_size
        data_end = name_end + data_size
        if data_end > len(raw):
            raise ValueError("truncated FCF payload")
        name = raw[cursor:name_end].decode()
        path = PurePosixPath(name)
        if not name or path.is_absolute() or ".." in path.parts or name in seen:
            raise ValueError("unsafe or duplicate path")
        seen.add(name)
        minimum_name_bytes = (
            name_size
            if minimum_name_bytes is None
            else min(minimum_name_bytes, name_size)
        )
        maximum_name_bytes = max(maximum_name_bytes, name_size)
        if name == "cmix21/english.dic":
            dictionary = raw[name_end:data_end]
        cursor = data_end
    if cursor != len(raw) or len(seen) != count or dictionary is None:
        raise ValueError("invalid FCF closure")

    if (
        dictionary[:4] != b"BPD1"
        or len(dictionary) < 5
        or dictionary[4] not in (0, 1)
    ):
        raise ValueError("invalid BPDQ header")
    previous = b""
    records = 0
    maximum_lcp = 0
    for record in dictionary[5:].splitlines():
        if not record:
            raise ValueError("empty BPDQ record")
        lcp = record[0] - 32
        if lcp < 0 or lcp > len(previous):
            raise ValueError("invalid BPDQ prefix")
        previous = previous[:lcp] + record[1:]
        maximum_lcp = max(maximum_lcp, lcp)
        records += 1

    receipt = {
        "all_bpdq_prefixes_valid": True,
        "all_fcf_bounds_valid": True,
        "all_paths_relative_safe_unique": True,
        "bpdq_maximum_lcp": maximum_lcp,
        "bpdq_record_count": records,
        "fcf_final_cursor": cursor,
        "fcf_member_count": count,
        "fcf_minimum_name_bytes": minimum_name_bytes,
        "fcf_maximum_name_bytes": maximum_name_bytes,
        "fcf_trailing_bytes": len(raw) - cursor,
        "literal_member_present": "cmix21/.gamma_lflags" in seen,
        "payload_bytes": len(packed),
        "payload_sha256": sha256(packed),
        "raw_bytes": len(raw),
        "raw_sha256": sha256(raw),
        "schema": "closed_world_b2_closure_certificate_v1",
        "score_credit_bytes": 0,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
