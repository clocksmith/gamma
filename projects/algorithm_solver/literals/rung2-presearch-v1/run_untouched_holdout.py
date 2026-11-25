#!/usr/bin/env python3
"""Blind untouched-corpus Rung 2 evaluation for `bits-rung2-presearch-v2`.

Tests the frozen Miller-Madow-debiased pre-search predictor (`raw_predictor.py`)
against BOTH required baselines under the upgraded Rung 2 success bar:
  1. Layout baseline (`default_always_B`): always pick shared dictionary + separate
     per-language tables (`Design B`) with two-part MDL byte-cost stopping.
     Isolates untouched cells where `default_always_B` loses to the fair-search
     oracle by `> 1.0%`, and scores whether `raw_predictor` beats `default_always_B`
     on those cells AND overall.
  2. Stopping-size baseline (`mdl_byte_stop_kmax`): ordinary two-part MDL / byte-cost
     stopping along the full `K=4,096` chains (holding layout fixed), separated from
     pre-search `K_hat` truncation so layout gains and stopping-size gains/losses are
     never conflated.

Evaluated across 4 untouched first-party workspace language pairs x 3 corpus sizes
(12 cells total):
  - Zig (`fawn/*.zig`) vs. WGSL (`fawn/*.wgsl`) at n in {8, 30, 80}
  - C (`fawn/*.c`) vs. TypeScript (`hatch/*.ts`) at n in {8, 30, 80}
  - Shell (`reploid/*.sh`) vs. WGSL (`doppler/*.wgsl`) at n in {8, 30, 75}
  - Zig (`fawn/*.zig`) vs. disjoint Zig (`fawn/*.zig`) control at n in {8, 30, 80}
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
DECO_ROOT = Path('/Users/xyz/deco')
sys.path.insert(0, str(HERE))

import raw_predictor as RP  # noqa: E402
from equal_budget_eval import DEFAULT_ARMS, DEFAULT_K_GRID, evaluate_presearch_vs_oracle  # noqa: E402

SKIP_DIRS = {
    '.git', 'node_modules', '.venv', 'venv', 'target', 'dist',
    'build', '.zig-cache', 'zig-out', '__pycache__', 'third_party', 'vendor',
}


def sample_deterministic_pool(
    base_dir: Path,
    suffix: str,
    max_needed: int,
    *,
    min_bytes: int = 256,
    max_bytes: int = 4096,
) -> list[tuple[str, bytes]]:
    by_content_sha: dict[str, tuple[str, bytes]] = {}
    for cur, dirs, files in os.walk(base_dir):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith('.'))
        for fn in sorted(files):
            if not fn.endswith(suffix):
                continue
            fp = Path(cur) / fn
            try:
                sz = fp.stat().st_size
                if sz < min_bytes or sz > max_bytes:
                    continue
                raw = fp.read_bytes()
            except OSError:
                continue
            if b'\x00' in raw or not (min_bytes <= len(raw) <= max_bytes):
                continue
            c_sha = hashlib.sha256(raw).hexdigest()
            if c_sha not in by_content_sha:
                rel = str(fp.relative_to(DECO_ROOT))
                by_content_sha[c_sha] = (rel, raw)

    ranked = sorted(
        by_content_sha.items(),
        key=lambda kv: hashlib.sha256(f'bits-rung2-holdout:{kv[0]}'.encode('ascii')).hexdigest(),
    )
    if len(ranked) < max_needed:
        raise RuntimeError(f'only {len(ranked)} eligible {suffix} files under {base_dir} (need {max_needed})')
    return [kv[1] for kv in ranked[:max_needed]]


def main() -> None:
    t0 = time.perf_counter()
    pred_sha256 = hashlib.sha256(Path(RP.__file__).read_bytes()).hexdigest()

    zig_pool = sample_deterministic_pool(DECO_ROOT / 'fawn', '.zig', 180)
    wgsl_fawn = sample_deterministic_pool(DECO_ROOT / 'fawn', '.wgsl', 80)
    c_pool = sample_deterministic_pool(DECO_ROOT / 'fawn', '.c', 80)
    ts_pool = sample_deterministic_pool(DECO_ROOT / 'hatch', '.ts', 80)
    sh_pool = sample_deterministic_pool(DECO_ROOT / 'reploid', '.sh', 75)
    wgsl_dopp = sample_deterministic_pool(DECO_ROOT / 'doppler', '.wgsl', 75)

    suite_specs = [
        ('zig_vs_wgsl_n8', zig_pool[:8], wgsl_fawn[:8]),
        ('zig_vs_wgsl_n30', zig_pool[:30], wgsl_fawn[:30]),
        ('zig_vs_wgsl_n80', zig_pool[:80], wgsl_fawn[:80]),
        ('c_vs_ts_n8', c_pool[:8], ts_pool[:8]),
        ('c_vs_ts_n30', c_pool[:30], ts_pool[:30]),
        ('c_vs_ts_n80', c_pool[:80], ts_pool[:80]),
        ('sh_vs_wgsl_n8', sh_pool[:8], wgsl_dopp[:8]),
        ('sh_vs_wgsl_n30', sh_pool[:30], wgsl_dopp[:30]),
        ('sh_vs_wgsl_n75', sh_pool[:75], wgsl_dopp[:75]),
        ('zig_vs_zig_ctrl_n8', zig_pool[:8], zig_pool[90:98]),
        ('zig_vs_zig_ctrl_n30', zig_pool[:30], zig_pool[90:120]),
        ('zig_vs_zig_ctrl_n80', zig_pool[:80], zig_pool[90:170]),
    ]

    evaluations = []
    for label, pair1, pair2 in suite_specs:
        docs_1 = [b for _, b in pair1]
        docs_2 = [b for _, b in pair2]
        res = evaluate_presearch_vs_oracle(
            docs_1, docs_2,
            label=label,
            k_grid=DEFAULT_K_GRID,
            arms=DEFAULT_ARMS,
            limit_seconds=2.5,
            step=64,
        )
        res['oracle_cells_compact'] = [
            {
                'layout': c['layout'],
                'K': c['K'],
                'feasible': c['feasible'],
                'total_bytes': c.get('total_bytes'),
                'entries': c.get('entries'),
                'reparsed_pairs_evaluated': c.get('reparsed_pairs_evaluated'),
            }
            for c in res.pop('oracle_cells')
        ]
        res['manifest_files_sample'] = {
            'lang1_count': len(pair1),
            'lang2_count': len(pair2),
            'lang1_first3': [p for p, _ in pair1[:3]],
            'lang2_first3': [p for p, _ in pair2[:3]],
        }
        evaluations.append(res)
        m = res['metrics']
        p = res['prediction']
        o = res['oracle']
        dl = res['decoupled_layout_score']
        ds = res['decoupled_stopping_score']
        print(
            f"[{label:22s}] raw={res['raw_bytes_total']:7d}B | "
            f"pred=({p['layout_hat']},K={p['K_hat']:4d}) {p['executed_total_bytes']:6d}B | "
            f"ora=({o['best_layout']},K={o['best_K']:4d}) {o['best_total_bytes']:6d}B | "
            f"defB_loss={dl['default_always_B_loss_bytes']:+4d}B ({dl['default_always_B_loss_pct']:+.2f}%) | "
            f"layout_gain_vs_defB={dl['layout_gain_over_default_B_bytes']:+4d}B | "
            f"mdl_save={ds['ordinary_mdl_stopping_saving_bytes']}B k_trunc={ds['k_hat_presearch_truncation_cost_bytes']:+4d}B | "
            f"saved={m['search_seconds_saved_vs_grid']:.1f}s",
            flush=True,
        )

    # Upgraded Rung 2 bar summary:
    # 1. Subset where `default_always_B` loses to the fair-search oracle by > 1.0%
    gt1_cells = [e for e in evaluations if e['decoupled_layout_score']['default_B_misses_gt_1pct']]
    gt1_beats = sum(1 for e in gt1_cells if e['decoupled_layout_score']['beats_default_B'])
    gt1_mean_gain = (
        sum(int(e['decoupled_layout_score']['layout_gain_over_default_B_bytes'] or 0) for e in gt1_cells) / len(gt1_cells)
        if gt1_cells else 0.0
    )

    all_layout_gain = sum(int(e['decoupled_layout_score']['layout_gain_over_default_B_bytes'] or 0) for e in evaluations)
    all_layout_regret = sum(int(e['decoupled_layout_score']['layout_regret_vs_oracle_bytes']) for e in evaluations)
    all_mdl_saving = sum(int(e['decoupled_stopping_score']['ordinary_mdl_stopping_saving_bytes'] or 0) for e in evaluations)
    all_k_trunc_cost = sum(int(e['decoupled_stopping_score']['k_hat_presearch_truncation_cost_bytes']) for e in evaluations)
    plug_in_total_lost = sum(
        int(e['ablations']['plug_in_mi_without_miller_madow']['bytes_lost_vs_oracle'] or 0) for e in evaluations
    )

    exact_layout_hits = sum(1 for e in evaluations if e['metrics']['picked_exact_layout'])
    within_1pct_hits = sum(1 for e in evaluations if e['metrics']['picked_within_1pct_materiality'])

    out_doc = {
        'schema': 'bits-rung2-untouched-holdout-results/v2',
        'frozen_predictor_rule_version': RP.FROZEN_RULE_VERSION,
        'frozen_predictor_sha256': pred_sha256,
        'post_hoc_retuning': False,
        'cells_evaluated': len(evaluations),
        'upgraded_rung2_layout_bar': {
            'cells_where_default_always_B_misses_gt_1pct': len(gt1_cells),
            'cell_labels_where_default_B_misses_gt_1pct': [e['label'] for e in gt1_cells],
            'predictor_beats_default_B_on_gt_1pct_misses': f'{gt1_beats}/{len(gt1_cells)}',
            'mean_layout_bytes_gained_over_default_B_on_gt_1pct_misses': round(gt1_mean_gain, 2),
            'total_layout_bytes_gained_over_default_B_all_12_cells': all_layout_gain,
            'total_layout_regret_vs_oracle_all_12_cells': all_layout_regret,
            'uncorrected_plug_in_mi_total_bytes_lost_all_12_cells': plug_in_total_lost,
        },
        'decoupled_stopping_vs_mdl_summary': {
            'total_ordinary_mdl_byte_stopping_saving_over_tokmin_fill_bytes': all_mdl_saving,
            'total_presearch_k_hat_truncation_extra_cost_vs_full_mdl_bytes': all_k_trunc_cost,
            'mean_search_seconds_saved_vs_single_layout_k4096': round(
                sum(e['decoupled_stopping_score']['search_seconds_saved_vs_single_layout_kmax'] for e in evaluations) / len(evaluations),
                3,
            ),
        },
        'overall_summary': {
            'exact_layout_accuracy': f'{exact_layout_hits}/{len(evaluations)}',
            'within_1pct_materiality_rate': f'{within_1pct_hits}/{len(evaluations)}',
            'mean_total_bytes_lost_vs_oracle': round(sum(e['metrics']['bytes_lost'] for e in evaluations) / len(evaluations), 2),
            'total_search_seconds_saved_vs_full_grid': round(
                sum(e['metrics']['search_seconds_saved_vs_grid'] for e in evaluations), 2
            ),
            'wall_elapsed_sec': round(time.perf_counter() - t0, 2),
        },
        'evaluations': evaluations,
    }
    out_dir = HERE / 'results'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'untouched_holdout_v2.json'
    out_path.write_text(json.dumps(out_doc, indent=2) + '\n', encoding='utf-8')
    print(f"\nWrote {out_path}:")
    print(json.dumps({
        'upgraded_rung2_layout_bar': out_doc['upgraded_rung2_layout_bar'],
        'decoupled_stopping_vs_mdl_summary': out_doc['decoupled_stopping_vs_mdl_summary'],
        'overall_summary': out_doc['overall_summary'],
    }, indent=2))


if __name__ == '__main__':
    main()
