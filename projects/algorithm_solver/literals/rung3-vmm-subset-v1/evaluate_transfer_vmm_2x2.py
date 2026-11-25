#!/usr/bin/env python3
"""2x2 Mechanism Ablation for De-Cannibalized Homotopy Revival & Leave-One-Document-Out Transfer VMM.

Tests two explicit, falsifiable causal hypotheses across all 3 suites (`codenet_py_js_200_to_200`,
`short_wgsl_vs_json_80_to_80`, `short_ts_vs_mjs_80_to_80`) and 4 seed generators (`bpe`,
`greedy-byte`, `greedy-entry`, and unordered `union_bpe_ge`):

  - Hypothesis H1 (In-Sample Substring Cannibalization):
    In Iteration 4 (`vmm_subset_results_v1.json`), one-shot simultaneous VMM (`revival=False,
    shrinkage='none'`) lost `-444 B` (`10,717` vs `10,273 B`) on `short_wgsl_vs_json` `greedy-entry`
    and `-286 B` (`11,492` vs `11,206 B`) on `short_ts_vs_mjs` `greedy-entry` even in-sample.
    Enabling `revival=True` (`revival_only_vmm`) should eliminate substring cannibalization and win
    in-sample on all `9/9` (`100%`) single-chain cells while making `union_bpe_ge` beat individual
    chains in-sample.

  - Hypothesis H2 (Cross-Document Single-File Overfitting):
    In Iteration 4, in-sample VMM lost `-2,997 B` held-out on CodeNet `greedy-entry` (`103,564` vs
    `100,567 B`) and bloated `union_bpe_ge` to `104,782 B` held-out by retaining `df = 1..2`
    problem-specific literals. Enabling Leave-One-Document-Out risk shrinkage (`shrinkage='loo_doc'`)
    should eliminate single-document memorization, turning `transfer_vmm` (`revival=True,
    shrinkage='loo_doc'`) into a simultaneous winner over `mdl_prefix_stop` on held-out `BIT3`
    random-access archives across generators and multi-generator unions.
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Sequence

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
CODENET_DIR = HERE.parent / 'codenet-replication-v1'
RUNG2_DIR = HERE.parent / 'rung2-presearch-v1'
SHORT_RA_DIR = HERE.parent / 'rung2-short-ra-bench-v1'

sys.path.insert(0, str(CODENET_DIR))
sys.path.insert(0, str(RUNG2_DIR))
sys.path.insert(0, str(SHORT_RA_DIR))
sys.path.insert(0, str(HERE))

from equal_budget_eval import (  # noqa: E402
    compile_engine,
    read_chain_entries,
    run_engine_arm,
    write_corpus_list,
)
from evaluate_vmm_rung3 import (  # noqa: E402
    eval_mdl_prefix_stop_design_b,
    serialize_in_and_heldout_bit3_with_c_speed,
)
from run_completed_chain_and_regime_eval import sample_band_pool  # noqa: E402
from run_ra_pareto_bench import ALL_SAFE_ROOTS, compile_c_bench  # noqa: E402
from transfer_vmm import transfer_variational_mm  # noqa: E402


CELLS_2X2 = (
    ('base_vmm', False, 'none'),
    ('revival_only_vmm', True, 'none'),
    ('loo_only_vmm', False, 'loo_doc'),
    ('transfer_vmm', True, 'loo_doc'),
)


def evaluate_suite_2x2(
    eng_bin: Path,
    c_bench_bin: Path,
    *,
    label: str,
    train_1: Sequence[bytes],
    train_2: Sequence[bytes],
    test_1: Sequence[bytes],
    test_2: Sequence[bytes],
    k_max: int,
    limit_sec: float,
) -> dict[str, Any]:
    all_train = list(train_1) + list(train_2)
    with tempfile.TemporaryDirectory(prefix=f'tvmm2x2-{label}-') as tmp:
        wdir = Path(tmp)
        lf = write_corpus_list(all_train, wdir, 'both', list(range(len(all_train))))

        chains: dict[str, list[bytes]] = {}
        for arm in ('bpe', 'greedy-byte', 'greedy-entry'):
            cp = wdir / f'{arm}.txt'
            run_engine_arm(
                eng_bin, arm=arm, policy='s1-whole', max_entry_len=16,
                k_max=k_max, limit_sec=limit_sec, list_file=lf, out_chain=cp, run_tag='tvmm',
            )
            chains[arm] = [e for _, _, e in read_chain_entries(cp)]

        chains['union_bpe_ge'] = list(dict.fromkeys(chains['bpe'] + chains['greedy-entry']))

        suite_out: dict[str, Any] = {}
        print(f'\n=== {label} (K_max={k_max}) ===', flush=True)
        for gen_name in ('bpe', 'greedy-byte', 'greedy-entry', 'union_bpe_ge'):
            seed = chains[gen_name]
            gen_res: dict[str, Any] = {}
            if gen_name != 'union_bpe_ge':
                mdl_ents = eval_mdl_prefix_stop_design_b(seed, train_1, train_2)
                gen_res['mdl_prefix_stop'] = serialize_in_and_heldout_bit3_with_c_speed(
                    c_bench_bin, mdl_ents, train_1, train_2, test_1, test_2, wdir, f'{gen_name}_mdl',
                )
            else:
                gen_res['mdl_prefix_stop'] = None

            for cell_name, rev, shr in CELLS_2X2:
                tv = transfer_variational_mm(
                    train_1, train_2, seed, n_tables=2, revival=rev, shrinkage=shr,
                )
                ev = serialize_in_and_heldout_bit3_with_c_speed(
                    c_bench_bin, tv['entries'], train_1, train_2, test_1, test_2, wdir, f'{gen_name}_{cell_name}',
                )
                ev['certified_nash'] = tv['is_certified_nash_fixed_point']
                ev['revived_total'] = tv.get('revived_substrings_used', 0)
                gen_res[cell_name] = ev

            if gen_res['mdl_prefix_stop'] is not None:
                m_in = gen_res['mdl_prefix_stop']['in_sample_ra_bytes']
                m_ho = gen_res['mdl_prefix_stop']['held_out_ra_bytes']
                gen_res['deltas_vs_mdl_prefix_stop'] = {
                    cell_name: {
                        'in_sample_saved_bytes': m_in - gen_res[cell_name]['in_sample_ra_bytes'],
                        'held_out_saved_bytes': m_ho - gen_res[cell_name]['held_out_ra_bytes'],
                    }
                    for cell_name, _, _ in CELLS_2X2
                }
                print(
                    f"  {gen_name:13s} | MDL={m_in:6d}/{m_ho:6d} "
                    f"| Base={gen_res['base_vmm']['in_sample_ra_bytes']:6d}/{gen_res['base_vmm']['held_out_ra_bytes']:6d} "
                    f"| RevOnly={gen_res['revival_only_vmm']['in_sample_ra_bytes']:6d}/{gen_res['revival_only_vmm']['held_out_ra_bytes']:6d} "
                    f"| LOOOnly={gen_res['loo_only_vmm']['in_sample_ra_bytes']:6d}/{gen_res['loo_only_vmm']['held_out_ra_bytes']:6d} "
                    f"| TransferVMM={gen_res['transfer_vmm']['in_sample_ra_bytes']:6d}/{gen_res['transfer_vmm']['held_out_ra_bytes']:6d} "
                    f"(HO vs MDL: {m_ho - gen_res['transfer_vmm']['held_out_ra_bytes']:+d}B)",
                    flush=True,
                )
            else:
                print(
                    f"  {gen_name:13s} | (unordered union) "
                    f"| Base={gen_res['base_vmm']['in_sample_ra_bytes']:6d}/{gen_res['base_vmm']['held_out_ra_bytes']:6d} "
                    f"| RevOnly={gen_res['revival_only_vmm']['in_sample_ra_bytes']:6d}/{gen_res['revival_only_vmm']['held_out_ra_bytes']:6d} "
                    f"| LOOOnly={gen_res['loo_only_vmm']['in_sample_ra_bytes']:6d}/{gen_res['loo_only_vmm']['held_out_ra_bytes']:6d} "
                    f"| TransferVMM={gen_res['transfer_vmm']['in_sample_ra_bytes']:6d}/{gen_res['transfer_vmm']['held_out_ra_bytes']:6d}",
                    flush=True,
                )
            suite_out[gen_name] = gen_res

    return {'label': label, 'k_max': k_max, 'generators': suite_out}


def summarize_2x2(suites: Sequence[dict[str, Any]]) -> dict[str, Any]:
    single_gens = ('bpe', 'greedy-byte', 'greedy-entry')
    summary: dict[str, Any] = {}
    for cell_name, _, _ in CELLS_2X2:
        in_wins = 0
        ho_wins = 0
        in_sum = 0
        ho_sum = 0
        total_cells = 0
        for s in suites:
            for g in single_gens:
                d = s['generators'][g]['deltas_vs_mdl_prefix_stop'][cell_name]
                total_cells += 1
                if d['in_sample_saved_bytes'] > 0:
                    in_wins += 1
                if d['held_out_saved_bytes'] > 0:
                    ho_wins += 1
                in_sum += d['in_sample_saved_bytes']
                ho_sum += d['held_out_saved_bytes']
        summary[cell_name] = {
            'single_chain_cells': total_cells,
            'in_sample_wins_vs_mdl_prefix': in_wins,
            'held_out_wins_vs_mdl_prefix': ho_wins,
            'net_in_sample_bytes_saved_vs_mdl_prefix': in_sum,
            'net_held_out_bytes_saved_vs_mdl_prefix': ho_sum,
        }
    return summary


def main() -> None:
    t0 = time.perf_counter()
    manifest = json.loads((CODENET_DIR / 'manifest.json').read_text(encoding='utf-8'))
    pri_pairs = manifest['splits']['primary']['pairs']
    sec_pairs = manifest['splits']['secondary']['pairs']
    pri_py = [(CODENET_DIR / p['python']['path']).read_bytes() for p in pri_pairs]
    pri_js = [(CODENET_DIR / p['javascript']['path']).read_bytes() for p in pri_pairs]
    sec_py = [(CODENET_DIR / p['python']['path']).read_bytes() for p in sec_pairs]
    sec_js = [(CODENET_DIR / p['javascript']['path']).read_bytes() for p in sec_pairs]

    wgsl_short = sample_band_pool(ALL_SAFE_ROOTS, ['.wgsl'], 160, min_bytes=64, max_bytes=240, seed_tag='r2b-ws')
    json_short = sample_band_pool(ALL_SAFE_ROOTS, ['.json'], 160, min_bytes=64, max_bytes=240, seed_tag='r2b-js')
    ts_short = sample_band_pool(ALL_SAFE_ROOTS, ['.ts'], 160, min_bytes=64, max_bytes=260, seed_tag='r2b-tss')
    mjs_short = sample_band_pool(ALL_SAFE_ROOTS, ['.mjs', '.cjs', '.js'], 160, min_bytes=64, max_bytes=280, seed_tag='r2b-mjss')

    with tempfile.TemporaryDirectory(prefix='tvmm2x2-bins-') as btmp:
        bdir = Path(btmp)
        eng_bin = compile_engine(bdir)
        c_bench_bin = compile_c_bench(bdir)

        suites = [
            evaluate_suite_2x2(
                eng_bin, c_bench_bin,
                label='codenet_py_js_200_to_200',
                train_1=pri_py, train_2=pri_js, test_1=sec_py, test_2=sec_js,
                k_max=4096, limit_sec=15.0,
            ),
            evaluate_suite_2x2(
                eng_bin, c_bench_bin,
                label='short_wgsl_vs_json_80_to_80',
                train_1=[b for _, b in wgsl_short[:80]], train_2=[b for _, b in json_short[:80]],
                test_1=[b for _, b in wgsl_short[80:160]], test_2=[b for _, b in json_short[80:160]],
                k_max=1024, limit_sec=8.0,
            ),
            evaluate_suite_2x2(
                eng_bin, c_bench_bin,
                label='short_ts_vs_mjs_80_to_80',
                train_1=[b for _, b in ts_short[:80]], train_2=[b for _, b in mjs_short[:80]],
                test_1=[b for _, b in ts_short[80:160]], test_2=[b for _, b in mjs_short[80:160]],
                k_max=1024, limit_sec=8.0,
            ),
        ]

    agg = summarize_2x2(suites)
    print('\n=== 2x2 Aggregate Summary Across All 9 Single-Chain Cells ===')
    print(json.dumps(agg, indent=2), flush=True)

    report = {
        'schema': 'bits-rung3-transfer-vmm-2x2/v1',
        'elapsed_sec': round(time.perf_counter() - t0, 2),
        'aggregate_9_cell_summary': agg,
        'suites': suites,
    }
    out_dir = HERE / 'results'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'transfer_vmm_2x2_results_v1.json'
    out_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'\nWrote {out_path}')


if __name__ == '__main__':
    main()
