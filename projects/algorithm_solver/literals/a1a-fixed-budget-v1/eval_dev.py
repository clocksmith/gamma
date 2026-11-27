#!/usr/bin/env python3
"""Repriced common-serializer evaluation, deployment controls, zstd benchmark, and ancestor diagnostics.

Evaluates ONLY local spent development corpora inside the worktree:
  - primary (CodeNet training split, 400 files, 259,706 B) -> training dev gate
  - dev, fresh, fresh2, Express, ramda, TheAlgorithms/Python -> diagnostic description only

Never modifies any frozen folder.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
import time
from collections import Counter
from multiprocessing import Pool
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
OH = LIT / "objective-holdout-v1"
CL = LIT / "closure-holdout-v1"
CHAINS_DIR = HERE / "out" / "chains"
BIN_DIR = HERE / "bin"

import headers as H
import independent_decode as ID
import validate_encoders as VE

ALPHA = 171
SMALL_SLOTS = 84
LARGE_SLOTS = 3924
SMALL_FLAT_FRAG = 566
LARGE_FLAT_FRAG = 43480
TOL = 1.02

DEV_CORPORA = {
    "primary": (OH / "frozen/sets/train.json", LIT),
    "dev": (OH / "frozen/sets/dev.json", LIT),
    "fresh": (OH / "sets/fresh.json", OH),
    "fresh2": (CL / "sets/fresh2.json", CL),
    "Express": (OH / "sets/project.json", OH),
    "ramda": (CL / "sets/project-javascript.json", CL),
    "TheAlgorithms/Python": (CL / "sets/project-python.json", CL),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_corpus(name: str) -> Tuple[List[bytes], List[Path]]:
    spec_path, root = DEV_CORPORA[name]
    spec = json.loads(spec_path.read_text())
    docs: List[bytes] = []
    paths: List[Path] = []
    for f in spec["files"]:
        p = root / f["path"]
        raw = p.read_bytes()
        if "sha256" in f and sha256(raw) != f["sha256"]:
            raise SystemExit(f"{name}: hash mismatch on {f['path']}")
        docs.append(raw)
        paths.append(p)
    return docs, paths


def parse_chain_file(path: Path) -> Dict[str, object]:
    entries: List[bytes] = []
    train_tokens: List[int] = []
    flat_stored_bytes: List[int] = []
    explicit_pairs: Dict[bytes, Tuple[bytes, bytes]] = {}
    b_lines: List[Dict[str, object]] = []
    m_lines: List[Tuple[bytes, bytes]] = []
    diag: Dict[str, object] = {}

    for line in path.read_text().splitlines():
        if line.startswith("E "):
            parts = line.split()
            if len(parts) == 6:
                flat_stored_bytes.append(int(parts[2]))
                train_tokens.append(int(parts[3]))
                entries.append(bytes.fromhex(parts[5]))
        elif line.startswith("P "):
            parts = line.split()
            if len(parts) == 4:
                explicit_pairs[bytes.fromhex(parts[3])] = (bytes.fromhex(parts[1]), bytes.fromhex(parts[2]))
        elif line.startswith("M "):
            parts = line.split()
            if len(parts) == 3:
                m_lines.append((bytes.fromhex(parts[1]), bytes.fromhex(parts[2])))
        elif line.startswith("B "):
            info: Dict[str, object] = {}
            for tok in line.split()[1:]:
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    info[k] = v
            b_lines.append(info)
        elif line.startswith("D "):
            for tok in line.split()[2:]:
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    try:
                        diag[k] = int(v)
                    except ValueError:
                        try:
                            diag[k] = float(v)
                        except ValueError:
                            diag[k] = v

    return {
        "entries": entries,
        "train_tokens": train_tokens,
        "flat_stored_bytes": flat_stored_bytes,
        "explicit_pairs": explicit_pairs,
        "b_lines": b_lines,
        "m_lines": m_lines,
        "diag": diag,
    }


def prefix_len_for_budget(
    entries: List[bytes],
    budget_kind: str,
    budget_val: int,
    explicit_pairs: Optional[Dict[bytes, Tuple[bytes, bytes]]] = None,
) -> Optional[int]:
    """Return max total entry count n (including ALPHA leaves) fitting budget, or None if chain too short."""
    if budget_kind == "slots":
        target = ALPHA + budget_val
        return target if len(entries) >= target else None

    if budget_kind == "flat_frag":
        acc = 0
        best = ALPHA
        for i in range(ALPHA, len(entries)):
            acc += 1 + len(entries[i])
            if acc <= budget_val:
                best = i + 1
            else:
                return best
        # Chain ended before exceeding budget; return None if it fell short of budget
        return best if acc >= budget_val - 16 else None

    if budget_kind == "flat_header":
        # Binary search on A1AF header bytes
        if H.header_size_summary(entries)["flat_header_bytes"] < budget_val - 20:
            return None
        lo, hi = ALPHA, len(entries)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if H.header_size_summary(entries[:mid])["flat_header_bytes"] <= budget_val:
                lo = mid
            else:
                hi = mid - 1
        return lo

    if budget_kind == "dag_header":
        full_sz = H.header_size_summary(entries, explicit_pairs=explicit_pairs)["dag_header_bytes"]
        if full_sz < budget_val - 20:
            return None
        lo, hi = ALPHA, len(entries)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if H.header_size_summary(entries[:mid], explicit_pairs=explicit_pairs)["dag_header_bytes"] <= budget_val:
                lo = mid
            else:
                hi = mid - 1
        return lo

    raise ValueError(f"unknown budget_kind {budget_kind}")


def longest_match_tokens(entries: Sequence[bytes], docs: Sequence[bytes]) -> int:
    """Exact greedy left-to-right longest-match (AC/trie longest-match) token count."""
    vocab = set(entries)
    max_l = max(len(e) for e in entries)
    total = 0
    for raw in docs:
        i = 0
        n = len(raw)
        while i < n:
            lim = max_l if n - i >= max_l else n - i
            step = 1
            for l in range(lim, 1, -1):
                if raw[i : i + l] in vocab:
                    step = l
                    break
            i += step
            total += 1
    return total


def bpe_merge_replay_tokens(merges: Sequence[Tuple[bytes, bytes]], docs: Sequence[bytes]) -> int:
    """Fast HF-tokenizers-backed exact BPE merge replay (verified 100% equivalent to ref replay)."""
    tok, _, _ = VE.build_hf_byte_bpe_tokenizer(merges)
    total = 0
    for raw in docs:
        enc = tok.encode(VE.encode_bytes_to_bpe_str(raw))
        total += len(enc.tokens)
    return total


# Worker globals for multiprocessing min-token DP and complete-archive evaluation
_DOCS_MAP: Dict[str, List[bytes]] = {}


def _pool_init(docs_map: Dict[str, List[bytes]]) -> None:
    global _DOCS_MAP
    _DOCS_MAP = docs_map


def _eval_tokens_on_corpora(args):
    key, entries, corpora_names, compute_lm = args
    d = H.Dictionary(entries)
    tok_out = {}
    single_out = {}
    lm_out = {}
    for cname in corpora_names:
        docs = _DOCS_MAP[cname]
        t = 0
        s1 = 0
        for raw in docs:
            syms = H.parse_tokens(d.edges(raw))
            t += len(syms)
            s1 += sum(1 for s in syms if s == d.ESC or len(d.entries[s]) == 1)
        tok_out[cname] = t
        single_out[cname] = s1
        if compute_lm:
            lm_out[cname] = longest_match_tokens(entries, docs)
    return key, tok_out, single_out, lm_out


def _eval_complete_archive(args):
    """Fit canonical Huffman table on primary ONLY, encode primary and dev in BOTH A1AF & A1AD,
    and verify 100% byte-for-byte recovery via standalone independent_decode.py."""
    key, entries, explicit_pairs, measure_latency = args
    primary_docs = _DOCS_MAP["primary"]
    dev_docs = _DOCS_MAP["dev"]

    t0 = time.perf_counter()
    dag = H.build_dag_spec(entries, explicit_pairs=explicit_pairs)
    emitted = dag.emitted_entries
    d = H.Dictionary(emitted)
    prim_edges = [d.edges(raw) for raw in primary_docs]
    lengths, _, _, passes = H.fit_table(d, prim_edges)

    prim_parses = [H.parse_bits(e, lengths, d.ESC)[0] for e in prim_edges]
    prim_ser = H.serialize_dual_archives(dag, lengths, primary_docs, prim_parses)

    dev_edges = [d.edges(raw) for raw in dev_docs]
    dev_parses = [H.parse_bits(e, lengths, d.ESC)[0] for e in dev_edges]
    dev_ser = H.serialize_dual_archives(dag, lengths, dev_docs, dev_parses)

    # Independent verification of BOTH A1AF and A1AD on dev (and primary)
    dec_pf = ID.verify_archive_against_sources(prim_ser["flat_archive"], primary_docs)
    dec_pd = ID.verify_archive_against_sources(prim_ser["dag_archive"], primary_docs)
    dec_df = ID.decode_archive(dev_ser["flat_archive"], measure_per_file_ns=measure_latency)
    assert dec_df["files"] == dev_docs, f"{key}: A1AF dev decode mismatch"
    dec_dd = ID.decode_archive(dev_ser["dag_archive"], measure_per_file_ns=measure_latency)
    assert dec_dd["files"] == dev_docs, f"{key}: A1AD dev decode mismatch"
    assert dec_pf["tokens"] == dec_pd["tokens"]
    assert dec_df["tokens"] == dec_dd["tokens"]

    lat = None
    if measure_latency:
        def stats_us(ns_list: List[int]) -> Dict[str, float]:
            arr = sorted(x / 1000.0 for x in ns_list)
            n = len(arr)
            return {
                "mean_us": round(sum(arr) / n, 3),
                "p50_us": round(arr[int(0.50 * (n - 1))], 3),
                "p95_us": round(arr[int(0.95 * (n - 1))], 3),
                "p99_us": round(arr[int(0.99 * (n - 1))], 3),
            }
        lat = {
            "a1af_python_independent": stats_us(dec_df["per_file_decode_ns"]),
            "a1ad_python_independent": stats_us(dec_dd["per_file_decode_ns"]),
            "a1af_header_decode_us": round(dec_df["header_decode_ns"] / 1000.0, 3),
            "a1ad_header_decode_us": round(dec_dd["header_decode_ns"] / 1000.0, 3),
        }

    return key, {
        "emitted_entries": len(emitted),
        "dag_nodes": len(dag.nodes),
        "dag_mode": prim_ser["dag_mode"],
        "table_fit_passes": passes,
        "flat_header_bytes": prim_ser["flat_header_bytes"],
        "dag_header_bytes": prim_ser["dag_header_bytes"],
        "flat_dict_bytes": prim_ser["flat_dict_bytes"],
        "dag_dict_bytes": prim_ser["dag_dict_bytes"],
        "table_bytes": prim_ser["table_bytes"],
        "primary": {
            "bit_parse_tokens": dec_pd["tokens"],
            "escapes": dec_pd["escapes"],
            "payload_bytes": prim_ser["payload_bytes"],
            "flat_complete_bytes": prim_ser["flat_complete_bytes"],
            "flat_complete_bits": prim_ser["flat_complete_bits"],
            "dag_complete_bytes": prim_ser["dag_complete_bytes"],
            "dag_complete_bits": prim_ser["dag_complete_bits"],
            "flat_ra_bytes": prim_ser["flat_random_access_bytes"],
            "dag_ra_bytes": prim_ser["dag_random_access_bytes"],
        },
        "dev": {
            "bit_parse_tokens": dec_dd["tokens"],
            "escapes": dec_dd["escapes"],
            "payload_bytes": dev_ser["payload_bytes"],
            "flat_complete_bytes": dev_ser["flat_complete_bytes"],
            "flat_complete_bits": dev_ser["flat_complete_bits"],
            "dag_complete_bytes": dev_ser["dag_complete_bytes"],
            "dag_complete_bits": dev_ser["dag_complete_bits"],
            "flat_ra_bytes": dev_ser["flat_random_access_bytes"],
            "dag_ra_bytes": dev_ser["dag_random_access_bytes"],
        },
        "independent_decode_verified": True,
        "decode_latency_dev": lat,
        "eval_seconds": round(time.perf_counter() - t0, 3),
    }


def compute_breakeven_horizon(
    header_a: int, payload_a: int, header_b: int, payload_b: int, corpus_bytes: int, n_files: int
) -> Dict[str, object]:
    """Break-even corpus horizon M* where arm A complete bytes equal arm B complete bytes.

    Complete_A(M) = header_A + (payload_A / corpus_bytes) * M.
    Returns M*_bytes and M*_files (or 'dominates' / 'dominated').
    """
    ra = payload_a / corpus_bytes
    rb = payload_b / corpus_bytes
    dh = header_a - header_b
    dr = rb - ra  # payload byte savings per source byte for A over B
    avg_file = corpus_bytes / max(1, n_files)
    if dh <= 0 and dr >= 0:
        return {"status": "a_dominates", "m_star_bytes": 0.0, "m_star_files": 0.0}
    if dh >= 0 and dr <= 0:
        return {"status": "b_dominates", "m_star_bytes": None, "m_star_files": None}
    if dh > 0 and dr > 0:
        mb = dh / dr
        return {"status": "a_wins_above_m_star", "m_star_bytes": round(mb, 1), "m_star_files": round(mb / avg_file, 2)}
    # dh < 0 and dr < 0: A has smaller header, B has smaller payload -> A wins BELOW M*
    mb = (-dh) / (-dr)
    return {"status": "a_wins_below_m_star", "m_star_bytes": round(mb, 1), "m_star_files": round(mb / avg_file, 2)}


def evaluate_sentencepiece_controls(corpora_docs: Dict[str, List[bytes]], singles: List[bytes]) -> Dict[str, object]:
    """Score SentencePiece Unigram models under both native Viterbi and common min-token DP."""
    import sentencepiece as spm

    sp_dir = CHAINS_DIR / "sentencepiece"
    out = {}
    for model_path in sorted(sp_dir.glob("unigram_*.model")):
        vs = model_path.stem.split("_")[1]
        sp = spm.SentencePieceProcessor()
        sp.load(str(model_path))

        # Extract byte vocabulary (1..16 byte pieces) + training single-byte alphabet
        vocab_bytes = list(singles)
        seen = set(vocab_bytes)
        for idx in range(sp.get_piece_size()):
            if sp.is_control(idx) or sp.is_unknown(idx) or sp.is_byte(idx):
                continue
            piece = sp.id_to_piece(idx).replace("\u2581", " ").encode("utf-8")
            if 1 <= len(piece) <= 16 and piece not in seen:
                seen.add(piece)
                vocab_bytes.append(piece)

        hsz = H.header_size_summary(vocab_bytes)
        d = H.Dictionary(vocab_bytes)
        dp_toks = {}
        native_toks = {}
        native_rt_ok = True
        for cname, docs in corpora_docs.items():
            dp_toks[cname] = sum(len(H.parse_tokens(d.edges(raw))) for raw in docs)
            nt = 0
            for raw in docs:
                # Encode line-by-line preserving newlines as separate single-byte tokens if needed
                txt = raw.decode("utf-8", errors="replace")
                ids = sp.encode(txt, out_type=int)
                nt += len(ids)
                if cname == "dev" and raw.decode("utf-8", errors="strict") == txt:
                    if sp.decode(ids) != txt:
                        native_rt_ok = False
            native_toks[cname] = nt

        out[f"sp-unigram-{vs}"] = {
            "requested_vocab_size": int(vs),
            "extracted_entries": len(vocab_bytes),
            "extracted_fragments": len(vocab_bytes) - len(singles),
            "header_summary": hsz,
            "common_dp_tokens": dp_toks,
            "native_viterbi_tokens": native_toks,
            "native_utf8_roundtrip_dev": native_rt_ok,
        }
    return out


def evaluate_hf_bpe_controls(corpora_docs: Dict[str, List[bytes]], singles: List[bytes]) -> Dict[str, object]:
    """Score stock HF ByteLevel BPE models under both native merge replay and common min-token DP."""
    from tokenizers import Tokenizer

    hf_dir = CHAINS_DIR / "hf_bpe"
    out = {}
    for jpath in sorted(hf_dir.glob("hf_bpe_*.json")):
        vs = jpath.stem.split("_")[-1]
        tk = Tokenizer.from_file(str(jpath))
        model_json = json.loads(jpath.read_text())
        vocab_map = model_json["model"]["vocab"]
        merges_raw = model_json["model"]["merges"]

        # Reconstruct byte entries in merge creation order
        entries = list(singles)
        seen = set(entries)
        for m in merges_raw:
            if isinstance(m, str):
                a, b = m.split(" ", 1)
            else:
                a, b = m[0], m[1]
            ab = VE.decode_bpe_str_to_bytes(a + b)
            if 2 <= len(ab) <= 16 and ab not in seen:
                seen.add(ab)
                entries.append(ab)

        hsz = H.header_size_summary(entries)
        d = H.Dictionary(entries)
        dp_toks = {}
        native_toks = {}
        native_rt_ok = True
        for cname, docs in corpora_docs.items():
            dp_toks[cname] = sum(len(H.parse_tokens(d.edges(raw))) for raw in docs)
            nt = 0
            for raw in docs:
                txt = raw.decode("utf-8", errors="replace")
                enc = tk.encode(txt)
                nt += len(enc.ids)
                if cname == "dev":
                    dec = tk.decode(enc.ids)
                    if dec != txt:
                        native_rt_ok = False
            native_toks[cname] = nt

        out[f"hf-bytelevel-bpe-{vs}"] = {
            "requested_vocab_size": int(vs),
            "vocab_entries_in_model": len(vocab_map),
            "extracted_entries": len(entries),
            "extracted_fragments": len(entries) - len(singles),
            "header_summary": hsz,
            "common_dp_tokens": dp_toks,
            "native_hf_tokens": native_toks,
            "native_utf8_roundtrip_dev": native_rt_ok,
        }
    return out


def run_zstd_comparisons(corpora_paths: Dict[str, List[Path]], primary_paths: List[Path]) -> Dict[str, object]:
    """Run lean-framed and standard-framed zstd complete-archive benchmarks with measured p95 decode latency."""
    zstd_bench = BIN_DIR / "zstd_bench"
    if not zstd_bench.exists():
        subprocess.run(
            ["cc", "-O3", "-Wall", "-I/opt/homebrew/include", "-L/opt/homebrew/lib",
             "-Wl,-rpath,/opt/homebrew/lib", "-o", str(zstd_bench), str(HERE / "zstd_bench.c"), "-lzstd"],
            check=True,
        )
    dict_8k = OH / "frozen/zstd-train-8k.dict"
    out_dir = HERE / "out" / "zstd"
    out_dir.mkdir(parents=True, exist_ok=True)
    dict_32k = out_dir / "zstd-train-32k.dict"
    if not dict_32k.exists():
        subprocess.run(
            ["/opt/homebrew/bin/zstd", "--train", "--maxdict=32768", "-q", "-f", "-o", str(dict_32k)]
            + [str(p) for p in primary_paths],
            check=True,
        )

    results = {}
    with tempfile.TemporaryDirectory() as td:
        td_p = Path(td)
        for cname in ("primary", "dev", "fresh", "fresh2", "Express", "ramda", "TheAlgorithms/Python"):
            lst = td_p / f"{cname.replace('/', '_')}.list"
            lst.write_text("\n".join(str(p) for p in corpora_paths[cname]) + "\n")
            c_res = {}
            configs = [
                ("zstd19_lean_dict8k", "19", "1", str(dict_8k)),
                ("zstd19_lean_dict32k", "19", "1", str(dict_32k)),
                ("zstd19_lean_nodict", "19", "1", "none"),
                ("zstd19_std_dict8k", "19", "0", str(dict_8k)),
            ]
            for label, lvl, lean, dp in configs:
                p = subprocess.run([str(zstd_bench), lvl, lean, dp, "40", str(lst)], capture_output=True, text=True, check=True)
                c_res[label] = json.loads(p.stdout)
            results[cname] = c_res
    return results


def _ablate_ancestor_chunk(args):
    """Worker: disable each ancestor symbol individually for emission only on unseen dev files."""
    anc_syms, entries, base_file_tokens, files_using_map = args
    dev_docs = _DOCS_MAP["dev"]
    d = H.Dictionary(entries)
    out = {}
    for sym in anc_syms:
        fidxs = files_using_map[sym]
        if not fidxs:
            out[sym] = 0
            continue
        delta = 0
        for fi in fidxs:
            # Reparse doc fi with `sym` disabled (removed from edges)
            raw = dev_docs[fi]
            edges = d.edges(raw)
            filtered = [[(l, s) for (l, s) in here if s != sym] for here in edges]
            new_toks = len(H.parse_tokens(filtered))
            delta += new_toks - base_file_tokens[fi]
        out[sym] = delta
    return out


def run_ancestor_diagnostics(
    arm_name: str,
    entries: List[bytes],
    explicit_pairs: Optional[Dict[bytes, Tuple[bytes, bytes]]],
    b_lines: List[Dict[str, object]],
    primary_docs: List[bytes],
    dev_docs: List[bytes],
    pool: Pool,
) -> Dict[str, object]:
    """Requirement 4: count purchased, shared, emitted, unused ancestors; disable individually & jointly."""
    dag = H.build_dag_spec(entries, explicit_pairs=explicit_pairs)
    A = len(dag.leaves)
    M = len(dag.nodes)
    assert dag.mode == H.FLAG_MODE_PAIR, f"{arm_name}: expected pure-pair closed DAG"

    # Compute out-degree of every DAG node (how many later nodes reference it as left or right child)
    child_refs = Counter()
    for idx, (kind, val) in enumerate(dag.defs):
        assert kind == "pair"
        l, r = val  # type: ignore[misc]
        child_refs[l] += 1
        child_refs[r] += 1

    purchased_multi = list(range(A, M))
    promoted_ancestors = [i for i in purchased_multi if child_refs[i] >= 1]
    shared_ancestors = [i for i in purchased_multi if child_refs[i] >= 2]
    dag_roots = [i for i in purchased_multi if child_refs[i] == 0]

    # Count bundle-promoted non-root ancestors from B lines (within this prefix)
    node_set = set(dag.nodes)
    bundle_anc_set = set()
    bundle_shared_anc_set = set()
    for bl in b_lines:
        raw_nodes = str(bl.get("nodes", "")).split(",")
        nroots = int(bl.get("roots", 0))
        for item in raw_nodes:
            if item.startswith("A:"):
                b = bytes.fromhex(item[2:])
                if b in node_set:
                    bundle_anc_set.add(b)
                    if nroots >= 2:
                        bundle_shared_anc_set.add(b)

    # Measure exact emissions on primary and unseen dev
    d = H.Dictionary(dag.nodes)
    prim_uses = [0] * M
    for raw in primary_docs:
        for s in H.parse_tokens(d.edges(raw)):
            if s < M:
                prim_uses[s] += 1

    dev_uses = [0] * M
    dev_files_using: Dict[int, List[int]] = {i: [] for i in range(M)}
    dev_base_file_tokens: List[int] = []
    for fi, raw in enumerate(dev_docs):
        syms = H.parse_tokens(d.edges(raw))
        dev_base_file_tokens.append(len(syms))
        seen_f = set()
        for s in syms:
            if s < M:
                dev_uses[s] += 1
                if s not in seen_f:
                    seen_f.add(s)
                    dev_files_using[s].append(fi)
    dev_base_total = sum(dev_base_file_tokens)

    emitted_anc_prim = [i for i in promoted_ancestors if prim_uses[i] > 0]
    unused_anc_prim = [i for i in promoted_ancestors if prim_uses[i] == 0]
    emitted_anc_dev = [i for i in promoted_ancestors if dev_uses[i] > 0]
    unused_anc_dev = [i for i in promoted_ancestors if dev_uses[i] == 0]

    # Joint disabling (emission only, retaining FULL storage DAG via A1AD emit_mask!)
    def joint_disable(disabled_indices: Sequence[int], label: str) -> Dict[str, object]:
        dis_set = set(disabled_indices)
        emit_mask = [i not in dis_set for i in range(M)]
        dag_m = H.build_dag_spec(dag.nodes, emit_mask=emit_mask, explicit_pairs=explicit_pairs)
        emitted = dag_m.emitted_entries
        dm = H.Dictionary(emitted)
        new_dev_toks = sum(len(H.parse_tokens(dm.edges(raw))) for raw in dev_docs)
        # Also fit Huffman table on primary & verify A1AD archive with emit_mask via independent_decode!
        prim_e = [dm.edges(raw) for raw in primary_docs]
        lengths, _, _, _ = H.fit_table(dm, prim_e)
        dev_e = [dm.edges(raw) for raw in dev_docs]
        dev_p = [H.parse_bits(e, lengths, dm.ESC)[0] for e in dev_e]
        ser = H.serialize_dual_archives(dag_m, lengths, dev_docs, dev_p)
        dec = ID.verify_archive_against_sources(ser["dag_archive"], dev_docs)
        return {
            "label": label,
            "disabled_count": len(dis_set),
            "dag_nodes_retained": M,
            "emitted_entries": len(emitted),
            "dev_min_tokens": new_dev_toks,
            "dev_tokens_saved_by_disabled_ancestors": new_dev_toks - dev_base_total,
            "dev_tokens_delta_pct": round(100.0 * (new_dev_toks / dev_base_total - 1.0), 3),
            "a1ad_header_bytes": ser["dag_header_bytes"],
            "a1ad_dev_complete_bytes": ser["dag_complete_bytes"],
            "a1ad_dev_bit_tokens": dec["tokens"],
            "independent_decode_verified": True,
        }

    joint_results = {
        "disable_unused_on_primary_ancestors": joint_disable(unused_anc_prim, "unused_on_primary"),
        "disable_all_promoted_ancestors": joint_disable(promoted_ancestors, "all_promoted_ancestors"),
        "disable_all_shared_ancestors": joint_disable(shared_ancestors, "all_shared_ancestors"),
    }
    if bundle_anc_set:
        b_idxs = [i for i in range(A, M) if dag.nodes[i] in bundle_anc_set]
        joint_results["disable_bundle_promoted_ancestors"] = joint_disable(b_idxs, "bundle_promoted_ancestors")

    # Individual disabling of EVERY promoted ancestor on unseen dev (parallelized across Pool)
    chunk_size = max(1, (len(promoted_ancestors) + 15) // 16)
    chunks = [promoted_ancestors[i : i + chunk_size] for i in range(0, len(promoted_ancestors), chunk_size)]
    indiv_deltas: Dict[int, int] = {}
    if chunks:
        jobs = [(ch, dag.nodes, dev_base_file_tokens, {s: dev_files_using[s] for s in ch}) for ch in chunks]
        for part in pool.map(_ablate_ancestor_chunk, jobs):
            indiv_deltas.update(part)

    vals = sorted(indiv_deltas.values())
    n_anc = len(vals)
    pos_vals = [v for v in vals if v > 0]
    top10 = sorted(indiv_deltas.items(), key=lambda kv: (-kv[1], kv[0]))[:10]

    return {
        "arm": arm_name,
        "dag_nodes": M,
        "leaves": A,
        "purchased_multi": len(purchased_multi),
        "dag_roots_non_ancestors": len(dag_roots),
        "promoted_ancestors_dag": len(promoted_ancestors),
        "shared_ancestors_dag": len(shared_ancestors),
        "bundle_promoted_ancestors": len(bundle_anc_set),
        "bundle_shared_ancestors": len(bundle_shared_anc_set),
        "emitted_ancestors_primary": len(emitted_anc_prim),
        "unused_ancestors_primary": len(unused_anc_prim),
        "emitted_ancestors_dev": len(emitted_anc_dev),
        "unused_ancestors_dev": len(unused_anc_dev),
        "dev_base_min_tokens": dev_base_total,
        "joint_disabling_dev": joint_results,
        "individual_disabling_dev": {
            "ancestors_tested": n_anc,
            "saving_positive_tokens": len(pos_vals),
            "saving_zero_tokens": n_anc - len(pos_vals),
            "sum_individual_tokens_saved": sum(vals),
            "mean_tokens_saved": round(sum(vals) / max(1, n_anc), 3),
            "median_tokens_saved": vals[n_anc // 2] if n_anc else 0,
            "p95_tokens_saved": vals[int(0.95 * (n_anc - 1))] if n_anc else 0,
            "max_tokens_saved": vals[-1] if n_anc else 0,
            "top10_ancestors": [
                {
                    "node_id": nid,
                    "hex": dag.nodes[nid].hex(),
                    "ascii_preview": repr(dag.nodes[nid].decode("utf-8", errors="replace")),
                    "dag_out_degree": child_refs[nid],
                    "dev_uses": dev_uses[nid],
                    "dev_tokens_saved_indiv": delta,
                }
                for nid, delta in top10
            ],
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=8)
    args = ap.parse_args()
    t_start = time.perf_counter()

    corpora_docs: Dict[str, List[bytes]] = {}
    corpora_paths: Dict[str, List[Path]] = {}
    for cname in DEV_CORPORA:
        docs, paths = load_corpus(cname)
        corpora_docs[cname] = docs
        corpora_paths[cname] = paths
    singles = [bytes([b]) for b in sorted({b for raw in corpora_docs["primary"] for b in raw})]
    assert len(singles) == ALPHA

    # Load all chain-based arms
    chain_paths = {
        "open": CL / "out/exact/exact-entry-s1-whole.txt",
        "open-byte": CL / "out/bundle/open-byte-ext.txt",
        "exact-closed": CL / "out/bundle/pair-ext.txt",
        "pair-byte": CHAINS_DIR / "pair-byte-exact-full.txt",
        "prefix-bundle-byte": CL / "out/bundle/bundle-byte.txt",
        "prefix-bundle-slot": CL / "out/bundle/bundle-slot.txt",
        "shared-bundle-byte": CHAINS_DIR / "shared-bundle-byte.txt",
        "shared-bundle-slot": CHAINS_DIR / "shared-bundle-slot.txt",
        "shared-bundle-dag": CHAINS_DIR / "shared-bundle-dag.txt",
        "bpe": CHAINS_DIR / "bpe-ext.txt",
        "greedtok": CHAINS_DIR / "greedtok-ext.txt",
        "pathpiece": CHAINS_DIR / "pathpiece-ext.txt",
    }
    chains = {name: parse_chain_file(p) for name, p in chain_paths.items()}

    # Compute exact open reference headers at 84 and 3,924 fragments
    open_small_hdr = H.header_size_summary(chains["open"]["entries"][: ALPHA + SMALL_SLOTS])
    open_large_hdr = H.header_size_summary(chains["open"]["entries"][: ALPHA + LARGE_SLOTS])
    assert open_small_hdr["flat_frag_bytes"] == SMALL_FLAT_FRAG
    assert open_large_hdr["flat_frag_bytes"] == LARGE_FLAT_FRAG

    budgets = {
        "dag_header_small": ("dag_header", open_small_hdr["dag_header_bytes"]),
        "dag_header_large": ("dag_header", open_large_hdr["dag_header_bytes"]),
        "flat_frag_small": ("flat_frag", SMALL_FLAT_FRAG),
        "flat_frag_large": ("flat_frag", LARGE_FLAT_FRAG),
        "flat_header_small": ("flat_header", open_small_hdr["flat_header_bytes"]),
        "flat_header_large": ("flat_header", open_large_hdr["flat_header_bytes"]),
        "slots_small": ("slots", SMALL_SLOTS),
        "slots_large": ("slots", LARGE_SLOTS),
    }

    # Resolve prefix lengths per (budget, arm)
    resolved: Dict[str, Dict[str, int]] = {}
    token_jobs = []
    archive_jobs = []
    corpora_list = list(DEV_CORPORA.keys())

    # Arms whose complete archives (A1AF & A1AD) we build + independently decode on primary & dev
    archive_budgets = {"dag_header_small", "dag_header_large", "flat_frag_small", "flat_frag_large", "slots_small", "slots_large"}
    latency_arms = {"open", "open-byte", "exact-closed", "pair-byte", "shared-bundle-byte", "shared-bundle-dag", "bpe"}

    for bname, (bkind, bval) in budgets.items():
        resolved[bname] = {}
        for aname, ch in chains.items():
            n = prefix_len_for_budget(ch["entries"], bkind, bval, explicit_pairs=ch["explicit_pairs"] or None)
            if n is None:
                continue
            resolved[bname][aname] = n
            compute_lm = bname in ("dag_header_small", "dag_header_large", "flat_frag_small", "flat_frag_large", "slots_small", "slots_large")
            token_jobs.append(((bname, aname), ch["entries"][:n], corpora_list, compute_lm))
            if bname in archive_budgets:
                meas_lat = (aname in latency_arms and bname in ("dag_header_large", "slots_large"))
                archive_jobs.append(((bname, aname), ch["entries"][:n], ch["explicit_pairs"] or None, meas_lat))

    print(f"Evaluating {len(token_jobs)} (budget, arm) token jobs and {len(archive_jobs)} dual-archive jobs...", flush=True)
    with Pool(args.jobs, initializer=_pool_init, initargs=(corpora_docs,)) as pool:
        tok_results_list = pool.map(_eval_tokens_on_corpora, token_jobs)
        arch_results_list = pool.map(_eval_complete_archive, archive_jobs)

        # Run Ancestor Diagnostics (Requirement 4) at small & large matched DAG-header and slot budgets
        anc_diag = {}
        for aname in ("shared-bundle-byte", "shared-bundle-dag", "pair-byte", "exact-closed", "prefix-bundle-byte", "bpe"):
            ch = chains[aname]
            for bname in ("slots_small", "slots_large", "dag_header_small", "dag_header_large"):
                if aname not in resolved[bname]:
                    continue
                n = resolved[bname][aname]
                anc_diag[f"{aname}@{bname}"] = run_ancestor_diagnostics(
                    f"{aname}@{bname}",
                    ch["entries"][:n],
                    ch["explicit_pairs"] or None,
                    ch["b_lines"],
                    corpora_docs["primary"],
                    corpora_docs["dev"],
                    pool,
                )

    tok_map = {k: (t, s1, lm) for k, t, s1, lm in tok_results_list}
    arch_map = {k: v for k, v in arch_results_list}

    # Add native BPE merge replay on primary + dev + diagnostic sets for BPE at every budget
    bpe_m_lines = chains["bpe"]["m_lines"]
    bpe_native = {}
    for bname, (bkind, bval) in budgets.items():
        if "bpe" not in resolved[bname]:
            continue
        n = resolved[bname]["bpe"]
        n_frags = n - ALPHA
        # Exact M lines needed to produce the first n_frags distinct multi-byte entries
        seen_e = set(singles)
        used_merges = []
        for l_b, r_b in bpe_m_lines:
            used_merges.append((l_b, r_b))
            seen_e.add(l_b + r_b)
            if len(seen_e) >= n:
                break
        bpe_native[bname] = {
            cname: bpe_merge_replay_tokens(used_merges, corpora_docs[cname])
            for cname in corpora_list
        }

    # Evaluate SentencePiece Unigram & HF ByteLevel BPE deployment controls
    sp_controls = evaluate_sentencepiece_controls(corpora_docs, singles)
    hf_controls = evaluate_hf_bpe_controls(corpora_docs, singles)

    # Run lean-framed & standard-framed zstd benchmarks
    zstd_results = run_zstd_comparisons(corpora_paths, corpora_paths["primary"])

    # Assemble structured budget tables + explicit dev_gate checks
    budget_tables: Dict[str, object] = {}
    for bname, (bkind, bval) in budgets.items():
        rows = {}
        # Reference on primary: min(open, open-byte) for byte budgets; open for slot budgets
        if bkind == "slots":
            open_ref_tok = tok_map[(bname, "open")][0]["primary"]
            open_ref_name = "open"
        else:
            cand_refs = [(tok_map[(bname, a)][0]["primary"], a) for a in ("open", "open-byte") if (bname, a) in tok_map]
            open_ref_tok, open_ref_name = min(cand_refs)
        pb_tok = tok_map[(bname, "pair-byte")][0]["primary"] if (bname, "pair-byte") in tok_map else None

        for aname, n in resolved[bname].items():
            t_dict, s1_dict, lm_dict = tok_map[(bname, aname)]
            prim_tok = t_dict["primary"]
            hsz = H.header_size_summary(chains[aname]["entries"][:n], explicit_pairs=chains[aname]["explicit_pairs"] or None)
            row: Dict[str, object] = {
                "total_entries": n,
                "fragments": n - ALPHA,
                "header_summary": hsz,
                "primary_tokens": prim_tok,
                "vs_open_ref_pct": round(100.0 * (prim_tok / open_ref_tok - 1.0), 3),
                "within_2pct_open_ref": prim_tok <= TOL * open_ref_tok,
                "vs_pair_byte_pct": round(100.0 * (prim_tok / pb_tok - 1.0), 3) if pb_tok else None,
                "beats_pair_byte": (prim_tok < pb_tok) if pb_tok else None,
                "corpora_min_tokens": t_dict,
                "corpora_single_byte_tokens": s1_dict,
                "corpora_longest_match_tokens": lm_dict if lm_dict else None,
            }
            if (bname, aname) in arch_map:
                row["archive"] = arch_map[(bname, aname)]
            rows[aname] = row
        budget_tables[bname] = {
            "budget_kind": bkind,
            "budget_value": bval,
            "open_reference_arm": open_ref_name,
            "open_reference_primary_tokens": open_ref_tok,
            "pair_byte_primary_tokens": pb_tok,
            "arms": rows,
        }

    # Compute break-even horizons M* on unseen `dev` (400 files, 270,994 bytes)
    dev_bytes = sum(len(x) for x in corpora_docs["dev"])
    dev_nfiles = len(corpora_docs["dev"])
    z_dev_8k = zstd_results["dev"]["zstd19_lean_dict8k"]
    z_dev_32k = zstd_results["dev"]["zstd19_lean_dict32k"]
    horizons = {}
    for bname in ("dag_header_small", "dag_header_large", "flat_frag_small", "flat_frag_large", "slots_small", "slots_large"):
        h_row = {}
        op_arch = arch_map[(bname, "open")]
        for aname in ("shared-bundle-byte", "shared-bundle-dag", "exact-closed", "pair-byte", "bpe", "open-byte"):
            if (bname, aname) not in arch_map:
                continue
            aa = arch_map[(bname, aname)]
            h_row[aname] = {
                "a1ad_vs_a1af_same_arm": compute_breakeven_horizon(
                    aa["dag_header_bytes"], aa["dev"]["payload_bytes"],
                    aa["flat_header_bytes"], aa["dev"]["payload_bytes"],
                    dev_bytes, dev_nfiles,
                ),
                "a1ad_vs_open_a1ad": compute_breakeven_horizon(
                    aa["dag_header_bytes"], aa["dev"]["payload_bytes"],
                    op_arch["dag_header_bytes"], op_arch["dev"]["payload_bytes"],
                    dev_bytes, dev_nfiles,
                ),
                "a1ad_vs_zstd19_lean_dict8k": compute_breakeven_horizon(
                    aa["dag_header_bytes"], aa["dev"]["payload_bytes"],
                    z_dev_8k["dict_bytes"], z_dev_8k["payload_bytes"],
                    dev_bytes, dev_nfiles,
                ),
                "a1ad_vs_zstd19_lean_dict32k": compute_breakeven_horizon(
                    aa["dag_header_bytes"], aa["dev"]["payload_bytes"],
                    z_dev_32k["dict_bytes"], z_dev_32k["payload_bytes"],
                    dev_bytes, dev_nfiles,
                ),
            }
        horizons[bname] = h_row

    out = {
        "schema": "a1a-fixed-budget-v1.eval-dev/1",
        "open_reference_headers": {"small_84": open_small_hdr, "large_3924": open_large_hdr},
        "corpora_meta": {
            cname: {"files": len(docs), "bytes": sum(len(x) for x in docs)}
            for cname, docs in corpora_docs.items()
        },
        "budgets": budget_tables,
        "bpe_native_merge_replay": bpe_native,
        "sentencepiece_controls": sp_controls,
        "hf_bpe_controls": hf_controls,
        "zstd": zstd_results,
        "ancestor_diagnostics": anc_diag,
        "horizons_dev": horizons,
        "eval_wall_seconds": round(time.perf_counter() - t_start, 2),
    }

    out_path = HERE / "out" / "eval_dev.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(f"Wrote {out_path} in {out['eval_wall_seconds']}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
