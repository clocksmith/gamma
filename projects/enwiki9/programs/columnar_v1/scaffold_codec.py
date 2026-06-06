"""scaffold_codec — wordcode pre-pass for the prose-heavy scaffold channel.

The scaffold is the largest channel in every mode. It carries XML
boilerplate, prose article body, and (in Phase 1) the still-intact
{{template}} and [[wikilink]] constructs. lzma extracts most natural-
language redundancy from it, but misses the cross-window word-frequency
signal — words like "the", "and", "is", "with" appear millions of times
across enwik9 and lzma encodes each match as offset+length bits per
occurrence.

This codec runs a top-K most-byte-saving word substitution BEFORE the
single-stream lzma sees the buffer. Each admitted word becomes a
single-byte code in [0x80..0xFF]; the dictionary ships in the channel
bytes (header). lzma then sees a shorter, more redundant stream
(sentinel-bearing, code-bearing) and compresses it tighter.

This is type-aware compression: the scaffold channel is "prose-like" so
it gets a prose codec; narrow-vocab columns get dict-coding; atom
channels get raw lzma. Each typed appropriately. Roundtrip is
byte-perfect by construction (escape pairs handle literal high bytes).

ESC = 0x02. CODE_BASE = 0x80. Code range = [0x80, 0xFF]. Literals in
[0x80, 0xFF] or equal to ESC are escaped: ESC + byte. Decoder walks
left-to-right; ESC means "next byte is a literal", any other byte
>= 0x80 means "code reference".

Scaffold contains the four-byte XML/template/wikilink sentinels (e.g.
0x00 0x00 0xFE 0xF1). The 0xFE byte gets escaped (→ 0x02 0xFE) and
recovered byte-perfect on unpack — sentinel preservation is built in.
"""

from __future__ import annotations

import re
import struct

ESC = 0x02
CODE_BASE = 0x80
MAX_K = 128
MIN_WORD_LEN = 3
MAX_WORD_LEN = 32
MIN_WORD_FREQ = 2
WORD_RE = re.compile(rb"[A-Za-z]{%d,%d}" % (MIN_WORD_LEN, MAX_WORD_LEN))


def _pick_words(data: bytes, k: int = MAX_K) -> list[bytes]:
    counts: dict[bytes, int] = {}
    for m in WORD_RE.finditer(data):
        w = m.group(0)
        counts[w] = counts.get(w, 0) + 1
    scored: list[tuple[int, bytes]] = []
    for w, f in counts.items():
        if f < MIN_WORD_FREQ:
            continue
        save = f * (len(w) - 1) - (1 + len(w))
        if save > 0:
            scored.append((save, w))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [w for _, w in scored[:k]]


def _escape(chunk: bytes) -> bytes:
    if not any(b == ESC or b >= CODE_BASE for b in chunk):
        return chunk
    out = bytearray()
    for b in chunk:
        if b == ESC or b >= CODE_BASE:
            out.append(ESC)
        out.append(b)
    return bytes(out)


def _substitute(data: bytes, words: list[bytes]) -> bytes:
    if not words:
        return _escape(data)
    code_map = {w: bytes([CODE_BASE + i]) for i, w in enumerate(words)}
    pat = re.compile(b"|".join(re.escape(w) for w in words))
    parts: list[bytes] = []
    pos = 0
    for m in pat.finditer(data):
        if m.start() > pos:
            parts.append(_escape(data[pos : m.start()]))
        parts.append(code_map[m.group(0)])
        pos = m.end()
    if pos < len(data):
        parts.append(_escape(data[pos:]))
    return b"".join(parts)


def _expand(stream: bytes, words: list[bytes]) -> bytes:
    out = bytearray()
    pos = 0
    n = len(stream)
    while pos < n:
        b = stream[pos]
        if b == ESC:
            pos += 1
            out.append(stream[pos])
            pos += 1
        elif b >= CODE_BASE:
            idx = b - CODE_BASE
            if idx >= len(words):
                raise ValueError(f"bad code {b:#x} idx={idx}")
            out.extend(words[idx])
            pos += 1
        else:
            out.append(b)
            pos += 1
    return bytes(out)


def pack(data: bytes) -> bytes:
    """data → packed bytes (header + substituted body). Header carries
    the word dictionary; body uses single-byte codes for substituted
    words and ESC-prefix escapes for literal high bytes / ESC bytes."""
    words = _pick_words(data)
    body = _substitute(data, words)
    header = bytearray()
    if not 0 <= len(words) <= 255:
        raise ValueError(f"word count {len(words)} out of range")
    header.append(len(words))
    for w in words:
        if not 1 <= len(w) <= 255:
            raise ValueError(f"word length {len(w)} out of range")
        header.append(len(w))
        header.extend(w)
    out = bytearray()
    out.extend(struct.pack(">I", len(header)))
    out.extend(header)
    out.extend(body)
    return bytes(out)


def unpack(packed: bytes) -> bytes:
    (hlen,) = struct.unpack(">I", packed[:4])
    header = packed[4 : 4 + hlen]
    body = packed[4 + hlen :]
    k = header[0]
    pos = 1
    words: list[bytes] = []
    for _ in range(k):
        L = header[pos]
        pos += 1
        words.append(header[pos : pos + L])
        pos += L
    return _expand(body, words)
