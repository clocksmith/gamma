#!/usr/bin/env python3
"""Verified chain loader, B1RA archive serializer, and prefix grid evaluator for A1b.

Reuses ONLY existing SHA-256-verified chains fitted on CodeNet primary and local
spent development corpora already present in the worktree. Never modifies any
frozen folder or fetches external data.
"""

from __future__ import annotations

import hashlib
import heapq
import io
import json
import os
import resource
import subprocess
import sys
import tarfile
import time
from fractions import Fraction
from multiprocessing import Pool
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LITERALS = HERE.parent
WORKTREE = LITERALS.parent.parent.parent

MAGIC = b"B1RA"
MAX_ENTRY_LEN = 16
MAX_TABLE_PASSES = 15

# Common prefix grid K = number of multi-byte fragments added to the 171-byte base alphabet.
PRIMARY_GRID: tuple[int, ...] = (0, 32, 64, 128, 256, 512, 1024, 2048, 3072, 4096)
FIXED_ARMS_K: tuple[int, ...] = (512, 2048, 4096)
# Frozen 3-point geometric pilot (exact 8x geometric spacing spanning [64, 4096]).
PILOT_GRID_K: tuple[int, ...] = (64, 512, 4096)

# Primary decimal horizons M (source bytes) and diagnostic horizon sweep for lower envelope.
PRIMARY_HORIZONS: tuple[int, ...] = (100_000, 100_000_000)
DIAGNOSTIC_HORIZONS: tuple[int, ...] = (
    10_000,
    30_000,
    100_000,
    300_000,
    1_000_000,
    3_000_000,
    10_000_000,
    30_000_000,
    100_000_000,
    1_000_000_000,
)

PRIMARY_CHAIN_NAME = "exact_closed"

