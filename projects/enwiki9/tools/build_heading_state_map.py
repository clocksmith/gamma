#!/usr/bin/env python3
"""Build a decoder-visible section-heading state for every WRT byte."""

from __future__ import annotations

import argparse
from pathlib import Path
import struct

from wrt_exact import parse_store
from wrt_twinstream_shadow import emission_groups


def classify(line: bytes) -> int | None:
    text = line.strip().lower()
    if text.startswith(b"</page"):
        return 0
    if len(text) < 4 or not text.startswith(b"==") or not text.endswith(b"=="):
        return None
    heading = text.strip(b"= \t")
    if b"early life" in heading or b"personal life" in heading:
        return 1
    if b"career" in heading:
        return 2
    if b"history" in heading:
        return 3
    if b"geography" in heading:
        return 4
    if b"demographic" in heading:
        return 5
    if b"reception" in heading or b"legacy" in heading:
        return 6
    if (
        b"works" in heading
        or b"publication" in heading
        or b"bibliograph" in heading
    ):
        return 7
    if (
        b"reference" in heading
        or b"external link" in heading
        or b"see also" in heading
    ):
        return 8
    return 9


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    parsed = parse_store(args.store, args.dictionary)
    groups = emission_groups(parsed)
    states = bytearray(len(parsed.stream))
    line = bytearray()
    state = 0
    counts = [0] * 10
    cursor = 0
    for group in groups:
        if group.start != cursor:
            raise RuntimeError("noncontiguous groups")
        states[group.start : group.end] = bytes((state,)) * (group.end - group.start)
        for value in group.decoded:
            line.append(value)
            if value == 10:
                next_state = classify(bytes(line))
                if next_state is not None:
                    state = next_state
                    counts[state] += 1
                line.clear()
        cursor = group.end
    if cursor != len(parsed.stream):
        raise RuntimeError("incomplete WRT coverage")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("wb") as output:
        output.write(b"HEADMAP1")
        output.write(struct.pack("<QQ", len(parsed.stream), len(parsed.decoded)))
        output.write(states)
    print(
        f"wrt_bytes={len(parsed.stream)} raw_bytes={len(parsed.decoded)} "
        f"groups={len(groups)} transitions={counts}"
    )


if __name__ == "__main__":
    main()
