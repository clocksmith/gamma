#!/usr/bin/env python3
"""Frozen Pre-Compression Codec Regime Predictor (`bits-rung2-codec-regime-v1`).

Predicts BEFORE running any dictionary search (`engine.c`) or `zstd --train` whether
a static two-part Huffman dictionary archive (`BIT3`: `dict + canonical Huffman tables +
4 B/file bit-offset index`, zero per-file block headers) or a tuned Zstandard shared-dict
archive (`ZST3`: `zstd -19 --train --no-check` with optimal `maxdict` + `4 B/file` frame
index) yields the smaller random-access container, separately for:
  1. `in_sample` archival (dictionary & code tables fit to the target batch), and
  2. `held_out` transfer (dictionary & code tables frozen on a disjoint training batch
     from the same distribution).

Physical byte-balance model (uses ONLY O(N) raw byte/window statistics, zero subprocesses):
  - Per-file framing gap (`BIT3` advantage on short records):
      Each independently decodable `zstd --no-check` frame carries a mandatory 4 B frame
      magic (`0xFD2FB528`), 1 B frame header descriptor, 1-4 B `dictID`, 1-2 B frame
      content size, 3 B block header, and 2-5 B literal/sequence section headers (~14 B
      minimum per file), whereas `BIT3` terminates each record with a single `EOF` Huffman
      codeword (~1.1 B) and zero per-file headers -> ~`12.8 * M` bytes saved by `BIT3`.
  - Intra-document local LZ77 matchable bytes (`ZST3` advantage on long/self-repetitive files):
      Scans each document `d` in O(|d|) for 8-byte substrings repeated earlier inside the
      SAME document (`intra_doc_repeat8_bytes`), partitioned into:
        * `local_only_repeat8_bytes`: 8-byte intra-document repeats whose 8-gram occurs in
          fewer than `MIN_GLOBAL_DOC_FREQ` (5) distinct documents across the corpus (100%
          inaccessible to an MDL-optimal global dictionary, compressed by per-file LZ77),
        * `shared_intra_repeat8_bytes`: 8-byte intra-document repeats that also appear in
          >= 5 documents (partially captured by `BIT3`'s <=16 B phrases, more compactly
          captured by LZ77 when spans exceed 16 B).
  - Vocabulary transfer loss (`held_out` penalty on `BIT3`):
      On unseen files, frozen static phrases suffer out-of-vocabulary fallback to shorter
      tokens/bytes while `ZST3`'s intra-file LZ77 adapts dynamically to unseen local names.

Calibration provenance: constants frozen solely on saved `codenet-replication-v1` and
`rung3_archive_search_results.json` (`codenet_py_js`, `zig_vs_wgsl`, `c_vs_ts`) prior to
running the untouched short/medium/long holdout suite.
"""
from __future__ import annotations

import time
from collections import Counter
from typing import Sequence

from raw_predictor import predict_presearch

FROZEN_REGIME_VERSION = 'bits-rung2-codec-regime-v1'

# Physical constants calibrated solely on saved Rung 3 receipts before blind holdout
ZSTD_NET_FRAME_OVERHEAD_BYTES = 22.0   # zstd per-frame magic+header+per-block literal/FSE tree tax minus BIT3 EOF
ZSTD_DICT_GRID = (1024, 2048, 4096, 8192)
MIN_GLOBAL_DOC_FREQ = 5                # minimum document frequency for an 8-gram to amortize globally
COEF_LOCAL_LZ77_SAVING = 0.14          # net ZST3 vs BIT3 byte gain per non-global intra-doc repeated byte
COEF_LONG_SPAN_LZ77_SAVING = 0.04      # extra LZ77 gain on >16B spans among globally shared intra-doc repeats
COEF_BIT3_CROSS_DOC_HUFFMAN = 0.09     # corpus-optimal static Huffman density advantage on cross-doc 8-grams
COEF_BIT3_OOV_TRANSFER_PENALTY = 0.038 # held-out OOV phrase-miss penalty per raw byte on static BIT3 vocab


def extract_intra_vs_cross_repetition(
    docs_1: Sequence[bytes],
    docs_2: Sequence[bytes],
) -> dict[str, float | int]:
    """Measure intra-document vs. cross-document 8-byte repetition in O(N) time."""
    t0 = time.perf_counter()
    all_docs = list(docs_1) + list(docs_2)
    m_total = len(all_docs)
    n_total = sum(len(d) for d in all_docs)
    mean_doc_bytes = (n_total / m_total) if m_total > 0 else 0.0

    # Pass 1: document frequency of 8-grams across the corpus
    doc_freq8: Counter[bytes] = Counter()
    for d in all_docs:
        ln = len(d)
        if ln >= 8:
            doc_freq8.update({d[i:i + 8] for i in range(ln - 7)})

    # Pass 2: greedy non-overlapping / covered byte positions of intra-doc vs cross-doc 8-grams
    local_only_repeat_bytes = 0
    shared_intra_repeat_bytes = 0
    cross_doc_only_bytes = 0

    for d in all_docs:
        ln = len(d)
        if ln < 8:
            continue
        seen_in_doc: set[bytes] = set()
        covered_until = -1
        for i in range(ln - 7):
            g8 = d[i:i + 8]
            df = doc_freq8[g8]
            if g8 in seen_in_doc:
                # Count newly covered bytes of this intra-doc repeat span
                start = max(i, covered_until + 1)
                newly = max(0, (i + 8) - start)
                covered_until = max(covered_until, i + 7)
                if df < MIN_GLOBAL_DOC_FREQ:
                    local_only_repeat_bytes += newly
                else:
                    shared_intra_repeat_bytes += newly
            else:
                seen_in_doc.add(g8)
                if df >= MIN_GLOBAL_DOC_FREQ and i > covered_until:
                    start = max(i, covered_until + 1)
                    cross_doc_only_bytes += max(0, (i + 8) - start)
                    covered_until = max(covered_until, i + 7)

    intra_total = local_only_repeat_bytes + shared_intra_repeat_bytes
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return {
        'M_total': m_total,
        'N_total': n_total,
        'mean_doc_bytes': round(mean_doc_bytes, 2),
        'local_only_repeat8_bytes': local_only_repeat_bytes,
        'shared_intra_repeat8_bytes': shared_intra_repeat_bytes,
        'cross_doc_first_occ8_bytes': cross_doc_only_bytes,
        'local_repeat8_fraction': round(local_only_repeat_bytes / n_total, 6) if n_total > 0 else 0.0,
        'intra_repeat8_fraction': round(intra_total / n_total, 6) if n_total > 0 else 0.0,
        'cross_doc8_fraction': round(cross_doc_only_bytes / n_total, 6) if n_total > 0 else 0.0,
        'scan_ms': round(elapsed_ms, 3),
    }


