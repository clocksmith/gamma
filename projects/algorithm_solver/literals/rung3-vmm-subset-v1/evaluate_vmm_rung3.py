#!/usr/bin/env python3
"""Rung 3 Benchmark: Variational Two-Part MM Subset Selection vs. 2026 MDL Prefix Stopping.

Runs two clean, reproducible experiments (leaving `codenet-replication-v1/` untouched):
  1. Exported CodeNet Nash Certificate & Unordered `tokbest` Rescue Audit:
     - Audits all exported `codenet-replication-v1` dictionaries (`primary` & `secondary`,
       `K in {256, 1024, 4096}`, `Design A`, `Design B`, `Design C`, `tokbest`) to check whether
       `byte_encode.py`'s emitted parses achieve `0`-bit suboptimality under their emitted active
       Huffman tables (`is_certified_nash_fixed_point`).
     - Separates simple post-hoc zero-count pruning (`46` and `63` dead entries on `tokbest`)
       from full Variational Two-Part MM (`vmm_subset_polish`), testing how much of the `18.2%` /
       `17.2%` token-selection penalty VMM recovers from an unordered 4,096-entry dictionary.
  2. Head-to-Head vs. Two-Part MDL Prefix Stopping (Liyanage & Yvon 2026; Nouri 2026):
     - Compares `mdl-prefix-stop` (sweeping candidate prefix sizes + iterative bit-cost reparsing)
       against `vmm-subset` on identical search chains (`BPE`, `greedy-byte`, `greedy-entry`, and
       `BPE U greedy-entry` union) across:
         * CodeNet `primary -> secondary` (`K_max = 4,096`, Design B),
         * Untouched `short_wgsl_vs_json_80_to_80` (`L_mean = 149 B`, 2D Pareto regime),
         * Untouched `short_ts_vs_mjs_80_to_80` (`L_mean = 151 B`, 2D Pareto regime),
       evaluating both in-sample and disjoint held-out serialized `BIT3` random-access bytes +
       native-C single-record seek latency (`ra_codecs_bench.c`).
"""
from __future__ import annotations

import json
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
RUNG2_DIR = HERE.parent / 'rung2-presearch-v1'
SHORT_RA_DIR = HERE.parent / 'rung2-short-ra-bench-v1'
DECO_ROOT = Path('/Users/xyz/deco')

sys.path.insert(0, str(CODENET_DIR))
sys.path.insert(0, str(RUNG2_DIR))
sys.path.insert(0, str(SHORT_RA_DIR))
sys.path.insert(0, str(HERE))

import byte_encode as BE  # noqa: E402
from equal_budget_eval import (  # noqa: E402
    candidate_prefix_sizes,
    compile_engine,
    read_chain_entries,
    run_engine_arm,
    write_corpus_list,
)
from run_completed_chain_and_regime_eval import (  # noqa: E402
    sample_band_pool,
    serialize_and_verify_bit3_archive,
)
from run_ra_pareto_bench import ALL_SAFE_ROOTS, compile_c_bench, run_c_bench, write_raw_verify_blob  # noqa: E402
from vmm_subset_polish import certify_emitted_table_optimality, variational_two_part_mm  # noqa: E402


def load_hex_dict(path: Path) -> list[bytes]:
    return [bytes.fromhex(x.strip()) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]


