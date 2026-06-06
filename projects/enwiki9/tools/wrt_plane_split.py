#!/usr/bin/env python3
"""Split fx2 WRT-preprocessed bytes into high-byte planes.

The transform is reversible and table-free.  It does not parse the dictionary;
it only separates bytes with the high bit set from the rest of the stream.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import struct

MAGIC = b"WPS1"
HEADER = struct.Struct("<4sQQQ")


def split_planes(data: bytes) -> tuple[bytes, bytes, bytes]:
    flags = bytearray((len(data) + 7) // 8)
    low = bytearray()
    high = bytearray()
    for pos, b in enumerate(data):
        if b >= 128:
            flags[pos >> 3] |= 1 << (pos & 7)
            high.append(b - 128)
        else:
            low.append(b)
    return bytes(flags), bytes(low), bytes(high)


def join_planes(size: int, flags: bytes, low: bytes, high: bytes) -> bytes:
    out = bytearray()
    li = hi = 0
    for pos in range(size):
        if flags[pos >> 3] & (1 << (pos & 7)):
            if hi >= len(high):
                raise ValueError("truncated high plane")
            out.append(high[hi] + 128)
            hi += 1
        else:
            if li >= len(low):
                raise ValueError("truncated low plane")
            out.append(low[li])
            li += 1
    if li != len(low) or hi != len(high):
        raise ValueError("unused plane bytes")
    return bytes(out)


def encode_container(data: bytes) -> bytes:
    flags, low, high = split_planes(data)
    return HEADER.pack(MAGIC, len(data), len(flags), len(low)) + flags + low + high


def decode_container(blob: bytes) -> bytes:
    if len(blob) < HEADER.size:
        raise ValueError("truncated header")
    magic, size, flag_len, low_len = HEADER.unpack(blob[: HEADER.size])
    if magic != MAGIC:
        raise ValueError("bad magic")
    start = HEADER.size
    flags = blob[start : start + flag_len]
    low_start = start + flag_len
    low = blob[low_start : low_start + low_len]
    high = blob[low_start + low_len :]
    return join_planes(size, flags, low, high)


def write_parts(data: bytes, prefix: pathlib.Path) -> dict[str, object]:
    flags, low, high = split_planes(data)
    paths = {
        "flags": prefix.with_suffix(prefix.suffix + ".flags"),
        "low": prefix.with_suffix(prefix.suffix + ".low"),
        "high": prefix.with_suffix(prefix.suffix + ".high"),
        "meta": prefix.with_suffix(prefix.suffix + ".json"),
    }
    paths["flags"].write_bytes(flags)
    paths["low"].write_bytes(low)
    paths["high"].write_bytes(high)
    meta = stats_payload(data, flags, low, high)
    paths["meta"].write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    return {"paths": {key: str(value) for key, value in paths.items()}, **meta}


def stats_payload(data: bytes, flags: bytes, low: bytes, high: bytes) -> dict[str, object]:
    high_count = len(high)
    low_count = len(low)
    return {
        "input_bytes": len(data),
        "flags_bytes": len(flags),
        "low_bytes": low_count,
        "high_bytes": high_count,
        "container_bytes": HEADER.size + len(flags) + low_count + high_count,
        "high_share": high_count / len(data) if data else 0.0,
        "low_share": low_count / len(data) if data else 0.0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    enc = sub.add_parser("encode")
    enc.add_argument("input", type=pathlib.Path)
    enc.add_argument("output", type=pathlib.Path)
    enc.add_argument("--verify", action="store_true")
    dec = sub.add_parser("decode")
    dec.add_argument("input", type=pathlib.Path)
    dec.add_argument("output", type=pathlib.Path)
    parts = sub.add_parser("parts")
    parts.add_argument("input", type=pathlib.Path)
    parts.add_argument("prefix", type=pathlib.Path)
    stats = sub.add_parser("stats")
    stats.add_argument("input", type=pathlib.Path)
    args = ap.parse_args()

    if args.cmd == "encode":
      data = args.input.read_bytes()
      blob = encode_container(data)
      args.output.write_bytes(blob)
      if args.verify and decode_container(blob) != data:
          raise SystemExit("roundtrip failed")
      flags, low, high = split_planes(data)
      print(json.dumps(stats_payload(data, flags, low, high), sort_keys=True))
    elif args.cmd == "decode":
      args.output.write_bytes(decode_container(args.input.read_bytes()))
    elif args.cmd == "parts":
      print(json.dumps(write_parts(args.input.read_bytes(), args.prefix), sort_keys=True))
    elif args.cmd == "stats":
      data = args.input.read_bytes()
      flags, low, high = split_planes(data)
      print(json.dumps(stats_payload(data, flags, low, high), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
