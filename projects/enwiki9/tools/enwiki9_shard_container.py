#!/usr/bin/env python3
"""Pack independent codec archives into a small reversible shard container."""

from __future__ import annotations

import argparse
import struct
from pathlib import Path


MAGIC = b"E9SHARD1"
HEADER = struct.Struct("<8sI")
ENTRY = struct.Struct("<II")


def pack(archives: list[Path], raw_sizes: list[int], output: Path) -> int:
    if not archives or len(archives) != len(raw_sizes):
        raise ValueError("archives and raw_sizes must have the same positive length")
    payloads = [path.read_bytes() for path in archives]
    for raw_size, payload in zip(raw_sizes, payloads):
        if not 0 <= raw_size <= 0xFFFFFFFF:
            raise ValueError("raw shard size exceeds uint32")
        if len(payload) > 0xFFFFFFFF:
            raise ValueError("archive shard size exceeds uint32")
    directory = bytearray(HEADER.pack(MAGIC, len(payloads)))
    for raw_size, payload in zip(raw_sizes, payloads):
        directory.extend(ENTRY.pack(raw_size, len(payload)))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(bytes(directory) + b"".join(payloads))
    return len(directory)


def unpack(container: Path, output_dir: Path) -> list[dict[str, int | str]]:
    data = container.read_bytes()
    if len(data) < HEADER.size:
        raise ValueError("truncated shard container header")
    magic, count = HEADER.unpack_from(data)
    if magic != MAGIC or count < 1:
        raise ValueError("invalid shard container header")
    directory_bytes = HEADER.size + count * ENTRY.size
    if len(data) < directory_bytes:
        raise ValueError("truncated shard container directory")

    entries = [ENTRY.unpack_from(data, HEADER.size + index * ENTRY.size) for index in range(count)]
    output_dir.mkdir(parents=True, exist_ok=True)
    cursor = directory_bytes
    rows: list[dict[str, int | str]] = []
    for index, (raw_size, archive_size) in enumerate(entries):
        end = cursor + archive_size
        if end > len(data):
            raise ValueError("truncated shard archive payload")
        path = output_dir / f"shard-{index:03d}.comp"
        path.write_bytes(data[cursor:end])
        rows.append(
            {
                "index": index,
                "raw_bytes": raw_size,
                "archive_bytes": archive_size,
                "path": str(path.resolve()),
            }
        )
        cursor = end
    if cursor != len(data):
        raise ValueError("trailing bytes after shard archive payloads")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    pack_parser = subparsers.add_parser("pack")
    pack_parser.add_argument("--output", type=Path, required=True)
    pack_parser.add_argument("--archive", type=Path, action="append", required=True)
    pack_parser.add_argument("--raw-size", type=int, action="append", required=True)
    unpack_parser = subparsers.add_parser("unpack")
    unpack_parser.add_argument("--container", type=Path, required=True)
    unpack_parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "pack":
        directory_bytes = pack(args.archive, args.raw_size, args.output)
        print(f"container_bytes={args.output.stat().st_size} directory_bytes={directory_bytes}")
    else:
        rows = unpack(args.container, args.output_dir)
        print(f"shards={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
