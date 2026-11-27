#!/usr/bin/env python3
"""Dual header serializer (A1AF flat-literal and A1AD construction-DAG) for A1a.

Serializes one fixed emitted vocabulary, token stream, and canonical Huffman code table
in both formats, counting every byte the recipient needs (`complete_bits`).
"""
from __future__ import annotations

import heapq
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

MAGIC_FLAT = b"A1AF"
MAGIC_DAG = b"A1AD"
MAX_ENTRY_LEN = 16
MAX_TABLE_PASSES = 15

FLAG_MODE_PAIR = 0x00
FLAG_MODE_HYBRID = 0x01
FLAG_HAS_EMIT_MASK = 0x04
FLAG_HAS_MERGE_RANKS = 0x08


def varint(n: int) -> bytes:
    if n < 0:
        raise ValueError("varint requires non-negative integer")
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def read_varint(buf: bytes, pos: int) -> Tuple[int, int]:
    shift = 0
    value = 0
    start = pos
    while True:
        if pos >= len(buf):
            raise ValueError("varint truncated")
        b = buf[pos]
        pos += 1
        value |= (b & 0x7F) << shift
        if not (b & 0x80):
            if pos - start > 1 and b == 0:
                raise ValueError("non-canonical varint")
            return value, pos
        shift += 7


class BitWriter:
    def __init__(self) -> None:
        self.out = bytearray()
        self.acc = 0
        self.nbits = 0

    def put(self, value: int, nbits: int) -> None:
        if nbits == 0:
            return
        if value < 0 or value >= (1 << nbits):
            raise ValueError(f"value {value} does not fit in {nbits} bits")
        self.acc = (self.acc << nbits) | value
        self.nbits += nbits
        while self.nbits >= 8:
            self.nbits -= 8
            self.out.append((self.acc >> self.nbits) & 0xFF)
        self.acc &= (1 << self.nbits) - 1

    def finish(self) -> bytes:
        if self.nbits:
            self.out.append((self.acc << (8 - self.nbits)) & 0xFF)
            self.acc = 0
            self.nbits = 0
        return bytes(self.out)

    @property
    def bit_length(self) -> int:
        return len(self.out) * 8 + self.nbits


def huffman_lengths(counts: Sequence[int]) -> List[int]:
    """Deterministic optimal prefix code lengths (ties by creation order)."""
    n = len(counts)
    if n < 2:
        raise ValueError("need at least 2 symbols")
    if any(c < 1 for c in counts):
        raise ValueError("all counts must be >= 1")
    heap = [(c, i) for i, c in enumerate(counts)]
    heapq.heapify(heap)
    parent = [-1] * (2 * n - 1)
    nxt = n
    while len(heap) > 1:
        c1, a = heapq.heappop(heap)
        c2, b = heapq.heappop(heap)
        parent[a] = nxt
        parent[b] = nxt
        heapq.heappush(heap, (c1 + c2, nxt))
        nxt += 1
    depth = [0] * (2 * n - 1)
    for node in range(2 * n - 3, -1, -1):
        depth[node] = depth[parent[node]] + 1
    lengths = depth[:n]
    top = max(lengths)
    if sum(1 << (top - l) for l in lengths) != (1 << top):
        raise AssertionError("Kraft sum != 1")
    if top > 255:
        raise ValueError("Huffman code length exceeds 255")
    return lengths


def canonical_codes(lengths: Sequence[int]) -> List[int]:
    order = sorted(range(len(lengths)), key=lambda s: (lengths[s], s))
    codes = [0] * len(lengths)
    code = 0
    prev = lengths[order[0]]
    for s in order:
        code <<= lengths[s] - prev
        prev = lengths[s]
        codes[s] = code
        code += 1
    return codes


class Dictionary:
    """Emitted dictionary with exact DP token/bit parsers (matching bits_oh.py)."""

    def __init__(self, entries: Sequence[bytes]) -> None:
        if len(set(entries)) != len(entries):
            raise ValueError("duplicate entry")
        if not entries:
            raise ValueError("empty dictionary")
        self.entries = list(entries)
        self.n = len(entries)
        self.ESC = self.n
        self.EOF = self.n + 1
        self.single = [-1] * 256
        self.multi: Dict[bytes, int] = {}
        self.prefix2 = set()
        lens = set()
        for i, e in enumerate(entries):
            if not (1 <= len(e) <= MAX_ENTRY_LEN):
                raise ValueError(f"entry length {len(e)} out of range 1..{MAX_ENTRY_LEN}")
            if len(e) == 1:
                self.single[e[0]] = i
            else:
                self.multi[e] = i
                self.prefix2.add(e[:2])
                lens.add(len(e))
        self.multi_lens = sorted(lens)

    def edges(self, raw: bytes) -> List[List[Tuple[int, int]]]:
        n = len(raw)
        single = self.single
        multi = self.multi
        prefix2 = self.prefix2
        lens = self.multi_lens
        esc = self.ESC
        out: List[List[Tuple[int, int]]] = []
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


