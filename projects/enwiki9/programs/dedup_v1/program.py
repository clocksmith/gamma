"""dedup_v1 — fixed-size chunk deduplication, then lzma --extreme -9.

Splits input into 256-byte chunks, hashes each. For each chunk, if the
identical chunk has been seen before, emit a back-reference; else emit a
literal. The output stream is then lzma'd. The point is to capture
cross-article duplicates that exceed lzma's match window.

Frame format per chunk in the dedup'd stream (before lzma):
    0x00 + chunk_data         (literal, exactly CHUNK_SIZE bytes for full
                               chunks; final partial chunk is 0x02 + length(2B) + data)
    0x01 + ref_idx (4B BE)    (back-reference to chunk index ref_idx)

Reversibility: the decoder rebuilds the chunk array by replaying the same
order: every literal is appended to the chunk list, every reference indexes
into it.
"""

from __future__ import annotations

import hashlib
import lzma
import struct

CHUNK_SIZE = 256
PRESET = 9 | lzma.PRESET_EXTREME


def _dedup(data: bytes) -> bytes:
    """returns a dedup'd byte stream (smaller-or-equal modulo overhead)."""
    chunks: list[bytes] = []
    seen: dict[bytes, int] = {}
    out: list[bytes] = []
    n = len(data)
    pos = 0
    while pos + CHUNK_SIZE <= n:
        chunk = data[pos : pos + CHUNK_SIZE]
        h = hashlib.sha1(chunk).digest()[:8]
        idx = seen.get(h)
        if idx is not None and chunks[idx] == chunk:
            out.append(b"\x01" + struct.pack(">I", idx))
        else:
            seen[h] = len(chunks)
            chunks.append(chunk)
            out.append(b"\x00" + chunk)
        pos += CHUNK_SIZE
    if pos < n:
        tail = data[pos:]
        out.append(b"\x02" + struct.pack(">H", len(tail)) + tail)
    return b"".join(out)


def _undedup(stream: bytes) -> bytes:
    chunks: list[bytes] = []
    out: list[bytes] = []
    pos = 0
    n = len(stream)
    while pos < n:
        op = stream[pos]
        pos += 1
        if op == 0x00:
            chunk = stream[pos : pos + CHUNK_SIZE]
            chunks.append(chunk)
            out.append(chunk)
            pos += CHUNK_SIZE
        elif op == 0x01:
            (idx,) = struct.unpack(">I", stream[pos : pos + 4])
            out.append(chunks[idx])
            pos += 4
        elif op == 0x02:
            (ln,) = struct.unpack(">H", stream[pos : pos + 2])
            pos += 2
            out.append(stream[pos : pos + ln])
            pos += ln
        else:
            raise ValueError(f"bad op {op:#x} at offset {pos - 1}")
    return b"".join(out)


def compress(data: bytes) -> bytes:
    return lzma.compress(_dedup(data), preset=PRESET)


def decompress(data: bytes) -> bytes:
    return _undedup(lzma.decompress(data))
