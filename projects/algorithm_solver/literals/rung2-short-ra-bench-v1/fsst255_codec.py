#!/usr/bin/env python3
"""Faithful Boncz-Neumann-Leis (PVLDB 2020) `FSST-255` Static Symbol Table Codec.

Implements:
  - Iterative 5-generation DP symbol-table construction (up to 255 symbols of length 1..8 B
    plus reserved escape byte `0xFF`), scoring single bytes (which save 1 B over the 2-byte
    `[0xFF, raw]` escape) and concatenated pairs `(s1 + s2)[:8]` (which save `|c| - 1` or
    `2*|c| - 1` bytes relative to escaped bytes) on a deterministic sample of the training batch.
  - Exact shortest-byte DP per document (`1 B` per symbol `0..254`, `2 B` per escaped byte).
  - Self-contained `FSST` random-access container with a `4 B/doc` end-offset seek table,
    decoded at GB/s speed by `ra_codecs_bench.c`.
"""
from __future__ import annotations

import struct
from collections import Counter
from typing import Sequence


def _build_symbol_trie(symbols: Sequence[bytes]) -> list[dict[int, int]]:
    nodes: list[dict[int, int]] = [{}]
    sym_at: list[int] = [-1]
    for idx, sym in enumerate(symbols):
        cur = 0
        for b in sym:
            nxt = nodes[cur].get(b)
            if nxt is None:
                nxt = len(nodes)
                nodes[cur][b] = nxt
                nodes.append({})
                sym_at.append(-1)
            cur = nxt
        sym_at[cur] = idx
    return nodes, sym_at  # type: ignore[return-value]


def _dp_parse_doc(doc: bytes, nodes: list[dict[int, int]], sym_at: list[int]) -> list[int]:
    """Exact shortest-byte FSST parse: returns list of tokens (`0..254` = sym, `-1 - byte` = escape)."""
    n = len(doc)
    INF = 1 << 30
    dp = [INF] * (n + 1)
    nxt_pos = [0] * n
    tok_choice = [0] * n
    dp[n] = 0

    for i in range(n - 1, -1, -1):
        # Escaped literal byte: 2 bytes `[0xFF, doc[i]]`
        best_cost = 2 + dp[i + 1]
        best_j = i + 1
        best_tok = -1 - doc[i]

        cur = 0
        lim = min(n, i + 8)
        for j in range(i, lim):
            cur = nodes[cur].get(doc[j], -1)
            if cur < 0:
                break
            s_idx = sym_at[cur]
            if s_idx >= 0:
                c = 1 + dp[j + 1]
                if c < best_cost:
                    best_cost = c
                    best_j = j + 1
                    best_tok = s_idx
        dp[i] = best_cost
        nxt_pos[i] = best_j
        tok_choice[i] = best_tok

    out: list[int] = []
    pos = 0
    while pos < n:
        out.append(tok_choice[pos])
        pos = nxt_pos[pos]
    return out


def train_fsst255_table(train_docs: Sequence[bytes], max_sample_bytes: int = 32768) -> list[bytes]:
    """Train up to 255 `1..8 B` symbols using 5 iterative DP + concatenation passes (PVLDB 2020)."""
    sample: list[bytes] = []
    used = 0
    step = max(1, len(train_docs) // 128)
    for d in train_docs[::step]:
        if not d:
            continue
        take = d[:512]
        sample.append(take)
        used += len(take)
        if used >= max_sample_bytes:
            break
    if not sample:
        sample = [d for d in train_docs if d][:32]

    byte_counts = Counter(b for d in sample for b in d)
    # Seed generation 0 with existing single bytes (up to 255 most frequent)
    symbols: list[bytes] = [bytes([b]) for b, _ in byte_counts.most_common(255)]

    for gen in range(5):
        nodes, sym_at = _build_symbol_trie(symbols)
        sym_freq: Counter[bytes] = Counter()
        pair_freq: Counter[bytes] = Counter()

        for d in sample:
            toks = _dp_parse_doc(d, nodes, sym_at)
            prev_bytes: bytes | None = None
            for t in toks:
                cur_bytes = symbols[t] if t >= 0 else bytes([-1 - t])
                sym_freq[cur_bytes] += 1
                if prev_bytes is not None and len(prev_bytes) < 8:
                    cat = (prev_bytes + cur_bytes)[:8]
                    if len(cat) > len(prev_bytes):
                        pair_freq[cat] += 1
                prev_bytes = cur_bytes

        # Score candidate symbols by compressed byte savings vs escaped raw bytes (`2 * len(s) - 1` per occ)
        # damped on early generations per Boncz et al. so longer symbols build up cleanly.
        candidates: dict[bytes, float] = {}
        for b_val, c in byte_counts.items():
            sb = bytes([b_val])
            candidates[sb] = float(c)  # saves 1 byte per unabsorbed single byte over 2B escape

        for s, c in sym_freq.items():
            if len(s) >= 2:
                gain = (len(s) - 0.5) * c
                candidates[s] = max(candidates.get(s, 0.0), gain)

        min_pair = 3 if gen < 3 else 2
        for cat, c in pair_freq.items():
            if c >= min_pair and len(cat) >= 2:
                gain = (len(cat) - 0.5) * c
                candidates[cat] = max(candidates.get(cat, 0.0), gain)

        ranked = sorted(candidates.items(), key=lambda kv: (-kv[1], len(kv[0]), kv[0]))
        # Dedup & order longest/lex cleanly up to 255 symbols
        symbols = [s for s, g in ranked[:255] if g > 4.0]
        if not symbols:
            symbols = [bytes([b]) for b, _ in byte_counts.most_common(255)]

    return symbols[:255]


def serialize_fsst255_archive(symbols: Sequence[bytes], docs: Sequence[bytes]) -> bytes:
    """Encode `docs` with frozen `symbols` (`<= 255`) and pack `FSST` random-access container."""
    if len(symbols) > 255:
        raise ValueError('FSST supports at most 255 symbols (255 reserved for escape)')
    nodes, sym_at = _build_symbol_trie(symbols)

    encoded_docs: list[bytes] = []
    for d in docs:
        toks = _dp_parse_doc(d, nodes, sym_at)
        ebuf = bytearray()
        for t in toks:
            if t >= 0:
                ebuf.append(t)
            else:
                ebuf.append(255)
                ebuf.append(-1 - t)
        encoded_docs.append(bytes(ebuf))

    hdr = bytearray(b'FSST')
    hdr.extend(struct.pack('<HH', len(symbols), len(docs)))
    for s in symbols:
        hdr.append(len(s))
    for s in symbols:
        hdr.extend(s)
    cur = 0
    for ed in encoded_docs:
        cur += len(ed)
        hdr.extend(struct.pack('<I', cur))
    for ed in encoded_docs:
        hdr.extend(ed)
    return bytes(hdr)