def parse_tokens(edges: Sequence[Sequence[Tuple[int, int]]]) -> List[int]:
    n = len(edges)
    big = n + 1
    best = [big] * (n + 1)
    prev: List[Optional[Tuple[int, int]]] = [None] * (n + 1)
    best[0] = 0
    for i in range(n):
        c = best[i] + 1
        for l, sym in edges[i]:
            j = i + l
            if c < best[j]:
                best[j] = c
                prev[j] = (i, sym)
    out = []
    at = n
    while at > 0:
        at, sym = prev[at]  # type: ignore[misc]
        out.append(sym)
    out.reverse()
    return out


def parse_bits(
    edges: Sequence[Sequence[Tuple[int, int]]],
    lengths: Sequence[int],
    esc: int,
    banned: int = -1,
) -> Tuple[List[int], int]:
    n = len(edges)
    inf = 1 << 60
    bits = [inf] * (n + 1)
    toks = [0] * (n + 1)
    prev: List[Optional[Tuple[int, int]]] = [None] * (n + 1)
    bits[0] = 0
    esc_cost = lengths[esc] + 8
    for i in range(n):
        b0 = bits[i]
        t1 = toks[i] + 1
        for l, sym in edges[i]:
            if sym == banned:
                continue
            j = i + l
            c = b0 + (esc_cost if sym == esc else lengths[sym])
            if c < bits[j] or (c == bits[j] and t1 < toks[j]):
                bits[j] = c
                toks[j] = t1
                prev[j] = (i, sym)
    out = []
    at = n
    while at > 0:
        at, sym = prev[at]  # type: ignore[misc]
        out.append(sym)
    out.reverse()
    return out, bits[n]


def fit_table(
    dictionary: Dictionary,
    files_edges: Sequence[Sequence[Sequence[Tuple[int, int]]]],
) -> Tuple[List[int], List[int], int, int]:
    n = dictionary.n
    esc = dictionary.ESC
    eof = dictionary.EOF

    def lengths_of(counts: Sequence[int]) -> List[int]:
        return huffman_lengths([c if c > 0 else 1 for c in counts])

    def cost(counts: Sequence[int], lengths: Sequence[int]) -> int:
        return sum(c * l for c, l in zip(counts, lengths)) + 8 * counts[esc]

    counts = [0] * (n + 2)
    for edges in files_edges:
        for sym in parse_tokens(edges):
            counts[sym] += 1
    counts[eof] = max(1, len(files_edges))
    lengths = lengths_of(counts)
    bits = cost(counts, lengths)
    passes = 0
    for step in range(1, MAX_TABLE_PASSES + 1):
        c2 = [0] * (n + 2)
        for edges in files_edges:
            syms, _ = parse_bits(edges, lengths, esc)
            for sym in syms:
                c2[sym] += 1
        c2[eof] = max(1, len(files_edges))
        l2 = lengths_of(c2)
        b2 = cost(c2, l2)
        if b2 < bits:
            counts, lengths, bits, passes = c2, l2, b2, step
        else:
            break
    return lengths, counts, bits, passes


@dataclass
class DAGSpec:
    """Ordered storage DAG with optional emit mask and optional merge ranks."""

    leaves: List[bytes]  # strictly sorted 1-byte entries (nodes 0..A-1)
    nodes: List[bytes]  # all M entries in topological order (first A == leaves)
    defs: List[Tuple[str, object]]  # for i in A..M-1: ('pair',(l,r))|('literal',b)|('list',[ids])
    mode: int  # FLAG_MODE_PAIR (0) or FLAG_MODE_HYBRID (1)
    emit_mask: Optional[List[bool]] = None  # length M if present; None means all emitted
    merge_ranks: Optional[List[int]] = None  # length M-A if present

    @property
    def emitted_entries(self) -> List[bytes]:
        if self.emit_mask is None:
            return list(self.nodes)
        return [e for e, keep in zip(self.nodes, self.emit_mask) if keep]


