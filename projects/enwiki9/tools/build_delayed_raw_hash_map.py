#!/usr/bin/env python3
"""Build one decoder-visible completed-raw suffix hash per WRT byte."""

from __future__ import annotations

import argparse
from pathlib import Path
import struct

from wrt_exact import parse_store
from wrt_twinstream_shadow import emission_groups, fnv64


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    parsed = parse_store(args.store, args.dictionary)
    groups = emission_groups(parsed)
    raw_history = bytearray()
    hashes = [0] * len(parsed.stream)
    cursor = 0
    seed = 0x84222325CBF29CE4
    for group in groups:
        if group.start != cursor:
            raise RuntimeError("noncontiguous emission groups")
        raw_hash = fnv64(seed, bytes(raw_history[-8:]))
        for position in range(group.start, group.end):
            hashes[position] = raw_hash
        raw_history.extend(group.decoded)
        cursor = group.end
    if cursor != len(parsed.stream):
        raise RuntimeError("incomplete WRT coverage")
    if bytes(raw_history) != parsed.decoded:
        raise RuntimeError("raw reconstruction mismatch")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("wb") as output:
        output.write(b"RAWHASH1")
        output.write(struct.pack("<QQ", len(parsed.stream), len(raw_history)))
        for value in hashes:
            output.write(struct.pack("<Q", value))
    print(
        f"wrt_bytes={len(parsed.stream)} raw_bytes={len(raw_history)} "
        f"groups={len(groups)} output={args.output}"
    )


if __name__ == "__main__":
    main()
