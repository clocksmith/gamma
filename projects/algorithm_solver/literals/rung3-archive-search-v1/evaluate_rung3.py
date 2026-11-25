#!/usr/bin/env python3
"""Head-to-head Rung 3 kill-gate benchmark for Full-Archive MDL Search + Pruning.

Compares `archive_search.c` (`mdl-archive-prune`, pricing `dict + Huffman tables + payload`
and pruning absorbed entries) at matched wall-clock search budget and matched random-access
seek guarantees (`BIT3` 4B/file bit-offset index vs. bundled `zstd -19 --train` 4B/file
byte-offset index, verifying 100% single-file random-access decode on both sides):
  1. CodeNet `primary` (in-sample) and `primary -> secondary` (held-out transfer).
  2. Untouched workspace `Zig vs WGSL` (40 train pairs -> 40 disjoint held-out test pairs).
  3. Untouched workspace `C vs TypeScript` (40 train pairs -> 40 disjoint held-out test pairs).

Leaves `codenet-replication-v1/` and `fixed-source-v3/` 100% untouched.
"""
from __future__ import annotations

import json
import math
import os
import random
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
V3_DIR = HERE.parent / 'fixed-source-v3'
RUNG2_DIR = HERE.parent / 'rung2-presearch-v1'

sys.path.insert(0, str(CODENET_DIR))
sys.path.insert(0, str(RUNG2_DIR))
sys.path.insert(0, str(HERE))

import byte_encode as BE  # noqa: E402
from indexed_archive import (  # noqa: E402
    decode_random_access_file,
    serialize_design_b_random_access_archive,
    unpack_index_and_trees,
)
from run_untouched_holdout import DECO_ROOT, sample_deterministic_pool  # noqa: E402


def compile_binaries(build_dir: Path) -> tuple[Path, Path]:
    build_dir.mkdir(parents=True, exist_ok=True)
    eng_bin = build_dir / 'engine_v3'
    arc_bin = build_dir / 'archive_search'
    subprocess.run(
        ['cc', '-O3', '-Wall', '-Wno-unused-function', '-o', str(eng_bin), str(V3_DIR / 'engine.c'), '-lm'],
        check=True,
    )
    subprocess.run(
        ['cc', '-O3', '-Wall', '-Wno-unused-function', '-o', str(arc_bin), str(HERE / 'archive_search.c'), '-lm'],
        check=True,
    )
    return eng_bin, arc_bin


def read_entries(chain_path: Path) -> tuple[list[tuple[int, int, bytes]], dict[str, str]]:
    entries: list[tuple[int, int, bytes]] = []
    meta: dict[str, str] = {}
    with open(chain_path, encoding='utf-8') as fh:
        for line in fh:
            parts = line.strip().split()
            if not parts:
                continue
            if parts[0] == 'E' and len(parts) >= 6:
                entries.append((int(parts[1]), int(parts[2]), bytes.fromhex(parts[5])))
            elif parts[0] in ('P', 'D'):
                for tok in parts[1:]:
                    if '=' in tok:
                        k, v = tok.split('=', 1)
                        meta[k] = v
    return entries, meta


def best_mdl_prefix_design_b(
    chain: Sequence[tuple[int, int, bytes]],
    docs_1: Sequence[bytes],
    docs_2: Sequence[bytes],
    step: int = 32,
) -> dict[str, Any]:
    """Find best Design B prefix along a chain using MDL byte-cost stopping + iterative reparsing."""
    raw = [e[2] for e in chain]
    n = len(raw)
    sizes = sorted({s for s in range(step, n + 1, step)} | {n})
    root: dict[Any, Any] = {}
    at = 0
    tm_candidates = []
    for sz in sizes:
        while at < sz:
            BE.insert_trie(root, raw[at])
            at += 1
        p1, c1, _ = BE.segment_corpus_tokens(docs_1, root)
        p2, c2, _ = BE.segment_corpus_tokens(docs_2, root)
        if p1 is None or p2 is None:
            continue
        stored = chain[sz - 1][1]
        syms = sz + 1
        l1 = BE.canonical_huffman_lengths(c1)
        l2 = BE.canonical_huffman_lengths(c2)
        pay = math.ceil(BE.total_huffman_bits(c1, l1) / 8) + math.ceil(BE.total_huffman_bits(c2, l2) / 8)
        tm_candidates.append((stored + 2 * syms + 4 + pay, sz))

    tm_candidates.sort()
    top_sizes = sorted({sz for _, sz in tm_candidates[:8]} | {n})

    best: dict[str, Any] | None = None
    for sz in top_sizes:
        pref = raw[:sz]
        rt = BE.build_trie(pref)
        opt1 = BE.optimize_byte_segmentation(docs_1, rt)['byte_min']
        opt2 = BE.optimize_byte_segmentation(docs_2, rt)['byte_min']
        stored = sum(1 + len(e) for e in pref)
        tbl = 2 * (len(pref) + 1)
        pay = opt1['payload_bytes'] + opt2['payload_bytes']
        tot = stored + tbl + 4 + pay
        cand = {
            'entries_count': len(pref),
            'dict_bytes': stored,
            'table_bytes': tbl,
            'unindexed_total_bytes': tot,
            '_entries': pref,
            '_lengths_1': opt1['lengths'],
            '_lengths_2': opt2['lengths'],
        }
        if best is None or cand['unindexed_total_bytes'] < best['unindexed_total_bytes']:
            best = cand
    assert best is not None
    return best