# Verified chains fitted strictly on CodeNet primary (400 files, 259,706 B, 171 singles).
CHAIN_SPECS: dict[str, dict[str, Any]] = {
    "exact_closed": {
        "kind": "chain_txt",
        "path": "closure-holdout-v1/out/bundle/pair-ext.txt",
        "sha256_file": "closure-holdout-v1/out/bundle/SHA256SUMS",
        "sha256_name": "pair-ext.txt",
        "fit_lineage": "codenet_primary",
        "fit_org": "ibm_codenet",
        "description": "Exact closed token-gain chain (prefix 0..4096 identical to brute-force-verified exact-closed-s1-whole.txt)",
    },
    "exact_byte": {
        "kind": "chain_txt",
        "path": "closure-holdout-v1/out/bundle/open-byte-ext.txt",
        "sha256_file": "closure-holdout-v1/out/bundle/SHA256SUMS",
        "sha256_name": "open-byte-ext.txt",
        "fit_lineage": "codenet_primary",
        "fit_org": "ibm_codenet",
        "description": "Exact open gain-per-stored-byte chain",
    },
    "bundle_byte": {
        "kind": "chain_txt",
        "path": "closure-holdout-v1/out/bundle/bundle-byte.txt",
        "sha256_file": "closure-holdout-v1/out/bundle/SHA256SUMS",
        "sha256_name": "bundle-byte.txt",
        "fit_lineage": "codenet_primary",
        "fit_org": "ibm_codenet",
        "description": "Closure-preserving byte-priced bundle chain",
    },
    "bundle_slot": {
        "kind": "chain_txt",
        "path": "closure-holdout-v1/out/bundle/bundle-slot.txt",
        "sha256_file": "closure-holdout-v1/out/bundle/SHA256SUMS",
        "sha256_name": "bundle-slot.txt",
        "fit_lineage": "codenet_primary",
        "fit_org": "ibm_codenet",
        "description": "Closure-preserving slot-priced bundle chain",
    },
    "bpe": {
        "kind": "closure_frozen_json",
        "path": "closure-holdout-v1/frozen/dictionaries.json",
        "dict_key": "bpe-K4096",
        "pinned_sha256": "4f2d4410f6e6a841fbd01783ec9a0f03498f40f356d9f2996642debe0ba543b7",
        "fit_lineage": "codenet_primary",
        "fit_org": "ibm_codenet",
        "description": "Frozen BPE chain (max 3,924 multi-byte fragments, total cap 4,096)",
    },
    "exact_open": {
        "kind": "chain_txt",
        "path": "closure-holdout-v1/out/exact/exact-entry-s1-whole.txt",
        "sha256_file": "closure-holdout-v1/out/exact/SHA256SUMS",
        "sha256_name": "exact-entry-s1-whole.txt",
        "fit_lineage": "codenet_primary",
        "fit_org": "ibm_codenet",
        "description": "Brute-force-verified exact open token-gain chain (max 3,925 multi-byte fragments)",
    },
    "exact_norm_p2": {
        "kind": "chain_txt",
        "path": "closure-holdout-v1/out/exact/exact-norm-p2-nowhole.txt",
        "sha256_file": "closure-holdout-v1/out/exact/SHA256SUMS",
        "sha256_name": "exact-norm-p2-nowhole.txt",
        "fit_lineage": "codenet_primary",
        "fit_org": "ibm_codenet",
        "description": "Brute-force-verified exact normalized 2-problem-support chain (max 3,925 multi-byte fragments)",
    },
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def current_peak_rss_bytes() -> int:
    """Return process peak RSS in bytes (macOS reports bytes; Linux reports KiB)."""
    ru = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(ru) if sys.platform == "darwin" else int(ru) * 1024


def varint(n: int) -> bytes:
    if n < 0:
        raise ValueError(f"negative varint: {n}")
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def varint_len(n: int) -> int:
    if n < 0:
        raise ValueError(f"negative varint: {n}")
    if n == 0:
        return 1
    return (n.bit_length() + 6) // 7


def huffman_lengths(counts: list[int]) -> list[int]:
    """Optimal deterministic canonical prefix-code lengths. All counts >= 1."""
    n = len(counts)
    if n < 2:
        raise ValueError("need at least 2 symbols")
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
    if sum(1 << (top - ln) for ln in lengths) != (1 << top):
        raise AssertionError("Kraft sum is not exactly one")
    return lengths


def canonical_codes(lengths: list[int]) -> list[int]:
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


def build_header(entries: list[bytes], lengths: list[int]) -> bytes:
    if len(lengths) != len(entries) + 2:
        raise ValueError("expected one code length per entry, then ESC, then EOF")
    out = bytearray(MAGIC)
    out += varint(len(entries))
    for e in entries:
        if not (1 <= len(e) <= MAX_ENTRY_LEN):
            raise ValueError(f"entry length out of range: {len(e)}")
        out.append(len(e))
        out += e
    if max(lengths) > 255 or min(lengths) < 1:
        raise ValueError("code length out of range 1..255")
    out += bytes(lengths)
    return bytes(out)


class Dictionary:
    """Ordered dictionary: entry i -> i, ESC -> n, EOF -> n + 1."""

    def __init__(self, entries: list[bytes]):
        if len(set(entries)) != len(entries):
            raise ValueError("duplicate dictionary entry")
        self.entries = list(entries)
        self.n = len(entries)
        self.ESC = self.n
        self.EOF = self.n + 1
        self.single = [-1] * 256
        self.multi: dict[bytes, int] = {}
        self.prefix2: set[bytes] = set()
        # Group multi-byte lengths per 2-byte prefix for faster exact matching.
        self.prefix2_lens: dict[bytes, tuple[int, ...]] = {}
        tmp_lens: dict[bytes, set[int]] = {}
        for i, e in enumerate(entries):
            ln = len(e)
            if ln == 1:
                self.single[e[0]] = i
            else:
                self.multi[e] = i
                p2 = e[:2]
                self.prefix2.add(p2)
                tmp_lens.setdefault(p2, set()).add(ln)
        for p2, lset in tmp_lens.items():
            self.prefix2_lens[p2] = tuple(sorted(lset))

    def ram_footprint_bytes(self) -> int:
        """Frozen deployment RAM model (bytes) for dictionary + lookup tables + codes.

        Deterministic representation independent of Python object overhead:
        - Raw entry strings + 2-byte offset/length descriptors: sum(len(e) + 2)
        - 256-entry single-byte LUT (int16): 512 B
        - Canonical code/length table for (n + 2) symbols (uint32 code + uint8 len): 5 * (n + 2) B
        - Open-addressed hash table for multi-byte entries at 2x load (8 B slot): 16 * n_multi B
        """
        raw_entries = sum(len(e) + 2 for e in self.entries)
        single_lut = 256 * 2
        code_lut = 5 * (self.n + 2)
        n_multi = len(self.multi)
        hash_lut = 16 * n_multi
        return raw_entries + single_lut + code_lut + hash_lut

    def edges(self, raw: bytes) -> tuple[list[list[tuple[int, int]]], int, int]:
        """Return (edges, edge_scans, edge_matches).

        edges[i] = [(length, symbol), ...] for every matching entry at i, shortest first.
        """
        n = len(raw)
        single = self.single
        multi = self.multi
        p2_lens = self.prefix2_lens
        esc = self.ESC
        out: list[list[tuple[int, int]]] = []
        matches = 0
        for i in range(n):
            s = single[raw[i]]
            here = [(1, s if s >= 0 else esc)]
            if i + 2 <= n:
                lens = p2_lens.get(raw[i : i + 2])
                if lens is not None:
                    for ln in lens:
                        if i + ln > n:
                            break
                        matches += 1
                        sym = multi.get(raw[i : i + ln])
                        if sym is not None:
                            here.append((ln, sym))
            out.append(here)
        return out, n, matches


def parse_tokens(edges: list[list[tuple[int, int]]]) -> tuple[list[int], int]:
    """Exact minimum number of tokens; returns (symbol_list, dp_relaxations)."""
    n = len(edges)
    big = n + 1
    best = [big] * (n + 1)
    prev: list[tuple[int, int] | None] = [None] * (n + 1)
    best[0] = 0
    relax = 0
    for i in range(n):
        c = best[i] + 1
        for ln, sym in edges[i]:
            relax += 1
            j = i + ln
            if c < best[j]:
                best[j] = c
                prev[j] = (i, sym)
    out: list[int] = []
    at = n
    while at > 0:
        step = prev[at]
        assert step is not None
        at, sym = step
        out.append(sym)
    out.reverse()
    return out, relax


def parse_bits(
    edges: list[list[tuple[int, int]]],
    lengths: list[int],
    esc: int,
) -> tuple[list[int], int, int]:
    """Exact minimum code bits for fixed lengths; ties prefer fewer tokens.

    Returns (symbols, total_bits_excluding_eof, dp_relaxations).
    """
    n = len(edges)
    inf = 1 << 60
    bits = [inf] * (n + 1)
    toks = [0] * (n + 1)
    prev: list[tuple[int, int] | None] = [None] * (n + 1)
    bits[0] = 0
    esc_cost = lengths[esc] + 8
    relax = 0
    for i in range(n):
        b0 = bits[i]
        t1 = toks[i] + 1
        for ln, sym in edges[i]:
            relax += 1
            j = i + ln
            c = b0 + (esc_cost if sym == esc else lengths[sym])
            if c < bits[j] or (c == bits[j] and t1 < toks[j]):
                bits[j] = c
                toks[j] = t1
                prev[j] = (i, sym)
    out: list[int] = []
    at = n
    while at > 0:
        step = prev[at]
        assert step is not None
        at, sym = step
        out.append(sym)
    out.reverse()
    return out, bits[n], relax


def fit_table(
    dictionary: Dictionary,
    files_edges: list[list[list[tuple[int, int]]]],
) -> tuple[list[int], list[int], int, int, int]:
    """Fit canonical Huffman lengths strictly on fitting files.

    Returns (lengths, counts, payload_bits, passes, dp_relaxations).
    """
    n = dictionary.n
    esc = dictionary.ESC
    eof = dictionary.EOF

    def lengths_of(cnts: list[int]) -> list[int]:
        return huffman_lengths([c if c > 0 else 1 for c in cnts])

    def cost(cnts: list[int], lens: list[int]) -> int:
        return sum(c * ln for c, ln in zip(cnts, lens)) + 8 * cnts[esc]

    counts = [0] * (n + 2)
    total_relax = 0
    for edges in files_edges:
        syms, r = parse_tokens(edges)
        total_relax += r
        for sym in syms:
            counts[sym] += 1
    counts[eof] = len(files_edges)
    lengths = lengths_of(counts)
    bits = cost(counts, lengths)
    passes = 0
    for step in range(1, MAX_TABLE_PASSES + 1):
        c2 = [0] * (n + 2)
        for edges in files_edges:
            syms, _, r = parse_bits(edges, lengths, esc)
            total_relax += r
            for sym in syms:
                c2[sym] += 1
        c2[eof] = len(files_edges)
        l2 = lengths_of(c2)
        b2 = cost(c2, l2)
        if b2 < bits:
            counts, lengths, bits, passes = c2, l2, b2, step
        else:
            break
    return lengths, counts, bits, passes, total_relax


class BitWriter:
    __slots__ = ("out", "acc", "nbits", "total_bits_written")

    def __init__(self) -> None:
        self.out = bytearray()
        self.acc = 0
        self.nbits = 0
        self.total_bits_written = 0

    def put(self, code: int, length: int) -> None:
        self.acc = (self.acc << length) | code
        self.nbits += length
        self.total_bits_written += length
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


def encode_b1ra_archive(
    dictionary: Dictionary,
    lengths: list[int],
    header_bytes: bytes,
    docs: list[bytes],
    compute_min_tokens: bool = False,
) -> tuple[bytes, dict[str, Any]]:
    """Serialize a real B1RA archive with exact work & diagnostic accounting."""
    t0 = time.perf_counter()
    codes = canonical_codes(lengths)
    esc = dictionary.ESC
    eof = dictionary.EOF
    entries = dictionary.entries
    eof_code = codes[eof]
    eof_len = lengths[eof]
    esc_code = codes[esc]
    esc_len = lengths[esc]

    record_payloads: list[bytes] = []
    record_lengths: list[int] = []
    edge_scans = 0
    edge_matches = 0
    dp_relaxations = 0
    bit_writes = 0
    total_tokens = 0
    total_min_tokens = 0
    total_escapes = 0
    total_payload_bits = 0
    used_entries: set[int] = set()
    multi_entry_uses = 0
    single_or_esc_uses = 0

    for raw in docs:
        edges, scans, matches = dictionary.edges(raw)
        edge_scans += scans
        edge_matches += matches
        if compute_min_tokens:
            tok_syms, _ = parse_tokens(edges)
            total_min_tokens += len(tok_syms)
        syms, parse_b, relax = parse_bits(edges, lengths, esc)
        dp_relaxations += relax

        writer = BitWriter()
        pos = 0
        for sym in syms:
            if sym == esc:
                writer.put(esc_code, esc_len)
                writer.put(raw[pos], 8)
                pos += 1
                total_escapes += 1
                single_or_esc_uses += 1
            else:
                writer.put(codes[sym], lengths[sym])
                e = entries[sym]
                pos += len(e)
                used_entries.add(sym)
                if len(e) > 1:
                    multi_entry_uses += 1
                else:
                    single_or_esc_uses += 1
            total_tokens += 1
        if pos != len(raw):
            raise AssertionError(f"parse covered {pos} != {len(raw)} bytes")
        writer.put(eof_code, eof_len)
        rec_bytes = writer.finish()
        if writer.total_bits_written != parse_b + eof_len:
            raise AssertionError("bit write count mismatch with parse_bits cost")
        bit_writes += writer.total_bits_written
        total_payload_bits += writer.total_bits_written
        record_payloads.append(rec_bytes)
        record_lengths.append(len(rec_bytes))

    framing = bytearray(varint(len(docs)))
    for p_j in record_lengths:
        framing += varint(p_j)
    framing_bytes = bytes(framing)
    payload_bytes = b"".join(record_payloads)
    archive = header_bytes + framing_bytes + payload_bytes
    elapsed = time.perf_counter() - t0

    source_bytes = sum(len(d) for d in docs)
    h_bytes = len(header_bytes)
    f_bytes = len(framing_bytes)
    p_bytes = len(payload_bytes)
    b_bytes = f_bytes + p_bytes
    assert h_bytes + b_bytes == len(archive)

    stats = {
        "source_bytes": source_bytes,
        "record_count": len(docs),
        "entries_count": dictionary.n,
        "header_bytes": h_bytes,
        "dict_bytes": sum(1 + len(e) for e in entries),
        "code_table_bytes": dictionary.n + 2,
        "framing_bytes": f_bytes,
        "payload_bytes": p_bytes,
        "payload_bits": total_payload_bits,
        "body_bytes": b_bytes,
        "complete_bytes": len(archive),
        "r_hat": b_bytes / source_bytes if source_bytes > 0 else 0.0,
        "tokens": total_tokens,
        "min_tokens": total_min_tokens if compute_min_tokens else None,
        "escapes": total_escapes,
        "distinct_entries_used": len(used_entries),
        "unused_entries": dictionary.n - len(used_entries),
        "multi_entry_uses": multi_entry_uses,
        "single_or_esc_uses": single_or_esc_uses,
        "avg_code_len_header": sum(lengths) / len(lengths),
        "max_code_len_header": max(lengths),
        "realized_bits_per_token": total_payload_bits / max(1, total_tokens),
        "bytes_per_token": source_bytes / max(1, total_tokens),
        "dict_ram_bytes": dictionary.ram_footprint_bytes(),
        "archive_sha256": sha256_bytes(archive),
        "work": {
            "wall_seconds": elapsed,
            "edge_scans": edge_scans,
            "edge_matches": edge_matches,
            "dp_relaxations": dp_relaxations,
            "bit_writes": bit_writes,
            "total_ops": edge_scans + edge_matches + dp_relaxations + bit_writes,
            "peak_rss_bytes": current_peak_rss_bytes(),
        },
    }
    return archive, stats


def horizon_objective_exact(header_bytes: int, body_bytes: int, source_bytes: int, M: int) -> Fraction:
    """Exact rational H_K + M * (body_bytes / source_bytes)."""
    return Fraction(header_bytes) + Fraction(M * body_bytes, source_bytes)


def select_best_prefix_exact(
    candidates: list[dict[str, Any]],
    M: int,
) -> dict[str, Any]:
    """Minimize H_K + M * r_hat_K over candidates; exact ties strictly prefer smaller H_K, then smaller K."""
    if not candidates:
        raise ValueError("no candidate prefixes")

    def sort_key(c: dict[str, Any]) -> tuple[Fraction, int, int, str]:
        if "body_bytes" in c and "source_bytes" in c:
            obj = horizon_objective_exact(
                int(c["header_bytes"]), int(c["body_bytes"]), int(c["source_bytes"]), int(M)
            )
        else:
            # Support synthetic curves given directly as exact (header_bytes, r_hat)
            r_val = c["r_hat"]
            r_frac = r_val if isinstance(r_val, Fraction) else Fraction(str(r_val))
            obj = Fraction(int(c["header_bytes"])) + Fraction(int(M)) * r_frac
        return (obj, int(c["header_bytes"]), int(c["K"]), str(c.get("chain", "")))

    return min(candidates, key=sort_key)


def _verify_sha256sum_entry(sha_file: Path, target_name: str, actual_path: Path) -> str:
    expected = None
    for line in sha_file.read_text().splitlines():
        if not line.strip():
            continue
        digest, rel = line.split(None, 1)
        if rel.strip() == target_name:
            expected = digest.strip()
            break
    if expected is None:
        raise RuntimeError(f"{target_name} not found in {sha_file}")
    actual = sha256_bytes(actual_path.read_bytes())
    if actual != expected:
        raise RuntimeError(f"SHA-256 mismatch for {actual_path}: got {actual}, want {expected}")
    return actual


def load_verified_chain(chain_name: str) -> dict[str, Any]:
    """Load and SHA-256-verify an existing chain from closure-holdout-v1."""
    if chain_name not in CHAIN_SPECS:
        raise KeyError(f"unknown verified chain: {chain_name}")
    spec = CHAIN_SPECS[chain_name]
    path = LITERALS / spec["path"]
    if not path.exists():
        raise FileNotFoundError(f"missing verified chain file: {path}")

    if spec["kind"] == "chain_txt":
        digest = _verify_sha256sum_entry(LITERALS / spec["sha256_file"], spec["sha256_name"], path)
        entries = [
            bytes.fromhex(line.split()[5])
            for line in path.read_text().splitlines()
            if line.startswith("E ")
        ]
    elif spec["kind"] == "closure_frozen_json":
        raw = path.read_bytes()
        digest = sha256_bytes(raw)
        if digest != spec["pinned_sha256"]:
            raise RuntimeError(f"pinned SHA-256 mismatch for {path}")
        payload = json.loads(raw.decode("utf-8"))
        entries = [bytes.fromhex(h) for h in payload["dictionaries"][spec["dict_key"]]]
    else:
        raise ValueError(f"unsupported chain kind: {spec['kind']}")

    singles = [e for e in entries if len(e) == 1]
    frags = [e for e in entries if len(e) > 1]
    if len(singles) != 171:
        raise AssertionError(f"{chain_name}: expected 171 singles, got {len(singles)}")
    if len(set(entries)) != len(entries):
        raise AssertionError(f"{chain_name}: duplicate entries in chain")

    eligible_grid = [k for k in PRIMARY_GRID if k <= len(frags)]
    if max(eligible_grid) < len(frags) and max(eligible_grid) < max(PRIMARY_GRID):
        # Include the verified cap maximum (3924) for 4096-cap chains like bpe/exact_open/exact_norm_p2.
        eligible_grid.append(min(len(frags), 3924))
    eligible_grid = sorted(set(eligible_grid))

    return {
        "name": chain_name,
        "path": str(path),
        "source_sha256": digest,
        "fit_lineage": spec["fit_lineage"],
        "fit_org": spec["fit_org"],
        "description": spec["description"],
        "singles": singles,
        "fragments": frags,
        "max_fragments": len(frags),
        "eligible_grid": eligible_grid,
    }


def load_fit_corpus() -> dict[str, Any]:
    """Load the exact CodeNet primary fitting corpus used to build the verified chains."""
    manifest_path = LITERALS / "objective-holdout-v1/frozen/sets/train.json"
    spec = json.loads(manifest_path.read_text())
    docs: list[bytes] = []
    file_hashes: list[str] = []
    for item in spec["files"]:
        raw = (LITERALS / item["path"]).read_bytes()
        h = sha256_bytes(raw)
        if h != item["sha256"]:
            raise RuntimeError(f"fit corpus hash mismatch: {item['path']}")
        docs.append(raw)
        file_hashes.append(h)
    return {
        "lineage_id": "codenet_primary",
        "org_id": "ibm_codenet",
        "role": "fit",
        "language": "python+javascript",
        "source": spec.get("source", "CodeNet primary"),
        "docs": docs,
        "file_hashes": file_hashes,
        "record_count": len(docs),
        "source_bytes": sum(len(d) for d in docs),
    }


def load_spent_lineages() -> list[dict[str, Any]]:
    """Load all local spent non-fit lineages with strict org/repo provenance metadata.

    Returns both:
    - role == 'dev_disjoint': 7 non-CodeNet spent codebases across 6 distinct orgs
      (5 external third-party repos + 2 distinct clocksmith/gamma codebases tagged org_id='clocksmith').
    - role == 'in_dist_codenet_diag': 2 held-out CodeNet splits (same collection as fit,
      STRICTLY excluded from repo-disjoint calibration and primary dev scoring).
    """
    lineages: list[dict[str, Any]] = []

    def _add(
        lineage_id: str,
        org_id: str,
        role: str,
        language: str,
        source_desc: str,
        docs: list[bytes],
    ) -> None:
        hashes = [sha256_bytes(d) for d in docs]
        lineages.append(
            {
                "lineage_id": lineage_id,
                "org_id": org_id,
                "role": role,
                "language": language,
                "source": source_desc,
                "docs": docs,
                "file_hashes": hashes,
                "record_count": len(docs),
                "source_bytes": sum(len(d) for d in docs),
            }
        )

    # 1. expressjs/express (objective-holdout-v1 spent project)
    sp = json.loads((LITERALS / "objective-holdout-v1/sets/project.json").read_text())
    _add(
        "expressjs_express",
        "expressjs",
        "dev_disjoint",
        "javascript",
        sp["source"],
        [(LITERALS / "objective-holdout-v1" / f["path"]).read_bytes() for f in sp["files"]],
    )

    # 2. ramda/ramda (closure-holdout-v1 spent JS project)
    sp = json.loads((LITERALS / "closure-holdout-v1/sets/project-javascript.json").read_text())
    _add(
        "ramda_ramda",
        "ramda",
        "dev_disjoint",
        "javascript",
        sp["source"],
        [(LITERALS / "closure-holdout-v1" / f["path"]).read_bytes() for f in sp["files"]],
    )

    # 3. TheAlgorithms/Python (closure-holdout-v1 spent Python project)
    sp = json.loads((LITERALS / "closure-holdout-v1/sets/project-python.json").read_text())
    _add(
        "TheAlgorithms_Python",
        "TheAlgorithms",
        "dev_disjoint",
        "python",
        sp["source"],
        [(LITERALS / "closure-holdout-v1" / f["path"]).read_bytes() for f in sp["files"]],
    )

    # 4 & 5. lodash/lodash and python/cpython (witness-scaling-v1 deduplicated cohorts)
    ws = json.loads((LITERALS / "witness-scaling-v1/cohorts.json").read_text())
    for src, lid, oid, lang in (
        ("lodash", "lodash_lodash", "lodash", "javascript"),
        ("cpython", "python_cpython", "python", "python"),
    ):
        seen: dict[str, tuple[str, bytes]] = {}
        for cohort in ws["cohorts"]:
            if cohort["source"] != src:
                continue
            for pr in cohort["programs"]:
                raw = pr["text"].encode("utf-8")
                h = sha256_bytes(raw)
                if h != pr["sha256"]:
                    raise RuntimeError(f"witness-scaling hash mismatch for {pr['id']}")
                seen.setdefault(h, (pr["id"], raw))
        ordered_docs = [raw for _, raw in sorted(seen.values(), key=lambda x: x[0])]
        src_meta = ws["sources"][src]
        _add(
            lid,
            oid,
            "dev_disjoint",
            lang,
            f"{src_meta['name']} {src_meta['version']} ({src_meta['licence']})",
            ordered_docs,
        )

    # 6. Authored LeetCode catalogue dev split (scaling-v1 spent dev set; org=clocksmith)
    sp = json.loads((LITERALS / "scaling-v1/sets/catalogue-dev.json").read_text())
    _add(
        "authored_catalogue_dev",
        "clocksmith",
        "dev_disjoint",
        "python+javascript",
        "projects/algorithm_solver/catalogue/authored (scaling-v1 dev split, 200 problems)",
        [(WORKTREE / f["path"]).read_bytes() for f in sp["files"]],
    )

    # 7. Gamma core Python package (capacity-boundary-v1 spent repo; org=clocksmith)
    # This calibration lineage is the Gamma package used to fit the locked predictor.
    # Reading the current checkout quietly changes its examples after a package edit.
    fit_revision = "7e9d8abffd4bec0395002171110c2195571a6b78"
    snapshot = subprocess.check_output(["git", "-C", str(WORKTREE), "archive", fit_revision, "gamma"])
    with tarfile.open(fileobj=io.BytesIO(snapshot)) as archive:
        members = sorted(
            (m for m in archive.getmembers() if m.isfile() and m.name.endswith(".py")),
            key=lambda m: Path(m.name),
        )
        gamma_docs = [archive.extractfile(m).read() for m in members]
    _add(
        "clocksmith_gamma_core",
        "clocksmith",
        "dev_disjoint",
        "python",
        "clocksmith/gamma core package (gamma/**/*.py)",
        gamma_docs,
    )

    # In-distribution CodeNet diagnostic strata (same collection as fit; NEVER in repo-disjoint cal!)
    sp = json.loads((LITERALS / "objective-holdout-v1/sets/fresh.json").read_text())
    _add(
        "codenet_fresh",
        "ibm_codenet",
        "in_dist_codenet_diag",
        "python+javascript",
        sp["source"] + " (objective-holdout-v1 fresh)",
        [(LITERALS / "objective-holdout-v1" / f["path"]).read_bytes() for f in sp["files"]],
    )

    sp = json.loads((LITERALS / "closure-holdout-v1/sets/fresh2.json").read_text())
    _add(
        "codenet_fresh2",
        "ibm_codenet",
        "in_dist_codenet_diag",
        "python+javascript",
        sp["source"] + " (closure-holdout-v1 fresh2)",
        [(LITERALS / "closure-holdout-v1" / f["path"]).read_bytes() for f in sp["files"]],
    )

    return lineages


# ---- Parallel header fitting & archive grid scoring --------------------------

_FIT_DOCS: list[bytes] = []


def _init_fit_worker(docs: list[bytes]) -> None:
    global _FIT_DOCS
    _FIT_DOCS = docs


def _fit_one_header(task: tuple[str, int, list[bytes]]) -> dict[str, Any]:
    chain_name, K, entries = task
    t0 = time.perf_counter()
    d = Dictionary(entries)
    edges_list = []
    edge_scans = 0
    edge_matches = 0
    for raw in _FIT_DOCS:
        ed, sc, ma = d.edges(raw)
        edges_list.append(ed)
        edge_scans += sc
        edge_matches += ma
    lengths, counts, payload_bits, passes, dp_relax = fit_table(d, edges_list)
    hdr = build_header(entries, lengths)
    elapsed = time.perf_counter() - t0
    return {
        "chain": chain_name,
        "K": K,
        "entries": entries,
        "lengths": lengths,
        "header_bytes_raw": hdr,
        "header_bytes": len(hdr),
        "header_sha256": sha256_bytes(hdr),
        "table_passes": passes,
        "fit_payload_bits": payload_bits,
        "avg_code_len": sum(lengths) / len(lengths),
        "max_code_len": max(lengths),
        "dict_ram_bytes": d.ram_footprint_bytes(),
        "fit_work": {
            "wall_seconds": elapsed,
            "edge_scans": edge_scans,
            "edge_matches": edge_matches,
            "dp_relaxations": dp_relax,
            "total_ops": edge_scans + edge_matches + dp_relax,
            "peak_rss_bytes": current_peak_rss_bytes(),
        },
    }


def fit_all_prefix_headers(
    chains: dict[str, dict[str, Any]],
    fit_corpus: dict[str, Any],
    jobs: int = 8,
) -> dict[tuple[str, int], dict[str, Any]]:
    """Fit frozen B1RA headers strictly on fit_corpus for every verified (chain, K)."""
    tasks: list[tuple[str, int, list[bytes]]] = []
    k0_added = False
    k0_chains: list[str] = []
    for cname, ch in chains.items():
        singles = ch["singles"]
        frags = ch["fragments"]
        for K in ch["eligible_grid"]:
            if K == 0:
                k0_chains.append(cname)
                if not k0_added:
                    tasks.append((cname, 0, list(singles)))
                    k0_added = True
            else:
                tasks.append((cname, K, singles + frags[:K]))

    t0 = time.perf_counter()
    if jobs > 1 and len(tasks) > 1:
        with Pool(min(jobs, len(tasks)), initializer=_init_fit_worker, initargs=(fit_corpus["docs"],)) as pool:
            fitted = pool.map(_fit_one_header, tasks, chunksize=1)
    else:
        _init_fit_worker(fit_corpus["docs"])
        fitted = [_fit_one_header(t) for t in tasks]

    headers: dict[tuple[str, int], dict[str, Any]] = {}
    k0_proto = None
    for row in fitted:
        headers[(row["chain"], row["K"])] = row
        if row["K"] == 0:
            k0_proto = row

    # K=0 is identical across all chains sharing the same 171-byte base alphabet.
    assert k0_proto is not None
    for cname in k0_chains:
        if (cname, 0) not in headers:
            copy_row = dict(k0_proto)
            copy_row["chain"] = cname
            headers[(cname, 0)] = copy_row

    total_wall = time.perf_counter() - t0
    for row in headers.values():
        row["batch_wall_seconds"] = total_wall
    return headers


# Independent worker evaluation for (lineage, chain, K) -> serialize + independent decode.
_EVAL_LINEAGES: dict[str, list[bytes]] = {}
_EVAL_HEADERS: dict[tuple[str, int], dict[str, Any]] = {}


def _init_eval_worker(
    lineage_docs: dict[str, list[bytes]],
    headers: dict[tuple[str, int], dict[str, Any]],
) -> None:
    global _EVAL_LINEAGES, _EVAL_HEADERS
    _EVAL_LINEAGES = lineage_docs
    _EVAL_HEADERS = headers


def _eval_one_cell(task: tuple[str, str, int, bool]) -> dict[str, Any]:
    import independent_decode as ID  # local independent verifier (stdlib only)

    lineage_id, chain_name, K, compute_min_tok = task
    docs = _EVAL_LINEAGES[lineage_id]
    hdr_info = _EVAL_HEADERS[(chain_name, K)]
    d = Dictionary(hdr_info["entries"])
    archive, stats = encode_b1ra_archive(
        d,
        hdr_info["lengths"],
        hdr_info["header_bytes_raw"],
        docs,
        compute_min_tokens=compute_min_tok,
    )
    # Independently decode EVERY archive to prove 100% byte fidelity and 0 B drift!
    dec = ID.verify_archive_against_sources(
        archive, docs, expected_header_bytes=hdr_info["header_bytes_raw"]
    )
    if not dec["all_ok"]:
        raise AssertionError(
            f"independent decode FAILED for ({lineage_id}, {chain_name}, K={K}): {dec}"
        )
    if (
        dec["complete_bytes"] != stats["complete_bytes"]
        or dec["header_bytes"] != stats["header_bytes"]
        or dec["body_bytes"] != stats["body_bytes"]
        or dec["tokens"] != stats["tokens"]
        or dec["escapes"] != stats["escapes"]
    ):
        raise AssertionError(
            f"encoder/decoder accounting drift for ({lineage_id}, {chain_name}, K={K})"
        )

    stats["lineage_id"] = lineage_id
    stats["chain"] = chain_name
    stats["K"] = K
    stats["header_sha256"] = hdr_info["header_sha256"]
    stats["independent_decode_ok"] = True
    stats["fidelity"] = dec["fidelity"]
    stats["random_access_spot_check_ok"] = dec["random_access_spot_check_ok"]
    stats["padding_bits_total"] = dec["padding_bits"]
    return stats


def evaluate_full_grid(
    lineages: list[dict[str, Any]],
    chains: dict[str, dict[str, Any]],
    headers: dict[tuple[str, int], dict[str, Any]],
    jobs: int = 8,
) -> list[dict[str, Any]]:
    """Serialize and independently decode archives for every (lineage, chain, K)."""
    lineage_docs = {lin["lineage_id"]: lin["docs"] for lin in lineages}
    tasks: list[tuple[str, str, int, bool]] = []
    # Deduplicate K=0 across chains during compute, then mirror to every chain.
    k0_chains = [cname for cname, ch in chains.items() if 0 in ch["eligible_grid"]]
    primary_k0_chain = PRIMARY_CHAIN_NAME if PRIMARY_CHAIN_NAME in k0_chains else k0_chains[0]

    for lin in lineages:
        lid = lin["lineage_id"]
        for cname, ch in chains.items():
            for K in ch["eligible_grid"]:
                if K == 0 and cname != primary_k0_chain:
                    continue
                compute_min_tok = cname == PRIMARY_CHAIN_NAME
                tasks.append((lid, cname, K, compute_min_tok))

    # Ensure HERE is on sys.path for worker import of independent_decode.
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))

    if jobs > 1 and len(tasks) > 1:
        with Pool(
            min(jobs, os.cpu_count() or 1),
            initializer=_init_eval_worker,
            initargs=(lineage_docs, headers),
        ) as pool:
            rows = pool.map(_eval_one_cell, tasks, chunksize=1)
    else:
        _init_eval_worker(lineage_docs, headers)
        rows = [_eval_one_cell(t) for t in tasks]

    # Mirror K=0 rows cleanly to every chain (same 171-byte dictionary & header).
    k0_by_lin = {r["lineage_id"]: r for r in rows if r["K"] == 0 and r["chain"] == primary_k0_chain}
    for lid, base_row in k0_by_lin.items():
        for cname in k0_chains:
            if cname == primary_k0_chain:
                continue
            dup = dict(base_row)
            dup["chain"] = cname
            rows.append(dup)

    rows.sort(key=lambda r: (r["lineage_id"], r["chain"], r["K"]))
    return rows


