#!/usr/bin/env python3
"""Equal-budget pre-search vs. ground-truth oracle evaluator for BITS Rung 2.

Implements:
  1. Zero cross-layout union floor (`allow_union_floor=False` always).
  2. Equal wall-clock search budget (`limit_seconds` for shared `both`; `limit_seconds / 2`
     per language for separate `C`) and symmetric iterative bit-cost reparsing (`top_reparse=10`
     candidate prefixes per layout for A, B, and per-language C = up to 100 `(K_1, K_2)` pairs).
  3. Explicit baseline & decoupled attribution required by the upgraded Rung 2 bar:
     - `default_always_B`: always pick shared dictionary + separate tables (Design B) with
       two-part MDL byte-cost prefix stopping (`mdl_byte_stop`). Identifies cells where
       `default_always_B` loses to the fair-search oracle by `> 1.0%`.
     - `mdl_byte_stop_Kmax`: ordinary two-part MDL / byte-cost stopping along the full `K_max`
       chains (holding layout fixed), vs `fill_all_Kmax` (token-minimizing full-budget stop)
       and `presearch_K_hat_stop` (truncating search at `K_hat` before running `engine.c`).
     - Additively decomposes total regret into `layout_regret_bytes` + `k_hat_truncation_bytes`.

Leaves `codenet-replication-v1/` and `fixed-source-v3/` completely untouched (read-only).
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
from pathlib import Path
from typing import Any, Sequence

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
CODENET_DIR = HERE.parent / 'codenet-replication-v1'
V3_DIR = HERE.parent / 'fixed-source-v3'

sys.path.insert(0, str(CODENET_DIR))
import byte_encode as BE  # noqa: E402
from raw_predictor import DEFAULT_K_GRID, predict_presearch  # noqa: E402

ROUTING_BYTES = 4
DEFAULT_ARMS = ('greedy-entry', 'greedy-byte', 'greedtok', 'bpe', 'freq-occ')
DEFAULT_TOP_REPARSE = 10


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_engine(build_dir: Path) -> Path:
    build_dir.mkdir(parents=True, exist_ok=True)
    engine_bin = build_dir / 'engine'
    if engine_bin.exists():
        return engine_bin
    engine_src = V3_DIR / 'engine.c'
    subprocess.run(
        ['cc', '-O3', '-Wall', '-Wno-unused-function', '-o', str(engine_bin), str(engine_src), '-lm'],
        check=True,
    )
    return engine_bin


def read_chain_entries(path: Path) -> list[tuple[int, int, bytes]]:
    out: list[tuple[int, int, bytes]] = []
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            parts = line.strip().split()
            if len(parts) >= 6 and parts[0] == 'E':
                out.append((int(parts[1]), int(parts[2]), bytes.fromhex(parts[5])))
    return out


def write_corpus_list(docs: Sequence[bytes], dest_dir: Path, stem: str, groups: Sequence[int] | None = None) -> Path:
    files_dir = dest_dir / f'{stem}_docs'
    files_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    for idx, raw in enumerate(docs):
        fp = files_dir / f'doc_{idx:04d}.bin'
        fp.write_bytes(raw)
        paths.append(str(fp))
    list_file = dest_dir / f'{stem}.txt'
    list_file.write_text('\n'.join(paths) + '\n', encoding='utf-8')
    grp_vals = list(groups) if groups is not None else list(range(len(docs)))
    (dest_dir / f'{stem}.groups').write_text('\n'.join(str(g) for g in grp_vals) + '\n', encoding='utf-8')
    return list_file


def run_engine_arm(
    engine_bin: Path,
    *,
    arm: str,
    policy: str,
    max_entry_len: int,
    k_max: int,
    limit_sec: float,
    list_file: Path,
    out_chain: Path,
    run_tag: str,
) -> float:
    out_chain.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env['FSV3_GROUPS'] = str(list_file.with_suffix('.groups'))
    env['FSV3_RECEIPT'] = (
        f'manifest=rung2-presearch pool={list_file.stem} cuts=doc impl=engine-v3 run={run_tag}'
    )
    env.pop('FSV3_CUTS', None)

    t0 = time.perf_counter()
    rem = max(0.05, limit_sec)
    subprocess.run(
        [
            str(engine_bin), arm, policy, str(max_entry_len), str(k_max), f'{rem:.4f}',
            str(list_file), str(out_chain),
        ],
        env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return time.perf_counter() - t0


def candidate_prefix_sizes(total_entries: int, k_points: Sequence[int], step: int) -> list[int]:
    if total_entries <= 0:
        return []
    wanted = {s for s in range(step, total_entries + 1, step)} | {total_entries}
    for k in k_points:
        if 0 < k <= total_entries:
            wanted.add(k)
    for small in range(16, min(total_entries, 256) + 1, 16):
        wanted.add(small)
    return sorted(s for s in wanted if 0 < s <= total_entries)


def verify_exact_roundtrip_single(docs: Sequence[bytes], entries: Sequence[bytes]) -> dict[str, Any]:
    root = BE.build_trie(entries)
    opt = BE.optimize_byte_segmentation(docs, root)
    if opt is None:
        raise ValueError('entries failed to spell corpus during round-trip check')
    bm = opt['byte_min']
    codes = BE.assign_canonical_codes(bm['lengths'])
    payload, nbits = BE.encode_bitstream(bm['pieces'], codes)
    if nbits != bm['payload_bits'] or len(payload) != bm['payload_bytes']:
        raise AssertionError('bitstream length mismatch against Huffman bit sum')
    decoded = BE.decode_bitstream(payload, len(docs), BE.build_decode_tree(codes))
    if list(decoded) != list(docs):
        raise AssertionError('decoded documents differ from input documents')
    dict_bytes = sum(1 + len(e) for e in entries)
    table_bytes = len(entries) + 1
    return {
        'entries': len(entries),
        'dict_bytes': dict_bytes,
        'table_bytes': table_bytes,
        'payload_bytes': len(payload),
        'total_no_routing_bytes': dict_bytes + table_bytes + len(payload),
        'roundtrip_verified': True,
    }


def verify_exact_roundtrip_layout(
    layout: str,
    docs_1: Sequence[bytes],
    docs_2: Sequence[bytes],
    winner: dict[str, Any],
) -> bool:
    if layout == 'A':
        chk = verify_exact_roundtrip_single(list(docs_1) + list(docs_2), winner['_entries'])
        expected = chk['dict_bytes'] + chk['table_bytes'] + chk['payload_bytes']
        if expected != winner['total_bytes']:
            raise AssertionError(f"Design A roundtrip total {expected} != {winner['total_bytes']}")
        return True
    if layout == 'B':
        entries = winner['_entries']
        root = BE.build_trie(entries)
        opt1 = BE.optimize_byte_segmentation(docs_1, root)['byte_min']
        opt2 = BE.optimize_byte_segmentation(docs_2, root)['byte_min']
        c1 = BE.assign_canonical_codes(opt1['lengths'])
        c2 = BE.assign_canonical_codes(opt2['lengths'])
        pay1, _ = BE.encode_bitstream(opt1['pieces'], c1)
        pay2, _ = BE.encode_bitstream(opt2['pieces'], c2)
        if BE.decode_bitstream(pay1, len(docs_1), BE.build_decode_tree(c1)) != list(docs_1):
            raise AssertionError('Design B lang1 roundtrip failed')
        if BE.decode_bitstream(pay2, len(docs_2), BE.build_decode_tree(c2)) != list(docs_2):
            raise AssertionError('Design B lang2 roundtrip failed')
        dict_b = sum(1 + len(e) for e in entries)
        tbl_b = 2 * (len(entries) + 1)
        tot = dict_b + tbl_b + ROUTING_BYTES + len(pay1) + len(pay2)
        if tot != winner['total_bytes']:
            raise AssertionError(f"Design B roundtrip total {tot} != {winner['total_bytes']}")
        return True
    if layout == 'C':
        chk1 = verify_exact_roundtrip_single(docs_1, winner['_entries_1'])
        chk2 = verify_exact_roundtrip_single(docs_2, winner['_entries_2'])
        tot = chk1['total_no_routing_bytes'] + chk2['total_no_routing_bytes'] + ROUTING_BYTES
        if tot != winner['total_bytes']:
            raise AssertionError(f"Design C roundtrip total {tot} != {winner['total_bytes']}")
        return True
    raise ValueError(f'unknown layout {layout}')


def _score_shared_chains_symmetric(
    chain_entries_by_arm: dict[str, list[tuple[int, int, bytes]]],
    docs_1: Sequence[bytes],
    docs_2: Sequence[bytes],
    *,
    k_points: Sequence[int],
    step: int,
    layouts: Sequence[str],
    top_reparse: int = DEFAULT_TOP_REPARSE,
) -> list[dict[str, Any]]:
    """1-pass exact Huffman MDL scan over all prefixes + symmetric top-N iterative bit-cost reparsing."""
    docs_all = list(docs_1) + list(docs_2)
    # Pass 1: fast exact token-min + canonical Huffman across every candidate prefix
    tm_rows: list[dict[str, Any]] = []
    for arm, chain in chain_entries_by_arm.items():
        root: dict[Any, Any] = {}
        at = 0
        raw_entries = [e[2] for e in chain]
        for sz in candidate_prefix_sizes(len(raw_entries), k_points, step):
            while at < sz:
                BE.insert_trie(root, raw_entries[at])
                at += 1
            p1, c1, t1 = BE.segment_corpus_tokens(docs_1, root)
            if p1 is None:
                continue
            p2, c2, t2 = BE.segment_corpus_tokens(docs_2, root)
            if p2 is None:
                continue
            stored = chain[sz - 1][1]
            syms = sz + 1
            c_all = Counter(c1)
            c_all.update(c2)
            la = BE.canonical_huffman_lengths(c_all)
            pay_a = math.ceil(BE.total_huffman_bits(c_all, la) / 8)
            lp = BE.canonical_huffman_lengths(c1)
            lj = BE.canonical_huffman_lengths(c2)
            pay_b = math.ceil(BE.total_huffman_bits(c1, lp) / 8) + math.ceil(BE.total_huffman_bits(c2, lj) / 8)
            tm_rows.append({
                'arm': arm,
                'entries': sz,
                'stored': stored,
                'tokens': t1 + t2,
                'tm_A': stored + syms + pay_a,
                'tm_B': stored + 2 * syms + ROUTING_BYTES + pay_b,
                '_entries': raw_entries[:sz],
            })

    # Select top `top_reparse` distinct prefixes per (K, layout) + token-minimal endpoint for reparsing
    want_a: set[str] = set()
    want_b: set[str] = set()
    by_hash: dict[str, dict[str, Any]] = {}
    for r in tm_rows:
        h = sha256_bytes(b'\x00'.join(r['_entries']))
        r['_hash'] = h
        by_hash.setdefault(h, r)

    for k in k_points:
        sub = [r for r in tm_rows if r['entries'] <= k]
        if not sub:
            continue
        tok_best = min(sub, key=lambda r: (r['tokens'], r['tm_A']))
        if 'A' in layouts:
            want_a.add(tok_best['_hash'])
            for r in sorted(sub, key=lambda r: (r['tm_A'], r['tokens']))[:top_reparse]:
                want_a.add(r['_hash'])
        if 'B' in layouts:
            want_b.add(tok_best['_hash'])
            for r in sorted(sub, key=lambda r: (r['tm_B'], r['tokens']))[:top_reparse]:
                want_b.add(r['_hash'])

    reparse_a_cache: dict[str, dict[str, Any]] = {}
    reparse_b_cache: dict[str, dict[str, Any]] = {}
    for h in want_a:
        pref = by_hash[h]['_entries']
        stored = by_hash[h]['stored']
        syms = len(pref) + 1
        opt_a = BE.optimize_byte_segmentation(docs_all, BE.build_trie(pref))
        if opt_a is not None:
            bma = opt_a['byte_min']
            reparse_a_cache[h] = {
                'dict_bytes': stored,
                'table_bytes': syms,
                'routing_bytes': 0,
                'payload_bytes': bma['payload_bytes'],
                'total_bytes': stored + syms + bma['payload_bytes'],
                'tokens': bma['tokens'],
            }
    for h in want_b:
        pref = by_hash[h]['_entries']
        stored = by_hash[h]['stored']
        syms = len(pref) + 1
        root = BE.build_trie(pref)
        opt1 = BE.optimize_byte_segmentation(docs_1, root)
        opt2 = BE.optimize_byte_segmentation(docs_2, root)
        if opt1 is not None and opt2 is not None:
            bm1 = opt1['byte_min']
            bm2 = opt2['byte_min']
            pay_b = bm1['payload_bytes'] + bm2['payload_bytes']
            reparse_b_cache[h] = {
                'dict_bytes': stored,
                'table_bytes': 2 * syms,
                'routing_bytes': ROUTING_BYTES,
                'payload_bytes': pay_b,
                'total_bytes': stored + 2 * syms + ROUTING_BYTES + pay_b,
                'tokens': bm1['tokens'] + bm2['tokens'],
            }

    out: list[dict[str, Any]] = []
    for r in tm_rows:
        h = r['_hash']
        item = dict(r)
        if h in reparse_a_cache:
            item['A'] = reparse_a_cache[h]
        if h in reparse_b_cache:
            item['B'] = reparse_b_cache[h]
        out.append(item)
    return out


def _score_single_lang_chains_symmetric(
    chain_entries_by_arm: dict[str, list[tuple[int, int, bytes]]],
    docs: Sequence[bytes],
    *,
    k_points: Sequence[int],
    step: int,
    top_reparse: int = DEFAULT_TOP_REPARSE,
) -> list[dict[str, Any]]:
    """1-pass exact Huffman scan + symmetric top-N Pareto iterative bit-cost reparsing."""
    tm_pts: list[dict[str, Any]] = []
    for arm, chain in chain_entries_by_arm.items():
        root: dict[Any, Any] = {}
        at = 0
        raw_entries = [e[2] for e in chain]
        for sz in candidate_prefix_sizes(len(raw_entries), k_points, step):
            while at < sz:
                BE.insert_trie(root, raw_entries[at])
                at += 1
            p0, c0, t0 = BE.segment_corpus_tokens(docs, root)
            if p0 is None:
                continue
            stored = chain[sz - 1][1]
            syms = sz + 1
            l0 = BE.canonical_huffman_lengths(c0)
            pay0 = math.ceil(BE.total_huffman_bits(c0, l0) / 8)
            pref = raw_entries[:sz]
            tm_pts.append({
                'arm': arm,
                'entries': sz,
                'stored': stored,
                'tm_tokens': t0,
                'tm_cost': stored + syms + pay0,
                '_entries': pref,
                '_hash': sha256_bytes(b'\x00'.join(pref)),
            })

    # Pareto prune token-min points by (entries, tm_cost), then select top_reparse per K + Pareto spread
    tm_pts.sort(key=lambda p: (p['entries'], p['tm_cost'], p['tm_tokens'], p['arm']))
    pareto_tm: list[dict[str, Any]] = []
    best_tm = 1 << 60
    for p in tm_pts:
        if p['tm_cost'] < best_tm:
            pareto_tm.append(p)
            best_tm = p['tm_cost']

    chosen_hashes: set[str] = set()
    by_hash = {p['_hash']: p for p in tm_pts}
    for k in k_points:
        sub = [p for p in tm_pts if p['entries'] < k]
        for p in sorted(sub, key=lambda x: (x['tm_cost'], x['entries']))[:top_reparse]:
            chosen_hashes.add(p['_hash'])
        sub_par = [p for p in pareto_tm if p['entries'] < k]
        for p in sub_par:
            chosen_hashes.add(p['_hash'])

    reparsed_pts: list[dict[str, Any]] = []
    for h in sorted(chosen_hashes):
        p = by_hash[h]
        pref = p['_entries']
        opt = BE.optimize_byte_segmentation(docs, BE.build_trie(pref))
        if opt is None:
            continue
        bm = opt['byte_min']
        stored = p['stored']
        syms = len(pref) + 1
        reparsed_pts.append({
            'arm': p['arm'],
            'entries': len(pref),
            'stored': stored,
            'table_bytes': syms,
            'payload_bytes': bm['payload_bytes'],
            'cost': stored + syms + bm['payload_bytes'],
            'tokens': bm['tokens'],
            '_entries': pref,
        })

    reparsed_pts.sort(key=lambda p: (p['entries'], p['cost'], p['tokens'], p['arm']))
    return reparsed_pts


def _best_separate_exhaustive(
    pts_1: Sequence[dict[str, Any]],
    pts_2: Sequence[dict[str, Any]],
    k_budget: int,
) -> tuple[dict[str, Any] | None, int]:
    best: tuple[Any, ...] | None = None
    pairs_checked = 0
    for p1 in pts_1:
        if p1['entries'] >= k_budget:
            continue
        rem = k_budget - p1['entries']
        for p2 in pts_2:
            if p2['entries'] > rem:
                break
            pairs_checked += 1
            tot = p1['cost'] + p2['cost'] + ROUTING_BYTES
            cand = (tot, p1['tokens'] + p2['tokens'], p1['arm'], p2['arm'], p1, p2)
            if best is None or cand[:4] < best[:4]:
                best = cand
    if best is None:
        return None, pairs_checked
    tot, toks, arm1, arm2, p1, p2 = best
    return {
        'layout': 'C',
        'total_bytes': tot,
        'dict_bytes': p1['stored'] + p2['stored'],
        'table_bytes': p1['table_bytes'] + p2['table_bytes'],
        'routing_bytes': ROUTING_BYTES,
        'payload_bytes': p1['payload_bytes'] + p2['payload_bytes'],
        'entries': p1['entries'] + p2['entries'],
        'lang1_entries': p1['entries'],
        'lang2_entries': p2['entries'],
        'lang1_arm': arm1,
        'lang2_arm': arm2,
        'tokens': toks,
        'reparsed_pairs_evaluated': pairs_checked,
        '_entries_1': p1['_entries'],
        '_entries_2': p2['_entries'],
    }, pairs_checked


def execute_single_choice(
    engine_bin: Path,
    docs_1: Sequence[bytes],
    docs_2: Sequence[bytes],
    *,
    layout: str,
    k_budget: int,
    arms: Sequence[str] = DEFAULT_ARMS,
    policy: str = 's1-whole',
    max_entry_len: int = 16,
    limit_seconds: float = 4.0,
    step: int = 64,
    top_reparse: int = DEFAULT_TOP_REPARSE,
    work_dir: Path,
) -> dict[str, Any]:
    """Execute ONLY the predicted `(layout, k_budget)` with zero cross-layout search."""
    work_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    n_arms = max(1, len(arms))

    if layout in ('A', 'B'):
        both_docs = list(docs_1) + list(docs_2)
        both_groups = list(range(len(docs_1))) + list(range(len(docs_2)))
        both_list = write_corpus_list(both_docs, work_dir, 'both', groups=both_groups)
        per_arm_limit = limit_seconds / n_arms
        chains: dict[str, list[tuple[int, int, bytes]]] = {}
        engine_sec = 0.0
        for arm in arms:
            cpath = work_dir / 'chains' / f'both-{arm}.txt'
            engine_sec += run_engine_arm(
                engine_bin, arm=arm, policy=policy, max_entry_len=max_entry_len,
                k_max=k_budget, limit_sec=per_arm_limit, list_file=both_list,
                out_chain=cpath, run_tag=f'pred-{layout}-K{k_budget}',
            )
            chains[arm] = read_chain_entries(cpath)

        if (work_dir / 'lang1.txt').exists() or (work_dir / 'lang2.txt').exists():
            raise AssertionError('cross-layout leakage detected in shared prediction execution')

        rows = _score_shared_chains_symmetric(
            chains, docs_1, docs_2, k_points=(k_budget,), step=step, layouts=(layout,), top_reparse=top_reparse,
        )
        usable = [r for r in rows if r['entries'] <= k_budget and layout in r]
        if not usable:
            return {'feasible': False, 'layout': layout, 'K': k_budget, 'elapsed_sec': round(time.perf_counter() - t0, 4)}
        best_r = min(usable, key=lambda r: (r[layout]['total_bytes'], r[layout]['tokens'], r['arm'], r['entries']))
        winner = {
            'layout': layout,
            'K': k_budget,
            'arm': best_r['arm'],
            'entries': best_r['entries'],
            **best_r[layout],
            '_entries': best_r['_entries'],
        }
        rt_ok = verify_exact_roundtrip_layout(layout, docs_1, docs_2, winner)
        return {
            'feasible': True,
            'allow_union_floor': False,
            'wall_budget_cap_sec': limit_seconds,
            'engine_elapsed_sec': round(engine_sec, 4),
            'elapsed_sec': round(time.perf_counter() - t0, 4),
            'roundtrip_verified': rt_ok,
            **{k: v for k, v in winner.items() if not k.startswith('_')},
        }

    if layout == 'C':
        list1 = write_corpus_list(docs_1, work_dir, 'lang1')
        list2 = write_corpus_list(docs_2, work_dir, 'lang2')
        per_lang_total_limit = limit_seconds / 2.0
        per_arm_limit = per_lang_total_limit / n_arms
        chains1: dict[str, list[tuple[int, int, bytes]]] = {}
        chains2: dict[str, list[tuple[int, int, bytes]]] = {}
        engine_sec = 0.0
        for arm in arms:
            c1 = work_dir / 'chains' / f'lang1-{arm}.txt'
            c2 = work_dir / 'chains' / f'lang2-{arm}.txt'
            engine_sec += run_engine_arm(
                engine_bin, arm=arm, policy=policy, max_entry_len=max_entry_len,
                k_max=k_budget, limit_sec=per_arm_limit, list_file=list1,
                out_chain=c1, run_tag=f'pred-C1-K{k_budget}',
            )
            engine_sec += run_engine_arm(
                engine_bin, arm=arm, policy=policy, max_entry_len=max_entry_len,
                k_max=k_budget, limit_sec=per_arm_limit, list_file=list2,
                out_chain=c2, run_tag=f'pred-C2-K{k_budget}',
            )
            chains1[arm] = read_chain_entries(c1)
            chains2[arm] = read_chain_entries(c2)

        if (work_dir / 'both.txt').exists():
            raise AssertionError('cross-layout leakage detected in Design C prediction execution')

        pts1 = _score_single_lang_chains_symmetric(chains1, docs_1, k_points=(k_budget,), step=step, top_reparse=top_reparse)
        pts2 = _score_single_lang_chains_symmetric(chains2, docs_2, k_points=(k_budget,), step=step, top_reparse=top_reparse)
        winner_c, pairs_checked = _best_separate_exhaustive(pts1, pts2, k_budget)
        if winner_c is None:
            return {'feasible': False, 'layout': 'C', 'K': k_budget, 'reparsed_pairs_evaluated': pairs_checked, 'elapsed_sec': round(time.perf_counter() - t0, 4)}
        rt_ok = verify_exact_roundtrip_layout('C', docs_1, docs_2, winner_c)
        return {
            'feasible': True,
            'allow_union_floor': False,
            'wall_budget_cap_sec': limit_seconds,
            'lang1_wall_cap_sec': per_lang_total_limit,
            'lang2_wall_cap_sec': per_lang_total_limit,
            'engine_elapsed_sec': round(engine_sec, 4),
            'elapsed_sec': round(time.perf_counter() - t0, 4),
            'roundtrip_verified': rt_ok,
            'K': k_budget,
            **{k: v for k, v in winner_c.items() if not k.startswith('_')},
        }

    raise ValueError(f'unsupported layout: {layout}')


def evaluate_equal_budget_oracle(
    engine_bin: Path,
    docs_1: Sequence[bytes],
    docs_2: Sequence[bytes],
    *,
    k_grid: Sequence[int] = DEFAULT_K_GRID,
    arms: Sequence[str] = DEFAULT_ARMS,
    policy: str = 's1-whole',
    max_entry_len: int = 16,
    limit_seconds: float = 4.0,
    step: int = 64,
    top_reparse: int = DEFAULT_TOP_REPARSE,
    work_dir: Path,
) -> dict[str, Any]:
    """Evaluate all `(layout in {'A','B','C'}, K in k_grid)` + token-min full-budget baseline."""
    work_dir.mkdir(parents=True, exist_ok=True)
    t0_grid = time.perf_counter()
    k_max = max(k_grid)
    n_arms = max(1, len(arms))

    # 1. Shared (`both`) search with total cap `limit_seconds` (NO union floor)
    t_shared0 = time.perf_counter()
    both_docs = list(docs_1) + list(docs_2)
    both_groups = list(range(len(docs_1))) + list(range(len(docs_2)))
    both_list = write_corpus_list(both_docs, work_dir, 'oracle_both', groups=both_groups)
    shared_per_arm_limit = limit_seconds / n_arms
    shared_chains: dict[str, list[tuple[int, int, bytes]]] = {}
    for arm in arms:
        cpath = work_dir / 'chains' / f'both-{arm}.txt'
        run_engine_arm(
            engine_bin, arm=arm, policy=policy, max_entry_len=max_entry_len,
            k_max=k_max, limit_sec=shared_per_arm_limit, list_file=both_list,
            out_chain=cpath, run_tag='oracle-both',
        )
        shared_chains[arm] = read_chain_entries(cpath)
    shared_rows = _score_shared_chains_symmetric(
        shared_chains, docs_1, docs_2, k_points=k_grid, step=step, layouts=('A', 'B'), top_reparse=top_reparse,
    )
    shared_total_sec = time.perf_counter() - t_shared0

    # 2. Separate (`lang1` + `lang2`) search with total cap `limit_seconds / 2 + limit_seconds / 2 == limit_seconds`
    t_sep0 = time.perf_counter()
    list1 = write_corpus_list(docs_1, work_dir, 'oracle_lang1')
    list2 = write_corpus_list(docs_2, work_dir, 'oracle_lang2')
    sep_per_lang_limit = limit_seconds / 2.0
    sep_per_arm_limit = sep_per_lang_limit / n_arms
    chains1: dict[str, list[tuple[int, int, bytes]]] = {}
    chains2: dict[str, list[tuple[int, int, bytes]]] = {}
    for arm in arms:
        c1 = work_dir / 'chains' / f'lang1-{arm}.txt'
        c2 = work_dir / 'chains' / f'lang2-{arm}.txt'
        run_engine_arm(
            engine_bin, arm=arm, policy=policy, max_entry_len=max_entry_len,
            k_max=k_max, limit_sec=sep_per_arm_limit, list_file=list1,
            out_chain=c1, run_tag='oracle-lang1',
        )
        run_engine_arm(
            engine_bin, arm=arm, policy=policy, max_entry_len=max_entry_len,
            k_max=k_max, limit_sec=sep_per_arm_limit, list_file=list2,
            out_chain=c2, run_tag='oracle-lang2',
        )
        chains1[arm] = read_chain_entries(c1)
        chains2[arm] = read_chain_entries(c2)

    pts1 = _score_single_lang_chains_symmetric(chains1, docs_1, k_points=k_grid, step=step, top_reparse=top_reparse)
    pts2 = _score_single_lang_chains_symmetric(chains2, docs_2, k_points=k_grid, step=step, top_reparse=top_reparse)
    sep_total_sec = time.perf_counter() - t_sep0

    cells: list[dict[str, Any]] = []
    best_overall: dict[str, Any] | None = None
    best_overall_raw: dict[str, Any] | None = None

    for k in sorted(k_grid):
        usable_shared = [r for r in shared_rows if r['entries'] <= k]
        for layout in ('A', 'B'):
            feas = [r for r in usable_shared if layout in r]
            if not feas:
                cells.append({'layout': layout, 'K': k, 'feasible': False})
                continue
            win = min(feas, key=lambda r: (r[layout]['total_bytes'], r[layout]['tokens'], r['arm'], r['entries']))
            tok_best = min(feas, key=lambda r: (r['tokens'], r[layout]['total_bytes']))
            cell = {
                'layout': layout,
                'K': k,
                'feasible': True,
                'arm': win['arm'],
                'entries': win['entries'],
                'token_min_stop_total_bytes': tok_best[layout]['total_bytes'],
                **win[layout],
            }
            cells.append(cell)
            if best_overall is None or (cell['total_bytes'], cell['K']) < (best_overall['total_bytes'], best_overall['K']):
                best_overall = cell
                best_overall_raw = {**cell, '_entries': win['_entries']}

        win_c, pairs_cnt = _best_separate_exhaustive(pts1, pts2, k)
        if win_c is None:
            cells.append({'layout': 'C', 'K': k, 'feasible': False, 'reparsed_pairs_evaluated': pairs_cnt})
        else:
            cell_c = {
                'layout': 'C',
                'K': k,
                'feasible': True,
                **{ck: cv for ck, cv in win_c.items() if not ck.startswith('_')},
            }
            cells.append(cell_c)
            if best_overall is None or (cell_c['total_bytes'], cell_c['K']) < (best_overall['total_bytes'], best_overall['K']):
                best_overall = cell_c
                best_overall_raw = win_c

    if best_overall is None or best_overall_raw is None:
        raise RuntimeError('no feasible cell found in oracle grid')

    oracle_rt = verify_exact_roundtrip_layout(best_overall['layout'], docs_1, docs_2, best_overall_raw)
    grid_sec = time.perf_counter() - t0_grid
    return {
        'allow_union_floor': False,
        'shared_wall_cap_sec': limit_seconds,
        'separate_wall_cap_sec': limit_seconds,
        'separate_lang1_cap_sec': sep_per_lang_limit,
        'separate_lang2_cap_sec': sep_per_lang_limit,
        'shared_elapsed_sec': round(shared_total_sec, 4),
        'separate_elapsed_sec': round(sep_total_sec, 4),
        'full_grid_elapsed_sec': round(grid_sec, 4),
        'oracle_winner': best_overall,
        'oracle_roundtrip_verified': oracle_rt,
        'cells': cells,
    }


def evaluate_presearch_vs_oracle(
    docs_1: Sequence[bytes],
    docs_2: Sequence[bytes],
    *,
    label: str = 'unnamed_pair',
    k_grid: Sequence[int] = DEFAULT_K_GRID,
    arms: Sequence[str] = DEFAULT_ARMS,
    policy: str = 's1-whole',
    max_entry_len: int = 16,
    limit_seconds: float = 4.0,
    step: int = 64,
    top_reparse: int = DEFAULT_TOP_REPARSE,
) -> dict[str, Any]:
    """Run frozen raw predictor, isolated predicted search, equal-budget oracle, and decoupled baselines."""
    with tempfile.TemporaryDirectory(prefix='bits-rung2-') as tmp:
        tmp_path = Path(tmp)
        engine_bin = compile_engine(tmp_path / 'build')

        pred = predict_presearch(docs_1, docs_2, k_grid=k_grid, max_entry_len=max_entry_len)
        if not pred['feasible']:
            return {'label': label, 'feasible': False, 'prediction': pred}

        pred_exec = execute_single_choice(
            engine_bin, docs_1, docs_2,
            layout=str(pred['layout_hat']),
            k_budget=int(pred['K_hat']),
            arms=arms,
            policy=policy,
            max_entry_len=max_entry_len,
            limit_seconds=limit_seconds,
            step=step,
            top_reparse=top_reparse,
            work_dir=tmp_path / 'predicted_only',
        )
        oracle = evaluate_equal_budget_oracle(
            engine_bin, docs_1, docs_2,
            k_grid=k_grid,
            arms=arms,
            policy=policy,
            max_entry_len=max_entry_len,
            limit_seconds=limit_seconds,
            step=step,
            top_reparse=top_reparse,
            work_dir=tmp_path / 'equal_budget_oracle',
        )

    oracle_win = oracle['oracle_winner']
    k_max = max(k_grid)
    pred_layout = str(pred['layout_hat'])
    pred_k = int(pred['K_hat'])

    def find_cell(layout_name: str, k_val: int) -> dict[str, Any] | None:
        return next(
            (c for c in oracle['cells'] if c.get('feasible') and c['layout'] == layout_name and c['K'] == k_val),
            None,
        )

    # 1. Default baseline: "always pick shared dictionary + separate tables (Design B)" with MDL byte stopping
    default_b_cell = find_cell('B', k_max)
    default_b_bytes = int(default_b_cell['total_bytes']) if default_b_cell else None
    oracle_bytes = int(oracle_win['total_bytes'])
    default_b_loss_bytes = (default_b_bytes - oracle_bytes) if default_b_bytes is not None else None
    default_b_loss_pct = round(100.0 * default_b_loss_bytes / oracle_bytes, 4) if default_b_loss_bytes is not None else None
    default_b_misses_gt_1pct = bool(default_b_loss_pct is not None and default_b_loss_pct > 1.0)

    # 2. Decoupled Layout Score (holding MDL byte-cost stopping fixed at K_max)
    pred_layout_kmax_cell = find_cell(pred_layout, k_max)
    pred_layout_kmax_bytes = int(pred_layout_kmax_cell['total_bytes']) if pred_layout_kmax_cell else int(pred_exec['total_bytes'])
    layout_regret_bytes = pred_layout_kmax_bytes - oracle_bytes
    layout_gain_over_default_b = (default_b_bytes - pred_layout_kmax_bytes) if default_b_bytes is not None else None

    # 3. Decoupled Stopping-Size Score (holding layout fixed at pred_layout: token-min fill vs MDL stop vs K_hat truncation)
    pred_exec_bytes = int(pred_exec['total_bytes'])
    tok_fill_kmax_bytes = pred_layout_kmax_cell.get('token_min_stop_total_bytes') if pred_layout_kmax_cell else None
    mdl_gain_over_tok_fill = (
        int(tok_fill_kmax_bytes) - pred_layout_kmax_bytes
        if tok_fill_kmax_bytes is not None else None
    )
    k_hat_truncation_cost = pred_exec_bytes - pred_layout_kmax_bytes

    # 4. Naive 1-byte MI & uncorrected plug-in MI ablations
    naive = pred['naive_byte_mi_baseline']
    naive_cell = find_cell(str(naive['layout_hat']), int(naive['K_hat'])) if naive.get('feasible') else None
    naive_bytes_lost = (int(naive_cell['total_bytes']) - oracle_bytes) if naive_cell else None

    plug_in = pred['plug_in_no_mm_baseline']
    plug_cell = find_cell(str(plug_in['layout_hat']), int(plug_in['K_hat']))
    plug_bytes_lost = (int(plug_cell['total_bytes']) - oracle_bytes) if plug_cell else None

    pred_total_sec = (float(pred['predictor_elapsed_ms']) / 1000.0) + float(pred_exec['elapsed_sec'])
    grid_sec = float(oracle['full_grid_elapsed_sec'])
    single_layout_kmax_sec = float(oracle['shared_elapsed_sec']) if pred_layout in ('A', 'B') else float(oracle['separate_elapsed_sec'])
    bytes_lost = pred_exec_bytes - oracle_bytes
    pct_regret = round(100.0 * bytes_lost / oracle_bytes, 4)

    return {
        'schema': 'bits-rung2-presearch-eval/v2',
        'label': label,
        'hypothesis_status': 'empirical_evaluation',
        'raw_bytes_total': int(pred['features']['N_total']),
        'prediction': {
            'rule_version': pred['rule_version'],
            'layout_hat': pred_layout,
            'K_hat': pred_k,
            'predictor_elapsed_ms': pred['predictor_elapsed_ms'],
            'executed_total_bytes': pred_exec_bytes,
            'executed_elapsed_sec': round(pred_total_sec, 4),
            'roundtrip_verified': pred_exec['roundtrip_verified'],
        },
        'decoupled_layout_score': {
            'oracle_layout': oracle_win['layout'],
            'predicted_layout': pred_layout,
            'default_always_B_mdl_bytes': default_b_bytes,
            'default_always_B_loss_bytes': default_b_loss_bytes,
            'default_always_B_loss_pct': default_b_loss_pct,
            'default_B_misses_gt_1pct': default_b_misses_gt_1pct,
            'predicted_layout_mdl_kmax_bytes': pred_layout_kmax_bytes,
            'layout_regret_vs_oracle_bytes': layout_regret_bytes,
            'layout_gain_over_default_B_bytes': layout_gain_over_default_b,
            'beats_default_B': bool(layout_gain_over_default_b is not None and layout_gain_over_default_b > 0),
        },
        'decoupled_stopping_score': {
            'layout_held_fixed': pred_layout,
            'token_min_fill_kmax_bytes': tok_fill_kmax_bytes,
            'mdl_byte_stop_kmax_bytes': pred_layout_kmax_bytes,
            'presearch_k_hat_mdl_bytes': pred_exec_bytes,
            'ordinary_mdl_stopping_saving_bytes': mdl_gain_over_tok_fill,
            'k_hat_presearch_truncation_cost_bytes': k_hat_truncation_cost,
            'search_seconds_saved_vs_single_layout_kmax': round(single_layout_kmax_sec - pred_total_sec, 4),
        },
        'ablations': {
            'naive_1byte_mi': {
                **naive,
                'bytes_lost_vs_oracle': naive_bytes_lost,
            },
            'plug_in_mi_without_miller_madow': {
                **plug_in,
                'bytes_lost_vs_oracle': plug_bytes_lost,
            },
        },
        'oracle': {
            'best_layout': oracle_win['layout'],
            'best_K': oracle_win['K'],
            'best_total_bytes': oracle_bytes,
            'full_grid_elapsed_sec': grid_sec,
            'shared_elapsed_sec': oracle['shared_elapsed_sec'],
            'separate_elapsed_sec': oracle['separate_elapsed_sec'],
            'shared_wall_cap_sec': oracle['shared_wall_cap_sec'],
            'separate_wall_cap_sec': oracle['separate_wall_cap_sec'],
            'allow_union_floor': oracle['allow_union_floor'],
            'roundtrip_verified': oracle['oracle_roundtrip_verified'],
        },
        'metrics': {
            'bytes_lost': bytes_lost,
            'pct_regret': pct_regret,
            'picked_exact_layout': pred_layout == oracle_win['layout'],
            'picked_within_1pct_materiality': abs(pct_regret) < 1.0,
            'search_seconds_saved_vs_grid': round(grid_sec - pred_total_sec, 4),
            'search_speedup_vs_grid': round(grid_sec / max(1e-6, pred_total_sec), 2),
        },
        'oracle_cells': oracle['cells'],
    }


def _load_dir_docs(dir_path: Path, max_files: int | None = None) -> list[bytes]:
    files = sorted(p for p in dir_path.rglob('*') if p.is_file())
    if max_files is not None:
        files = files[:max_files]
    if not files:
        raise ValueError(f'no files found in {dir_path}')
    return [p.read_bytes() for p in files]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--codenet-split', choices=('primary', 'secondary'), default=None)
    parser.add_argument('--n-pairs', type=int, default=50)
    parser.add_argument('--dir1', type=Path, default=None)
    parser.add_argument('--dir2', type=Path, default=None)
    parser.add_argument('--max-files', type=int, default=None)
    parser.add_argument('--label', default='pair-eval')
    parser.add_argument('--k-grid', default='256,512,1024,2048,4096')
    parser.add_argument('--arms', default=','.join(DEFAULT_ARMS))
    parser.add_argument('--limit-seconds', type=float, default=4.0)
    parser.add_argument('--step', type=int, default=64)
    args = parser.parse_args()

    k_grid = tuple(int(x.strip()) for x in args.k_grid.split(',') if x.strip())
    arms = tuple(x.strip() for x in args.arms.split(',') if x.strip())

    if args.codenet_split:
        manifest = json.loads((CODENET_DIR / 'manifest.json').read_text(encoding='utf-8'))
        pairs = manifest['splits'][args.codenet_split]['pairs'][: args.n_pairs]
        docs_1 = [(CODENET_DIR / p['python']['path']).read_bytes() for p in pairs]
        docs_2 = [(CODENET_DIR / p['javascript']['path']).read_bytes() for p in pairs]
        label = f'codenet-{args.codenet_split}-np{len(pairs)}'
    elif args.dir1 and args.dir2:
        docs_1 = _load_dir_docs(args.dir1, args.max_files)
        docs_2 = _load_dir_docs(args.dir2, args.max_files)
        label = args.label
    else:
        parser.error('specify either --codenet-split or both --dir1 and --dir2')
        return

    res = evaluate_presearch_vs_oracle(
        docs_1, docs_2,
        label=label,
        k_grid=k_grid,
        arms=arms,
        limit_seconds=args.limit_seconds,
        step=args.step,
    )
    print(json.dumps(res, indent=2))


if __name__ == '__main__':
    main()
