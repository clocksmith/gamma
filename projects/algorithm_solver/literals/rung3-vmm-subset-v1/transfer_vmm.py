#!/usr/bin/env python3
"""De-Cannibalized Pooled-Substring Revival & Leave-One-Document-Out Transfer VMM (`transfer_vmm.py`).

Resolves two structural failure modes discovered in one-shot in-sample VMM (`vmm_subset_polish.py`):

  1. Superstring-Substring Nash Lock-In (`revival=True` vs `False`):
     Suppose core substring `u` (`"function "`, 13 occurrences) is covered 12 times by 6 distinct
     superstrings `v_0..v_5` (`"function call_k("`, 2 occurrences each), leaving `n^(0)(u) = 1`.
     - Against 16 single bytes (~80 bits/occ), each `v_k` (`4 + 152/2 = 80` bits/occ) barely breaks
       even, locking in `6 * 19 = 114 B` of headers.
     - Standard VMM prices `u` at its cannibalized count `n^(0)(u) = 1` (`6 + 96/1 = 102` bits/occ),
       so NO `v_k` steps aside for `u`; `u` dies and all 6 `v_k` stay locked in (`255 B` vs `192 B`).
     -> Pooled-Substring De-Cannibalization (`revival=True`) computes exact pooled support across
        active superstrings `v supset u` via per-document bitmasks:
          c_pool_s(u) = c_s(u) + sum_{v supset u} c_s(v),
          df_pool(u)  = popcount(doc_mask(u) | OR_{v supset u} doc_mask(v)),
        runs de-cannibalized shortest-path passes so unamortized superstrings yield to `u`, polishes
        with exact standard (`beta = 1`) VMM on realized counts, and keeps the strict realized
        objective minimum (`objective_bits(revival=True) <= objective_bits(revival=False)` guaranteed).

  2. Single-Document Memorization / OOV Kraft Tax (`shrinkage='loo_doc'` vs `'none'`):
     On disjoint held-out documents, entries `w` with active document frequency `df(w) = 1` have
     zero leave-one-document-out transfer expectation (`alpha_LOO(w) = (df(w) - 1) / df(w) = 0`),
     yet pay full dictionary + table header bytes AND steal Laplace-smoothed Huffman Kraft mass.
     -> Minimizes the self-consistent Leave-One-Document-Out two-part risk:
          B_hat_LOO(D', P, ell) = sum_{w in D' \\ Sigma} H(w) * (df(w) / (df(w) - 1)) + sum_s n_s(w) ell_s(w)
        (with `df(w) <= 1` assigned `+inf`).
"""
from __future__ import annotations

import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
CODENET_DIR = HERE.parent / 'codenet-replication-v1'
sys.path.insert(0, str(CODENET_DIR))
sys.path.insert(0, str(HERE))

import byte_encode as BE  # noqa: E402
from vmm_subset_polish import polish_to_certified_nash_single  # noqa: E402


def popcount(x: int) -> int:
    return bin(x).count('1')


def raw_corpus_doc_freq(docs: Sequence[bytes], entries: Sequence[bytes]) -> dict[bytes, int]:
    """Count in how many distinct training documents each byte-string `e` occurs as a substring."""
    df: dict[bytes, int] = {}
    for e in entries:
        if len(e) <= 1:
            df[e] = len(docs)
        else:
            df[e] = sum(1 for d in docs if e in d)
    return df


def build_superstring_map(multibyte_entries: Sequence[bytes]) -> dict[bytes, list[bytes]]:
    """Map each substring `u` to all proper superstrings `v in multibyte_entries` (`u != v`, `u in v`)."""
    by_bytes = set(multibyte_entries)
    sup_map: dict[bytes, list[bytes]] = {}
    for v in multibyte_entries:
        L = len(v)
        seen_sub: set[bytes] = set()
        for i in range(L):
            for j in range(i + 2, L + 1):
                if i == 0 and j == L:
                    continue
                frag = v[i:j]
                if frag in by_bytes and frag not in seen_sub:
                    seen_sub.add(frag)
                    sup_map.setdefault(frag, []).append(v)
    return sup_map


