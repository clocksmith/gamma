#!/usr/bin/env python3
"""Matched Random-Access Size & Native-C Throughput Pareto Benchmark (`rung2-short-ra-bench-v1`).

Compares FOUR random-access container codecs (all carrying an explicit `4 B/doc` random-access
seek table and verified byte-for-byte in reverse order by `ra_codecs_bench.c`):
  1. `BIT3` (Static `<=16 B` dictionary + 1 or 2 global canonical Huffman tables + 12-bit LUT C decoder).
  2. `FSST-255` (Boncz, Neumann, & Leis, PVLDB 2020: `<=255` `1..8 B` static symbol table + `0xFF`
     2-byte escape + 8-byte word-copy C decoder).
  3. `DFL3` (Raw headerless `DEFLATE`, RFC 1951 `wbits = -15`, zero frame/magic/checksum wrapper,
     with training-tuned shared preset dictionary `maxdict in {0, 1024, 2048, 4096, 8192}` + C `zlib`).
  4. `ZST3` (Tuned `zstd -19 --no-check` with training-tuned shared dictionary `maxdict in
     {0, 1024, 2048, 4096, 8192}` + C `ZSTD_DCtx` & pre-digested `ZSTD_DDict`).

Evaluates held-out archive bytes AND native C random-access single-document seek latency (`ns/seek`)
and throughput (`MiB/s`, `100,000` pseudo-random seeks per cell) across:
  - CodeNet Held-Out (`primary -> secondary`, `400` files, `K = 1,024` and `K = 4,096`) — closing
    the DCC venue held-out throughput measurement under matched random-access guarantees while
    keeping `codenet-replication-v1/` and `dcc-v5/` completely untouched.
  - Untouched Workspace Short, Medium, and Long Held-Out Suites (`short_wgsl_vs_json_80_to_80`,
    `short_ts_vs_mjs_80_to_80`, `med_ts_vs_json_50_to_50`, `long_js_vs_wgsl_40_to_40`).
"""
from __future__ import annotations

import json
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import zlib
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
CODENET_DIR = HERE.parent / 'codenet-replication-v1'
RUNG2_DIR = HERE.parent / 'rung2-presearch-v1'
DECO_ROOT = Path('/Users/xyz/deco')

sys.path.insert(0, str(CODENET_DIR))
sys.path.insert(0, str(RUNG2_DIR))
sys.path.insert(0, str(HERE))

import byte_encode as BE  # noqa: E402
from equal_budget_eval import compile_engine  # noqa: E402
from fsst255_codec import serialize_fsst255_archive, train_fsst255_table  # noqa: E402
from regime_predictor import predict_codec_and_layout_regime  # noqa: E402
from run_completed_chain_and_regime_eval import (  # noqa: E402
    build_and_eval_bit3_pair,
    sample_band_pool,
    serialize_and_verify_bit3_archive,
)

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