def main() -> int:
    """Build and independently verify the full prefix grid, caching results to out/prefix_grid.json."""
    out_dir = HERE / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = min(8, os.cpu_count() or 1)

    t0 = time.perf_counter()
    fit_corpus = load_fit_corpus()
    chains = {name: load_verified_chain(name) for name in CHAIN_SPECS}
    lineages = load_spent_lineages()

    t_fit0 = time.perf_counter()
    headers = fit_all_prefix_headers(chains, fit_corpus, jobs=jobs)
    fit_wall = time.perf_counter() - t_fit0

    t_eval0 = time.perf_counter()
    rows = evaluate_full_grid(lineages, chains, headers, jobs=jobs)
    eval_wall = time.perf_counter() - t_eval0

    # Strip raw bytes before serializing JSON metadata.
    header_meta = {
        f"{cname}:K{K}": {
            k: v
            for k, v in h.items()
            if k not in ("entries", "lengths", "header_bytes_raw")
        }
        for (cname, K), h in sorted(headers.items())
    }
    lineage_meta = [
        {k: v for k, v in lin.items() if k != "docs"} for lin in lineages
    ]
    chain_meta = {
        cname: {k: v for k, v in ch.items() if k not in ("singles", "fragments")}
        for cname, ch in chains.items()
    }
    payload = {
        "schema": "gamma.bits-a1b.prefix-grid.v1",
        "primary_chain": PRIMARY_CHAIN_NAME,
        "primary_grid": list(PRIMARY_GRID),
        "fixed_arms_k": list(FIXED_ARMS_K),
        "pilot_grid_k": list(PILOT_GRID_K),
        "primary_horizons": list(PRIMARY_HORIZONS),
        "diagnostic_horizons": list(DIAGNOSTIC_HORIZONS),
        "fit_corpus": {k: v for k, v in fit_corpus.items() if k != "docs"},
        "chains": chain_meta,
        "lineages": lineage_meta,
        "headers": header_meta,
        "rows": rows,
        "timing": {
            "fit_headers_wall_seconds": round(fit_wall, 3),
            "evaluate_grid_wall_seconds": round(eval_wall, 3),
            "total_wall_seconds": round(time.perf_counter() - t0, 3),
        },
    }
    out_path = out_dir / "prefix_grid.json"
    out_path.write_text(json.dumps(payload, indent=1) + "\n")
    print(
        f"Built and independently verified {len(rows)} archives across "
        f"{len(lineages)} lineages x {len(chains)} chains in "
        f"{payload['timing']['total_wall_seconds']:.2f}s -> {out_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