def _min_spelling_ids(word: bytes, id_map: Dict[bytes, int]) -> Optional[List[int]]:
    n = len(word)
    big = n + 1
    best = [big] * (n + 1)
    back: List[Optional[Tuple[int, int]]] = [None] * (n + 1)
    best[0] = 0
    for i in range(n):
        if best[i] >= big:
            continue
        for j in range(i + 1, n + 1):
            nid = id_map.get(word[i:j])
            if nid is not None and best[i] + 1 < best[j]:
                best[j] = best[i] + 1
                back[j] = (i, nid)
    if best[n] >= big:
        return None
    out = []
    at = n
    while at > 0:
        at, nid = back[at]  # type: ignore[misc]
        out.append(nid)
    out.reverse()
    return out


def build_dag_spec(
    entries: Sequence[bytes],
    emit_mask: Optional[Sequence[bool]] = None,
    merge_ranks: Optional[Sequence[int]] = None,
    explicit_pairs: Optional[Dict[bytes, Tuple[bytes, bytes]]] = None,
    force_hybrid: bool = False,
) -> DAGSpec:
    """Build an optimal A1AD DAGSpec for an ordered entry list.

    Leaves (all 1-byte entries) are placed first in strictly ascending byte order,
    followed by multi-byte entries in their supplied topological order.
    If every multi-byte entry is a binary pair of earlier entries (and force_hybrid=False),
    uses pure-pair mode (mode=0); otherwise uses hybrid mode (mode=1) choosing the cheapest
    bit representation (pair, list, or literal) per non-leaf node.
    """
    entries_list = list(entries)
    if len(set(entries_list)) != len(entries_list):
        raise ValueError("duplicate entries in DAG")
    orig_index = {e: idx for idx, e in enumerate(entries_list)}
    leaves = sorted(e for e in entries_list if len(e) == 1)
    multis = [e for e in entries_list if len(e) > 1]
    nodes = leaves + multis
    if emit_mask is not None:
        if len(emit_mask) != len(entries_list):
            raise ValueError("emit_mask length mismatch")
        # Remap emit_mask to reordered leaves + multis order
        reordered_mask = [bool(emit_mask[orig_index[e]]) for e in nodes]
        if all(reordered_mask):
            reordered_mask = None
    else:
        reordered_mask = None

    id_map: Dict[bytes, int] = {b: i for i, b in enumerate(leaves)}
    defs_pair_check: List[Optional[Tuple[int, int]]] = []
    all_pairs = not force_hybrid

    for idx, word in enumerate(multis):
        node_i = len(leaves) + idx
        if not (2 <= len(word) <= MAX_ENTRY_LEN):
            raise ValueError(f"multi-byte entry length {len(word)} out of range")
        pair: Optional[Tuple[int, int]] = None
        if explicit_pairs and word in explicit_pairs:
            la, ra = explicit_pairs[word]
            if la in id_map and ra in id_map:
                pair = (id_map[la], id_map[ra])
        if pair is None:
            for split in range(1, len(word)):
                left_id = id_map.get(word[:split])
                if left_id is not None:
                    right_id = id_map.get(word[split:])
                    if right_id is not None:
                        pair = (left_id, right_id)
                        break
        defs_pair_check.append(pair)
        if pair is None:
            all_pairs = False
        id_map[word] = node_i

    if all_pairs:
        defs = [("pair", p) for p in defs_pair_check]
        return DAGSpec(
            leaves=leaves,
            nodes=nodes,
            defs=defs,
            mode=FLAG_MODE_PAIR,
            emit_mask=reordered_mask,
            merge_ranks=list(merge_ranks) if merge_ranks is not None else None,
        )

    # Hybrid mode: choose cheapest of pair / list / literal per multi-byte node.
    id_map = {b: i for i, b in enumerate(leaves)}
    defs = []
    for idx, word in enumerate(multis):
        node_i = len(leaves) + idx
        w_i = max(1, (node_i - 1).bit_length())
        lit_bits = 4 + 8 * len(word)
        best_kind = "literal"
        best_val: object = word
        best_bits = lit_bits

        pair = defs_pair_check[idx]
        if pair is not None:
            pair_bits = 2 * w_i
            if pair_bits < best_bits:
                best_kind, best_val, best_bits = "pair", pair, pair_bits

        sp = _min_spelling_ids(word, id_map)
        if sp is not None and 2 <= len(sp) <= MAX_ENTRY_LEN:
            if len(sp) == 2:
                pair_bits = 2 * w_i
                if pair_bits < best_bits:
                    best_kind, best_val, best_bits = "pair", (sp[0], sp[1]), pair_bits
            else:
                list_bits = 4 + len(sp) * w_i
                if list_bits < best_bits:
                    best_kind, best_val, best_bits = "list", sp, list_bits

        defs.append((best_kind, best_val))
        id_map[word] = node_i

    return DAGSpec(
        leaves=leaves,
        nodes=nodes,
        defs=defs,
        mode=FLAG_MODE_HYBRID,
        emit_mask=reordered_mask,
        merge_ranks=list(merge_ranks) if merge_ranks is not None else None,
    )


