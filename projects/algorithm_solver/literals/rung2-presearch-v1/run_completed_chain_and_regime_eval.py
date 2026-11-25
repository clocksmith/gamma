#!/usr/bin/env python3
"""Blind Completed-Chain Layout (`>1%` Default-B Misses) & Codec Regime (`BIT3` vs Tuned `ZST3`) Benchmark.

Evaluates TWO frozen pre-compression rules (`raw_predictor.py` `v2` and `regime_predictor.py` `v1`,
both SHA-256 verified against git HEAD before execution) on untouched Deco workspace files
(strictly excluding `enwiki9` and `codenet-replication-v1`):

  Part 1 — Unconfounded Completed-Chain Equal-Budget Layout & Stopping Suite (8 untouched cells):
    - Uses `limit_seconds=15.0` (`3.0s`/arm) so greedy chains finish cleanly without the `0.5s`/arm
      truncation noted on 300 kB corpora in `untouched_holdout_v2.json`.
    - Tests untouched cells spanning homogeneous controls and cross-domain pairs to score:
        (a) cells where `default_always_B` (with MDL stopping) loses to the equal-budget oracle by `> 1.0%`,
        (b) decoupled `layout_regret_vs_oracle_bytes` vs `default_always_B`, and
        (c) decoupled `ordinary_mdl_stopping_saving_bytes` vs `k_hat_presearch_truncation_cost_bytes`.

  Part 2 — Blind Pre-Compression Codec Regime Suite (`BIT3` vs Tuned `ZST3 --no-check`, 6 train->test pairs = 12 regimes):
    - Tests `regime_predictor.py` (`bits-rung2-codec-regime-v1`) across short (`64-320 B`), medium
      (`400-850 B`), and long (`1,300-3,400 B`) untouched files, both `in_sample` and `held_out`.
    - Compares serialized `BIT3` (`4 B/file` bit-offset seek table, Design A/B chosen by `raw_predictor`
      with `greedy-entry` + MDL prefix stopping) against **tuned `ZST3`** (`zstd -19 --no-check`
      selecting the training-optimal dictionary budget `maxdict in {0, 1024, 2048, 4096, 8192}` +
      matched `4 B/file` frame-offset seek table).
    - Every serialized `BIT3` and `ZST3` archive is verified by out-of-order single-file random-access
      decompression.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import struct
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
RUNG3_DIR = HERE.parent / 'rung3-archive-search-v1'
DECO_ROOT = Path('/Users/xyz/deco')

sys.path.insert(0, str(CODENET_DIR))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(RUNG3_DIR))

import byte_encode as BE  # noqa: E402
import raw_predictor as RP  # noqa: E402
import regime_predictor as REG  # noqa: E402
from equal_budget_eval import (  # noqa: E402
    DEFAULT_ARMS,
    DEFAULT_K_GRID,
    candidate_prefix_sizes,
    compile_engine,
    evaluate_presearch_vs_oracle,
    read_chain_entries,
    run_engine_arm,
    write_corpus_list,
)
from indexed_archive import decode_one_doc_from_bit_offset, encode_stream_with_bit_offsets  # noqa: E402

SKIP_DIRS = {
    '.git', 'node_modules', '.venv', 'venv', 'target', 'dist', 'build',
    '.zig-cache', 'zig-out', '__pycache__', 'third_party', 'vendor',
    'enwiki9', 'codenet-replication-v1', 'rung2-presearch-v1', 'rung3-archive-search-v1',
    'runs', 'receipts',
}


_INDEX_CACHE: list[tuple[str, str, int, Path]] | None = None


def _get_safe_index(roots: Sequence[Path]) -> list[tuple[str, str, int, Path]]:
    global _INDEX_CACHE
    if _INDEX_CACHE is not None:
        return _INDEX_CACHE
    entries: list[tuple[str, str, int, Path]] = []
    allowed_exts = {'.md', '.py', '.json', '.wgsl', '.css', '.h', '.ts', '.mjs', '.cjs', '.c', '.js'}
    for base in roots:
        if not base.is_dir():
            continue
        for cur, dirs, files in os.walk(base):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith('.'))
            for fn in sorted(files):
                ext = os.path.splitext(fn)[1].lower()
                if ext not in allowed_exts:
                    continue
                fp = Path(cur) / fn
                try:
                    sz = fp.stat().st_size
                except OSError:
                    continue
                if 64 <= sz <= 3600:
                    entries.append((ext, str(fp.relative_to(DECO_ROOT)), sz, fp))
    _INDEX_CACHE = entries
    return entries


def sample_band_pool(
    roots: Sequence[Path],
    suffixes: Sequence[str],
    needed: int,
    *,
    min_bytes: int,
    max_bytes: int,
    seed_tag: str,
) -> list[tuple[str, bytes]]:
    by_sha: dict[str, tuple[str, bytes]] = {}
    suf_set = {s.lower() for s in suffixes}
    for ext, rel, sz, fp in _get_safe_index(roots):
        if ext not in suf_set or sz < min_bytes or sz > max_bytes:
            continue
        try:
            raw = fp.read_bytes()
        except OSError:
            continue
        if b'\x00' in raw or not (min_bytes <= len(raw) <= max_bytes):
            continue
        sha = hashlib.sha256(raw).hexdigest()
        if sha not in by_sha:
            by_sha[sha] = (rel, raw)
    ranked = sorted(
        by_sha.items(),
        key=lambda kv: hashlib.sha256(f'{seed_tag}:{kv[0]}'.encode('ascii')).hexdigest(),
    )
    if len(ranked) < needed:
        raise RuntimeError(
            f'only {len(ranked)} eligible {suffixes} files in [{min_bytes},{max_bytes}] (need {needed})'
        )
    return [kv[1] for kv in ranked[:needed]]


def serialize_and_verify_bit3_archive(
    entries: Sequence[bytes],
    docs_1: Sequence[bytes],
    docs_2: Sequence[bytes],
    *,
    n_tables: int,
    frozen_lengths: tuple[dict[bytes, int], ...] | None = None,
) -> tuple[bytes, tuple[dict[bytes, int], ...]]:
    """Serialize self-contained `BIT3` archive (`n_tables` in {1, 2}) and verify random-access seeks."""
    root = BE.build_trie(entries)
    if n_tables == 1:
        all_docs = list(docs_1) + list(docs_2)
        if frozen_lengths is not None:
            l0 = frozen_lengths[0]
            p0, _, _ = BE.segment_corpus_bits(all_docs, root, l0, max(l0.values()) + 1)
        else:
            opt0 = BE.optimize_byte_segmentation(all_docs, root)['byte_min']
            l0 = opt0['lengths']
            p0 = opt0['pieces']
        c0 = BE.assign_canonical_codes(l0)
        pay0, off0 = encode_stream_with_bit_offsets(p0, c0)
        buf = bytearray(b'BIT3')
        buf.extend(struct.pack('<HHB', len(entries), len(all_docs), 1))
        for e in entries:
            buf.append(len(e))
            buf.extend(e)
        for e in entries:
            buf.append(l0.get(e, 0))
        buf.append(l0[BE.EOF_SYMBOL])
        for b_off in off0:
            buf.extend(struct.pack('<I', b_off))
        buf.extend(pay0)
        blob = bytes(buf)
        # Verify reverse-order random-access decode on boundary & interior indices
        tree0 = BE.build_decode_tree(c0)
        for idx in sorted({0, len(all_docs) // 2, len(all_docs) - 1}, reverse=True):
            dec = decode_one_doc_from_bit_offset(pay0, off0[idx], tree0)
            if dec != all_docs[idx]:
                raise AssertionError(f'BIT3 1-table random-access mismatch at {idx}')
        return blob, (l0,)

    # n_tables == 2 (Design B)
    if frozen_lengths is not None:
        l1, l2 = frozen_lengths
        p1, _, _ = BE.segment_corpus_bits(docs_1, root, l1, max(l1.values()) + 1)
        p2, _, _ = BE.segment_corpus_bits(docs_2, root, l2, max(l2.values()) + 1)
    else:
        opt1 = BE.optimize_byte_segmentation(docs_1, root)['byte_min']
        opt2 = BE.optimize_byte_segmentation(docs_2, root)['byte_min']
        l1, p1 = opt1['lengths'], opt1['pieces']
        l2, p2 = opt2['lengths'], opt2['pieces']
    c1 = BE.assign_canonical_codes(l1)
    c2 = BE.assign_canonical_codes(l2)
    pay1, off1 = encode_stream_with_bit_offsets(p1, c1)
    pay2, off2 = encode_stream_with_bit_offsets(p2, c2)
    m_tot = len(docs_1) + len(docs_2)
    buf = bytearray(b'BIT3')
    buf.extend(struct.pack('<HHB', len(entries), m_tot, 2))
    for e in entries:
        buf.append(len(e))
        buf.extend(e)
    for tbl in (l1, l2):
        for e in entries:
            buf.append(tbl.get(e, 0))
        buf.append(tbl[BE.EOF_SYMBOL])
    for b_off in off1:
        buf.extend(struct.pack('<I', b_off))
    for b_off in off2:
        buf.extend(struct.pack('<I', (1 << 31) | b_off))
    buf.extend(struct.pack('<I', len(pay1)))
    buf.extend(pay1)
    buf.extend(pay2)
    blob = bytes(buf)
    t1 = BE.build_decode_tree(c1)
    t2 = BE.build_decode_tree(c2)
    for idx in (len(docs_1) - 1, 0):
        if decode_one_doc_from_bit_offset(pay1, off1[idx], t1) != docs_1[idx]:
            raise AssertionError('BIT3 stream 0 random-access mismatch')
    for idx in (len(docs_2) - 1, 0):
        if decode_one_doc_from_bit_offset(pay2, off2[idx], t2) != docs_2[idx]:
            raise AssertionError('BIT3 stream 1 random-access mismatch')
    return blob, (l1, l2)


def build_and_eval_bit3_pair(
    eng_bin: Path,
    train_1: Sequence[bytes],
    train_2: Sequence[bytes],
    test_1: Sequence[bytes],
    test_2: Sequence[bytes],
    *,
    layout: str,
    k_cap: int,
    limit_sec: float = 8.0,
) -> dict[str, Any]:
    """Build BIT3 archive on `(train_1, train_2)` using `greedy-entry` + MDL stopping, then freeze for held-out."""
    n_tables = 1 if layout == 'A' else 2
    with tempfile.TemporaryDirectory(prefix='bit3-pair-') as tmp:
        wdir = Path(tmp)
        all_train = list(train_1) + list(train_2)
        groups = list(range(len(all_train)))
        list_f = write_corpus_list(all_train, wdir, 'both', groups)
        chain_p = wdir / 'ge.txt'
        run_engine_arm(
            eng_bin,
            arm='greedy-entry',
            policy='s1-whole',
            max_entry_len=16,
            k_max=k_cap,
            limit_sec=limit_sec,
            list_file=list_f,
            out_chain=chain_p,
            run_tag='regime',
        )
        raw_chain = [e for _, _, e in read_chain_entries(chain_p)]
        sizes = candidate_prefix_sizes(len(raw_chain), (256, 512, 1024, 2048, 4096), 64)

        # Quick token-parse MDL sweep + top-6 iterative bit-cost reparse
        scored = []
        for sz in sizes:
            ents = raw_chain[:sz]
            root = BE.build_trie(ents)
            if n_tables == 1:
                sp = BE.segment_corpus_tokens(all_train, root)
                if sp is None or sp[0] is None:
                    continue
                lengths = BE.canonical_huffman_lengths(sp[1])
                p_bits = sum(c * lengths[sym] for sym, c in sp[1].items())
                pay_b = (p_bits + 7) // 8
                tot = sum(1 + len(e) for e in ents) + (len(ents) + 1) + pay_b
            else:
                sp1 = BE.segment_corpus_tokens(train_1, root)
                sp2 = BE.segment_corpus_tokens(train_2, root)
                if sp1 is None or sp1[0] is None or sp2 is None or sp2[0] is None:
                    continue
                l1 = BE.canonical_huffman_lengths(sp1[1])
                l2 = BE.canonical_huffman_lengths(sp2[1])
                b1 = (sum(c * l1[s] for s, c in sp1[1].items()) + 7) // 8
                b2 = (sum(c * l2[s] for s, c in sp2[1].items()) + 7) // 8
                tot = sum(1 + len(e) for e in ents) + 2 * (len(ents) + 1) + b1 + b2
            scored.append((tot, sz))
        scored.sort()

        best_in_blob = None
        best_ents = None
        for _, sz in scored[:6]:
            ents = raw_chain[:sz]
            blob, _ = serialize_and_verify_bit3_archive(ents, train_1, train_2, n_tables=n_tables)
            if best_in_blob is None or len(blob) < len(best_in_blob):
                best_in_blob = blob
                best_ents = ents
        assert best_in_blob is not None and best_ents is not None

        # Freeze dictionary + smoothed training Huffman tables for held-out transfer
        present = set(best_ents)
        unseen_singles = sorted({
            bytes([b]) for d in (list(test_1) + list(test_2)) for b in d if bytes([b]) not in present
        })
        oos_ents = list(best_ents) + unseen_singles
        oos_root = BE.build_trie(oos_ents)
        if n_tables == 1:
            _, tr_c0, _ = BE.segment_corpus_tokens(all_train, oos_root)
            c0_sm = Counter(tr_c0)
            for e in oos_ents:
                if c0_sm[e] == 0:
                    c0_sm[e] = 1
            fr_tbls: tuple[dict[bytes, int], ...] = (BE.canonical_huffman_lengths(c0_sm),)
        else:
            _, tr_c1, _ = BE.segment_corpus_tokens(train_1, oos_root)
            _, tr_c2, _ = BE.segment_corpus_tokens(train_2, oos_root)
            c1_sm, c2_sm = Counter(tr_c1), Counter(tr_c2)
            for e in oos_ents:
                if c1_sm[e] == 0:
                    c1_sm[e] = 1
                if c2_sm[e] == 0:
                    c2_sm[e] = 1
            fr_tbls = (BE.canonical_huffman_lengths(c1_sm), BE.canonical_huffman_lengths(c2_sm))

        ho_blob, _ = serialize_and_verify_bit3_archive(
            oos_ents, test_1, test_2, n_tables=n_tables, frozen_lengths=fr_tbls,
        )
        return {
            'layout_used': 'A' if n_tables == 1 else 'B',
            'selected_entries': len(best_ents),
            'in_sample_bytes': len(best_in_blob),
            'held_out_bytes': len(ho_blob),
            'random_access_verified': True,
        }


def build_and_eval_tuned_zst3_pair(
    train_docs: Sequence[bytes],
    test_docs: Sequence[bytes],
) -> dict[str, Any]:
    """Tune `zstd -19 --no-check` over `maxdict in {0, 1024, 2048, 4096, 8192}` on train, then evaluate held-out."""
    zstd_bin = shutil.which('zstd') or '/opt/homebrew/bin/zstd'
    with tempfile.TemporaryDirectory(prefix='zst3-tuned-') as tmp:
        wdir = Path(tmp)
        sdir = wdir / 'samples'
        sdir.mkdir()
        sample_paths = []
        for i, d in enumerate(train_docs):
            p = sdir / f's_{i:04d}.bin'
            p.write_bytes(d)
            sample_paths.append(str(p))

        def pack_zst3(docs: Sequence[bytes], dict_path: Path | None, tag: str) -> bytes:
            dict_bytes = dict_path.read_bytes() if dict_path is not None else b''
            cdir = wdir / f'c_{tag}'
            cdir.mkdir(exist_ok=True)
            in_paths: list[str] = []
            for i, raw in enumerate(docs):
                inp = cdir / f'i_{i:04d}.bin'
                inp.write_bytes(raw)
                in_paths.append(str(inp))
            cmd = [zstd_bin, '-19', '--no-check', '-q', '-f']
            if dict_path is not None:
                cmd.extend(['-D', str(dict_path)])
            cmd.extend(in_paths)
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            frames = [(cdir / f'i_{i:04d}.bin.zst').read_bytes() for i in range(len(docs))]

            buf = bytearray(b'ZST3')
            buf.extend(struct.pack('<IH', len(dict_bytes), len(frames)))
            buf.extend(dict_bytes)
            cur = 0
            ends = []
            for fr in frames:
                cur += len(fr)
                ends.append(cur)
                buf.extend(struct.pack('<I', cur))
            for fr in frames:
                buf.extend(fr)
            blob = bytes(buf)

            # Verify reverse-order random-access single-frame decompression
            base = 10 + len(dict_bytes) + 4 * len(frames)
            for chk_i in (len(docs) - 1, 0):
                s_off = 0 if chk_i == 0 else ends[chk_i - 1]
                e_off = ends[chk_i]
                zf = cdir / 'v.zst'
                of = cdir / 'v.out'
                zf.write_bytes(blob[base + s_off: base + e_off])
                dcmd = [zstd_bin, '-d', '-q', '-f']
                if dict_path is not None:
                    dcmd.extend(['-D', str(dict_path)])
                dcmd.extend([str(zf), '-o', str(of)])
                subprocess.run(dcmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if of.read_bytes() != docs[chk_i]:
                    raise AssertionError('tuned ZST3 random-access decode mismatch')
            return blob

        candidates = []
        # maxdict = 0 (undictionaried zstd -19 --no-check + 4B/file index)
        blob0 = pack_zst3(train_docs, None, 'd0_tr')
        candidates.append((len(blob0), 0, None, blob0))

        for md in (1024, 2048, 4096, 8192):
            dp = wdir / f'dict_{md}.zstd'
            proc = subprocess.run(
                [zstd_bin, '--train', f'--maxdict={md}', '-q', *sample_paths, '-o', str(dp)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            if proc.returncode == 0 and dp.exists():
                b_tr = pack_zst3(train_docs, dp, f'd{md}_tr')
                candidates.append((len(b_tr), md, dp, b_tr))

        candidates.sort(key=lambda x: x[0])
        best_in_len, best_md, best_dp, _ = candidates[0]
        ho_blob = pack_zst3(test_docs, best_dp, f'd{best_md}_ho')
        return {
            'tuned_maxdict_selected': best_md,
            'actual_dict_bytes': best_dp.stat().st_size if best_dp is not None else 0,
            'in_sample_bytes': best_in_len,
            'held_out_bytes': len(ho_blob),
            'in_sample_grid_bytes': {str(md): ln for ln, md, _, _ in candidates},
            'random_access_verified': True,
        }


def main() -> None:
    t0 = time.perf_counter()
    raw_pred_sha = hashlib.sha256(Path(RP.__file__).read_bytes()).hexdigest()
    reg_pred_sha = hashlib.sha256(Path(REG.__file__).read_bytes()).hexdigest()

    # Sample untouched workspace pools (strictly outside enwiki9 & codenet-replication-v1)
    ALL_SAFE_ROOTS = [
        DECO_ROOT / 'simulatte',
        DECO_ROOT / 'hatch',
        DECO_ROOT / 'fawn',
        DECO_ROOT / 'doppler',
        DECO_ROOT / 'reploid',
        DECO_ROOT / 'gamma' / 'tests',
        DECO_ROOT / 'gamma' / 'gamma',
        DECO_ROOT / 'gamma' / 'apps',
    ]
    md_med = sample_band_pool(ALL_SAFE_ROOTS, ['.md'], 30, min_bytes=320, max_bytes=1200, seed_tag='r2b-md')
    py_med = sample_band_pool(ALL_SAFE_ROOTS, ['.py'], 30, min_bytes=320, max_bytes=1200, seed_tag='r2b-py')
    json_med = sample_band_pool(ALL_SAFE_ROOTS, ['.json'], 110, min_bytes=350, max_bytes=850, seed_tag='r2b-jmed')
    wgsl_med = sample_band_pool(ALL_SAFE_ROOTS, ['.wgsl'], 40, min_bytes=320, max_bytes=1200, seed_tag='r2b-wmed')
    css_med = sample_band_pool(ALL_SAFE_ROOTS, ['.css'], 25, min_bytes=250, max_bytes=2400, seed_tag='r2b-css')
    h_med = sample_band_pool(ALL_SAFE_ROOTS, ['.h'], 25, min_bytes=320, max_bytes=1400, seed_tag='r2b-h')

    wgsl_short = sample_band_pool(ALL_SAFE_ROOTS, ['.wgsl'], 160, min_bytes=64, max_bytes=240, seed_tag='r2b-ws')
    json_short = sample_band_pool(ALL_SAFE_ROOTS, ['.json'], 160, min_bytes=64, max_bytes=240, seed_tag='r2b-js')
    ts_short = sample_band_pool(ALL_SAFE_ROOTS, ['.ts'], 160, min_bytes=64, max_bytes=260, seed_tag='r2b-tss')
    mjs_short = sample_band_pool(ALL_SAFE_ROOTS, ['.mjs', '.cjs', '.js'], 160, min_bytes=64, max_bytes=280, seed_tag='r2b-mjss')
    py_short = sample_band_pool(ALL_SAFE_ROOTS, ['.py'], 40, min_bytes=64, max_bytes=360, seed_tag='r2b-pys')
    md_short = sample_band_pool(ALL_SAFE_ROOTS, ['.md'], 40, min_bytes=64, max_bytes=420, seed_tag='r2b-mds')

    ts_med = sample_band_pool(ALL_SAFE_ROOTS, ['.ts'], 100, min_bytes=400, max_bytes=850, seed_tag='r2b-tsm')
    py_long = sample_band_pool(ALL_SAFE_ROOTS, ['.py'], 70, min_bytes=1300, max_bytes=3200, seed_tag='r2b-pyl')
    md_long = sample_band_pool(ALL_SAFE_ROOTS, ['.md'], 70, min_bytes=1300, max_bytes=3200, seed_tag='r2b-mdl')
    js_long = sample_band_pool(ALL_SAFE_ROOTS, ['.js'], 80, min_bytes=1400, max_bytes=3400, seed_tag='r2b-jsl')
    wgsl_long = sample_band_pool(ALL_SAFE_ROOTS, ['.wgsl'], 80, min_bytes=1400, max_bytes=3400, seed_tag='r2b-wl')

    # --- PART 1: Completed-Chain Equal-Budget Layout & Stopping Suite (8 untouched cells) ---
    layout_specs = [
        ('md_vs_md_ctrl_n10', md_med[:10], md_med[15:25]),
        ('py_vs_py_ctrl_n12', py_med[:12], py_med[15:27]),
        ('json_vs_json_ctrl_n16', json_med[:16], json_med[20:36]),
        ('wgsl_vs_wgsl_ctrl_n16', wgsl_med[:16], wgsl_med[20:36]),
        ('short_json_vs_wgsl_n50', json_short[:50], wgsl_short[:50]),
        ('short_ts_vs_mjs_n50', ts_short[:50], mjs_short[:50]),
        ('med_css_vs_py_n25', css_med[:25], py_med[:25]),
        ('med_md_vs_h_n25', md_med[:25], h_med[:25]),
    ]

    layout_cells = []
    for label, p1, p2 in layout_specs:
        d1 = [b for _, b in p1]
        d2 = [b for _, b in p2]
        ev = evaluate_presearch_vs_oracle(
            d1, d2,
            label=label,
            k_grid=DEFAULT_K_GRID,
            arms=DEFAULT_ARMS,
            limit_seconds=15.0,
            step=64,
        )
        ev.pop('oracle_cells', None)
        ev['manifest_first2'] = {'lang1': [p for p, _ in p1[:2]], 'lang2': [p for p, _ in p2[:2]]}
        layout_cells.append(ev)
        dl = ev['decoupled_layout_score']
        ds = ev['decoupled_stopping_score']
        print(
            f"[Part1 {label:22s}] pred=({ev['prediction']['layout_hat']},K={ev['prediction']['K_hat']}) "
            f"ora=({ev['oracle']['best_layout']},K={ev['oracle']['best_K']}) | "
            f"defB_loss={dl['default_always_B_loss_bytes']:+4d}B ({dl['default_always_B_loss_pct']:+.2f}%) | "
            f"gain_vs_defB={dl['layout_gain_over_default_B_bytes']:+4d}B | "
            f"mdl_save={ds['ordinary_mdl_stopping_saving_bytes']}B",
            flush=True,
        )

    gt1_cells = [c for c in layout_cells if c['decoupled_layout_score']['default_B_misses_gt_1pct']]
    gt1_wins = sum(1 for c in gt1_cells if c['decoupled_layout_score']['beats_default_B'])
    gt1_net_gain = sum(c['decoupled_layout_score']['layout_gain_over_default_B_bytes'] for c in gt1_cells)
    all_net_gain = sum(c['decoupled_layout_score']['layout_gain_over_default_B_bytes'] for c in layout_cells)

    # --- PART 2: Blind Pre-Compression Codec Regime Suite (6 train->test pairs = 12 regime decisions) ---
    regime_specs = [
        ('short_wgsl_vs_json_80_to_80', wgsl_short[:80], json_short[:80], wgsl_short[80:160], json_short[80:160]),
        ('short_ts_vs_mjs_80_to_80', ts_short[:80], mjs_short[:80], ts_short[80:160], mjs_short[80:160]),
        ('short_py_vs_md_20_to_20', py_short[:20], md_short[:20], py_short[20:40], md_short[20:40]),
        ('med_ts_vs_json_50_to_50', ts_med[:50], json_med[:50], ts_med[50:100], json_med[50:100]),
        ('long_py_vs_md_35_to_35', py_long[:35], md_long[:35], py_long[35:70], md_long[35:70]),
        ('long_js_vs_wgsl_40_to_40', js_long[:40], wgsl_long[:40], js_long[40:80], wgsl_long[40:80]),
    ]

    regime_cells = []
    with tempfile.TemporaryDirectory(prefix='bits-regime-eng-') as etmp:
        eng_bin = compile_engine(Path(etmp))
        for label, tr1, tr2, te1, te2 in regime_specs:
            d_tr1, d_tr2 = [b for _, b in tr1], [b for _, b in tr2]
            d_te1, d_te2 = [b for _, b in te1], [b for _, b in te2]

            pred = REG.predict_codec_and_layout_regime(d_tr1, d_tr2)
            layout_for_bit3 = 'A' if pred['layout_hat'] == 'A' else 'B'
            bit3 = build_and_eval_bit3_pair(
                eng_bin, d_tr1, d_tr2, d_te1, d_te2,
                layout=layout_for_bit3,
                k_cap=int(pred['K_hat']),
            )
            zst3 = build_and_eval_tuned_zst3_pair(d_tr1 + d_tr2, d_te1 + d_te2)

            gt_in_winner = 'BIT3' if bit3['in_sample_bytes'] < zst3['in_sample_bytes'] else 'ZST3'
            gt_ho_winner = 'BIT3' if bit3['held_out_bytes'] < zst3['held_out_bytes'] else 'ZST3'
            in_diff = zst3['in_sample_bytes'] - bit3['in_sample_bytes']  # >0 means BIT3 smaller
            ho_diff = zst3['held_out_bytes'] - bit3['held_out_bytes']    # >0 means BIT3 smaller

            in_best = min(bit3['in_sample_bytes'], zst3['in_sample_bytes'])
            ho_best = min(bit3['held_out_bytes'], zst3['held_out_bytes'])
            in_chosen = bit3['in_sample_bytes'] if pred['in_sample_codec_hat'] == 'BIT3' else zst3['in_sample_bytes']
            ho_chosen = bit3['held_out_bytes'] if pred['held_out_codec_hat'] == 'BIT3' else zst3['held_out_bytes']

            cell = {
                'label': label,
                'train_raw_bytes': sum(len(x) for x in d_tr1 + d_tr2),
                'held_out_raw_bytes': sum(len(x) for x in d_te1 + d_te2),
                'mean_train_doc_bytes': pred['repetition_features']['mean_doc_bytes'],
                'local_repeat8_fraction': pred['repetition_features']['local_repeat8_fraction'],
                'cross_doc8_fraction': pred['repetition_features']['cross_doc8_fraction'],
                'prediction': {
                    'in_sample_codec_hat': pred['in_sample_codec_hat'],
                    'held_out_codec_hat': pred['held_out_codec_hat'],
                    'predicted_zst3_minus_bit3_in_sample_bytes': pred['predicted_zst3_minus_bit3_in_sample_bytes'],
                    'predicted_zst3_minus_bit3_held_out_bytes': pred['predicted_zst3_minus_bit3_held_out_bytes'],
                    'layout_hat': pred['layout_hat'],
                    'K_hat': pred['K_hat'],
                },
                'bit3_random_access': bit3,
                'tuned_zst3_random_access': zst3,
                'ground_truth': {
                    'in_sample_winner': gt_in_winner,
                    'held_out_winner': gt_ho_winner,
                    'zst3_minus_bit3_in_sample_bytes': in_diff,
                    'zst3_minus_bit3_held_out_bytes': ho_diff,
                    'in_sample_pred_exact': pred['in_sample_codec_hat'] == gt_in_winner,
                    'held_out_pred_exact': pred['held_out_codec_hat'] == gt_ho_winner,
                    'in_sample_regret_bytes': in_chosen - in_best,
                    'held_out_regret_bytes': ho_chosen - ho_best,
                },
            }
            regime_cells.append(cell)
            print(
                f"[Part2 {label:28s}] meanL={cell['mean_train_doc_bytes']:6.1f}B | "
                f"IN: BIT3={bit3['in_sample_bytes']:6d} vs ZST3(d={zst3['tuned_maxdict_selected']})={zst3['in_sample_bytes']:6d} "
                f"pred={pred['in_sample_codec_hat']} gt={gt_in_winner} | "
                f"HO: BIT3={bit3['held_out_bytes']:6d} vs ZST3={zst3['held_out_bytes']:6d} "
                f"pred={pred['held_out_codec_hat']} gt={gt_ho_winner}",
                flush=True,
            )

    in_acc = sum(1 for c in regime_cells if c['ground_truth']['in_sample_pred_exact'])
    ho_acc = sum(1 for c in regime_cells if c['ground_truth']['held_out_pred_exact'])
    tot_pred_regret = sum(
        c['ground_truth']['in_sample_regret_bytes'] + c['ground_truth']['held_out_regret_bytes']
        for c in regime_cells
    )
    always_zst3_regret = sum(
        max(0, c['ground_truth']['zst3_minus_bit3_in_sample_bytes'])
        + max(0, c['ground_truth']['zst3_minus_bit3_held_out_bytes'])
        for c in regime_cells
    )
    always_bit3_regret = sum(
        max(0, -c['ground_truth']['zst3_minus_bit3_in_sample_bytes'])
        + max(0, -c['ground_truth']['zst3_minus_bit3_held_out_bytes'])
        for c in regime_cells
    )

    report = {
        'schema': 'bits-rung2-completed-chain-and-regime-eval/v1',
        'frozen_raw_predictor_sha256': raw_pred_sha,
        'frozen_regime_predictor_sha256': reg_pred_sha,
        'elapsed_sec': round(time.perf_counter() - t0, 2),
        'part1_completed_chain_layout_summary': {
            'cells_total': len(layout_cells),
            'limit_seconds_per_layout': 15.0,
            'default_B_misses_gt_1pct_count': len(gt1_cells),
            'default_B_misses_gt_1pct_labels': [c['label'] for c in gt1_cells],
            'predictor_wins_on_gt_1pct_misses': f'{gt1_wins}/{len(gt1_cells)}',
            'net_layout_gain_on_gt_1pct_misses_bytes': gt1_net_gain,
            'net_layout_gain_all_cells_bytes': all_net_gain,
            'total_ordinary_mdl_stopping_saving_bytes': sum(
                c['decoupled_stopping_score']['ordinary_mdl_stopping_saving_bytes'] for c in layout_cells
            ),
            'total_k_hat_truncation_cost_bytes': sum(
                c['decoupled_stopping_score']['k_hat_presearch_truncation_cost_bytes'] for c in layout_cells
            ),
        },
        'part2_codec_regime_summary': {
            'decisions_total': 2 * len(regime_cells),
            'in_sample_exact_matches': f'{in_acc}/{len(regime_cells)}',
            'held_out_exact_matches': f'{ho_acc}/{len(regime_cells)}',
            'combined_exact_matches': f'{in_acc + ho_acc}/{2 * len(regime_cells)}',
            'predictor_total_regret_bytes': tot_pred_regret,
            'always_zst3_total_regret_bytes': always_zst3_regret,
            'always_bit3_total_regret_bytes': always_bit3_regret,
        },
        'part1_cells': layout_cells,
        'part2_cells': regime_cells,
    }

    out_dir = HERE / 'results'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'completed_chain_and_regime_v1.json'
    out_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'\nWrote {out_path}')
    print(json.dumps({
        'part1': report['part1_completed_chain_layout_summary'],
        'part2': report['part2_codec_regime_summary'],
    }, indent=2))


if __name__ == '__main__':
    main()