def audit_exported_codenet_certificates(
    pri_py: Sequence[bytes], pri_js: Sequence[bytes],
    sec_py: Sequence[bytes], sec_js: Sequence[bytes],
) -> dict[str, Any]:
    splits = {
        'primary': (pri_py, pri_js, list(pri_py) + list(pri_js)),
        'secondary': (sec_py, sec_js, list(sec_py) + list(sec_js)),
    }
    stream_checks = []
    for hex_file in sorted((CODENET_DIR / 'dictionaries').glob('*.hex')):
        name = hex_file.name
        split_key = 'primary' if name.startswith('primary_') else 'secondary'
        py_d, js_d, all_d = splits[split_key]
        ents = load_hex_dict(hex_file)

        if '_C_py_' in name:
            bm = BE.optimize_byte_segmentation(py_d, BE.build_trie(ents))['byte_min']
            c = certify_emitted_table_optimality(py_d, ents, bm['lengths'], bm['payload_bits'])
            stream_checks.append({'dict_file': name, 'stream': 'python', **c})
        elif '_C_js_' in name:
            bm = BE.optimize_byte_segmentation(js_d, BE.build_trie(ents))['byte_min']
            c = certify_emitted_table_optimality(js_d, ents, bm['lengths'], bm['payload_bits'])
            stream_checks.append({'dict_file': name, 'stream': 'javascript', **c})
        elif '_B_' in name:
            bm1 = BE.optimize_byte_segmentation(py_d, BE.build_trie(ents))['byte_min']
            bm2 = BE.optimize_byte_segmentation(js_d, BE.build_trie(ents))['byte_min']
            c1 = certify_emitted_table_optimality(py_d, ents, bm1['lengths'], bm1['payload_bits'])
            c2 = certify_emitted_table_optimality(js_d, ents, bm2['lengths'], bm2['payload_bits'])
            stream_checks.append({'dict_file': name, 'stream': 'python', **c1})
            stream_checks.append({'dict_file': name, 'stream': 'javascript', **c2})
        else:
            bm = BE.optimize_byte_segmentation(all_d, BE.build_trie(ents))['byte_min']
            c = certify_emitted_table_optimality(all_d, ents, bm['lengths'], bm['payload_bits'])
            stream_checks.append({'dict_file': name, 'stream': 'merged', **c})

    # Also test unordered `tokbest` at K=4096: dead-entry-only pruning vs. full VMM rescue!
    tokbest_rescue = {}
    for split_key, (py_d, js_d, all_d) in splits.items():
        tb_ents = load_hex_dict(CODENET_DIR / 'dictionaries' / f'{split_key}_K4096_tokbest.hex')
        a_ents = load_hex_dict(CODENET_DIR / 'dictionaries' / f'{split_key}_K4096_A_tm.hex')

        bm_tb = BE.optimize_byte_segmentation(all_d, BE.build_trie(tb_ents))['byte_min']
        tb_reparsed_bytes = sum(1 + len(e) for e in tb_ents) + (len(tb_ents) + 1) + bm_tb['payload_bytes']

        bm_a = BE.optimize_byte_segmentation(all_d, BE.build_trie(a_ents))['byte_min']
        a_reparsed_bytes = sum(1 + len(e) for e in a_ents) + (len(a_ents) + 1) + bm_a['payload_bytes']

        # Dead-entry-only pruning (deleting the 46 / 63 zero-count entries after reparsing):
        req_s = {bytes([b]) for d in all_d for b in d}
        alive_only = [e for e in tb_ents if (e in req_s) or bm_tb['lengths'].get(e, 0) > 0]
        dead_pruned_bytes = sum(1 + len(e) for e in alive_only) + (len(alive_only) + 1) + bm_tb['payload_bytes']

        # Full Variational Two-Part MM on unordered `tokbest`:
        vmm_res = variational_two_part_mm(py_d, js_d, tb_ents, n_tables=1)
        gap_initial = tb_reparsed_bytes - a_reparsed_bytes
        gap_recovered = tb_reparsed_bytes - vmm_res['total_archive_bytes']
        tokbest_rescue[split_key] = {
            'size_selected_A_bytes': a_reparsed_bytes,
            'tokbest_reparsed_bytes': tb_reparsed_bytes,
            'tokbest_dead_pruned_only_bytes': dead_pruned_bytes,
            'dead_entries_removed_only': len(tb_ents) - len(alive_only),
            'tokbest_after_vmm_bytes': vmm_res['total_archive_bytes'],
            'vmm_selected_entries': len(vmm_res['entries']),
            'penalty_gap_closed_pct': round(100.0 * gap_recovered / gap_initial, 2),
        }

    n_certified = sum(1 for s in stream_checks if s['is_certified_nash_fixed_point'])
    return {
        'streams_audited': len(stream_checks),
        'certified_zero_bit_gap_streams': n_certified,
        'max_parse_suboptimality_bits': max(s['parse_suboptimality_bits'] for s in stream_checks),
        'tokbest_k4096_vmm_rescue': tokbest_rescue,
    }


