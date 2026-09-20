#!/usr/bin/env python3
"""Bounded, verified block compressor. No claim of Hutter Prize qualification.

Candidates: literal bytes, Deflate, Bzip2, LZMA, optional C++ context/role codec.
Each block resets candidate state. Exact payload lengths choose the winner;
method identifiers, lengths and checksums are stored in the actual archive.
Python libraries and an optional native executable are dependencies, not free.
"""
from __future__ import annotations
import argparse
import bz2
import hashlib
import json
import lzma
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import time
import zlib
from typing import BinaryIO

MAGIC = b"GCB\x01\r\n\x1a\n"
HEADER = struct.Struct("<8sIQ32s")
BLOCK = struct.Struct("<BIIII")
MAX_BLOCK = 1 << 20
MAX_PACKED = 32 * MAX_BLOCK + 65536
NAMES = {0: "stored", 1: "deflate", 2: "bzip2", 3: "lzma", 4: "context", 5: "role-history"}
METHODS = {v: k for k, v in NAMES.items()}
CANONICAL_SIZE = 1_000_000_000
CANONICAL_HASH = "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def exact(f: BinaryIO, n: int) -> bytes:
    data = f.read(n)
    require(len(data) == n, "truncated archive")
    return data


def native(data: bytes, *, encode: bool, mode: int, cpp: Path) -> bytes:
    require(cpp.is_file(), "native codec is required but missing")
    with tempfile.TemporaryDirectory(prefix="crg-") as directory:
        source, target = Path(directory) / "input", Path(directory) / "output"
        source.write_bytes(data)
        command = [str(cpp.resolve()), "c" if encode else "d", str(source), str(target)]
        if encode:
            command.append("base" if mode == 4 else "history")
        result = subprocess.run(command, capture_output=True, timeout=60)
        require(result.returncode == 0,
                "native codec failed: " + result.stderr.decode("utf-8", errors="replace")[:1024])
        require(target.is_file() and target.stat().st_size <= MAX_PACKED, "native output exceeds bound")
        return target.read_bytes()


def encode_block(raw: bytes, mode: int, cpp: Path | None = None) -> bytes:
    require(len(raw) <= MAX_BLOCK, "block too large")
    if mode == 0:
        return raw
    if mode == 1:
        return zlib.compress(raw, 9)
    if mode == 2:
        return bz2.compress(raw, compresslevel=9)
    if mode == 3:
        return lzma.compress(raw, format=lzma.FORMAT_XZ, preset=6, check=lzma.CHECK_CRC64)
    require(mode in (4, 5) and cpp is not None, "unknown or unavailable method")
    return native(raw, encode=True, mode=mode, cpp=cpp)


def decode_block(payload: bytes, mode: int, n: int, cpp: Path | None = None) -> bytes:
    require(0 <= n <= MAX_BLOCK and len(payload) <= MAX_PACKED, "invalid block bounds")
    if mode == 0:
        raw = payload
    elif mode in (1, 2, 3):
        decoder = (zlib.decompressobj() if mode == 1 else bz2.BZ2Decompressor()
                   if mode == 2 else lzma.LZMADecompressor(format=lzma.FORMAT_XZ, memlimit=128 << 20))
        # Bound output before allocating it. Reject concatenated/trailing streams.
        raw = decoder.decompress(payload, n + 1)
        require(decoder.eof and not decoder.unused_data, "incomplete or concatenated compressed block")
        if mode == 1:
            require(not decoder.unconsumed_tail, "unconsumed Deflate bytes")
    else:
        require(mode in (4, 5) and cpp is not None, "native codec required or unknown method")
        require(len(payload) >= 24 and payload[:4] == b"CGR1" and payload[4] == mode - 4,
                "native block mode mismatch")
        raw = native(payload, encode=False, mode=mode, cpp=cpp)
    require(len(raw) == n, "decoded length mismatch")
    return raw


def _publish(temp: Path, output: Path) -> None:
    # Atomic publication without overwriting a prior file. Temp is on same FS.
    os.link(temp, output)
    temp.unlink()


def compress_file(source: Path, output: Path, *, block_size: int = MAX_BLOCK,
                  method: str = "auto", cpp: Path | None = None) -> dict:
    require(1 <= block_size <= MAX_BLOCK, "block size must be 1..1048576")
    require(source.resolve() != output.resolve(), "input equals output")
    require(not output.exists(), "output already exists")
    require(method == "auto" or method in METHODS, "unknown method")
    stat = source.stat()
    candidates = [0, 1, 2, 3] + ([4, 5] if cpp else []) if method == "auto" else [METHODS[method]]
    start = time.perf_counter()
    rows, offset, digest = [], 0, hashlib.sha256()
    fd, name = tempfile.mkstemp(prefix=".gcb-", dir=output.parent)
    temp = Path(name)
    try:
        with os.fdopen(fd, "w+b") as out, source.open("rb") as inp:
            out.write(HEADER.pack(MAGIC, block_size, stat.st_size, bytes(32)))
            while raw := inp.read(block_size):
                options = []
                for mode in candidates:
                    payload = encode_block(raw, mode, cpp)
                    require(len(payload) <= MAX_PACKED, "encoded block exceeds bound")
                    options.append((mode, payload))
                selected, payload = min(options, key=lambda item: (len(item[1]), item[0]))
                require(decode_block(payload, selected, len(raw), cpp) == raw, "candidate fails inverse")
                out.write(BLOCK.pack(selected, len(raw), len(payload), zlib.crc32(raw), zlib.crc32(payload)))
                out.write(payload)
                rows.append({"offset": offset, "raw_bytes": len(raw), "selected": NAMES[selected],
                             "payload_bytes": len(payload), "record_bytes": BLOCK.size + len(payload),
                             "candidate_payloads": {NAMES[m]: len(p) for m, p in options}})
                offset += len(raw)
                digest.update(raw)
            after = source.stat()
            require((stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns) ==
                    (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) and offset == stat.st_size,
                    "input changed during encoding")
            out.seek(0)
            out.write(HEADER.pack(MAGIC, block_size, offset, digest.digest()))
            out.flush()
            os.fsync(out.fileno())
        _publish(temp, output)
    finally:
        temp.unlink(missing_ok=True)
    return {"format": "GCB1", "input_bytes": offset, "input_sha256": digest.hexdigest(),
            "archive_bytes": output.stat().st_size, "seconds": time.perf_counter() - start,
            "blocks": rows, "package_accounting_complete": False, "hutter_win_established": False}


