"""promethea_lzma_v1 — bidirectional two-layer self-referential SLP + lzma.

Self-referential structure that crosses the byte/word boundary:

  Layer A (Word codes):
    Top K_w words by saving = freq*(len-1) - dict_cost. One-pass byte-level
    substitution. Each admitted word becomes a CODE token referencing a
    variable-length byte body.

  Layer B (RePair digrams over the post-Layer-A token stream):
    Iterative greedy 2-token folding. The token stream contains literal
    byte tokens AND Layer A word codes; RePair pairs may be (literal,
    literal), (literal, word_code), (word_code, literal), or
    (word_code, word_code). A Layer B rule can therefore reference Layer A
    codes — bidirectional self-reference between byte-level and word-level
    grammar. Stops when no positive-saving digram remains, when the code
    budget is exhausted, or after MAX_PASSES.

Code budget: K_w (Layer A) + K_d (Layer B) <= 128 total. Word codes get
indices 0..K_w-1; digram codes get K_w..K_w+K_d-1.

Token domain (in-memory): int values, 0..255 = literal byte, 256+i =
CODE(i) = reference to rule i.

Byte encoding (output side) — same scheme as omega_lzma_v1 so the body bytes
can be parsed unambiguously:
  literal byte b in [0..0x7F] and b != ESC (0x01): 1 byte = b
  literal byte b == ESC: 2 bytes = ESC ESC
  literal byte b in [0x80..0xFF]: 2 bytes = ESC b
  CODE(i): 1 byte = 0x80 + i  (since K_w + K_d <= 128)

Note: this v1 holds the whole token stream as a Python list of ints.
Practical scope ceiling on this hardware: ~10 MB before memory pressure.
A bytestream-native v2 can scale further; out of scope here.

Reject list (do not silently re-introduce):
  - any operation that breaks the byte-perfect roundtrip
  - any non-deterministic admission order (e.g., dict iteration without sort)
  - any escape scheme that conflates literal high-bytes with code references
"""

from __future__ import annotations

import lzma
import re
import struct
from collections import Counter

PRESET = 9 | lzma.PRESET_EXTREME
ESC = 0x01
CODE_BASE = 0x80
MAX_TOTAL_CODES = 128

K_WORDS = 64
K_DIGRAMS = 64
MIN_WORD_FREQ = 4
MIN_WORD_LEN = 3
MAX_WORD_LEN = 24
MIN_DIGRAM_FREQ = 8
MAX_DIGRAM_PASSES = 256
WORD_RE = re.compile(rb"[A-Za-z]{%d,%d}" % (MIN_WORD_LEN, MAX_WORD_LEN))

_CODE_TAG = 256


def _is_code(t: int) -> bool:
    return t >= _CODE_TAG


def _code_idx(t: int) -> int:
    return t - _CODE_TAG


def _make_code(i: int) -> int:
    return _CODE_TAG + i


# ---------- Layer A: word substitution ----------

def _pick_words(data: bytes, k: int) -> list[bytes]:
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


def _substitute_words(data: bytes, words: list[bytes]) -> list[int]:
    if not words:
        return list(data)
    pattern = re.compile(b"|".join(re.escape(w) for w in words))
    word_to_token = {w: _make_code(i) for i, w in enumerate(words)}
    tokens: list[int] = []
    pos = 0
    for m in pattern.finditer(data):
        if m.start() > pos:
            tokens.extend(data[pos : m.start()])
        tokens.append(word_to_token[m.group(0)])
        pos = m.end()
    if pos < len(data):
        tokens.extend(data[pos:])
    return tokens


# ---------- Layer B: RePair on the token stream ----------

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


def _repair(
    tokens: list[int], next_code_idx: int, max_admissions: int
) -> tuple[list[tuple[int, int]], list[int]]:
    rules: list[tuple[int, int]] = []
    for _ in range(min(max_admissions, MAX_DIGRAM_PASSES)):
        if next_code_idx + len(rules) >= MAX_TOTAL_CODES:
            break
        counts = _count_pairs(tokens)
        if not counts:
            break
        best_pair, best_freq = counts.most_common(1)[0]
        if best_freq < MIN_DIGRAM_FREQ:
            break
        new_token = _make_code(next_code_idx + len(rules))
        rules.append(best_pair)
        tokens = _replace_pair(tokens, best_pair, new_token)
    return rules, tokens


# ---------- byte encoding of the body token stream ----------

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


# ---------- archive serialization ----------

def _serialize(
    words: list[bytes],
    digrams: list[tuple[int, int]],
    body_tokens: list[int],
) -> bytes:
    out = bytearray()
    out.append(len(words))
    for w in words:
        if not 1 <= len(w) <= 255:
            raise ValueError(f"word length {len(w)} out of range")
        out.append(len(w))
        out.extend(w)
    out.extend(struct.pack(">H", len(digrams)))
    for a, b in digrams:
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


def _parse(
    inner: bytes,
) -> tuple[list[bytes], list[tuple[int, int]], list[int]]:
    pos = 0
    nw = inner[pos]
    pos += 1
    words: list[bytes] = []
    for _ in range(nw):
        L = inner[pos]
        pos += 1
        words.append(inner[pos : pos + L])
        pos += L
    (nd,) = struct.unpack(">H", inner[pos : pos + 2])
    pos += 2
    digrams: list[tuple[int, int]] = []
    for _ in range(nd):
        a_type = inner[pos]
        a_val = inner[pos + 1]
        pos += 2
        b_type = inner[pos]
        b_val = inner[pos + 1]
        pos += 2
        a_tok = _make_code(a_val) if a_type else a_val
        b_tok = _make_code(b_val) if b_type else b_val
        digrams.append((a_tok, b_tok))
    (blen,) = struct.unpack(">I", inner[pos : pos + 4])
    pos += 4
    body_bytes = inner[pos : pos + blen]
    body_tokens = _bytes_to_tokens(body_bytes)
    return words, digrams, body_tokens


def _expand(
    words: list[bytes],
    digrams: list[tuple[int, int]],
    body_tokens: list[int],
) -> bytes:
    expansions: list[bytes] = []
    for w in words:
        expansions.append(bytes(w))
    for a, b in digrams:
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
    words = _pick_words(data, K_WORDS)
    tokens = _substitute_words(data, words)
    digrams, body_tokens = _repair(tokens, len(words), K_DIGRAMS)
    inner = _serialize(words, digrams, body_tokens)
    return lzma.compress(inner, preset=PRESET)


def decompress(arch: bytes) -> bytes:
    inner = lzma.decompress(arch)
    words, digrams, body_tokens = _parse(inner)
    return _expand(words, digrams, body_tokens)