def eval_mdl_prefix_stop_design_b(
    chain: Sequence[bytes],
    train_1: Sequence[bytes],
    train_2: Sequence[bytes],
) -> list[bytes]:
    sizes = candidate_prefix_sizes(len(chain), (256, 512, 1024, 2048, 4096), 64)
    scored = []
    for sz in sizes:
        ents = chain[:sz]
        rt = BE.build_trie(ents)
        sp1 = BE.segment_corpus_tokens(train_1, rt)
        sp2 = BE.segment_corpus_tokens(train_2, rt)
        if sp1[0] is None or sp2[0] is None:
            continue
        l1 = BE.canonical_huffman_lengths(sp1[1])
        l2 = BE.canonical_huffman_lengths(sp2[1])
        b1 = (BE.total_huffman_bits(sp1[1], l1) + 7) // 8
        b2 = (BE.total_huffman_bits(sp2[1], l2) + 7) // 8
        tot = sum(1 + len(e) for e in ents) + 2 * (len(ents) + 1) + 4 + b1 + b2
        scored.append((tot, sz))
    scored.sort()

    best_tot = 1 << 60
    best_ents: list[bytes] = list(chain)
    for _, sz in scored[:6]:
        ents = list(chain[:sz])
        blob, _ = serialize_and_verify_bit3_archive(ents, train_1, train_2, n_tables=2)
        if len(blob) < best_tot:
            best_tot = len(blob)
            best_ents = ents
    return best_ents


def serialize_in_and_heldout_bit3_with_c_speed(
    c_bench_bin: Path,
    entries: Sequence[bytes],
    train_1: Sequence[bytes],
    train_2: Sequence[bytes],
    test_1: Sequence[bytes],
    test_2: Sequence[bytes],
    wdir: Path,
    tag: str,
) -> dict[str, Any]:
    in_blob, _ = serialize_and_verify_bit3_archive(entries, train_1, train_2, n_tables=2)
    present = set(entries)
    all_test = list(test_1) + list(test_2)
    unseen = sorted({bytes([b]) for d in all_test for b in d if bytes([b]) not in present})
    oos_e = list(entries) + unseen
    rt = BE.build_trie(oos_e)
    _, tc1, _ = BE.segment_corpus_tokens(train_1, rt)
    _, tc2, _ = BE.segment_corpus_tokens(train_2, rt)
    sm1, sm2 = Counter(tc1), Counter(tc2)
    for e in oos_e:
        if sm1[e] == 0:
            sm1[e] = 1
        if sm2[e] == 0:
            sm2[e] = 1
    fr = (BE.canonical_huffman_lengths(sm1), BE.canonical_huffman_lengths(sm2))
    ho_blob, _ = serialize_and_verify_bit3_archive(oos_e, test_1, test_2, n_tables=2, frozen_lengths=fr)

    raw_v = wdir / f'rv_{tag}.bin'
    ho_p = wdir / f'ho_{tag}.bit3'
    write_raw_verify_blob(all_test, raw_v)
    ho_p.write_bytes(ho_blob)
    perf = run_c_bench(c_bench_bin, 'BIT3', ho_p, raw_v, num_seeks=50000)
    return {
        'entries': len(entries),
        'in_sample_ra_bytes': len(in_blob),
        'held_out_ra_bytes': len(ho_blob),
        'held_out_ns_per_seek': perf['ns_per_seek'],
        'held_out_mib_per_sec': perf['decoded_mib_per_sec'],
    }