def decompress_file(source: Path, output: Path, *, cpp: Path | None = None,
                    max_output: int = 1_000_000_000) -> dict:
    require(source.resolve() != output.resolve(), "input equals output")
    require(not output.exists(), "output already exists")
    fd, name = tempfile.mkstemp(prefix=".gcb-", dir=output.parent)
    temp = Path(name)
    count, digest, modes = 0, hashlib.sha256(), []
    try:
        with os.fdopen(fd, "wb") as out, source.open("rb") as inp:
            magic, block_size, total, expected = HEADER.unpack(exact(inp, HEADER.size))
            require(magic == MAGIC and 1 <= block_size <= MAX_BLOCK, "invalid format header")
            require(0 <= total <= max_output, "declared output exceeds configured bound")
            while count < total:
                mode, n, length, raw_crc, payload_crc = BLOCK.unpack(exact(inp, BLOCK.size))
                require(mode in NAMES and n == min(block_size, total - count), "invalid block sequence")
                require(0 < length <= MAX_PACKED, "invalid compressed length")
                payload = exact(inp, length)
                require(zlib.crc32(payload) == payload_crc, "compressed checksum mismatch")
                raw = decode_block(payload, mode, n, cpp)
                require(zlib.crc32(raw) == raw_crc, "raw checksum mismatch")
                out.write(raw)
                digest.update(raw)
                count += n
                modes.append(NAMES[mode])
            require(not inp.read(1), "trailing archive bytes")
            require(digest.digest() == expected, "full decoded SHA-256 mismatch")
            out.flush()
            os.fsync(out.fileno())
        _publish(temp, output)
    finally:
        temp.unlink(missing_ok=True)
    return {"output_bytes": count, "output_sha256": digest.hexdigest(), "methods": modes,
            "canonical_enwik9_identity": count == CANONICAL_SIZE and digest.hexdigest() == CANONICAL_HASH,
            "hutter_win_established": False}


def benchmark(source: Path, cpp: Path | None) -> dict:
    require(source.stat().st_size <= MAX_BLOCK, "bench accepts at most one 1-MiB block")
    raw = source.read_bytes()
    rows = []
    for mode in [0, 1, 2, 3] + ([4, 5] if cpp else []):
        start = time.perf_counter()
        payload = encode_block(raw, mode, cpp)
        enc_s = time.perf_counter() - start
        start = time.perf_counter()
        restored = decode_block(payload, mode, len(raw), cpp)
        dec_s = time.perf_counter() - start
        repeat = encode_block(restored, mode, cpp)
        require(restored == raw and repeat == payload, "roundtrip or repeat failure")
        rows.append({"method": NAMES[mode], "payload_bytes": len(payload),
                     "GCB1_archive_bytes": HEADER.size + (BLOCK.size + len(payload) if raw else 0),
                     "encode_seconds": enc_s, "decode_seconds": dec_s,
                     "exact_inverse": True, "repeat_identical": True,
                     "sha256": hashlib.sha256(payload).hexdigest()})
    return {"input_bytes": len(raw), "input_sha256": hashlib.sha256(raw).hexdigest(), "rows": rows,
            "source_package_and_runtime_not_included": True, "hutter_win_established": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for cmd in ("encode", "decode", "bench"):
        p = sub.add_parser(cmd)
        p.add_argument("input", type=Path)
        if cmd != "bench":
            p.add_argument("output", type=Path)
        p.add_argument("--cpp", type=Path, help="optional compiled crg executable; required to decode its blocks")
        if cmd == "encode":
            p.add_argument("--method", choices=["auto"] + list(METHODS), default="auto")
            p.add_argument("--block-size", type=int, default=MAX_BLOCK)
        elif cmd == "decode":
            p.add_argument("--max-output", type=int, default=CANONICAL_SIZE)
    args = parser.parse_args()
    try:
        if args.command == "encode":
            result = compress_file(args.input, args.output, block_size=args.block_size, method=args.method, cpp=args.cpp)
        elif args.command == "decode":
            result = decompress_file(args.input, args.output, cpp=args.cpp, max_output=args.max_output)
        else:
            result = benchmark(args.input, args.cpp)
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, EOFError, lzma.LZMAError, zlib.error, subprocess.SubprocessError) as exc:
        parser.exit(2, f"error: {exc}\n")

if __name__ == "__main__":
    main()