def predict_codec_and_layout_regime(
    docs_1: Sequence[bytes],
    docs_2: Sequence[bytes],
) -> dict[str, object]:
    """Predict `(in_sample_winner, held_out_winner)` in `{'BIT3', 'ZST3'}` + `(layout_hat, K_hat)`."""
    t0 = time.perf_counter()
    layout_pred = predict_presearch(docs_1, docs_2)
    rep = extract_intra_vs_cross_repetition(docs_1, docs_2)

    m_tot = int(rep['M_total'])
    n_tot = int(rep['N_total'])
    mean_l = float(rep['mean_doc_bytes'])
    r_local = float(rep['local_only_repeat8_bytes'])
    r_shared_intra = float(rep['shared_intra_repeat8_bytes'])
    r_cross_first = float(rep['cross_doc_first_occ8_bytes'])

    # Predicted BIT3 header bytes (dict + table(s)) vs tuned ZST3 dictionary bytes:
    sel = layout_pred['selected_candidate']
    d_active = int(sel['predicted_active_entries'])
    sig_u = int(layout_pred['features']['sigma_union'])
    n_multi = max(0, d_active - sig_u)
    n_tables = 1 if layout_pred['layout_hat'] == 'A' else 2
    est_bit3_header = (2 * sig_u + 7.5 * n_multi) + n_tables * (d_active + 1)

    # Tuned ZST3 picks smallest dict in {1024, 2048, 4096, 8192} amortizing cross-doc support:
    est_zstd_dict = min(8192, max(1024, int(round(0.06 * n_tot / 1024.0)) * 1024 or 1024))

    # Positive `predicted_zst3_minus_bit3_bytes` => ZST3 archive is LARGER => BIT3 wins!
    # Negative `predicted_zst3_minus_bit3_bytes` => ZST3 archive is SMALLER => ZST3 wins!
    framing_adv_bit3 = ZSTD_NET_FRAME_OVERHEAD_BYTES * m_tot
    header_adv_bit3 = float(est_zstd_dict) - float(est_bit3_header)
    cross_huff_adv_bit3 = COEF_BIT3_CROSS_DOC_HUFFMAN * r_cross_first
    lz77_adv_zst3 = (
        COEF_LOCAL_LZ77_SAVING * r_local
        + COEF_LONG_SPAN_LZ77_SAVING * r_shared_intra
    )

    net_in_sample = (framing_adv_bit3 + header_adv_bit3 + cross_huff_adv_bit3) - lz77_adv_zst3
    # Held-out: shared dictionary size is fixed on training batch; BIT3 pays OOV phrase fallback on test bytes
    oov_penalty_bit3 = COEF_BIT3_OOV_TRANSFER_PENALTY * n_tot
    net_held_out = net_in_sample - oov_penalty_bit3

    in_sample_winner = 'BIT3' if net_in_sample > 0.0 else 'ZST3'
    held_out_winner = 'BIT3' if net_held_out > 0.0 else 'ZST3'

    return {
        'regime_rule_version': FROZEN_REGIME_VERSION,
        'layout_rule_version': layout_pred['rule_version'],
        'layout_hat': layout_pred['layout_hat'],
        'K_hat': layout_pred['K_hat'],
        'in_sample_codec_hat': in_sample_winner,
        'held_out_codec_hat': held_out_winner,
        'predicted_zst3_minus_bit3_in_sample_bytes': round(net_in_sample, 1),
        'predicted_zst3_minus_bit3_held_out_bytes': round(net_held_out, 1),
        'components_bytes': {
            'zst3_per_file_framing_penalty': round(framing_adv_bit3, 1),
            'zst3_minus_bit3_dict_table_header': round(header_adv_bit3, 1),
            'bit3_cross_doc_huffman_advantage': round(cross_huff_adv_bit3, 1),
            'zst3_intra_doc_lz77_advantage': round(lz77_adv_zst3, 1),
            'bit3_held_out_oov_penalty': round(oov_penalty_bit3, 1),
            'estimated_tuned_zstd_dict_bytes': est_zstd_dict,
            'estimated_bit3_header_bytes': round(est_bit3_header, 1),
        },
        'repetition_features': rep,
        'total_predictor_ms': round((time.perf_counter() - t0) * 1000.0, 3),
    }
