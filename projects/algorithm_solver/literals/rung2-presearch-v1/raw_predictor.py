#!/usr/bin/env python3
"""Frozen pre-search predictor for BITS Rung 2 (`bits-rung2-presearch-v1`).

Predicts `(layout_hat in {'A', 'B', 'C'}, K_hat)` BEFORE running any dictionary
search (`engine.c`) or shortest-path/Huffman parsing (`byte_encode.py`).

Sees ONLY raw document byte lists `(docs_1, docs_2)`:
  1. Exact single-byte alphabet cliffs:
       - Shared Designs A/B require K >= |Sigma_1 U Sigma_2|.
       - Separate Design C requires K >= |Sigma_1| + |Sigma_2|.
  2. Multi-scale raw divergence (1-byte + stride-1 4-byte window Jensen-Shannon
     redundancy) predicting post-dictionary symbol mutual information I(S; L)/8
     even when two programming languages share nearly identical ASCII character
     frequencies (`i_byte` small, `j4` large).
  3. Exact header trade-off identity between Design B (1 shared dict + 2 tables)
     and Design C (2 separate dicts + 2 tables):
       H_C - H_B = sum_{w in D_inter} (3 + |w|) - (|D_1| + |D_2|)
     Each shared single byte saves 4 B in Design B; each shared ~4-byte token
     saves ~7 B; each unshared entry adds +1 dead zero-count table byte in the
     other language's Huffman table under Design B.
  4. Amortized dictionary size estimator from recurring 4-byte substring support,
     selecting the smallest slot cap K_hat in k_grid that provides >= 15% headroom
     above the predicted active dictionary size so search terminates early when
     larger K cannot amortize extra entries.

Calibration provenance: constants frozen solely from `codenet-replication-v1`
(Python 3 / JavaScript ranks 0..399). Untouched language pairs and corpus sizes
must be evaluated without modifying these constants.

Zero external dependencies, zero subprocesses, zero dictionary search.
"""
from __future__ import annotations

import math
import time
from collections import Counter
from typing import Sequence

FROZEN_RULE_VERSION = 'bits-rung2-presearch-v1'
DEFAULT_K_GRID = (256, 512, 1024, 2048, 4096)
ROUTING_BYTES = 4

# Frozen calibration constants (fit solely on codenet-replication-v1 ranks 0..399)
MIN_GRAM4_SUPPORT = 6        # filter out singleton/rare 4-grams that never enter D (avoids Miller-Madow bias)
COEF_UNCOV_BYTE_MI = 0.45    # fraction of 1-byte MI superseded where supported 4-grams cover the stream
COEF_SUP_GRAM4_MI = 0.14     # stride-normalized lexical MI per supported 4-gram bit
COEF_DICT_REP12 = 0.45       # active multibyte entries per 4-gram with count >= 12
BYTES_PER_AMORT_SLOT = 75.0  # minimum raw bytes needed per amortized multibyte entry
DESIGN_B_PREFIX_RATIO = 0.88 # Design B optimal prefix shrinkage from 2-table header (+1 B/entry)
INT_ROUNDING_SLACK = 0.015   # finite-corpus integer codeword rounding slack per table entry
SHARED_MULTI_RATIO = 0.26    # shared multibyte entries per shared frequent 4-gram
AVG_NET_GAIN_PER_ENTRY = 3.8 # average net archive byte gain per admitted amortized entry
HEADROOM_FACTOR = 1.15       # slot headroom above predicted |D*| for candidate prefix selection


def _kl_mixture_bits(c1: Counter, n1: int, c2: Counter, n2: int) -> float:
    """Compute N_1 * D_KL(P_1 || P_mix) + N_2 * D_KL(P_2 || P_mix) in bits."""
    nt = n1 + n2
    if n1 <= 0 or n2 <= 0 or nt <= 0:
        return 0.0
    kl1 = 0.0
    for k, v in c1.items():
        if v > 0:
            pm = (v + c2.get(k, 0)) / nt
            kl1 += v * math.log2((v / n1) / pm)
    kl2 = 0.0
    for k, v in c2.items():
        if v > 0:
            pm = (c1.get(k, 0) + v) / nt
            kl2 += v * math.log2((v / n2) / pm)
    return kl1 + kl2


