"""wordcode_lzma_v1 — data-driven top-K word substitution + lzma.

WRT-class (Word Replacement Transform) preprocessor on the lzma back-end.
Picks the K most byte-saving words on the encode side, replaces each
occurrence with a single high-byte code, ships the dictionary inside
the archive, then lzma-compresses the substituted stream.

Different from ast_opcode_lzma_v1 (parser-driven, fixed XML/wikitext token
list): here the dictionary is derived from word frequencies in the actual
input, and contains real natural-language tokens like b"the", b"of", b"and",
b"section", etc. — the targets that account for most of lzma's match-bit
spend on the prose channel.

Substitution alphabet:
  - bytes [0x80..0xFF] are 128 code points
  - byte 0x02 is the literal-escape (ESC); appears nowhere in enwik9 ASCII
  - any source byte in [0x80..0xFF] or equal to 0x02 is emitted as ESC + byte

Archive layout (all inside the lzma stream):
  4B big-endian header_len
  header (header_len bytes):
      1B K (number of dict entries, 1..128)
      for each entry:
          1B word length L (1..255)
          L bytes word
  body: substituted stream
"""

from __future__ import annotations

import lzma
import re
import struct

PRESET = 9 | lzma.PRESET_EXTREME
ESC = 0x02
CODE_BASE = 0x80
MAX_K = 128
MIN_WORD_LEN = 3
MAX_WORD_LEN = 32
WORD_RE = re.compile(rb"[A-Za-z]{%d,%d}" % (MIN_WORD_LEN, MAX_WORD_LEN))


def _pick_words(data: bytes, k: int = MAX_K) -> list[bytes]:
    """Top-k words by savings = freq * (len - 1) - dict_cost."""
    counts: dict[bytes, int] = {}
    for m in WORD_RE.finditer(data):
        w = m.group(0)
        counts[w] = counts.get(w, 0) + 1
    scored: list[tuple[int, bytes]] = []
    for w, f in counts.items():
        if f < 2:
            continue
        save = f * (len(w) - 1) - (1 + len(w))
        if save > 0:
            scored.append((save, w))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [w for _, w in scored[:k]]


def _substitute(data: bytes, words: list[bytes]) -> bytes:
    code_map = {w: bytes([CODE_BASE + i]) for i, w in enumerate(words)}
    if not code_map:
        out = bytearray()
        for b in data:
            if b == ESC or b >= CODE_BASE:
                out.append(ESC)
            out.append(b)
        return bytes(out)

    pattern = re.compile(b"|".join(re.escape(w) for w in words))
    parts: list[bytes] = []
    pos = 0
    for m in pattern.finditer(data):
        if m.start() > pos:
            parts.append(_escape(data[pos : m.start()]))
        parts.append(code_map[m.group(0)])
        pos = m.end()
    if pos < len(data):
        parts.append(_escape(data[pos:]))
    return b"".join(parts)


def _escape(chunk: bytes) -> bytes:
    if not any(b == ESC or b >= CODE_BASE for b in chunk):
        return chunk
    out = bytearray()
    for b in chunk:
        if b == ESC or b >= CODE_BASE:
            out.append(ESC)
        out.append(b)
    return bytes(out)


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
                raise ValueError(f"bad code {b:#x} at {pos}")
            out.extend(words[idx])
            pos += 1
        else:
            out.append(b)
            pos += 1
    return bytes(out)


def _serialize_header(words: list[bytes]) -> bytes:
    out = bytearray()
    out.append(len(words))
    for w in words:
        if not 1 <= len(w) <= 255:
            raise ValueError(f"word length {len(w)} out of range")
        out.append(len(w))
        out.extend(w)
    return bytes(out)


def _parse_header(buf: bytes) -> list[bytes]:
    k = buf[0]
    pos = 1
    words: list[bytes] = []
    for _ in range(k):
        L = buf[pos]
        pos += 1
        words.append(buf[pos : pos + L])
        pos += L
    return words


def compress(data: bytes) -> bytes:
    words = _pick_words(data)
    body = _substitute(data, words)
    header = _serialize_header(words)
    inner = struct.pack(">I", len(header)) + header + body
    return lzma.compress(inner, preset=PRESET)


def decompress(arch: bytes) -> bytes:
    inner = lzma.decompress(arch)
    (hlen,) = struct.unpack(">I", inner[:4])
    header = inner[4 : 4 + hlen]
    body = inner[4 + hlen :]
    words = _parse_header(header)
    return _expand(body, words)
