#!/usr/bin/env python3
"""All 4 arms of BITS Experiment Card A2 with exact complete-bit accounting.

Arms (holding normalized JS, AST IR, AC32 entropy coder, tie order, and learning
budget strictly fixed):
  - Arm 1 (flat_bits): Flat literal dictionary + Viterbi DP parse + AC32 stream.
  - Arm 2 (context_ast): Context-coded AST with relative register IDs (max_depth=0).
  - Arm 3 (depth1_frames): Context-coded AST + learned depth-1 frames (max_depth=1).
  - Arm 4 (recursive_frames): Context-coded AST + learned recursive frames (max_depth=3).

All 4 arms serialize complete self-contained A2F1 binary archives decoded independently
by independent_decode.py + js_normalize_ast.mjs.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
import time
from typing import Any

from ast_frames import (
    AC32Sink,
    ArithmeticEncoder,
    BitCostSink,
    FrameDef,
    NUM_BASE_EXPR,
    NUM_BASE_STMT,
    Pools,
    TNode,
    all_base_context_specs,
    build_cum,
    build_pools,
    compute_costs_from_weights,
    emit_parsed_program,
    emit_uint,
    encode_varint,
    learn_frames_unified,
    parse_ast_optimal,
    quantize_weights,
    serialize_frame_definitions,
    serialize_table,
)

MAGIC = b"A2F1"

# ---------------------------------------------------------------------------
# Arm 1: Flat BITS (Dictionary Learner + Exact Minimum-Bit Viterbi DP + AC32)
# ---------------------------------------------------------------------------

FLAT_MAX_ENTRY_LEN = 16


@dataclass
class FlatBitsModel:
    entries: list[bytes]
    weights: list[int]
    header_bytes: bytes
    train_seconds: float
    op_counts: dict[str, int]


class FlatDictIndex:
    def __init__(self, entries: list[bytes]) -> None:
        self.entries = list(entries)
        self.n = len(entries)
        self.esc = self.n
        self.eof = self.n + 1
        self.single = [-1] * 256
        self.multi: dict[bytes, int] = {}
        self.prefix2: set[bytes] = set()
        lens: set[int] = set()
        for i, e in enumerate(entries):
            if len(e) == 1:
                self.single[e[0]] = i
            else:
                self.multi[e] = i
                self.prefix2.add(e[:2])
                lens.add(len(e))
        self.multi_lens = sorted(lens)

    def edges(self, raw: bytes) -> list[list[tuple[int, int]]]:
        n = len(raw)
        single = self.single
        multi = self.multi
        prefix2 = self.prefix2
        lens = self.multi_lens
        esc = self.esc
        out = []
        for i in range(n):
            s = single[raw[i]]
            here = [(1, s if s >= 0 else esc)]
            if i + 2 <= n and raw[i:i + 2] in prefix2:
                for l in lens:
                    if i + l > n:
                        break
                    sym = multi.get(raw[i:i + l])
                    if sym is not None:
                        here.append((l, sym))
            out.append(here)
        return out


def flat_parse_bits(edges: list[list[tuple[int, int]]], sym_costs: list[float], esc: int) -> tuple[list[int], float]:
    n = len(edges)
    inf = 1e18
    bits = [inf] * (n + 1)
    toks = [0] * (n + 1)
    prev: list[tuple[int, int] | None] = [None] * (n + 1)
    bits[0] = 0.0
    esc_cost = sym_costs[esc] + 8.0
    for i in range(n):
        b0 = bits[i]
        t1 = toks[i] + 1
        for l, sym in edges[i]:
            j = i + l
            c = b0 + (esc_cost if sym == esc else sym_costs[sym])
            if c + 1e-12 < bits[j] or (abs(c - bits[j]) <= 1e-12 and t1 < toks[j]):
                bits[j] = c
                toks[j] = t1
                prev[j] = (i, sym)
    out = []
    at = n
    while at > 0:
        step = prev[at]
        assert step is not None
        at, sym = step
        out.append(sym)
    out.reverse()
    return out, bits[n]


def train_flat_bits(
    train_files: list[bytes],
    train_lineages: list[str],
    max_entries: int = 512,
    min_lineage_support: int = 2,
) -> FlatBitsModel:
    """Learn a strong Flat BITS dictionary on training normalized JS bytes using BPE-style
    greedy merge rounds + exact Viterbi minimum-bit table refitting under AC32."""
    t0 = time.perf_counter()
    ops = {"bpe_merges": 0, "dp_bytes": 0}

    # Seed with all observed single bytes in training
    single_bytes = sorted({b for raw in train_files for b in raw})
    entries: list[bytes] = [bytes([b]) for b in single_bytes]
    entry_set: set[bytes] = set(entries)

    # Represent each training file as token IDs and iteratively merge highest-gain pairs
    # (respecting MAX_ENTRY_LEN=16 and min_lineage_support >= 2, deterministic tie order!)
    b2id = {bytes([b]): i for i, b in enumerate(single_bytes)}
    seqs = [[b2id[bytes([b])] for b in raw] for raw in train_files]
    id2bytes = list(entries)

    while len(entries) < max_entries:
        pair_counts: Counter[tuple[int, int]] = Counter()
        pair_lineages: dict[tuple[int, int], set[str]] = {}
        for seq, lin in zip(seqs, train_lineages):
            seen_p: set[tuple[int, int]] = set()
            for a, b in zip(seq, seq[1:]):
                if len(id2bytes[a]) + len(id2bytes[b]) > FLAT_MAX_ENTRY_LEN:
                    continue
                p = (a, b)
                pair_counts[p] += 1
                if p not in seen_p:
                    seen_p.add(p)
                    pair_lineages.setdefault(p, set()).add(lin)
        best_pair = None
        best_key = None
        for p, cnt in pair_counts.items():
            if cnt < 4 or len(pair_lineages[p]) < min_lineage_support:
                continue
            cand = id2bytes[p[0]] + id2bytes[p[1]]
            if cand in entry_set:
                continue
            # Estimate net complete-bit gain: cnt * ~6 bits saved - (1 + len(cand) + 1)*8 header bits
            gain = cnt * 5.5 - (len(cand) + 2) * 8.0
            if gain <= 0:
                continue
            key = (-round(gain, 6), cand)
            if best_key is None or key < best_key:
                best_key = key
                best_pair = p
        if best_pair is None:
            break
        new_bytes = id2bytes[best_pair[0]] + id2bytes[best_pair[1]]
        new_id = len(id2bytes)
        id2bytes.append(new_bytes)
        entries.append(new_bytes)
        entry_set.add(new_bytes)
        ops["bpe_merges"] += 1
        a_id, b_id = best_pair
        for si in range(len(seqs)):
            s = seqs[si]
            ns = []
            i = 0
            ls = len(s)
            while i < ls:
                if i + 1 < ls and s[i] == a_id and s[i + 1] == b_id:
                    ns.append(new_id)
                    i += 2
                else:
                    ns.append(s[i])
                    i += 1
            seqs[si] = ns

    # Fit exact AC32 probability table via 4 passes of exact minimum-bit Viterbi DP
    didx = FlatDictIndex(entries)
    n = didx.n
    esc = didx.esc
    eof = didx.eof
    train_edges = [didx.edges(raw) for raw in train_files]

    counts = [0] * (n + 2)
    for seq in seqs:
        for sym in seq:
            counts[sym] += 1
    counts[eof] = len(train_files)
    weights = quantize_weights(counts)

    for _ in range(4):
        tot = float(sum(weights))
        sym_costs = [math.log2(tot / float(w)) for w in weights]
        c2 = [0] * (n + 2)
        for edges in train_edges:
            ops["dp_bytes"] += len(edges)
            syms, _ = flat_parse_bits(edges, sym_costs, esc)
            for s in syms:
                c2[s] += 1
        c2[eof] = len(train_files)
        w2 = quantize_weights(c2)
        weights = w2

    # Build frozen A2F1 CodecKind=0 header
    hdr = bytearray(MAGIC)
    hdr.append(0)  # CodecKind = 0 (Flat BITS)
    hdr.append(0)  # MaxDepth = 0
    hdr += encode_varint(len(entries))
    for e in entries:
        hdr.append(len(e))
        hdr += e
    hdr += serialize_table(weights)

    return FlatBitsModel(
        entries=entries,
        weights=weights,
        header_bytes=bytes(hdr),
        train_seconds=time.perf_counter() - t0,
        op_counts=ops,
    )


def encode_flat_bits(model: FlatBitsModel, files: list[bytes]) -> dict[str, Any]:
    t0 = time.perf_counter()
    didx = FlatDictIndex(model.entries)
    cum = build_cum(model.weights)
    tot = float(sum(model.weights))
    sym_costs = [math.log2(tot / float(w)) for w in model.weights]
    esc = didx.esc
    eof = didx.eof

    enc = ArithmeticEncoder()
    per_file_bits: list[float] = []
    total_tokens = 0
    total_escapes = 0
    dp_bytes = 0

    for raw in files:
        edges = didx.edges(raw)
        dp_bytes += len(edges)
        syms, est_bits = flat_parse_bits(edges, sym_costs, esc)
        pos = 0
        for s in syms:
            enc.encode(cum, s)
            total_tokens += 1
            if s == esc:
                enc.encode_uniform(raw[pos], 256)
                total_escapes += 1
                pos += 1
            else:
                pos += len(model.entries[s])
        assert pos == len(raw)
        enc.encode(cum, eof)
        per_file_bits.append(est_bits + sym_costs[eof])

    payload = enc.finish()
    archive = model.header_bytes + encode_varint(len(files)) + payload
    return {
        "arm": "arm1_flat_bits",
        "archive": archive,
        "header_bytes": len(model.header_bytes),
        "count_varint_bytes": len(encode_varint(len(files))),
        "payload_bytes": len(payload),
        "complete_bytes": len(archive),
        "complete_bits": len(archive) * 8,
        "header_bits": len(model.header_bytes) * 8,
        "payload_bits": len(payload) * 8,
        "per_file_est_bits": per_file_bits,
        "tokens": total_tokens,
        "escapes": total_escapes,
        "encode_seconds": time.perf_counter() - t0,
        "op_counts": {"dp_bytes": dp_bytes, "ac_symbols": enc.sym_count},
        "frame_stats": {
            "total_frames": 0,
            "nested_frame_defs": 0,
            "frame_uses": 0,
            "recursive_frame_uses": 0,
            "nested_subframe_calls": 0,
            "switch_bits": 0.0,
            "frame_id_bits": 0.0,
            "shift_bits": 0.0,
            "frame_def_header_bytes": 0,
            "fallback_files": 0,
        },
    }


# ---------------------------------------------------------------------------
# Arms 2, 3, 4: Context-Coded AST (max_depth=0, 1, 3)
# ---------------------------------------------------------------------------

@dataclass
class AstCodecModel:
    arm_name: str
    max_depth: int
    pools: Pools
    weights: dict[str, list[int]]
    frames: list[FrameDef]
    header_bytes: bytes
    header_breakdown: dict[str, int]
    train_seconds: float
    op_counts: dict[str, int]


def build_ast_header(
    max_depth: int,
    pools: Pools,
    weights: dict[str, list[int]],
    frames: list[FrameDef],
) -> tuple[bytes, dict[str, int]]:
    has_frames = max_depth >= 1
    hdr = bytearray(MAGIC)
    hdr.append(1)          # CodecKind = 1 (Context-Coded AST + Optional Frames)
    hdr.append(max_depth)  # MaxDepth: 0 (Arm 2), 1 (Arm 3), 3 (Arm 4)
    env_end = len(hdr)

    pool_bytes = pools.serialize()
    hdr += pool_bytes
    pools_end = len(hdr)

    base_specs = all_base_context_specs(pools, has_frames=has_frames)
    cums: dict[str, list[int]] = {}
    for ctx, sz in base_specs:
        w = weights[ctx]
        assert len(w) == sz, f"table {ctx} len {len(w)} != {sz}"
        hdr += serialize_table(w)
        cums[ctx] = build_cum(w)
    base_tables_end = len(hdr)

    frame_tables_bytes = 0
    frame_def_bytes = 0
    if has_frames:
        f_e = sum(1 for f in frames if f.group == "EXPR")
        f_s = sum(1 for f in frames if f.group == "STMT")
        ft_start = len(hdr)
        hdr += encode_varint(f_e)
        hdr += encode_varint(f_s)
        if f_e > 0:
            hdr += serialize_table(weights["EXPR_FRAME_ID"])
        if f_s > 0:
            hdr += serialize_table(weights["STMT_FRAME_ID"])
        hdr += serialize_table(weights["REG_SHIFT"])
        def_mode_w = weights["DEF_MODE"]
        hdr += serialize_table(def_mode_w)
        frame_tables_bytes = len(hdr) - ft_start

        fd_start = len(hdr)
        def_blob = serialize_frame_definitions(frames, pools, cums, def_mode_w, max_depth)
        hdr += encode_varint(len(def_blob))
        hdr += def_blob
        frame_def_bytes = len(hdr) - fd_start

    breakdown = {
        "envelope_bytes": env_end,
        "pools_bytes": pools_end - env_end,
        "base_tables_bytes": base_tables_end - pools_end,
        "frame_tables_bytes": frame_tables_bytes,
        "frame_def_header_bytes": frame_def_bytes,
        "total_header_bytes": len(hdr),
    }
    return bytes(hdr), breakdown


def train_ast_arm(
    arm_name: str,
    train_irs: list[list[TNode] | None],
    train_lineages: list[str],
    train_raw_bytes: list[bytes],
    pools: Pools,
    max_depth: int,
    max_frames: int = 160,
    min_lineage_support: int = 2,
) -> AstCodecModel:
    t0 = time.perf_counter()
    ops: dict[str, int] = {"shift_evaluations": 0, "dp_nodes_visited": 0}
    frames, weights = learn_frames_unified(
        train_irs=train_irs,
        train_lineages=train_lineages,
        train_raw_bytes=train_raw_bytes,
        pools=pools,
        max_depth=max_depth,
        max_frames=max_frames,
        min_lineage_support=min_lineage_support,
        op_counter=ops,
    )
    hdr, breakdown = build_ast_header(max_depth, pools, weights, frames)
    return AstCodecModel(
        arm_name=arm_name,
        max_depth=max_depth,
        pools=pools,
        weights=weights,
        frames=frames,
        header_bytes=hdr,
        header_breakdown=breakdown,
        train_seconds=time.perf_counter() - t0,
        op_counts=ops,
    )


def encode_ast_arm(
    model: AstCodecModel,
    irs: list[list[TNode] | None],
    raw_bytes_list: list[bytes],
) -> dict[str, Any]:
    t0 = time.perf_counter()
    has_frames = model.max_depth >= 1
    cums = {ctx: build_cum(ws) for ctx, ws in model.weights.items()}
    costs = compute_costs_from_weights(model.weights)

    frames_by_root: dict[tuple[str, str], list[FrameDef]] = {}
    for f in model.frames:
        frames_by_root.setdefault((f.group, f.root_tag), []).append(f)

    enc = ArithmeticEncoder()
    ac_sink = AC32Sink(enc, cums)
    per_file_bits: list[float] = []
    ops: dict[str, int] = {"shift_evaluations": 0, "dp_nodes_visited": 0}
    frame_uses_stats: dict[str, int] = {
        "frame_uses": 0,
        "recursive_frame_uses": 0,
        "nested_subframe_calls": 0,
    }
    total_switch_bits = 0.0
    total_frame_id_bits = 0.0
    total_shift_bits = 0.0
    fallback_files = 0

    for ir, raw in zip(irs, raw_bytes_list):
        cost_sink = BitCostSink(costs)
        if ir is None:
            fallback_files += 1
            for s in (ac_sink, cost_sink):
                s.put("FILE_MODE", 1)
                emit_uint(s, len(raw))
                for b in raw:
                    s.put("INLINE_BYTE", b)
        else:
            choices, _ = parse_ast_optimal(ir, model.pools, costs, frames_by_root, has_frames and bool(model.frames), ops)
            ac_sink.put("FILE_MODE", 0)
            cost_sink.put("FILE_MODE", 0)
            emit_parsed_program(ac_sink, model.pools, ir, choices, stats=frame_uses_stats)
            emit_parsed_program(cost_sink, model.pools, ir, choices, stats=None)
        per_file_bits.append(cost_sink.bits)
        total_switch_bits += cost_sink.switch_bits
        total_frame_id_bits += cost_sink.frame_id_bits
        total_shift_bits += cost_sink.shift_bits

    payload = enc.finish()
    archive = model.header_bytes + encode_varint(len(irs)) + payload
    ops["ac_symbols"] = enc.sym_count
    nested_defs = sum(1 for f in model.frames if f.def_depth >= 2)
    depth_hist = Counter(f.def_depth for f in model.frames)

    return {
        "arm": model.arm_name,
        "max_depth": model.max_depth,
        "archive": archive,
        "header_bytes": len(model.header_bytes),
        "header_breakdown": model.header_breakdown,
        "count_varint_bytes": len(encode_varint(len(irs))),
        "payload_bytes": len(payload),
        "complete_bytes": len(archive),
        "complete_bits": len(archive) * 8,
        "header_bits": len(model.header_bytes) * 8,
        "payload_bits": len(payload) * 8,
        "per_file_est_bits": per_file_bits,
        "encode_seconds": time.perf_counter() - t0,
        "op_counts": ops,
        "frame_stats": {
            "total_frames": len(model.frames),
            "expr_frames": sum(1 for f in model.frames if f.group == "EXPR"),
            "stmt_frames": sum(1 for f in model.frames if f.group == "STMT"),
            "nested_frame_defs": nested_defs,
            "depth_histogram": {str(k): v for k, v in sorted(depth_hist.items())},
            "frame_uses": frame_uses_stats["frame_uses"],
            "recursive_frame_uses": frame_uses_stats["recursive_frame_uses"],
            "nested_subframe_calls": frame_uses_stats["nested_subframe_calls"],
            "switch_bits": round(total_switch_bits, 3),
            "frame_id_bits": round(total_frame_id_bits, 3),
            "shift_bits": round(total_shift_bits, 3),
            "frame_def_header_bytes": model.header_breakdown["frame_def_header_bytes"],
            "frame_tables_header_bytes": model.header_breakdown["frame_tables_bytes"],
            "fallback_files": fallback_files,
        },
    }