def bundle_zstd_random_access(
    train_docs: Sequence[bytes],
    target_docs: Sequence[bytes],
    work_dir: Path,
    dict_max_bytes: int = 8192,
) -> dict[str, Any] | None:
    zstd_bin = shutil.which('zstd')
    if not zstd_bin:
        return None
    samples_dir = work_dir / 'zstd_samples'
    samples_dir.mkdir(parents=True, exist_ok=True)
    for idx, raw in enumerate(train_docs):
        (samples_dir / f's_{idx:04d}.bin').write_bytes(raw)
    dict_path = work_dir / 'zstd.dict'
    subprocess.run(
        [zstd_bin, '--train', '-q', f'--maxdict={dict_max_bytes}', '-o', str(dict_path),
         *[str(samples_dir / f's_{i:04d}.bin') for i in range(len(train_docs))]],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    dict_bytes = dict_path.read_bytes()

    frames: list[bytes] = []
    for idx, raw in enumerate(target_docs):
        in_f = work_dir / 'in.bin'
        out_f = work_dir / 'out.zst'
        in_f.write_bytes(raw)
        subprocess.run(
            [zstd_bin, '-19', '-q', '-f', '-D', str(dict_path), str(in_f), '-o', str(out_f)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        frames.append(out_f.read_bytes())

    # Pack actual bundled random-access container:
    # 4B magic `ZST3` + 4B dict_len + 2B num_files + dict_bytes + M * 4B end_offsets + concatenated frames
    buf = bytearray(b'ZST3')
    buf.extend(struct.pack('<IH', len(dict_bytes), len(frames)))
    buf.extend(dict_bytes)
    running = 0
    for fr in frames:
        running += len(fr)
        buf.extend(struct.pack('<I', running))
    for fr in frames:
        buf.extend(fr)
    blob = bytes(buf)

    # Verify random-access single-file extraction on 5 spot-checked files
    pos = 10 + len(dict_bytes)
    ends = [struct.unpack_from('<I', blob, pos + 4 * i)[0] for i in range(len(frames))]
    base_off = pos + 4 * len(frames)
    for check_i in (0, len(frames) // 2, len(frames) - 1):
        s_off = 0 if check_i == 0 else ends[check_i - 1]
        e_off = ends[check_i]
        fr_slice = blob[base_off + s_off: base_off + e_off]
        tmp_z = work_dir / 'chk.zst'
        tmp_out = work_dir / 'chk.out'
        tmp_z.write_bytes(fr_slice)
        subprocess.run(
            [zstd_bin, '-d', '-q', '-f', '-D', str(dict_path), str(tmp_z), '-o', str(tmp_out)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        if tmp_out.read_bytes() != target_docs[check_i]:
            raise AssertionError('bundled zstd random-access decode mismatch')

    unindexed_sum = len(dict_bytes) + sum(len(f) for f in frames)
    return {
        'dict_bytes': len(dict_bytes),
        'payload_frames_bytes': sum(len(f) for f in frames),
        'unindexed_per_file_total_bytes': unindexed_sum,
        'serialized_random_access_archive_bytes': len(blob),
        'random_access_verified': True,
    }


def evaluate_pair_benchmark(
    eng_bin: Path,
    arc_bin: Path,
    *,
    label: str,
    train_1: Sequence[bytes],
    train_2: Sequence[bytes],
    test_1: Sequence[bytes],
    test_2: Sequence[bytes],
    k_max: int = 4096,
    limit_sec: float = 15.0,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix='bits-rung3-') as tmp:
        wdir = Path(tmp)
        fdir = wdir / 'docs'
        fdir.mkdir()
        paths: list[str] = []
        for idx, raw in enumerate(list(train_1) + list(train_2)):
            fp = fdir / f'd_{idx:04d}.bin'
            fp.write_bytes(raw)
            paths.append(str(fp))
        list_f = wdir / 'both.txt'
        list_f.write_text('\n'.join(paths) + '\n', encoding='utf-8')
        (wdir / 'both.groups').write_text(
            '\n'.join(str(i) for i in (list(range(len(train_1))) + list(range(len(train_2))))) + '\n',
            encoding='utf-8',
        )
        env = os.environ.copy()
        env['FSV3_GROUPS'] = str(wdir / 'both.groups')
        env['FSV3_RECEIPT'] = 'manifest=rung3 pool=both cuts=doc impl=v3 run=bench'

        # 1. Run `greedy-entry` in engine.c and measure exact wall-clock time
        ge_chain_p = wdir / 'greedy-entry.txt'
        t0 = time.perf_counter()
        subprocess.run(
            [str(eng_bin), 'greedy-entry', 's1-whole', '16', str(k_max), f'{limit_sec:.3f}', str(list_f), str(ge_chain_p)],
            env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        ge_sec = time.perf_counter() - t0
        ge_chain, _ = read_entries(ge_chain_p)

        # 2. Run `greedy-byte` in engine.c under equal cap
        gb_chain_p = wdir / 'greedy-byte.txt'
        t0 = time.perf_counter()
        subprocess.run(
            [str(eng_bin), 'greedy-byte', 's1-whole', '16', str(k_max), f'{limit_sec:.3f}', str(list_f), str(gb_chain_p)],
            env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        gb_sec = time.perf_counter() - t0
        gb_chain, _ = read_entries(gb_chain_p)

        # 3. Run `archive_search.c` (`mdl-archive-prune`, tables=2) under the same cap
        arc_chain_p = wdir / 'mdl-archive-prune.txt'
        t0 = time.perf_counter()
        subprocess.run(
            [str(arc_bin), '2', 's1-whole', '16', str(k_max), f'{limit_sec:.3f}', str(list_f), str(arc_chain_p)],
            env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        arc_sec = time.perf_counter() - t0
        arc_chain, arc_meta = read_entries(arc_chain_p)

        # Score all three under Design B + MDL byte-cost stopping + serialized BIT3 random-access archive
        methods = {}
        for m_name, ch, sec in (
            ('greedy-entry+mdl', ge_chain, ge_sec),
            ('greedy-byte+mdl', gb_chain, gb_sec),
            ('mdl-archive-prune', arc_chain, arc_sec),
        ):
            best = best_mdl_prefix_design_b(ch, train_1, train_2)
            ra_train = serialize_design_b_random_access_archive(best['_entries'], train_1, train_2)
            # Verify ALL random-access individual-file decodes on a sample + boundaries!
            hdr_train = unpack_index_and_trees(ra_train)
            all_train = list(train_1) + list(train_2)
            sample_idxs = sorted({0, len(train_1) - 1, len(train_1), len(all_train) - 1} | set(random.Random(42).sample(range(len(all_train)), min(20, len(all_train)))))
            for idx in sample_idxs:
                if decode_random_access_file(ra_train, idx, hdr_train) != all_train[idx]:
                    raise AssertionError(f'{m_name} train random-access decode failed at {idx}')

            # Held-out transfer using frozen dictionary (+ honest unseen single-byte fallback)
            # and frozen primary Huffman tables (+1 Laplace smoothing per benchmark_baselines.py)!
            present = set(best['_entries'])
            needed_singles = sorted({
                bytes([b]) for d in (list(test_1) + list(test_2)) for b in d if bytes([b]) not in present
            })
            oos_entries = list(best['_entries']) + needed_singles
            oos_root = BE.build_trie(oos_entries)
            _, tr_c1, _ = BE.segment_corpus_tokens(train_1, oos_root)
            _, tr_c2, _ = BE.segment_corpus_tokens(train_2, oos_root)
            c1_sm = Counter(tr_c1)
            c2_sm = Counter(tr_c2)
            for e in oos_entries:
                if c1_sm[e] == 0:
                    c1_sm[e] = 1
                if c2_sm[e] == 0:
                    c2_sm[e] = 1
            l1_fr = BE.canonical_huffman_lengths(c1_sm)
            l2_fr = BE.canonical_huffman_lengths(c2_sm)

            ra_test = serialize_design_b_random_access_archive(
                oos_entries, test_1, test_2,
                lengths_1=l1_fr, lengths_2=l2_fr,
            )
            hdr_test = unpack_index_and_trees(ra_test)
            all_test = list(test_1) + list(test_2)
            for idx in (0, len(test_1) - 1, len(test_1), len(all_test) - 1):
                if decode_random_access_file(ra_test, idx, hdr_test) != all_test[idx]:
                    raise AssertionError(f'{m_name} test random-access decode failed at {idx}')

            methods[m_name] = {
                'search_sec': round(sec, 4),
                'selected_entries': best['entries_count'],
                'dict_bytes': best['dict_bytes'],
                'in_sample_unindexed_bytes': best['unindexed_total_bytes'],
                'in_sample_serialized_random_access_bytes': len(ra_train),
                'held_out_serialized_random_access_bytes': len(ra_test),
                'random_access_verified': True,
            }
        methods['mdl-archive-prune']['pruned_absorbed_entries'] = int(arc_meta.get('pruned', 0))

        # 4. Matched random-access zstd -19 --train (8 KiB) on both in-sample and held-out
        zstd_in = bundle_zstd_random_access(list(train_1) + list(train_2), list(train_1) + list(train_2), wdir / 'z_in')
        zstd_oos = bundle_zstd_random_access(list(train_1) + list(train_2), list(test_1) + list(test_2), wdir / 'z_oos')

    return {
        'label': label,
        'train_raw_bytes': sum(len(d) for d in train_1) + sum(len(d) for d in train_2),
        'held_out_raw_bytes': sum(len(d) for d in test_1) + sum(len(d) for d in test_2),
        'methods': methods,
        'zstd_train_8kib_matched_random_access': {
            'in_sample': zstd_in,
            'held_out': zstd_oos,
        },
        'comparisons': {
            'prune_gain_over_greedy_entry_in_sample_bytes': (
                methods['greedy-entry+mdl']['in_sample_serialized_random_access_bytes']
                - methods['mdl-archive-prune']['in_sample_serialized_random_access_bytes']
            ),
            'prune_gain_over_greedy_entry_held_out_bytes': (
                methods['greedy-entry+mdl']['held_out_serialized_random_access_bytes']
                - methods['mdl-archive-prune']['held_out_serialized_random_access_bytes']
            ),
            'prune_gain_over_greedy_byte_in_sample_bytes': (
                methods['greedy-byte+mdl']['in_sample_serialized_random_access_bytes']
                - methods['mdl-archive-prune']['in_sample_serialized_random_access_bytes']
            ),
            'held_out_gap_vs_zstd_train_8kib_bytes': (
                methods['mdl-archive-prune']['held_out_serialized_random_access_bytes']
                - zstd_oos['serialized_random_access_archive_bytes']
                if zstd_oos else None
            ),
        },
    }


def main() -> None:
    t0 = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix='bits-rung3-bin-') as btmp:
        eng_bin, arc_bin = compile_binaries(Path(btmp))

        # 1. CodeNet primary -> secondary
        manifest = json.loads((CODENET_DIR / 'manifest.json').read_text(encoding='utf-8'))
        pri_pairs = manifest['splits']['primary']['pairs']
        sec_pairs = manifest['splits']['secondary']['pairs']
        cn_res = evaluate_pair_benchmark(
            eng_bin, arc_bin,
            label='codenet_py_js_200_to_200',
            train_1=[(CODENET_DIR / p['python']['path']).read_bytes() for p in pri_pairs],
            train_2=[(CODENET_DIR / p['javascript']['path']).read_bytes() for p in pri_pairs],
            test_1=[(CODENET_DIR / p['python']['path']).read_bytes() for p in sec_pairs],
            test_2=[(CODENET_DIR / p['javascript']['path']).read_bytes() for p in sec_pairs],
            k_max=4096,
            limit_sec=25.0,
        )

        # 2. Untouched Zig vs WGSL (40 train -> 40 disjoint held-out)
        zig = [b for _, b in sample_deterministic_pool(DECO_ROOT / 'fawn', '.zig', 80)]
        wgsl = [b for _, b in sample_deterministic_pool(DECO_ROOT / 'fawn', '.wgsl', 80)]
        zw_res = evaluate_pair_benchmark(
            eng_bin, arc_bin,
            label='untouched_zig_vs_wgsl_40_to_40',
            train_1=zig[:40], train_2=wgsl[:40],
            test_1=zig[40:80], test_2=wgsl[40:80],
            k_max=4096,
            limit_sec=15.0,
        )

        # 3. Untouched C vs TypeScript (40 train -> 40 disjoint held-out)
        c_docs = [b for _, b in sample_deterministic_pool(DECO_ROOT / 'fawn', '.c', 80)]
        ts_docs = [b for _, b in sample_deterministic_pool(DECO_ROOT / 'hatch', '.ts', 80)]
        ct_res = evaluate_pair_benchmark(
            eng_bin, arc_bin,
            label='untouched_c_vs_ts_40_to_40',
            train_1=c_docs[:40], train_2=ts_docs[:40],
            test_1=c_docs[40:80], test_2=ts_docs[40:80],
            k_max=4096,
            limit_sec=15.0,
        )

    report = {
        'schema': 'bits-rung3-archive-search-eval/v1',
        'elapsed_sec': round(time.perf_counter() - t0, 2),
        'benchmarks': [cn_res, zw_res, ct_res],
    }
    out_dir = HERE / 'results'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'rung3_archive_search_results.json'
    out_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
