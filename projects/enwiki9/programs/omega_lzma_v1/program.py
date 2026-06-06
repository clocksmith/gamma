"""omega_lzma_v1 — recursive RePair grammar over a token stream + lzma.

Self-referential structure:
  A grammar G of rules R_0, R_1, ..., R_{K-1}. Each rule body is a pair of
  TOKENS (not bytes). A token is either a literal byte (0..255) or a code
  reference to an earlier rule. Bodies can recursively reference earlier
  rules — the grammar is a Straight-Line Program (SLP), strict ordering, no
  cycles, finite expansion.

Why token stream and not byte stream:
  Byte-pair RePair on natural text has an unsolvable disambiguation problem
  when the alphabet has reserved code bytes — a literal high-byte (e.g.,
  UTF-8 0xC3 from "é") becomes indistinguishable from a code byte after
  greedy folding consumes the escape sentinel that preceded it. Earlier
  byte-pair attempt (`repair_digram_lzma_v1`) failed roundtrip at 100 KB
  for exactly this reason. The token stream is unambiguous by construction:
  parsing reads byte-pairs (ESC, X) -> literal X and bare bytes >= 0x80
  -> CODE, so literal high-bytes and code references never collide.

Pipeline:
  encode:
    bytes -> tokens (1 token per byte at start)
    iterate (greedy, freq-based):
        count token-pair frequencies
        pick highest-frequency pair with freq > MIN_FREQ
        admit a new code; replace pair with new code in stream
    serialize: K rules + body_tokens, each token serialized to 1-2 bytes
    lzma --extreme -9 the serialized inner stream

  decode:
    lzma decompress
    parse K rules + body_tokens
    expand each code to its full byte-string oldest-first
    expand body_tokens to bytes

Token byte encoding (output side):
    - literal byte b in [0..0x7F] and b != ESC: 1 byte = b
    - literal byte b == ESC (0x01): 2 bytes = ESC ESC
    - literal byte b in [0x80..0xFF]: 2 bytes = ESC b
    - code reference c in [0..127]:   1 byte = 0x80 + c

Decoder of bytes -> tokens:
    - byte == ESC: peek next; emit LITERAL(next); consume 2
    - byte >= 0x80: emit CODE(byte - 0x80); consume 1
    - otherwise:    emit LITERAL(byte); consume 1

Strict ordering (rule i body bytes are codes < i, or literal bytes) is
preserved by admission order, so expansion is well-defined.
"""

from __future__ import annotations

import lzma
import struct
from collections import Counter

PRESET = 9 | lzma.PRESET_EXTREME
ESC = 0x01
CODE_BASE = 0x80
MAX_CODES = 128
MIN_FREQ = 4

# Token domain:
#   0..255     : literal bytes
#   256..383   : CODE(0)..CODE(127), references to rules 0..127
_CODE_TAG = 256


def _is_code(t: int) -> bool:
    return t >= _CODE_TAG


def _code_idx(t: int) -> int:
    return t - _CODE_TAG


def _make_code(i: int) -> int:
    return _CODE_TAG + i


def _tokens_to_bytes(tokens: list[int]) -> bytes:
    out = bytearray()
    for t in tokens:
        if _is_code(t):
            out.append(CODE_BASE + _code_idx(t))
        elif t == ESC or t >= CODE_BASE:
            out.append(ESC)
            out.append(t)
        else:
            out.append(t)
    return bytes(out)


def _bytes_to_tokens(stream: bytes) -> list[int]:
    tokens: list[int] = []
    i = 0
    n = len(stream)
    while i < n:
        b = stream[i]
        if b == ESC:
            i += 1
            tokens.append(stream[i])
            i += 1
        elif b >= CODE_BASE:
            tokens.append(_make_code(b - CODE_BASE))
            i += 1
        else:
            tokens.append(b)
            i += 1
    return tokens


def _count_pairs(tokens: list[int]) -> Counter:
    c: Counter = Counter()
    for i in range(len(tokens) - 1):
        c[(tokens[i], tokens[i + 1])] += 1
    return c


def _replace_pair(
    tokens: list[int], pair: tuple[int, int], new_token: int
) -> list[int]:
    p0, p1 = pair
    out: list[int] = []
    i = 0
    n = len(tokens)
    while i < n - 1:
        if tokens[i] == p0 and tokens[i + 1] == p1:
            out.append(new_token)
            i += 2
        else:
            out.append(tokens[i])
            i += 1
    if i == n - 1:
        out.append(tokens[n - 1])
    return out


def _build(data: bytes) -> tuple[list[tuple[int, int]], list[int]]:
    tokens: list[int] = list(data)  # every byte starts as a literal token
    rules: list[tuple[int, int]] = []
    while len(rules) < MAX_CODES:
        counts = _count_pairs(tokens)
        if not counts:
            break
        best_pair, best_freq = counts.most_common(1)[0]
        if best_freq <= MIN_FREQ:
            break
        new_code_token = _make_code(len(rules))
        rules.append(best_pair)
        tokens = _replace_pair(tokens, best_pair, new_code_token)
    return rules, tokens


def _serialize(rules: list[tuple[int, int]], body_tokens: list[int]) -> bytes:
    out = bytearray()
    out.extend(struct.pack(">H", len(rules)))
    for a, b in rules:
        for t in (a, b):
            if _is_code(t):
                out.append(1)
                out.append(_code_idx(t))
            else:
                out.append(0)
                out.append(t)
    body = _tokens_to_bytes(body_tokens)
    out.extend(struct.pack(">I", len(body)))
    out.extend(body)
    return bytes(out)


def _parse(inner: bytes) -> tuple[list[tuple[int, int]], list[int]]:
    pos = 0
    (k,) = struct.unpack(">H", inner[pos : pos + 2])
    pos += 2
    rules: list[tuple[int, int]] = []
    for _ in range(k):
        a_type = inner[pos]
        a_val = inner[pos + 1]
        pos += 2
        b_type = inner[pos]
        b_val = inner[pos + 1]
        pos += 2
        a_tok = _make_code(a_val) if a_type else a_val
        b_tok = _make_code(b_val) if b_type else b_val
        rules.append((a_tok, b_tok))
    (blen,) = struct.unpack(">I", inner[pos : pos + 4])
    pos += 4
    body_bytes = inner[pos : pos + blen]
    return rules, _bytes_to_tokens(body_bytes)


def _expand(
    rules: list[tuple[int, int]], body_tokens: list[int]
) -> bytes:
    expansions: list[bytes] = []
    for a, b in rules:
        out = bytearray()
        for t in (a, b):
            if _is_code(t):
                out.extend(expansions[_code_idx(t)])
            else:
                out.append(t)
        expansions.append(bytes(out))
    out = bytearray()
    for t in body_tokens:
        if _is_code(t):
            out.extend(expansions[_code_idx(t)])
        else:
            out.append(t)
    return bytes(out)


def compress(data: bytes) -> bytes:
    rules, body_tokens = _build(data)
    inner = _serialize(rules, body_tokens)
    return lzma.compress(inner, preset=PRESET)


def decompress(arch: bytes) -> bytes:
    inner = lzma.decompress(arch)
    rules, body_tokens = _parse(inner)
    return _expand(rules, body_tokens)
