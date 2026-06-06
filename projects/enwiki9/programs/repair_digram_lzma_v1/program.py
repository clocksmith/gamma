"""repair_digram_lzma_v1 — RePair-lite greedy digram folding + lzma.

Iterative single-pass byte-pair replacement. Each pass:
  1. count all digrams (overlapping disallowed: scan left-to-right consuming pairs)
  2. find the most-frequent digram with savings > rule_cost
  3. assign it the next free code byte in [0x80..0xFF]
  4. rewrite the stream replacing every occurrence
  5. record the rule (code -> 2-byte body)

Stops when no digram has positive savings, when the code alphabet (128 slots)
is exhausted, or after MAX_PASSES iterations. Rule bodies can themselves
contain previously-assigned codes, giving a recursive grammar.

Distinct mechanism from wordcode_lzma_v1 (whole-word substitution, single pass)
and ast_opcode_lzma_v1 (parser-fixed token list). Here the substitutions
are byte-pairs discovered from the data, including non-letter pairs like
b"  " (double space), b"==", b"  ", b">\\n", b"</", etc., which lzma matches
but each match still costs offset/length bits.

Archive (all inside the lzma stream):
  2B big-endian K (number of rules)
  for each rule (in admission order, oldest first):
      2 bytes body (already substituted; may contain earlier codes)
  4B body_len, then body_len bytes of substituted body

ESC byte 0x02 escapes literal occurrences of code bytes [0x80..0xFF] and
the ESC byte itself in the substituted body.
"""

from __future__ import annotations

import lzma
import struct
from collections import Counter

PRESET = 9 | lzma.PRESET_EXTREME
ESC = 0x02
CODE_BASE = 0x80
MAX_CODES = 128
MAX_PASSES = 128
RULE_COST = 4  # 2 bytes header (in archive) + 2 bytes body; per-rule overhead


def _count_digrams(stream: bytes) -> Counter:
    c: Counter = Counter()
    n = len(stream)
    for i in range(n - 1):
        c[stream[i : i + 2]] += 1
    return c


def _replace_digram(stream: bytes, pair: bytes, code: int) -> bytes:
    out = bytearray()
    i = 0
    n = len(stream)
    code_byte = bytes([code])
    p0, p1 = pair[0], pair[1]
    while i < n - 1:
        if stream[i] == p0 and stream[i + 1] == p1:
            out.append(code)
            i += 2
        else:
            out.append(stream[i])
            i += 1
    if i == n - 1:
        out.append(stream[n - 1])
    return bytes(out)


def _escape_literals(stream: bytes, used_codes: set[int]) -> bytes:
    """Pre-encode: any byte in used_codes ∪ {ESC} that appears in original
    must be escaped *before* substitution begins. To keep things simple and
    sound, we escape ALL bytes in [0x80..0xFF] ∪ {ESC} in the original input
    once, before any rule is applied. Rules then operate over a stream where
    all literal high-bytes are already ESC-escaped, so matches against
    ordinary ASCII pairs are unaffected.
    """
    if not any(b == ESC or b >= CODE_BASE for b in stream):
        return stream
    out = bytearray()
    for b in stream:
        if b == ESC or b >= CODE_BASE:
            out.append(ESC)
        out.append(b)
    return bytes(out)


def _build(data: bytes) -> tuple[list[bytes], bytes]:
    stream = _escape_literals(data, set(range(CODE_BASE, 256)) | {ESC})
    rules: list[bytes] = []
    next_code = CODE_BASE
    for _ in range(MAX_PASSES):
        if next_code >= CODE_BASE + MAX_CODES:
            break
        counts = _count_digrams(stream)
        best_pair = None
        best_save = 0
        for pair, freq in counts.items():
            # An occurrence of the pair in stream is replaced with 1 byte;
            # rule body costs 2 bytes once. Savings: freq * (2-1) - 2 = freq - 2.
            # Plus the rule-table overhead is RULE_COST per rule (header bytes).
            save = freq - RULE_COST
            if save > best_save:
                # Don't fold a pair where either byte is ESC
                # (would over-escape downstream)
                if pair[0] == ESC or pair[1] == ESC:
                    continue
                best_save = save
                best_pair = pair
        if best_pair is None:
            break
        rules.append(best_pair)
        stream = _replace_digram(stream, best_pair, next_code)
        next_code += 1
    return rules, stream


def _serialize(rules: list[bytes], body: bytes) -> bytes:
    out = bytearray()
    out.extend(struct.pack(">H", len(rules)))
    for r in rules:
        if len(r) != 2:
            raise ValueError("rule body must be exactly 2 bytes")
        out.extend(r)
    out.extend(struct.pack(">I", len(body)))
    out.extend(body)
    return bytes(out)


def _parse(inner: bytes) -> tuple[list[bytes], bytes]:
    (k,) = struct.unpack(">H", inner[:2])
    pos = 2
    rules: list[bytes] = []
    for _ in range(k):
        rules.append(inner[pos : pos + 2])
        pos += 2
    (blen,) = struct.unpack(">I", inner[pos : pos + 4])
    pos += 4
    body = inner[pos : pos + blen]
    return rules, body


def _expand(rules: list[bytes], body: bytes) -> bytes:
    # Build the full byte expansion of every code, oldest-first.
    # rules[i] is the 2-byte body of code (CODE_BASE + i); a body byte may be
    # an earlier code (already in `expansions`).
    expansions: list[bytes] = []
    for r in rules:
        out = bytearray()
        for b in r:
            if b >= CODE_BASE:
                out.extend(expansions[b - CODE_BASE])
            else:
                out.append(b)
        expansions.append(bytes(out))
    # Expand the body.
    flat = bytearray()
    for b in body:
        if b >= CODE_BASE:
            flat.extend(expansions[b - CODE_BASE])
        else:
            flat.append(b)
    # Unescape ESC-prefixed literals.
    out = bytearray()
    i = 0
    n = len(flat)
    while i < n:
        b = flat[i]
        if b == ESC:
            i += 1
            out.append(flat[i])
            i += 1
        else:
            out.append(b)
            i += 1
    return bytes(out)


def compress(data: bytes) -> bytes:
    rules, body = _build(data)
    inner = _serialize(rules, body)
    return lzma.compress(inner, preset=PRESET)


def decompress(arch: bytes) -> bytes:
    inner = lzma.decompress(arch)
    rules, body = _parse(inner)
    return _expand(rules, body)