def extract_raw_corpus_features(
    docs_1: Sequence[bytes],
    docs_2: Sequence[bytes],
) -> dict[str, float | int]:
    """Extract raw byte, alphabet, and 4-byte window statistics in a single O(N) pass."""
    t0 = time.perf_counter()
    n1 = sum(len(d) for d in docs_1)
    n2 = sum(len(d) for d in docs_2)
    nt = n1 + n2

    b1 = Counter(b for d in docs_1 for b in d)
    b2 = Counter(b for d in docs_2 for b in d)
    s1 = set(b1)
    s2 = set(b2)
    s_union = s1 | s2
    s_inter = s1 & s2

    mi_byte_bits = _kl_mixture_bits(b1, n1, b2, n2)
    i_byte = (mi_byte_bits / nt) if nt > 0 else 0.0

    # Stride-1 exact 4-byte rolling windows; filter to count >= MIN_GRAM4_SUPPORT (6)
    # so singleton identifiers do not inject Miller-Madow finite-sample KL bias.
    g1 = Counter(d[i:i + 4] for d in docs_1 for i in range(max(0, len(d) - 3)))
    g2 = Counter(d[i:i + 4] for d in docs_2 for i in range(max(0, len(d) - 3)))
    w1 = sum(g1.values())
    w2 = sum(g2.values())
    wt = w1 + w2

    mi_g4_sup_bits = 0.0
    sup_occ = 0
    if w1 > 0 and w2 > 0 and wt > 0:
        for gram in (set(g1) | set(g2)):
            c1 = g1[gram]
            c2 = g2[gram]
            ct = c1 + c2
            if ct < MIN_GRAM4_SUPPORT:
                continue
            sup_occ += ct
            pm = ct / wt
            if c1 > 0:
                mi_g4_sup_bits += c1 * math.log2((c1 / w1) / pm)
            if c2 > 0:
                mi_g4_sup_bits += c2 * math.log2((c2 / w2) / pm)
    sup_coverage = min(1.0, sup_occ / wt) if wt > 0 else 0.0
    j4_sup = (mi_g4_sup_bits / wt) if wt > 0 else 0.0

    freq1_ge6 = {k for k, v in g1.items() if v >= 6}
    freq2_ge6 = {k for k, v in g2.items() if v >= 6}
    shared4_ge6 = len(freq1_ge6 & freq2_ge6)
    union4_ge6 = len(freq1_ge6 | freq2_ge6)
    jaccard4 = (shared4_ge6 / union4_ge6) if union4_ge6 > 0 else 0.0

    rep12_1 = sum(1 for v in g1.values() if v >= 12)
    rep12_2 = sum(1 for v in g2.values() if v >= 12)
    g_all = Counter(g1)
    g_all.update(g2)
    rep12_all = sum(1 for v in g_all.values() if v >= 12)

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return {
        'M_1': len(docs_1),
        'M_2': len(docs_2),
        'N_1': n1,
        'N_2': n2,
        'N_total': nt,
        'sigma_1': len(s1),
        'sigma_2': len(s2),
        'sigma_union': len(s_union),
        'sigma_inter': len(s_inter),
        'single_byte_mi_bits': round(mi_byte_bits, 3),
        'i_byte_bits_per_byte': round(i_byte, 6),
        'supported_gram4_mi_bits': round(mi_g4_sup_bits, 3),
        'supported_gram4_coverage': round(sup_coverage, 6),
        'j4_bits_per_window': round(j4_sup, 6),
        'jaccard4_ge6': round(jaccard4, 6),
        'shared4_ge6': shared4_ge6,
        'rep12_1': rep12_1,
        'rep12_2': rep12_2,
        'rep12_all': rep12_all,
        'feature_extract_ms': round(elapsed_ms, 3),
    }


def predict_naive_byte_mi(
    features: dict[str, float | int],
    k_grid: Sequence[int] = DEFAULT_K_GRID,
) -> dict[str, object]:
    """Textbook ablation baseline: uses ONLY raw single-byte mutual information I_1(X; L)/8.

    Limitations exposed by this baseline:
      1. Misses multi-byte keyword divergence when two languages share ASCII characters.
      2. Cannot distinguish Design B (shared dict + 2 tables) from Design C (2 dicts),
         because single-byte MI does not model dictionary deduplication vs dead table slots.
      3. Has no dictionary-size model, so it defaults to max(k_grid) and saves 0 search time.
    """
    sig_u = int(features['sigma_union'])
    feasible_ks = sorted(k for k in k_grid if k >= sig_u)
    if not feasible_ks:
        return {
            'feasible': False,
            'layout_hat': None,
            'K_hat': None,
            'reason': f'all K in {list(k_grid)} < sigma_union={sig_u}',
        }
    k_max = feasible_ks[-1]
    naive_saving_bytes = float(features['single_byte_mi_bits']) / 8.0
    # Textbook comparison against worst-case table header K_max + 5 (or min(K_max, N/180) + 5)
    est_d = min(k_max, sig_u + round(int(features['N_total']) / 180.0))
    extra_hdr = est_d + 1 + ROUTING_BYTES
    layout = 'B' if naive_saving_bytes > extra_hdr else 'A'
    return {
        'feasible': True,
        'layout_hat': layout,
        'K_hat': k_max,
        'naive_byte_mi_saving_bytes': round(naive_saving_bytes, 2),
        'assumed_extra_header_bytes': extra_hdr,
        'naive_net_B_over_A_bytes': round(naive_saving_bytes - extra_hdr, 2),
    }