def active_parse_doc_masks(
    pieces_list_1: Sequence[Sequence[bytes]],
    pieces_list_2: Sequence[Sequence[bytes]],
) -> dict[bytes, int]:
    """Build exact per-symbol document bitmask across `docs_1 + docs_2`."""
    masks: dict[bytes, int] = {}
    doc_idx = 0
    for seq in (pieces_list_1, pieces_list_2):
        for p in seq:
            bit = 1 << doc_idx
            for sym in set(p):
                masks[sym] = masks.get(sym, 0) | bit
            doc_idx += 1
    return masks


def compute_loo_objective_bits(
    entries: Sequence[bytes],
    req_singles: set[bytes],
    payload_bits_total: int,
    doc_masks: dict[bytes, int],
    n_tables: int,
    shrinkage: str,
) -> float:
    hdr_bits_total = 0.0
    for e in entries:
        h_bits = 8.0 * (1 + len(e) + n_tables)
        if e in req_singles or shrinkage == 'none':
            hdr_bits_total += h_bits
        else:
            d = popcount(doc_masks.get(e, 0))
            if d <= 1:
                return float('inf')
            hdr_bits_total += h_bits * (float(d) / float(d - 1))
    routing_bits = 32.0 if n_tables == 2 else 0.0
    return hdr_bits_total + routing_bits + float(payload_bits_total)