def build_flat_header(entries: Sequence[bytes], lengths: Sequence[int]) -> bytes:
    if len(lengths) != len(entries) + 2:
        raise ValueError("lengths must have len(entries) + 2 elements")
    if len(set(entries)) != len(entries):
        raise ValueError("duplicate entries")
    out = bytearray(MAGIC_FLAT)
    out += varint(len(entries))
    for e in entries:
        if not (1 <= len(e) <= MAX_ENTRY_LEN):
            raise ValueError("entry length out of range")
        out.append(len(e))
        out += e
    if min(lengths) < 1 or max(lengths) > 255:
        raise ValueError("code length out of range")
    out += bytes(lengths)
    return bytes(out)


def build_dag_header(dag: DAGSpec, lengths: Sequence[int]) -> bytes:
    emitted = dag.emitted_entries
    if len(lengths) != len(emitted) + 2:
        raise ValueError(f"lengths has {len(lengths)} entries, expected {len(emitted) + 2}")
    if min(lengths) < 1 or max(lengths) > 255:
        raise ValueError("code length out of range")

    M = len(dag.nodes)
    A = len(dag.leaves)
    R = M - A
    flags = dag.mode & 0x03
    has_emit = dag.emit_mask is not None
    has_ranks = dag.merge_ranks is not None and R > 0
    if has_emit:
        flags |= FLAG_HAS_EMIT_MASK
    if has_ranks:
        flags |= FLAG_HAS_MERGE_RANKS

    out = bytearray(MAGIC_DAG)
    out.append(flags)
    out += varint(M)
    out += varint(A)
    for b in dag.leaves:
        if len(b) != 1:
            raise ValueError("leaf must be 1 byte")
        out.append(b[0])

    bw = BitWriter()
    for idx, (kind, val) in enumerate(dag.defs):
        node_i = A + idx
        w_i = max(1, (node_i - 1).bit_length())
        if dag.mode == FLAG_MODE_PAIR:
            if kind != "pair":
                raise ValueError("pure-pair mode requires pair definitions")
            left, right = val  # type: ignore[misc]
            bw.put(left, w_i)
            bw.put(right, w_i)
        else:
            if kind == "pair":
                left, right = val  # type: ignore[misc]
                bw.put(0, 2)
                bw.put(left, w_i)
                bw.put(right, w_i)
            elif kind == "literal":
                word = val  # type: ignore[assignment]
                bw.put(1, 2)
                bw.put(len(word) - 1, 4)
                for byte_val in word:
                    bw.put(byte_val, 8)
            elif kind == "list":
                ids = val  # type: ignore[assignment]
                bw.put(2, 2)
                bw.put(len(ids) - 2, 4)
                for nid in ids:
                    bw.put(nid, w_i)
            else:
                raise ValueError(f"unknown DAG node kind {kind}")
    out += bw.finish()

    if has_ranks:
        assert dag.merge_ranks is not None
        if len(dag.merge_ranks) != R:
            raise ValueError("merge_ranks length mismatch")
        rw = max(1, (R - 1).bit_length())
        rbw = BitWriter()
        for r in dag.merge_ranks:
            rbw.put(r, rw)
        out += rbw.finish()

    if has_emit:
        assert dag.emit_mask is not None
        mask_bytes = bytearray((M + 7) // 8)
        for i, keep in enumerate(dag.emit_mask):
            if keep:
                mask_bytes[i >> 3] |= 1 << (i & 7)
        out += mask_bytes

    out += bytes(lengths)
    return bytes(out)


def encode_payload(
    dictionary: Dictionary,
    lengths: Sequence[int],
    files: Sequence[bytes],
    parses: Sequence[Sequence[int]],
) -> Tuple[bytes, List[int]]:
    codes = canonical_codes(lengths)
    esc = dictionary.ESC
    eof = dictionary.EOF
    entries = dictionary.entries
    writer = BitWriter()
    per_file: List[int] = []
    for raw, syms in zip(files, parses):
        pos = 0
        nb = 0
        for sym in syms:
            writer.put(codes[sym], lengths[sym])
            nb += lengths[sym]
            if sym == esc:
                writer.put(raw[pos], 8)
                nb += 8
                pos += 1
            else:
                pos += len(entries[sym])
        if pos != len(raw):
            raise AssertionError(f"parse covered {pos} bytes != {len(raw)}")
        writer.put(codes[eof], lengths[eof])
        nb += lengths[eof]
        per_file.append(nb)
    return writer.finish(), per_file


def serialize_dual_archives(
    dag: DAGSpec,
    lengths: Sequence[int],
    files: Sequence[bytes],
    parses: Sequence[Sequence[int]],
) -> Dict[str, object]:
    """Serialize one fixed emitted vocab + code table + token stream in BOTH A1AF and A1AD."""
    emitted = dag.emitted_entries
    dictionary = Dictionary(emitted)
    payload, per_file_bits = encode_payload(dictionary, lengths, files, parses)
    file_count_bytes = varint(len(files))

    flat_header = build_flat_header(emitted, lengths)
    dag_header = build_dag_header(dag, lengths)

    flat_archive = flat_header + file_count_bytes + payload
    dag_archive = dag_header + file_count_bytes + payload

    per_file_bytes = [(b + 7) // 8 for b in per_file_bits]
    ra_overhead = sum(per_file_bytes) + sum(len(varint(x)) for x in per_file_bytes)

    flat_dict_bytes = sum(1 + len(e) for e in emitted)
    dag_dict_bytes = len(dag_header) - 4 - 1 - len(varint(len(dag.nodes))) - len(varint(len(dag.leaves))) - (len(emitted) + 2)

    return {
        "emitted_entries": len(emitted),
        "dag_nodes": len(dag.nodes),
        "dag_mode": "pair" if dag.mode == FLAG_MODE_PAIR else "hybrid",
        "has_emit_mask": dag.emit_mask is not None,
        "has_merge_ranks": dag.merge_ranks is not None and len(dag.nodes) > len(dag.leaves),
        "flat_archive": flat_archive,
        "dag_archive": dag_archive,
        "flat_header_bytes": len(flat_header),
        "dag_header_bytes": len(dag_header),
        "flat_dict_bytes": flat_dict_bytes,
        "dag_dict_bytes": dag_dict_bytes,
        "table_bytes": len(emitted) + 2,
        "payload_bytes": len(payload),
        "payload_bits": sum(per_file_bits),
        "flat_complete_bytes": len(flat_archive),
        "flat_complete_bits": 8 * len(flat_archive),
        "dag_complete_bytes": len(dag_archive),
        "dag_complete_bits": 8 * len(dag_archive),
        "flat_random_access_bytes": len(flat_header) + len(file_count_bytes) + ra_overhead,
        "dag_random_access_bytes": len(dag_header) + len(file_count_bytes) + ra_overhead,
        "per_file_bits": per_file_bits,
    }


def header_size_summary(
    entries: Sequence[bytes],
    emit_mask: Optional[Sequence[bool]] = None,
    explicit_pairs: Optional[Dict[bytes, Tuple[bytes, bytes]]] = None,
) -> Dict[str, int]:
    """Compute exact flat and construction-DAG header bytes for a vocabulary."""
    dag = build_dag_spec(entries, emit_mask=emit_mask, explicit_pairs=explicit_pairs)
    emitted = dag.emitted_entries
    dummy_lengths = [1] * (len(emitted) + 2)
    flat_h = build_flat_header(emitted, dummy_lengths)
    dag_h = build_dag_header(dag, dummy_lengths)
    return {
        "dag_nodes": len(dag.nodes),
        "emitted_entries": len(emitted),
        "leaves": len(dag.leaves),
        "fragments": len(emitted) - sum(1 for e in emitted if len(e) == 1),
        "flat_dict_bytes": sum(1 + len(e) for e in emitted),
        "flat_frag_bytes": sum(1 + len(e) for e in emitted if len(e) > 1),
        "flat_header_bytes": len(flat_h),
        "dag_header_bytes": len(dag_h),
        "dag_dict_only_bytes": len(dag_h) - (len(emitted) + 2),
        "table_bytes": len(emitted) + 2,
        "dag_mode": dag.mode,
    }