def compile_c_bench(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    bin_path = out_dir / 'ra_codecs_bench'
    subprocess.run(
        [
            'cc', '-O3', '-Wall', '-Wextra', '-Wno-unused-parameter',
            '-I/opt/homebrew/include', '-L/opt/homebrew/lib',
            str(HERE / 'ra_codecs_bench.c'), '-lzstd', '-lz', '-o', str(bin_path),
        ],
        check=True,
    )
    return bin_path


def write_raw_verify_blob(docs: Sequence[bytes], dest: Path) -> None:
    buf = bytearray(struct.pack('<I', len(docs)))
    cur = 0
    for d in docs:
        cur += len(d)
        buf.extend(struct.pack('<I', cur))
    for d in docs:
        buf.extend(d)
    dest.write_bytes(bytes(buf))


def run_c_bench(bin_path: Path, codec: str, arc_path: Path, raw_verify_path: Path, num_seeks: int = 100000) -> dict[str, Any]:
    out = subprocess.check_output(
        [str(bin_path), codec, str(arc_path), str(raw_verify_path), str(num_seeks)],
        text=True,
    )
    return json.loads(out.strip())


def pack_dfl3_with_dict(docs: Sequence[bytes], zdict: bytes) -> bytes:
    blocks: list[bytes] = []
    for d in docs:
        co = zlib.compressobj(level=9, method=zlib.DEFLATED, wbits=-15, memLevel=9, zdict=zdict)
        blocks.append(co.compress(d) + co.flush(zlib.Z_FINISH))
    buf = bytearray(b'DFL3')
    buf.extend(struct.pack('<IH', len(zdict), len(blocks)))
    buf.extend(zdict)
    cur = 0
    for bl in blocks:
        cur += len(bl)
        buf.extend(struct.pack('<I', cur))
    for bl in blocks:
        buf.extend(bl)
    return bytes(buf)


def build_tuned_zst3_and_dfl3(
    train_docs: Sequence[bytes],
    test_docs: Sequence[bytes],
    wdir: Path,
) -> tuple[dict[str, Any], Path, dict[str, Any], Path]:
    """Train candidate shared dictionaries `{0, 1024, 2048, 4096, 8192}` on `train_docs` and pick optimal for ZST3 and DFL3."""
    zstd_bin = shutil.which('zstd') or '/opt/homebrew/bin/zstd'
    sdir = wdir / 'zsamples'
    sdir.mkdir(parents=True, exist_ok=True)
    spaths = []
    for i, d in enumerate(train_docs):
        p = sdir / f's_{i:04d}.bin'
        p.write_bytes(d)
        spaths.append(str(p))

    trained_dicts: list[tuple[int, Path | None, bytes]] = [(0, None, b'')]
    for md in (1024, 2048, 4096, 8192):
        dp = wdir / f'dict_{md}.bin'
        proc = subprocess.run(
            [zstd_bin, '--train', f'--maxdict={md}', '-q', *spaths, '-o', str(dp)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        if proc.returncode == 0 and dp.exists():
            # Note: `zstd --train` emits a formatted zstd dictionary whose tail holds raw content bytes;
            # `--train-fastcover` / `--train` raw content works directly as zlib preset `zdict` too
            # (zlib uses the last <=32 KiB bytes of `zdict`).
            trained_dicts.append((md, dp, dp.read_bytes()))

    def pack_zst3_docs(docs: Sequence[bytes], dp: Path | None, tag: str) -> bytes:
        dbytes = dp.read_bytes() if dp is not None else b''
        cdir = wdir / f'zc_{tag}'
        cdir.mkdir(exist_ok=True)
        in_ps = []
        for i, raw in enumerate(docs):
            ip = cdir / f'i_{i:04d}.bin'
            ip.write_bytes(raw)
            in_ps.append(str(ip))
        cmd = [zstd_bin, '-19', '--no-check', '-q', '-f']
        if dp is not None:
            cmd.extend(['-D', str(dp)])
        cmd.extend(in_ps)
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        frames = [(cdir / f'i_{i:04d}.bin.zst').read_bytes() for i in range(len(docs))]
        buf = bytearray(b'ZST3')
        buf.extend(struct.pack('<IH', len(dbytes), len(frames)))
        buf.extend(dbytes)
        cur = 0
        for fr in frames:
            cur += len(fr)
            buf.extend(struct.pack('<I', cur))
        for fr in frames:
            buf.extend(fr)
        return bytes(buf)

    # 1. Tune ZST3 on train_docs
    zst_cands = []
    for md, dp, _ in trained_dicts:
        b_tr = pack_zst3_docs(train_docs, dp, f'tr_{md}')
        zst_cands.append((len(b_tr), md, dp))
    zst_cands.sort(key=lambda x: x[0])
    z_in_bytes, z_best_md, z_best_dp = zst_cands[0]
    z_ho_blob = pack_zst3_docs(test_docs, z_best_dp, f'ho_{z_best_md}')
    z_ho_path = wdir / 'best_ho.zst3'
    z_ho_path.write_bytes(z_ho_blob)

    # 2. Tune DFL3 (`zlib` level=9, wbits=-15 raw headerless DEFLATE) on train_docs
    # Also include a raw-concatenation suffix dictionary (`raw_tail`) so zlib isn't disadvantaged by zstd dict headers!
    raw_concat = b''.join(train_docs[::max(1, len(train_docs) // 64)])
    dfl_cands = []
    for md, _, dbytes in trained_dicts:
        b_tr = pack_dfl3_with_dict(train_docs, dbytes)
        dfl_cands.append((len(b_tr), f'zdict_{md}', dbytes))
    for raw_sz in (1024, 2048, 4096, 8192):
        rdict = raw_concat[-raw_sz:] if len(raw_concat) >= raw_sz else raw_concat
        b_tr = pack_dfl3_with_dict(train_docs, rdict)
        dfl_cands.append((len(b_tr), f'raw_{raw_sz}', rdict))
    dfl_cands.sort(key=lambda x: x[0])
    d_in_bytes, d_best_tag, d_best_bytes = dfl_cands[0]
    d_ho_blob = pack_dfl3_with_dict(test_docs, d_best_bytes)
    d_ho_path = wdir / 'best_ho.dfl3'
    d_ho_path.write_bytes(d_ho_blob)

    return (
        {'tuned_maxdict': z_best_md, 'in_sample_bytes': z_in_bytes, 'held_out_bytes': len(z_ho_blob)},
        z_ho_path,
        {'tuned_dict_kind': d_best_tag, 'dict_bytes': len(d_best_bytes), 'in_sample_bytes': d_in_bytes, 'held_out_bytes': len(d_ho_blob)},
        d_ho_path,
    )


def build_bit3_held_out_blob_from_saved_codenet(
    dict_entries: Sequence[bytes],
    pri_1: Sequence[bytes],
    pri_2: Sequence[bytes],
    sec_1: Sequence[bytes],
    sec_2: Sequence[bytes],
) -> tuple[int, bytes]:
    in_blob, _ = serialize_and_verify_bit3_archive(dict_entries, pri_1, pri_2, n_tables=2)
    present = set(dict_entries)
    unseen = sorted({bytes([b]) for d in (list(sec_1) + list(sec_2)) for b in d if bytes([b]) not in present})
    oos_ents = list(dict_entries) + unseen
    root = BE.build_trie(oos_ents)
    _, tr1, _ = BE.segment_corpus_tokens(pri_1, root)
    _, tr2, _ = BE.segment_corpus_tokens(pri_2, root)
    c1, c2 = Counter(tr1), Counter(tr2)
    for e in oos_ents:
        if c1[e] == 0:
            c1[e] = 1
        if c2[e] == 0:
            c2[e] = 1
    fr = (BE.canonical_huffman_lengths(c1), BE.canonical_huffman_lengths(c2))
    ho_blob, _ = serialize_and_verify_bit3_archive(oos_ents, sec_1, sec_2, n_tables=2, frozen_lengths=fr)
    return len(in_blob), ho_blob


def load_saved_codenet_dict(k_budget: int) -> list[bytes]:
    hex_path = CODENET_DIR / f'dictionaries/primary_K{k_budget}_B_tm.hex'
    return [bytes.fromhex(ln.strip()) for ln in hex_path.read_text(encoding='utf-8').splitlines() if ln.strip()]


def evaluate_suite(
    c_bench_bin: Path,
    eng_bin: Path,
    *,
    label: str,
    train_1: Sequence[bytes],
    train_2: Sequence[bytes],
    test_1: Sequence[bytes],
    test_2: Sequence[bytes],
    fixed_bit3_entries: Sequence[bytes] | None = None,
    num_seeks: int = 100000,
) -> dict[str, Any]:
    all_train = list(train_1) + list(train_2)
    all_test = list(test_1) + list(test_2)
    with tempfile.TemporaryDirectory(prefix=f'ra-pareto-{label}-') as tmp:
        wdir = Path(tmp)
        raw_verify = wdir / 'test_raw.bin'
        write_raw_verify_blob(all_test, raw_verify)

        # 1. BIT3
        if fixed_bit3_entries is not None:
            b_in_len, b_ho_blob = build_bit3_held_out_blob_from_saved_codenet(
                fixed_bit3_entries, train_1, train_2, test_1, test_2,
            )
            bit3_meta = {'layout_used': 'B', 'selected_entries': len(fixed_bit3_entries), 'in_sample_bytes': b_in_len, 'held_out_bytes': len(b_ho_blob)}
        else:
            reg_pred = predict_codec_and_layout_regime(train_1, train_2)
            lay = 'A' if reg_pred['layout_hat'] == 'A' else 'B'
            # Capture actual serialized held-out blob by building via helper
            bit3_meta = build_and_eval_bit3_pair(
                eng_bin, train_1, train_2, test_1, test_2,
                layout=lay, k_cap=int(reg_pred['K_hat']),
            )
            # Re-serialize exact held-out blob for C speed benchmark using `eng_bin` chain
            # (we extend `build_and_eval_bit3_pair` inline via chain on train)
            from equal_budget_eval import candidate_prefix_sizes, read_chain_entries, run_engine_arm, write_corpus_list
            lf = write_corpus_list(all_train, wdir / 'b3w', 'both', list(range(len(all_train))))
            cp = wdir / 'b3w' / 'ge.txt'
            run_engine_arm(eng_bin, arm='greedy-entry', policy='s1-whole', max_entry_len=16, k_max=int(reg_pred['K_hat']), limit_sec=8.0, list_file=lf, out_chain=cp, run_tag='ra')
            rch = [e for _, _, e in read_chain_entries(cp)]
            ents = rch[:bit3_meta['selected_entries']]
            n_tbl = 1 if lay == 'A' else 2
            present = set(ents)
            unseen = sorted({bytes([b]) for d in all_test for b in d if bytes([b]) not in present})
            oos_e = list(ents) + unseen
            rt = BE.build_trie(oos_e)
            if n_tbl == 1:
                _, tc0, _ = BE.segment_corpus_tokens(all_train, rt)
                sm0 = Counter(tc0)
                for e in oos_e:
                    if sm0[e] == 0: sm0[e] = 1
                fr_t: tuple[dict[bytes, int], ...] = (BE.canonical_huffman_lengths(sm0),)
            else:
                _, tc1, _ = BE.segment_corpus_tokens(train_1, rt)
                _, tc2, _ = BE.segment_corpus_tokens(train_2, rt)
                sm1, sm2 = Counter(tc1), Counter(tc2)
                for e in oos_e:
                    if sm1[e] == 0: sm1[e] = 1
                    if sm2[e] == 0: sm2[e] = 1
                fr_t = (BE.canonical_huffman_lengths(sm1), BE.canonical_huffman_lengths(sm2))
            b_ho_blob, _ = serialize_and_verify_bit3_archive(oos_e, test_1, test_2, n_tables=n_tbl, frozen_lengths=fr_t)
            bit3_meta['held_out_bytes'] = len(b_ho_blob)

        b_ho_path = wdir / 'ho.bit3'
        b_ho_path.write_bytes(b_ho_blob)
        b_perf = run_c_bench(c_bench_bin, 'BIT3', b_ho_path, raw_verify, num_seeks)

        # 2. FSST-255 (PVLDB 2020)
        fsst_syms = train_fsst255_table(all_train)
        f_in_blob = serialize_fsst255_archive(fsst_syms, all_train)
        f_ho_blob = serialize_fsst255_archive(fsst_syms, all_test)
        f_ho_path = wdir / 'ho.fsst'
        f_ho_path.write_bytes(f_ho_blob)
        f_perf = run_c_bench(c_bench_bin, 'FSST', f_ho_path, raw_verify, num_seeks)

        # 3 & 4. Tuned ZST3 (`zstd -19 --no-check`) and Tuned DFL3 (`zlib -9 wbits=-15`)
        z_meta, z_ho_path, d_meta, d_ho_path = build_tuned_zst3_and_dfl3(all_train, all_test, wdir / 'zd')
        z_perf = run_c_bench(c_bench_bin, 'ZST3', z_ho_path, raw_verify, num_seeks)
        d_perf = run_c_bench(c_bench_bin, 'DFL3', d_ho_path, raw_verify, num_seeks)

    codecs = {
        'BIT3': {**bit3_meta, 'ns_per_seek': b_perf['ns_per_seek'], 'decoded_mib_per_sec': b_perf['decoded_mib_per_sec']},
        'FSST-255': {'symbols': len(fsst_syms), 'in_sample_bytes': len(f_in_blob), 'held_out_bytes': len(f_ho_blob), 'ns_per_seek': f_perf['ns_per_seek'], 'decoded_mib_per_sec': f_perf['decoded_mib_per_sec']},
        'DFL3-raw-zdict': {**d_meta, 'ns_per_seek': d_perf['ns_per_seek'], 'decoded_mib_per_sec': d_perf['decoded_mib_per_sec']},
        'ZST3-tuned': {**z_meta, 'ns_per_seek': z_perf['ns_per_seek'], 'decoded_mib_per_sec': z_perf['decoded_mib_per_sec']},
    }

    # Compute exact 2D Pareto frontier on held-out `(held_out_bytes MIN, ns_per_seek MIN)`
    pareto_optimal = []
    for name, m in codecs.items():
        dominated = any(
            other != name
            and codecs[other]['held_out_bytes'] <= m['held_out_bytes']
            and codecs[other]['ns_per_seek'] <= m['ns_per_seek']
            and (codecs[other]['held_out_bytes'] < m['held_out_bytes'] or codecs[other]['ns_per_seek'] < m['ns_per_seek'])
            for other in codecs
        )
        if not dominated:
            pareto_optimal.append(name)

    smallest_ho = min(codecs, key=lambda k: codecs[k]['held_out_bytes'])
    fastest_ho = min(codecs, key=lambda k: codecs[k]['ns_per_seek'])

    print(
        f"[{label:30s}] mean_test={sum(len(x) for x in all_test)/len(all_test):6.1f}B\n"
        f"  BIT3         : {codecs['BIT3']['held_out_bytes']:6d}B | {codecs['BIT3']['ns_per_seek']:7.1f} ns/seek | {codecs['BIT3']['decoded_mib_per_sec']:7.1f} MiB/s\n"
        f"  FSST-255     : {codecs['FSST-255']['held_out_bytes']:6d}B | {codecs['FSST-255']['ns_per_seek']:7.1f} ns/seek | {codecs['FSST-255']['decoded_mib_per_sec']:7.1f} MiB/s\n"
        f"  DFL3(-15+zd) : {codecs['DFL3-raw-zdict']['held_out_bytes']:6d}B | {codecs['DFL3-raw-zdict']['ns_per_seek']:7.1f} ns/seek | {codecs['DFL3-raw-zdict']['decoded_mib_per_sec']:7.1f} MiB/s\n"
        f"  ZST3(tuned)  : {codecs['ZST3-tuned']['held_out_bytes']:6d}B | {codecs['ZST3-tuned']['ns_per_seek']:7.1f} ns/seek | {codecs['ZST3-tuned']['decoded_mib_per_sec']:7.1f} MiB/s\n"
        f"  -> Smallest={smallest_ho} | Fastest={fastest_ho} | 2D Pareto={pareto_optimal}",
        flush=True,
    )
    return {
        'label': label,
        'train_docs': len(all_train),
        'held_out_docs': len(all_test),
        'train_raw_bytes': sum(len(x) for x in all_train),
        'held_out_raw_bytes': sum(len(x) for x in all_test),
        'mean_held_out_doc_bytes': round(sum(len(x) for x in all_test) / len(all_test), 2),
        'codecs': codecs,
        'smallest_held_out_codec': smallest_ho,
        'fastest_held_out_codec': fastest_ho,
        'pareto_2d_held_out': pareto_optimal,
    }


def main() -> None:
    t0 = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix='ra-pareto-bins-') as btmp:
        bdir = Path(btmp)
        c_bench_bin = compile_c_bench(bdir)
        eng_bin = compile_engine(bdir)

        # Load CodeNet primary -> secondary (for DCC held-out throughput + size comparison)
        manifest = json.loads((CODENET_DIR / 'manifest.json').read_text(encoding='utf-8'))
        pri_pairs = manifest['splits']['primary']['pairs']
        sec_pairs = manifest['splits']['secondary']['pairs']
        cn_pri_py = [(CODENET_DIR / p['python']['path']).read_bytes() for p in pri_pairs]
        cn_pri_js = [(CODENET_DIR / p['javascript']['path']).read_bytes() for p in pri_pairs]
        cn_sec_py = [(CODENET_DIR / p['python']['path']).read_bytes() for p in sec_pairs]
        cn_sec_js = [(CODENET_DIR / p['javascript']['path']).read_bytes() for p in sec_pairs]

        dict_k1024 = load_saved_codenet_dict(1024)
        dict_k4096 = load_saved_codenet_dict(4096)

        # Sample untouched workspace short/medium/long suites
        wgsl_short = sample_band_pool(ALL_SAFE_ROOTS, ['.wgsl'], 160, min_bytes=64, max_bytes=240, seed_tag='r2b-ws')
        json_short = sample_band_pool(ALL_SAFE_ROOTS, ['.json'], 160, min_bytes=64, max_bytes=240, seed_tag='r2b-js')
        ts_short = sample_band_pool(ALL_SAFE_ROOTS, ['.ts'], 160, min_bytes=64, max_bytes=260, seed_tag='r2b-tss')
        mjs_short = sample_band_pool(ALL_SAFE_ROOTS, ['.mjs', '.cjs', '.js'], 160, min_bytes=64, max_bytes=280, seed_tag='r2b-mjss')
        ts_med = sample_band_pool(ALL_SAFE_ROOTS, ['.ts'], 100, min_bytes=400, max_bytes=850, seed_tag='r2b-tsm')
        json_med = sample_band_pool(ALL_SAFE_ROOTS, ['.json'], 100, min_bytes=350, max_bytes=850, seed_tag='r2b-jmed')
        js_long = sample_band_pool(ALL_SAFE_ROOTS, ['.js'], 80, min_bytes=1400, max_bytes=3400, seed_tag='r2b-jsl')
        wgsl_long = sample_band_pool(ALL_SAFE_ROOTS, ['.wgsl'], 80, min_bytes=1400, max_bytes=3400, seed_tag='r2b-wl')

        suites = [
            evaluate_suite(
                c_bench_bin, eng_bin,
                label='codenet_held_out_K1024',
                train_1=cn_pri_py, train_2=cn_pri_js, test_1=cn_sec_py, test_2=cn_sec_js,
                fixed_bit3_entries=dict_k1024,
            ),
            evaluate_suite(
                c_bench_bin, eng_bin,
                label='codenet_held_out_K4096',
                train_1=cn_pri_py, train_2=cn_pri_js, test_1=cn_sec_py, test_2=cn_sec_js,
                fixed_bit3_entries=dict_k4096,
            ),
            evaluate_suite(
                c_bench_bin, eng_bin,
                label='short_wgsl_vs_json_80_to_80',
                train_1=[b for _, b in wgsl_short[:80]], train_2=[b for _, b in json_short[:80]],
                test_1=[b for _, b in wgsl_short[80:160]], test_2=[b for _, b in json_short[80:160]],
            ),
            evaluate_suite(
                c_bench_bin, eng_bin,
                label='short_ts_vs_mjs_80_to_80',
                train_1=[b for _, b in ts_short[:80]], train_2=[b for _, b in mjs_short[:80]],
                test_1=[b for _, b in ts_short[80:160]], test_2=[b for _, b in mjs_short[80:160]],
            ),
            evaluate_suite(
                c_bench_bin, eng_bin,
                label='med_ts_vs_json_50_to_50',
                train_1=[b for _, b in ts_med[:50]], train_2=[b for _, b in json_med[:50]],
                test_1=[b for _, b in ts_med[50:100]], test_2=[b for _, b in json_med[50:100]],
            ),
            evaluate_suite(
                c_bench_bin, eng_bin,
                label='long_js_vs_wgsl_40_to_40',
                train_1=[b for _, b in js_long[:40]], train_2=[b for _, b in wgsl_long[:40]],
                test_1=[b for _, b in js_long[40:80]], test_2=[b for _, b in wgsl_long[40:80]],
            ),
        ]

    report = {
        'schema': 'bits-ra-pareto-benchmark/v1',
        'elapsed_sec': round(time.perf_counter() - t0, 2),
        'seeks_per_cell': 100000,
        'suites': suites,
    }
    out_dir = HERE / 'results'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'ra_pareto_benchmark_v1.json'
    out_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'\nWrote {out_path}')


if __name__ == '__main__':
    main()