def compare_mdl_prefix_vs_vmm_on_suite(
    eng_bin: Path,
    c_bench_bin: Path,
    *,
    label: str,
    train_1: Sequence[bytes],
    train_2: Sequence[bytes],
    test_1: Sequence[bytes],
    test_2: Sequence[bytes],
    k_max: int,
    limit_sec: float = 12.0,
) -> dict[str, Any]:
    all_train = list(train_1) + list(train_2)
    with tempfile.TemporaryDirectory(prefix=f'vmm-{label}-') as tmp:
        wdir = Path(tmp)
        lf = write_corpus_list(all_train, wdir, 'both', list(range(len(all_train))))

        chains: dict[str, list[bytes]] = {}
        for arm in ('bpe', 'greedy-byte', 'greedy-entry'):
            cp = wdir / f'{arm}.txt'
            run_engine_arm(eng_bin, arm=arm, policy='s1-whole', max_entry_len=16, k_max=k_max, limit_sec=limit_sec, list_file=lf, out_chain=cp, run_tag='vmm')
            chains[arm] = [e for _, _, e in read_chain_entries(cp)]

        arms_out: dict[str, Any] = {}
        for arm in ('bpe', 'greedy-byte', 'greedy-entry'):
            mdl_ents = eval_mdl_prefix_stop_design_b(chains[arm], train_1, train_2)
            vmm_res = variational_two_part_mm(train_1, train_2, chains[arm], n_tables=2)
            vmm_ents = vmm_res['entries']

            mdl_eval = serialize_in_and_heldout_bit3_with_c_speed(
                c_bench_bin, mdl_ents, train_1, train_2, test_1, test_2, wdir, f'{arm}_mdl',
            )
            vmm_eval = serialize_in_and_heldout_bit3_with_c_speed(
                c_bench_bin, vmm_ents, train_1, train_2, test_1, test_2, wdir, f'{arm}_vmm',
            )
            arms_out[arm] = {
                'mdl_prefix_stop': mdl_eval,
                'vmm_subset': vmm_eval,
                'vmm_gain_in_sample_bytes': mdl_eval['in_sample_ra_bytes'] - vmm_eval['in_sample_ra_bytes'],
                'vmm_gain_held_out_bytes': mdl_eval['held_out_ra_bytes'] - vmm_eval['held_out_ra_bytes'],
            }

        # Also test multi-generator union `BPE U greedy-entry` + VMM (impossible for single-chain prefix stop!)
        union_seed = list(dict.fromkeys(chains['bpe'] + chains['greedy-entry']))
        union_vmm = variational_two_part_mm(train_1, train_2, union_seed, n_tables=2)
        union_eval = serialize_in_and_heldout_bit3_with_c_speed(
            c_bench_bin, union_vmm['entries'], train_1, train_2, test_1, test_2, wdir, 'union_vmm',
        )

    print(
        f"[{label:30s}]\n"
        f"  BPE          : MDL-stop={arms_out['bpe']['mdl_prefix_stop']['in_sample_ra_bytes']:6d}B (HO {arms_out['bpe']['mdl_prefix_stop']['held_out_ra_bytes']:6d}B) -> "
        f"VMM={arms_out['bpe']['vmm_subset']['in_sample_ra_bytes']:6d}B (HO {arms_out['bpe']['vmm_subset']['held_out_ra_bytes']:6d}B) "
        f"[in {arms_out['bpe']['vmm_gain_in_sample_bytes']:+d}B, HO {arms_out['bpe']['vmm_gain_held_out_bytes']:+d}B]\n"
        f"  greedy-byte  : MDL-stop={arms_out['greedy-byte']['mdl_prefix_stop']['in_sample_ra_bytes']:6d}B (HO {arms_out['greedy-byte']['mdl_prefix_stop']['held_out_ra_bytes']:6d}B) -> "
        f"VMM={arms_out['greedy-byte']['vmm_subset']['in_sample_ra_bytes']:6d}B (HO {arms_out['greedy-byte']['vmm_subset']['held_out_ra_bytes']:6d}B) "
        f"[in {arms_out['greedy-byte']['vmm_gain_in_sample_bytes']:+d}B, HO {arms_out['greedy-byte']['vmm_gain_held_out_bytes']:+d}B]\n"
        f"  greedy-entry : MDL-stop={arms_out['greedy-entry']['mdl_prefix_stop']['in_sample_ra_bytes']:6d}B (HO {arms_out['greedy-entry']['mdl_prefix_stop']['held_out_ra_bytes']:6d}B) -> "
        f"VMM={arms_out['greedy-entry']['vmm_subset']['in_sample_ra_bytes']:6d}B (HO {arms_out['greedy-entry']['vmm_subset']['held_out_ra_bytes']:6d}B) "
        f"[in {arms_out['greedy-entry']['vmm_gain_in_sample_bytes']:+d}B, HO {arms_out['greedy-entry']['vmm_gain_held_out_bytes']:+d}B]\n"
        f"  Union(BPE+GE)+VMM: in={union_eval['in_sample_ra_bytes']:6d}B | HO={union_eval['held_out_ra_bytes']:6d}B @ {union_eval['held_out_ns_per_seek']:.1f} ns/seek ({union_eval['held_out_mib_per_sec']:.1f} MiB/s)",
        flush=True,
    )
    return {
        'label': label,
        'arms': arms_out,
        'union_bpe_ge_vmm': union_eval,
    }