def predict_presearch(
    docs_1: Sequence[bytes],
    docs_2: Sequence[bytes],
    *,
    k_grid: Sequence[int] = DEFAULT_K_GRID,
    max_entry_len: int = 16,
) -> dict[str, object]:
    """Predict optimal `(layout_hat, K_hat)` from raw corpus bytes before any search."""
    t0 = time.perf_counter()
    feats = extract_raw_corpus_features(docs_1, docs_2)
    nt = int(feats['N_total'])
    n1 = int(feats['N_1'])
    n2 = int(feats['N_2'])
    sig1 = int(feats['sigma_1'])
    sig2 = int(feats['sigma_2'])
    sig_u = int(feats['sigma_union'])
    sig_i = int(feats['sigma_inter'])
    mi_byte_bits = float(feats['single_byte_mi_bits'])
    mi_g4_sup_bits = float(feats['supported_gram4_mi_bits'])
    sup_cov = float(feats['supported_gram4_coverage'])
    rep12_all = int(feats['rep12_all'])
    rep12_1 = int(feats['rep12_1'])
    rep12_2 = int(feats['rep12_2'])
    shared4_ge6 = int(feats['shared4_ge6'])

    # Uncapped amortized dictionary sizes predicted from raw recurring 4-byte support
    length_scale = min(1.15, max(0.65, math.log2(max(2, max_entry_len)) / 4.0))
    multi_a_inf = max(0, round(COEF_DICT_REP12 * length_scale * min(rep12_all, nt / BYTES_PER_AMORT_SLOT)))
    multi_b_inf = max(0, round(DESIGN_B_PREFIX_RATIO * multi_a_inf))
    multi_1_inf = max(0, round(COEF_DICT_REP12 * length_scale * min(rep12_1, n1 / BYTES_PER_AMORT_SLOT)))
    multi_2_inf = max(0, round(COEF_DICT_REP12 * length_scale * min(rep12_2, n2 / BYTES_PER_AMORT_SLOT)))

    d_a_inf = sig_u + multi_a_inf
    d_b_inf = sig_u + multi_b_inf
    d_c_inf = (sig1 + multi_1_inf) + (sig2 + multi_2_inf)

    # Evaluate relative archive byte difference vs single-byte Design A baseline across (layout, K)
    # Lower relative_bytes_vs_single_byte_A is better (more negative = smaller predicted archive).
    candidates: list[dict[str, object]] = []
    for k in sorted(k_grid):
        shared_ok = k >= sig_u
        sep_ok = k >= (sig1 + sig2)

        if shared_ok:
            d_a = min(k, d_a_inf)
            admitted_a = d_a - sig_u
            rel_a = -AVG_NET_GAIN_PER_ENTRY * admitted_a

            d_b = min(k, d_b_inf)
            admitted_b = d_b - sig_u
            # Supported 4-gram lexical MI realizes as multibyte entries enter D
            denom_lex = max(1, min(320, multi_b_inf))
            lex_realization = min(1.0, admitted_b / denom_lex) if multi_b_inf > 0 else 0.0
            eff_cov = sup_cov * lex_realization
            pred_mi_bits = (1.0 - COEF_UNCOV_BYTE_MI * eff_cov) * mi_byte_bits + (
                COEF_SUP_GRAM4_MI * mi_g4_sup_bits * lex_realization
            )
            pred_mi_bytes = pred_mi_bits / 8.0
            extra_b_cost = (d_b + 1 + ROUTING_BYTES) + INT_ROUNDING_SLACK * d_b
            delta_b_vs_a = pred_mi_bytes - extra_b_cost  # >0 means B beats A
            # Base shared-dict gain at d_b plus B-over-A table-split net advantage
            rel_b = (-AVG_NET_GAIN_PER_ENTRY * admitted_b) - delta_b_vs_a

            sufficient_a = k >= math.ceil(HEADROOM_FACTOR * d_a_inf)
            sufficient_b = k >= math.ceil(HEADROOM_FACTOR * d_b_inf)

            candidates.append({
                'layout': 'A',
                'K': k,
                'feasible': True,
                'predicted_active_entries': d_a,
                'headroom_sufficient': sufficient_a,
                'predicted_rel_bytes': round(rel_a, 2),
            })
            candidates.append({
                'layout': 'B',
                'K': k,
                'feasible': True,
                'predicted_active_entries': d_b,
                'headroom_sufficient': sufficient_b,
                'predicted_mi_saving_bytes': round(pred_mi_bytes, 2),
                'predicted_extra_table_cost_bytes': round(extra_b_cost, 2),
                'predicted_B_minus_A_saving_bytes': round(delta_b_vs_a, 2),
                'predicted_rel_bytes': round(rel_b, 2),
            })
        else:
            candidates.append({'layout': 'A', 'K': k, 'feasible': False, 'reason': f'K={k} < sigma_union={sig_u}'})
            candidates.append({'layout': 'B', 'K': k, 'feasible': False, 'reason': f'K={k} < sigma_union={sig_u}'})

        if sep_ok:
            avail_multi_c = k - (sig1 + sig2)
            want_multi_c = multi_1_inf + multi_2_inf
            if want_multi_c <= avail_multi_c or want_multi_c == 0:
                m1 = multi_1_inf
                m2 = multi_2_inf
            else:
                ratio1 = multi_1_inf / want_multi_c
                m1 = round(avail_multi_c * ratio1)
                m2 = avail_multi_c - m1
            d1 = sig1 + m1
            d2 = sig2 + m2
            m_inter = min(m1, m2, round(SHARED_MULTI_RATIO * shared4_ge6))
            # Exact header trade-off H_C - H_B = 4*|Sigma_inter| + 7*|M_inter| - (|D_1| + |D_2|)
            # plus slot-starvation loss when K caps C below B's deduplicated multibyte capacity.
            admitted_b_ref = min(k, d_b_inf) - sig_u
            unique_multi_c = m1 + m2 - m_inter
            starved_slots = max(0, admitted_b_ref - unique_multi_c)
            starvation_penalty = AVG_NET_GAIN_PER_ENTRY * starved_slots
            h_c_minus_h_b = (4.0 * sig_i + 7.0 * m_inter) - float(d1 + d2) + starvation_penalty

            # Reference rel_b at this K
            rel_b_here = next(
                c['predicted_rel_bytes'] for c in candidates if c['layout'] == 'B' and c['K'] == k
            )
            rel_c = float(rel_b_here) + h_c_minus_h_b
            sufficient_c = k >= math.ceil(HEADROOM_FACTOR * d_c_inf)
            candidates.append({
                'layout': 'C',
                'K': k,
                'feasible': True,
                'predicted_active_entries': d1 + d2,
                'predicted_d1': d1,
                'predicted_d2': d2,
                'predicted_shared_multibyte': m_inter,
                'predicted_C_minus_B_bytes': round(h_c_minus_h_b, 2),
                'headroom_sufficient': sufficient_c,
                'predicted_rel_bytes': round(rel_c, 2),
            })
        else:
            candidates.append({
                'layout': 'C',
                'K': k,
                'feasible': False,
                'reason': f'K={k} < sigma_1+sigma_2={sig1 + sig2}',
            })

    feasible = [c for c in candidates if c.get('feasible')]
    if not feasible:
        return {
            'rule_version': FROZEN_RULE_VERSION,
            'feasible': False,
            'layout_hat': None,
            'K_hat': None,
            'features': feats,
            'candidates': candidates,
            'naive_byte_mi_baseline': predict_naive_byte_mi(feats, k_grid=k_grid),
            'predictor_elapsed_ms': round((time.perf_counter() - t0) * 1000.0, 3),
        }

    # Pick minimum predicted_rel_bytes; tie-break on smallest K (saves search time when
    # d_inf already fits with headroom) and layout order ('B', 'A', 'C').
    layout_rank = {'B': 0, 'A': 1, 'C': 2}
    best = min(
        feasible,
        key=lambda c: (float(c['predicted_rel_bytes']), int(c['K']), layout_rank[str(c['layout'])]),
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return {
        'rule_version': FROZEN_RULE_VERSION,
        'feasible': True,
        'layout_hat': best['layout'],
        'K_hat': best['K'],
        'predicted_uncapped_sizes': {
            'D_A_inf': d_a_inf,
            'D_B_inf': d_b_inf,
            'D_C_inf': d_c_inf,
        },
        'selected_candidate': best,
        'features': feats,
        'candidates': candidates,
        'naive_byte_mi_baseline': predict_naive_byte_mi(feats, k_grid=k_grid),
        'predictor_elapsed_ms': round(elapsed_ms, 3),
    }
