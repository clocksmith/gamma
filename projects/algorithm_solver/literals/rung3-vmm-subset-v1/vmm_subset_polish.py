#!/usr/bin/env python3
"""Variational Two-Part Majorization-Minimization (VMM) Subset Selector & Nash Fixed-Point Certifier.

Solves two problems left open by fixed-dictionary iterative bit-cost reparsing (`byte_encode.py`)
and merge-order prefix stopping (Liyanage & Yvon 2026; Nouri 2026):

  1. Certified Mutual (Nash) Fixed-Point Verification (`certify_emitted_table_optimality`):
     Checks whether a pair `(pieces, lengths)` over dictionary `D` satisfies:
       (a) `lengths == canonical_huffman_lengths(counts(pieces))` (optimal prefix code for `pieces`), and
       (b) `min_{P in P(X, D_active)} B(P, lengths) == B(pieces, lengths)` where
           `D_active = {w in D : lengths[w] > 0}` (globally optimal parse under the emitted table,
           with zero fake provisional penalties).
     Iterating exact DP on `D_active` + exact Huffman coding is strictly monotone in integer bits
     and guaranteed to terminate at a 0-bit certified Nash fixed point `(gap_bits == 0)`.

  2. Variational Two-Part MM Subset Selection (`variational_two_part_mm`):
     Minimizes full two-part archive size over arbitrary subsets `D' subseteq D_0` (`Sigma subseteq D'`):
       L(P, ell) = sum_{w in D_0 \\ Sigma} H(w) * 1[n_P(w) > 0] + sum_w n_P(w) ell(w),
     where `H(w) = 8 * (1 + |w| + n_tables)` bits. At iterate `(P^(t), ell^(t))` with total count
     `n^(t)(w) > 0` across streams, the tight linear upper-bound surrogate over `D^(t)` assigns
     additive per-occurrence bit weight:
       c_tilde_s^(t)(w) = ell_s^(t)(w) + H(w) / n^(t)(w)   for w in D^(t) \\ Sigma,
     excising unamortized and absorbed intermediate scaffold entries (e.g. BPE sub-merges `"ret"`,
     `"retur"` once `"return"` forms) in linear-time shortest-path passes without requiring any
     merge order, followed by exact `gamma = 0` Nash fixed-point polishing.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
CODENET_DIR = HERE.parent / 'codenet-replication-v1'
sys.path.insert(0, str(CODENET_DIR))
import byte_encode as BE  # noqa: E402


def certify_emitted_table_optimality(
    docs: Sequence[bytes],
    entries: Sequence[bytes],
    emitted_lengths: dict[bytes, int],
    emitted_bits: int,
) -> dict[str, Any]:
    """Verify exact global parse optimality under the emitted active code-length table."""
    active_entries = [e for e in entries if emitted_lengths.get(e, 0) > 0]
    active_root = BE.build_trie(active_entries)
    _, dp_counts, _ = BE.segment_corpus_bits(docs, active_root, emitted_lengths, 1 << 30)
    if dp_counts is None:
        raise ValueError('active entries failed to spell corpus')
    dp_min_bits = BE.total_huffman_bits(dp_counts, emitted_lengths)
    gap_bits = emitted_bits - dp_min_bits
    return {
        'total_dict_entries': len(entries),
        'active_table_entries': len(active_entries),
        'zero_count_dead_entries': len(entries) - len(active_entries),
        'emitted_payload_bits': emitted_bits,
        'exact_dp_min_bits_under_emitted_table': dp_min_bits,
        'parse_suboptimality_bits': gap_bits,
        'is_certified_nash_fixed_point': (gap_bits == 0),
    }


def polish_to_certified_nash_single(
    docs: Sequence[bytes],
    entries: Sequence[bytes],
    init_counts: Counter | None = None,
    *,
    prune_dead_multibyte: bool = False,
    required_singles: set[bytes] | None = None,
    max_passes: int = 32,
) -> dict[str, Any]:
    """Monotone exact coordinate descent on `D_active` guaranteed to reach `gap_bits == 0`."""
    cur_entries = list(entries)
    req = required_singles if required_singles is not None else {bytes([b]) for d in docs for b in d}

    if init_counts is None:
        root = BE.build_trie(cur_entries)
        pieces, counts, _ = BE.segment_corpus_tokens(docs, root)
        if pieces is None:
            raise ValueError('entries cannot spell docs')
    else:
        counts = init_counts
        pieces = None

    lengths = BE.canonical_huffman_lengths(counts)
    cur_bits = BE.total_huffman_bits(counts, lengths)

    passes = 0
    for _ in range(max_passes):
        passes += 1
        if prune_dead_multibyte:
            cur_entries = [e for e in cur_entries if (e in req) or lengths.get(e, 0) > 0]
        active = [e for e in cur_entries if lengths.get(e, 0) > 0]
        act_root = BE.build_trie(active)
        new_pieces, new_counts, _ = BE.segment_corpus_bits(docs, act_root, lengths, 1 << 30)
        bits_under_old_table = BE.total_huffman_bits(new_counts, lengths)
        if bits_under_old_table == cur_bits and pieces is not None:
            # Exact Nash equilibrium reached!
            break
        pieces = new_pieces
        counts = new_counts
        lengths = BE.canonical_huffman_lengths(counts)
        cur_bits = BE.total_huffman_bits(counts, lengths)

    if prune_dead_multibyte:
        cur_entries = [e for e in cur_entries if (e in req) or lengths.get(e, 0) > 0]

    cert = certify_emitted_table_optimality(docs, cur_entries, lengths, cur_bits)
    assert cert['is_certified_nash_fixed_point'], f'failed to converge in {max_passes} passes: {cert}'

    dict_b = sum(1 + len(e) for e in cur_entries)
    tbl_b = len(cur_entries) + 1
    pay_b = (cur_bits + 7) // 8
    return {
        'entries': cur_entries,
        'pieces': pieces,
        'counts': counts,
        'lengths': lengths,
        'payload_bits': cur_bits,
        'payload_bytes': pay_b,
        'dict_bytes': dict_b,
        'table_bytes': tbl_b,
        'total_archive_bytes': dict_b + tbl_b + pay_b,
        'polish_passes': passes,
        'certificate': cert,
    }


def variational_two_part_mm(
    docs_1: Sequence[bytes],
    docs_2: Sequence[bytes],
    seed_entries: Sequence[bytes],
    *,
    n_tables: int = 1,
    max_mm_iters: int = 15,
) -> dict[str, Any]:
    """Select an archive-minimal subset `D' subseteq seed_entries` via Variational Two-Part MM."""
    if n_tables not in (1, 2):
        raise ValueError('n_tables must be 1 (Design A) or 2 (Design B)')

    all_docs = list(docs_1) + list(docs_2)
    req_singles = {bytes([b]) for d in all_docs for b in d}

    # Deduplicate seed_entries while guaranteeing all required single bytes are present
    seen: set[bytes] = set()
    cur_entries: list[bytes] = []
    for e in list(sorted(req_singles)) + list(seed_entries):
        if e not in seen:
            seen.add(e)
            cur_entries.append(e)

    if n_tables == 1:
        best_state = polish_to_certified_nash_single(
            all_docs, cur_entries, prune_dead_multibyte=True, required_singles=req_singles,
        )
        cur_entries = list(best_state['entries'])
        counts = best_state['counts']
        lengths = best_state['lengths']

        mm_trace = [{'iter': 0, 'entries': len(cur_entries), 'total_bytes': best_state['total_archive_bytes']}]
        for it in range(1, max_mm_iters + 1):
            eff_costs: dict[bytes, float] = {}
            for e in cur_entries:
                c = counts.get(e, 0)
                if e in req_singles:
                    eff_costs[e] = float(lengths.get(e, 16))
                elif c > 0:
                    header_bits = 8.0 * (1 + len(e) + 1)
                    eff_costs[e] = float(lengths[e]) + header_bits / float(c)
                else:
                    eff_costs[e] = 1e9

            _, mm_counts, _ = BE.segment_corpus_bits(all_docs, BE.build_trie(cur_entries), eff_costs, 1e9)
            cand_entries = [e for e in cur_entries if (e in req_singles) or mm_counts.get(e, 0) > 0]
            polished = polish_to_certified_nash_single(
                all_docs, cand_entries, mm_counts,
                prune_dead_multibyte=True, required_singles=req_singles,
            )
            mm_trace.append({
                'iter': it,
                'entries': len(polished['entries']),
                'total_bytes': polished['total_archive_bytes'],
            })
            if polished['total_archive_bytes'] < best_state['total_archive_bytes']:
                best_state = polished
                cur_entries = list(polished['entries'])
                counts = polished['counts']
                lengths = polished['lengths']
            else:
                break

        best_state['mm_trace'] = mm_trace
        best_state['n_tables'] = 1
        return best_state

    # n_tables == 2 (Design B: shared dictionary + 2 per-language canonical Huffman tables + 4B routing)
    def eval_design_b_nash(ents: Sequence[bytes], init_c1: Counter | None = None, init_c2: Counter | None = None) -> dict[str, Any]:
        p1 = polish_to_certified_nash_single(docs_1, ents, init_c1, prune_dead_multibyte=False)
        p2 = polish_to_certified_nash_single(docs_2, ents, init_c2, prune_dead_multibyte=False)
        kept = [
            e for e in ents
            if (e in req_singles) or p1['lengths'].get(e, 0) > 0 or p2['lengths'].get(e, 0) > 0
        ]
        if len(kept) < len(ents):
            p1 = polish_to_certified_nash_single(docs_1, kept, p1['counts'], prune_dead_multibyte=False)
            p2 = polish_to_certified_nash_single(docs_2, kept, p2['counts'], prune_dead_multibyte=False)
        dict_b = sum(1 + len(e) for e in kept)
        tbl_b = 2 * (len(kept) + 1)
        tot_b = dict_b + tbl_b + 4 + p1['payload_bytes'] + p2['payload_bytes']
        return {
            'entries': kept,
            'stream1': p1,
            'stream2': p2,
            'dict_bytes': dict_b,
            'table_bytes': tbl_b,
            'routing_bytes': 4,
            'payload_bytes': p1['payload_bytes'] + p2['payload_bytes'],
            'total_archive_bytes': tot_b,
            'n_tables': 2,
            'is_certified_nash_fixed_point': (
                p1['certificate']['is_certified_nash_fixed_point']
                and p2['certificate']['is_certified_nash_fixed_point']
            ),
        }

    best_b = eval_design_b_nash(cur_entries)
    cur_entries = list(best_b['entries'])
    mm_trace = [{'iter': 0, 'entries': len(cur_entries), 'total_bytes': best_b['total_archive_bytes']}]

    for it in range(1, max_mm_iters + 1):
        c1 = best_b['stream1']['counts']
        c2 = best_b['stream2']['counts']
        l1 = best_b['stream1']['lengths']
        l2 = best_b['stream2']['lengths']
        max1 = max(l1.values()) + 2
        max2 = max(l2.values()) + 2

        eff1: dict[bytes, float] = {}
        eff2: dict[bytes, float] = {}
        for e in cur_entries:
            tot_c = c1.get(e, 0) + c2.get(e, 0)
            if e in req_singles:
                eff1[e] = float(l1.get(e, max1))
                eff2[e] = float(l2.get(e, max2))
            elif tot_c > 0:
                hdr_surcharge = (8.0 * (1 + len(e) + 2)) / float(tot_c)
                eff1[e] = float(l1.get(e, max1)) + hdr_surcharge
                eff2[e] = float(l2.get(e, max2)) + hdr_surcharge
            else:
                eff1[e] = 1e9
                eff2[e] = 1e9

        trie = BE.build_trie(cur_entries)
        _, nc1, _ = BE.segment_corpus_bits(docs_1, trie, eff1, 1e9)
        _, nc2, _ = BE.segment_corpus_bits(docs_2, trie, eff2, 1e9)
        cand = [e for e in cur_entries if (e in req_singles) or (nc1.get(e, 0) + nc2.get(e, 0)) > 0]
        polished_b = eval_design_b_nash(cand, nc1, nc2)
        mm_trace.append({
            'iter': it,
            'entries': len(polished_b['entries']),
            'total_bytes': polished_b['total_archive_bytes'],
        })
        if polished_b['total_archive_bytes'] < best_b['total_archive_bytes']:
            best_b = polished_b
            cur_entries = list(polished_b['entries'])
        else:
            break

    best_b['mm_trace'] = mm_trace
    return best_b