def main() -> None:
    t0 = time.perf_counter()
    manifest = json.loads((CODENET_DIR / 'manifest.json').read_text(encoding='utf-8'))
    pri_pairs = manifest['splits']['primary']['pairs']
    sec_pairs = manifest['splits']['secondary']['pairs']
    pri_py = [(CODENET_DIR / p['python']['path']).read_bytes() for p in pri_pairs]
    pri_js = [(CODENET_DIR / p['javascript']['path']).read_bytes() for p in pri_pairs]
    sec_py = [(CODENET_DIR / p['python']['path']).read_bytes() for p in sec_pairs]
    sec_js = [(CODENET_DIR / p['javascript']['path']).read_bytes() for p in sec_pairs]

    cert_audit = audit_exported_codenet_certificates(pri_py, pri_js, sec_py, sec_js)
    print('Exported CodeNet Nash certificate & tokbest VMM rescue audit:')
    print(json.dumps(cert_audit, indent=2), flush=True)

    wgsl_short = sample_band_pool(ALL_SAFE_ROOTS, ['.wgsl'], 160, min_bytes=64, max_bytes=240, seed_tag='r2b-ws')
    json_short = sample_band_pool(ALL_SAFE_ROOTS, ['.json'], 160, min_bytes=64, max_bytes=240, seed_tag='r2b-js')
    ts_short = sample_band_pool(ALL_SAFE_ROOTS, ['.ts'], 160, min_bytes=64, max_bytes=260, seed_tag='r2b-tss')
    mjs_short = sample_band_pool(ALL_SAFE_ROOTS, ['.mjs', '.cjs', '.js'], 160, min_bytes=64, max_bytes=280, seed_tag='r2b-mjss')

    with tempfile.TemporaryDirectory(prefix='vmm-bins-') as btmp:
        bdir = Path(btmp)
        eng_bin = compile_engine(bdir)
        c_bench_bin = compile_c_bench(bdir)

        suites = [
            compare_mdl_prefix_vs_vmm_on_suite(
                eng_bin, c_bench_bin,
                label='codenet_py_js_200_to_200',
                train_1=pri_py, train_2=pri_js, test_1=sec_py, test_2=sec_js,
                k_max=4096, limit_sec=15.0,
            ),
            compare_mdl_prefix_vs_vmm_on_suite(
                eng_bin, c_bench_bin,
                label='short_wgsl_vs_json_80_to_80',
                train_1=[b for _, b in wgsl_short[:80]], train_2=[b for _, b in json_short[:80]],
                test_1=[b for _, b in wgsl_short[80:160]], test_2=[b for _, b in json_short[80:160]],
                k_max=1024, limit_sec=8.0,
            ),
            compare_mdl_prefix_vs_vmm_on_suite(
                eng_bin, c_bench_bin,
                label='short_ts_vs_mjs_80_to_80',
                train_1=[b for _, b in ts_short[:80]], train_2=[b for _, b in mjs_short[:80]],
                test_1=[b for _, b in ts_short[80:160]], test_2=[b for _, b in mjs_short[80:160]],
                k_max=1024, limit_sec=8.0,
            ),
        ]

    report = {
        'schema': 'bits-rung3-vmm-subset-eval/v1',
        'elapsed_sec': round(time.perf_counter() - t0, 2),
        'codenet_nash_certificate_and_tokbest_audit': cert_audit,
        'mdl_prefix_stop_vs_vmm_suites': suites,
    }
    out_dir = HERE / 'results'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'vmm_subset_results_v1.json'
    out_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'\nWrote {out_path}')


if __name__ == '__main__':
    main()
