#!/usr/bin/env python3
"""Split an enwiki9 XML byte stream at deterministic page boundaries."""

from __future__ import annotations

import argparse
import bisect
import hashlib
import json
from pathlib import Path
from typing import Any


PAGE_START = b"<page>"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def page_offsets(data: bytes) -> list[int]:
    offsets: list[int] = []
    position = 0
    while True:
        position = data.find(PAGE_START, position)
        if position < 0:
            return offsets
        offsets.append(position)
        position += len(PAGE_START)


def choose_boundaries(data: bytes, shard_count: int) -> list[int]:
    if shard_count < 1:
        raise ValueError("shard_count must be positive")
    offsets = page_offsets(data)
    if shard_count > 1 and len(offsets) < shard_count - 1:
        raise ValueError("not enough page boundaries for requested shards")

    boundaries = [0]
    for shard in range(1, shard_count):
        target = len(data) * shard // shard_count
        minimum_index = bisect.bisect_right(offsets, boundaries[-1])
        boundaries_after_this = shard_count - 1 - shard
        maximum_index = len(offsets) - 1 - boundaries_after_this
        if minimum_index > maximum_index:
            raise ValueError("cannot choose strictly increasing page boundaries")
        index = min(max(bisect.bisect_left(offsets, target), minimum_index), maximum_index)
        candidates = [offsets[index]]
        if index > minimum_index:
            candidates.append(offsets[index - 1])
        boundaries.append(min(candidates, key=lambda value: (abs(value - target), value)))
    boundaries.append(len(data))

    if len(set(boundaries)) != len(boundaries):
        raise ValueError("duplicate shard boundary")
    for boundary in boundaries[1:-1]:
        if data[boundary : boundary + len(PAGE_START)] != PAGE_START:
            raise ValueError("internal boundary is not a page start")
    return boundaries


def build_shards(input_path: Path, output_dir: Path, shard_count: int) -> dict[str, Any]:
    data = input_path.read_bytes()
    boundaries = choose_boundaries(data, shard_count)
    output_dir.mkdir(parents=True, exist_ok=True)

    shards = []
    reconstructed = bytearray()
    for index, (start, end) in enumerate(zip(boundaries, boundaries[1:])):
        payload = data[start:end]
        path = output_dir / f"shard-{index:03d}.raw"
        path.write_bytes(payload)
        reconstructed.extend(payload)
        shards.append(
            {
                "index": index,
                "start": start,
                "end": end,
                "bytes": len(payload),
                "sha256": sha256_bytes(payload),
                "path": str(path.resolve()),
                "starts_at_page_boundary": index == 0 or payload.startswith(PAGE_START),
            }
        )

    reconstructed_bytes = bytes(reconstructed)
    if reconstructed_bytes != data:
        raise RuntimeError("shards do not reconstruct the input exactly")
    return {
        "schema": "enwiki9_page_shards_v1",
        "claim_boundary": (
            "Deterministic raw-byte shard layout only. Codec reset cost, archive "
            "roundtrip, process-tree memory, runtime, counted directory bytes, and "
            "full-corpus score remain unproven."
        ),
        "input": {
            "path": str(input_path.resolve()),
            "bytes": len(data),
            "sha256": sha256_bytes(data),
        },
        "boundary_contract": {
            "marker_hex": PAGE_START.hex(),
            "internal_boundaries_are_page_starts": True,
            "selection": "nearest marker to each equal-byte target; lower offset breaks ties",
        },
        "shard_count": shard_count,
        "boundaries": boundaries,
        "shards": shards,
        "reconstruction": {
            "exact": True,
            "bytes": len(reconstructed_bytes),
            "sha256": sha256_bytes(reconstructed_bytes),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--shards", type=int, default=4)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()

    manifest = build_shards(args.input, args.output_dir, args.shards)
    manifest_path = args.manifest or args.output_dir / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
