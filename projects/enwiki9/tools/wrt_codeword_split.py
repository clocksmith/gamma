#!/usr/bin/env python3
"""Split fx2 WRT-style codewords from a preprocessed cmix input stream."""

from __future__ import annotations

import argparse
import json
import pathlib
import struct

MAGIC = b"WCS1"
HEADER = struct.Struct("<4sQQQQ")
ESC = 0
MARK1 = 1
MARK2 = 2
MARK3 = 3
LITERAL_MARKERS = {ESC, MARK1, MARK2, MARK3}
DICT_ESCAPE = 0x0C


def next_char(c: int) -> int:
    if c >= ord("{") and c < 127:
        c += ord("P") - ord("{")
    elif c >= ord("P") and c < ord("T"):
        c -= ord("P") - ord("{")
    elif (ord(":") <= c <= ord("?")) or (ord("J") <= c <= ord("O")):
        c ^= 0x70
    if c == ord("X") or c == ord("`"):
        c ^= ord("X") ^ ord("`")
    return c


def emit_literal(main: bytearray, b: int) -> None:
    if b in LITERAL_MARKERS:
        main.extend((ESC, b))
    else:
        main.append(b)


def split_stream(data: bytes) -> tuple[bytes, bytes, bytes, bytes]:
    logical = bytes(next_char(b) for b in data)
    main = bytearray()
    p0 = bytearray()
    p1 = bytearray()
    p2 = bytearray()
    i = 0
    while i < len(logical):
        c = logical[i]
        if c == DICT_ESCAPE:
            emit_literal(main, c)
            i += 1
            if i < len(logical):
                emit_literal(main, logical[i])
                i += 1
            continue
        if c >= 0x80:
            length = 1
            if c > 0xCF and i + 1 < len(logical):
                length = 2
                if logical[i + 1] > 0xCF and i + 2 < len(logical):
                    length = 3
            if length == 1:
                main.append(MARK1)
                p0.append(c - 0x80)
            elif length == 2:
                main.append(MARK2)
                p0.append(c - 0x80)
                p1.append(logical[i + 1])
            else:
                main.append(MARK3)
                p0.append(c - 0x80)
                p1.append(logical[i + 1])
                p2.append(logical[i + 2])
            i += length
            continue
        emit_literal(main, c)
        i += 1
    return bytes(main), bytes(p0), bytes(p1), bytes(p2)


def join_stream(main: bytes, p0: bytes, p1: bytes, p2: bytes) -> bytes:
    logical = bytearray()
    i = j0 = j1 = j2 = 0
    while i < len(main):
        c = main[i]
        i += 1
        if c == ESC:
            if i >= len(main):
                raise ValueError("truncated escape")
            logical.append(main[i])
            i += 1
        elif c == MARK1:
            if j0 >= len(p0):
                raise ValueError("truncated plane0")
            logical.append(p0[j0] + 0x80)
            j0 += 1
        elif c == MARK2:
            if j0 >= len(p0) or j1 >= len(p1):
                raise ValueError("truncated plane")
            logical.append(p0[j0] + 0x80)
            logical.append(p1[j1])
            j0 += 1
            j1 += 1
        elif c == MARK3:
            if j0 >= len(p0) or j1 >= len(p1) or j2 >= len(p2):
                raise ValueError("truncated plane")
            logical.append(p0[j0] + 0x80)
            logical.append(p1[j1])
            logical.append(p2[j2])
            j0 += 1
            j1 += 1
            j2 += 1
        else:
            logical.append(c)
    if j0 != len(p0) or j1 != len(p1) or j2 != len(p2):
        raise ValueError("unused plane bytes")
    return bytes(next_char(b) for b in logical)


def stats_payload(data: bytes, main: bytes, p0: bytes, p1: bytes, p2: bytes) -> dict[str, object]:
    codewords = len(p0)
    return {
        "input_bytes": len(data),
        "main_bytes": len(main),
        "plane0_bytes": len(p0),
        "plane1_bytes": len(p1),
        "plane2_bytes": len(p2),
        "codewords": codewords,
        "container_bytes": HEADER.size + len(main) + len(p0) + len(p1) + len(p2),
        "codeword_share": codewords / len(data) if data else 0.0,
    }


def encode_container(data: bytes) -> bytes:
    main, p0, p1, p2 = split_stream(data)
    return (
        HEADER.pack(MAGIC, len(main), len(p0), len(p1), len(p2))
        + main
        + p0
        + p1
        + p2
    )


def decode_container(blob: bytes) -> bytes:
    if len(blob) < HEADER.size:
        raise ValueError("truncated header")
    magic, main_len, p0_len, p1_len, p2_len = HEADER.unpack(blob[: HEADER.size])
    if magic != MAGIC:
        raise ValueError("bad magic")
    pos = HEADER.size
    main = blob[pos : pos + main_len]
    pos += main_len
    p0 = blob[pos : pos + p0_len]
    pos += p0_len
    p1 = blob[pos : pos + p1_len]
    pos += p1_len
    p2 = blob[pos : pos + p2_len]
    if pos + p2_len != len(blob):
        raise ValueError("trailing bytes")
    return join_stream(main, p0, p1, p2)


def write_parts(data: bytes, prefix: pathlib.Path) -> dict[str, object]:
    main, p0, p1, p2 = split_stream(data)
    paths = {
        "main": prefix.with_suffix(prefix.suffix + ".main"),
        "p0": prefix.with_suffix(prefix.suffix + ".p0"),
        "p1": prefix.with_suffix(prefix.suffix + ".p1"),
        "p2": prefix.with_suffix(prefix.suffix + ".p2"),
        "meta": prefix.with_suffix(prefix.suffix + ".json"),
    }
    paths["main"].write_bytes(main)
    paths["p0"].write_bytes(p0)
    paths["p1"].write_bytes(p1)
    paths["p2"].write_bytes(p2)
    meta = stats_payload(data, main, p0, p1, p2)
    paths["meta"].write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    return {"paths": {key: str(value) for key, value in paths.items()}, **meta}


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
    args = ap.parse_args()

    if args.cmd == "encode":
        data = args.input.read_bytes()
        blob = encode_container(data)
        args.output.write_bytes(blob)
        if args.verify and decode_container(blob) != data:
            raise SystemExit("roundtrip failed")
        main, p0, p1, p2 = split_stream(data)
        print(json.dumps(stats_payload(data, main, p0, p1, p2), sort_keys=True))
    elif args.cmd == "decode":
        args.output.write_bytes(decode_container(args.input.read_bytes()))
    elif args.cmd == "parts":
        print(json.dumps(write_parts(args.input.read_bytes(), args.prefix), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