def transfer_variational_mm(
    docs_1: Sequence[bytes],
    docs_2: Sequence[bytes],
    seed_entries: Sequence[bytes],
    *,
    n_tables: int = 2,
    revival: bool = True,
    shrinkage: str = 'loo_doc',
    max_mm_iters: int = 15,
    decan_passes: int = 2,
) -> dict[str, Any]:
    """2x2 configurable Variational Two-Part MM selector (`revival` x `shrinkage`)."""
    if n_tables not in (1, 2):
        raise ValueError('n_tables must be 1 or 2')
    if shrinkage not in ('none', 'loo_doc'):
        raise ValueError("shrinkage must be 'none' or 'loo_doc'")

    all_docs = list(docs_1) + list(docs_2)
    req_singles = {bytes([b]) for d in all_docs for b in d}

    seen: set[bytes] = set()
    universe: list[bytes] = []
    for e in list(sorted(req_singles)) + list(seed_entries):
        if e not in seen:
            seen.add(e)
            universe.append(e)

    if shrinkage == 'loo_doc':
        raw_df = raw_corpus_doc_freq(all_docs, universe)
        universe = [e for e in universe if (e in req_singles) or raw_df.get(e, 0) >= 2]

    multibyte_universe = [e for e in universe if e not in req_singles]
    sup_map = build_superstring_map(multibyte_universe) if revival else {}
    universe_order = {e: idx for idx, e in enumerate(universe)}

    def eval_nash_state(ents: Sequence[bytes], ic1: Counter | None = None, ic2: Counter | None = None) -> dict[str, Any]:
        if n_tables == 1:
            p = polish_to_certified_nash_single(
                all_docs, ents, ic1, prune_dead_multibyte=True, required_singles=req_singles,
            )
            kept = list(p['entries'])
            dmasks = active_parse_doc_masks(p['pieces'], ())
            if shrinkage == 'loo_doc':
                while True:
                    under = [e for e in kept if (e not in req_singles) and popcount(dmasks.get(e, 0)) <= 1]
                    if not under:
                        break
                    drop_set = set(under)
                    kept = [e for e in kept if e not in drop_set]
                    p = polish_to_certified_nash_single(
                        all_docs, kept, None, prune_dead_multibyte=True, required_singles=req_singles,
                    )
                    kept = list(p['entries'])
                    dmasks = active_parse_doc_masks(p['pieces'], ())
            obj_bits = compute_loo_objective_bits(kept, req_singles, p['payload_bits'], dmasks, 1, shrinkage)
            return {
                'entries': kept,
                'stream_single': p,
                'doc_masks': dmasks,
                'total_archive_bytes': p['total_archive_bytes'],
                'objective_bits': obj_bits,
                'is_certified_nash_fixed_point': p['certificate']['is_certified_nash_fixed_point'],
            }

        p1 = polish_to_certified_nash_single(docs_1, ents, ic1, prune_dead_multibyte=False)
        p2 = polish_to_certified_nash_single(docs_2, ents, ic2, prune_dead_multibyte=False)
        kept = [
            e for e in ents
            if (e in req_singles) or p1['lengths'].get(e, 0) > 0 or p2['lengths'].get(e, 0) > 0
        ]
        if len(kept) < len(ents):
            p1 = polish_to_certified_nash_single(docs_1, kept, p1['counts'], prune_dead_multibyte=False)
            p2 = polish_to_certified_nash_single(docs_2, kept, p2['counts'], prune_dead_multibyte=False)
        dmasks = active_parse_doc_masks(p1['pieces'], p2['pieces'])

        if shrinkage == 'loo_doc':
            while True:
                under = [e for e in kept if (e not in req_singles) and popcount(dmasks.get(e, 0)) <= 1]
                if not under:
                    break
                drop_set = set(under)
                kept = [e for e in kept if e not in drop_set]
                p1 = polish_to_certified_nash_single(docs_1, kept, None, prune_dead_multibyte=False)
                p2 = polish_to_certified_nash_single(docs_2, kept, None, prune_dead_multibyte=False)
                kept = [
                    e for e in kept
                    if (e in req_singles) or p1['lengths'].get(e, 0) > 0 or p2['lengths'].get(e, 0) > 0
                ]
                dmasks = active_parse_doc_masks(p1['pieces'], p2['pieces'])

        dict_b = sum(1 + len(e) for e in kept)
        tbl_b = 2 * (len(kept) + 1)
        tot_b = dict_b + tbl_b + 4 + p1['payload_bytes'] + p2['payload_bytes']
        pay_bits = p1['payload_bits'] + p2['payload_bits']
        obj_bits = compute_loo_objective_bits(kept, req_singles, pay_bits, dmasks, 2, shrinkage)
        return {
            'entries': kept,
            'stream1': p1,
            'stream2': p2,
            'doc_masks': dmasks,
            'dict_bytes': dict_b,
            'table_bytes': tbl_b,
            'routing_bytes': 4,
            'payload_bytes': p1['payload_bytes'] + p2['payload_bytes'],
            'total_archive_bytes': tot_b,
            'objective_bits': obj_bits,
            'is_certified_nash_fixed_point': (
                p1['certificate']['is_certified_nash_fixed_point']
                and p2['certificate']['is_certified_nash_fixed_point']
            ),
        }

    def run_exact_realized_vmm(init_state: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        best = init_state
        cur_ents = list(best['entries'])
        tr = []
        for it in range(1, max_mm_iters + 1):
            dmasks = best['doc_masks']
            if n_tables == 1:
                ps = best['stream_single']
                counts, lengths = ps['counts'], ps['lengths']
                max_l = max(lengths.values()) + 2
                eff: dict[bytes, float] = {}
                for e in cur_ents:
                    c = counts.get(e, 0)
                    if e in req_singles:
                        eff[e] = float(lengths.get(e, max_l))
                    elif c > 0:
                        h_bits = 8.0 * (1 + len(e) + 1)
                        if shrinkage == 'loo_doc':
                            d = popcount(dmasks.get(e, 0))
                            if d <= 1:
                                eff[e] = 1e9
                                continue
                            h_bits *= float(d) / float(d - 1)
                        eff[e] = float(lengths.get(e, max_l)) + h_bits / float(c)
                    else:
                        eff[e] = 1e9
                _, nc1, _ = BE.segment_corpus_bits(all_docs, BE.build_trie(cur_ents), eff, 1e9)
                cand = [e for e in cur_ents if (e in req_singles) or nc1.get(e, 0) > 0]
                nxt = eval_nash_state(cand, nc1, None)
            else:
                c1, c2 = best['stream1']['counts'], best['stream2']['counts']
                l1, l2 = best['stream1']['lengths'], best['stream2']['lengths']
                max1, max2 = max(l1.values()) + 2, max(l2.values()) + 2
                eff1, eff2 = {}, {}
                for e in cur_ents:
                    tot_c = c1.get(e, 0) + c2.get(e, 0)
                    if e in req_singles:
                        eff1[e] = float(l1.get(e, max1))
                        eff2[e] = float(l2.get(e, max2))
                    elif tot_c > 0:
                        h_bits = 8.0 * (1 + len(e) + 2)
                        if shrinkage == 'loo_doc':
                            d = popcount(dmasks.get(e, 0))
                            if d <= 1:
                                eff1[e] = 1e9
                                eff2[e] = 1e9
                                continue
                            h_bits *= float(d) / float(d - 1)
                        sur = h_bits / float(tot_c)
                        eff1[e] = float(l1.get(e, max1)) + sur
                        eff2[e] = float(l2.get(e, max2)) + sur
                    else:
                        eff1[e] = 1e9
                        eff2[e] = 1e9
                trie = BE.build_trie(cur_ents)
                _, nc1, _ = BE.segment_corpus_bits(docs_1, trie, eff1, 1e9)
                _, nc2, _ = BE.segment_corpus_bits(docs_2, trie, eff2, 1e9)
                cand = [e for e in cur_ents if (e in req_singles) or (nc1.get(e, 0) + nc2.get(e, 0)) > 0]
                nxt = eval_nash_state(cand, nc1, nc2)

            tr.append({
                'phase': 'realized_vmm',
                'iter': it,
                'entries': len(nxt['entries']),
                'total_archive_bytes': nxt['total_archive_bytes'],
                'objective_bits': round(nxt['objective_bits'], 2),
            })
            if nxt['objective_bits'] < best['objective_bits'] - 1e-6:
                best = nxt
                cur_ents = list(nxt['entries'])
            else:
                break
        return best, tr

    init_state = eval_nash_state(universe)
    best_std, trace_std = run_exact_realized_vmm(init_state)

    if not revival:
        best_std['trace'] = [{'phase': 'init', 'entries': len(init_state['entries']), 'total_archive_bytes': init_state['total_archive_bytes']}] + trace_std
        best_std['revival'] = False
        best_std['shrinkage'] = shrinkage
        best_std['n_tables'] = n_tables
        best_std['revived_substrings_used'] = 0
        return best_std

    # Branch B (`revival=True`): Pooled-Substring De-Cannibalization from `init_state` -> exact realized VMM!
    cur_decan = init_state
    decan_trace = []
    revived_count_total = 0

    for dp_idx in range(1, decan_passes + 1):
        active_set = set(cur_decan['entries'])
        dmasks = cur_decan['doc_masks']

        # Include all active entries PLUS any universe substring `u` that has an active superstring `v in active_set`
        decan_candidates: list[bytes] = []
        for e in universe:
            if e in active_set:
                decan_candidates.append(e)
            elif any(v in active_set for v in sup_map.get(e, ())):
                decan_candidates.append(e)

        if n_tables == 1:
            ps = cur_decan['stream_single']
            counts, lengths = ps['counts'], ps['lengths']
            tot_tok = max(1, sum(counts.values()))
            max_l = max(lengths.values()) + 2
            eff_d: dict[bytes, float] = {}
            for e in decan_candidates:
                if e in req_singles:
                    eff_d[e] = float(lengths.get(e, max_l))
                    continue
                active_sups = [v for v in sup_map.get(e, ()) if v in active_set]
                c_pool = counts.get(e, 0) + sum(counts.get(v, 0) for v in active_sups)
                if c_pool <= 0:
                    eff_d[e] = 1e9
                    continue
                pmask = dmasks.get(e, 0)
                for v in active_sups:
                    pmask |= dmasks.get(v, 0)
                h_bits = 8.0 * (1 + len(e) + 1)
                if shrinkage == 'loo_doc':
                    d = popcount(pmask)
                    if d <= 1:
                        eff_d[e] = 1e9
                        continue
                    h_bits *= float(d) / float(d - 1)
                l_est = float(lengths[e]) if (e in lengths and not active_sups) else min(
                    float(lengths.get(e, max_l)),
                    max(1.0, -math.log2(float(c_pool) / float(tot_tok))),
                )
                eff_d[e] = l_est + h_bits / float(c_pool)

            _, nc1, _ = BE.segment_corpus_bits(all_docs, BE.build_trie(decan_candidates), eff_d, 1e9)
            survived = [e for e in decan_candidates if (e in req_singles) or nc1.get(e, 0) > 0]
            rev_now = sum(1 for e in survived if e not in active_set)
            revived_count_total += rev_now
            nxt_decan = eval_nash_state(survived, nc1, None)
        else:
            c1, c2 = cur_decan['stream1']['counts'], cur_decan['stream2']['counts']
            l1, l2 = cur_decan['stream1']['lengths'], cur_decan['stream2']['lengths']
            tot1, tot2 = max(1, sum(c1.values())), max(1, sum(c2.values()))
            max1, max2 = max(l1.values()) + 2, max(l2.values()) + 2
            eff1_d, eff2_d = {}, {}
            for e in decan_candidates:
                if e in req_singles:
                    eff1_d[e] = float(l1.get(e, max1))
                    eff2_d[e] = float(l2.get(e, max2))
                    continue
                active_sups = [v for v in sup_map.get(e, ()) if v in active_set]
                cp1 = c1.get(e, 0) + sum(c1.get(v, 0) for v in active_sups)
                cp2 = c2.get(e, 0) + sum(c2.get(v, 0) for v in active_sups)
                cp_tot = cp1 + cp2
                if cp_tot <= 0:
                    eff1_d[e] = 1e9
                    eff2_d[e] = 1e9
                    continue
                pmask = dmasks.get(e, 0)
                for v in active_sups:
                    pmask |= dmasks.get(v, 0)
                h_bits = 8.0 * (1 + len(e) + 2)
                if shrinkage == 'loo_doc':
                    d = popcount(pmask)
                    if d <= 1:
                        eff1_d[e] = 1e9
                        eff2_d[e] = 1e9
                        continue
                    h_bits *= float(d) / float(d - 1)
                sur = h_bits / float(cp_tot)
                l1_est = float(l1[e]) if (e in l1 and not active_sups) else min(
                    float(l1.get(e, max1)),
                    max(1.0, -math.log2(max(1.0, float(cp1)) / float(tot1))),
                )
                l2_est = float(l2[e]) if (e in l2 and not active_sups) else min(
                    float(l2.get(e, max2)),
                    max(1.0, -math.log2(max(1.0, float(cp2)) / float(tot2))),
                )
                eff1_d[e] = l1_est + sur
                eff2_d[e] = l2_est + sur

            trie = BE.build_trie(decan_candidates)
            _, nc1, _ = BE.segment_corpus_bits(docs_1, trie, eff1_d, 1e9)
            _, nc2, _ = BE.segment_corpus_bits(docs_2, trie, eff2_d, 1e9)
            survived = [
                e for e in decan_candidates
                if (e in req_singles) or (nc1.get(e, 0) + nc2.get(e, 0)) > 0
            ]
            rev_now = sum(1 for e in survived if e not in active_set)
            revived_count_total += rev_now
            nxt_decan = eval_nash_state(survived, nc1, nc2)

        decan_trace.append({
            'phase': 'decan_pass',
            'iter': dp_idx,
            'revived_substrings': rev_now,
            'entries': len(nxt_decan['entries']),
            'total_archive_bytes': nxt_decan['total_archive_bytes'],
            'objective_bits': round(nxt_decan['objective_bits'], 2),
        })
        if set(nxt_decan['entries']) == active_set:
            cur_decan = nxt_decan
            break
        cur_decan = nxt_decan

    polished_decan, trace_post = run_exact_realized_vmm(cur_decan)

    if polished_decan['objective_bits'] < best_std['objective_bits'] - 1e-6:
        winner = polished_decan
        winner['trace'] = decan_trace + trace_post
        winner['revived_substrings_used'] = revived_count_total
    else:
        winner = best_std
        winner['trace'] = trace_std
        winner['revived_substrings_used'] = 0

    winner['revival'] = True
    winner['shrinkage'] = shrinkage
    winner['n_tables'] = n_tables
    return winner
