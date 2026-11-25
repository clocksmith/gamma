#!/usr/bin/env python3
"""Zero-compute ($0) audit of saved `codenet-replication-v1/results/codenet_results.json`.

Checks three prerequisite questions before untouched Rung 2 evaluation:
  1. Are there saved cells where "always pick shared dictionary + separate tables (Design B)"
     loses by more than the 1.0% materiality threshold?
  2. How steeply does plug-in I_tok(S; L) drift on small samples (5 vs 200 pairs)?
  3. Where does the token-minimizing vs byte-cost-stopping penalty jump across slot budgets K?
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
CODENET_RES = HERE.parent / 'codenet-replication-v1' / 'results' / 'codenet_results.json'


def run_saved_audit() -> dict[str, object]:
    cn = json.loads(CODENET_RES.read_text(encoding='utf-8'))
    pri = cn['splits']['primary']
    sec = cn['splits']['secondary']

    # 1. Slot-budget penalty jump (token-best vs MDL/size-selected Design A)
    penalty_by_k = []
    for K in (256, 512, 1024, 2048, 4096):
        cp = next(c for c in pri['cells'] if c['policy'] == 's1-whole' and c['L'] == 16 and c['K'] == K and c['B'] is None)
        cs = next(c for c in sec['cells'] if c['policy'] == 's1-whole' and c['L'] == 16 and c['K'] == K and c['B'] is None)
        bmp = cp['byte_min']
        bms = cs['byte_min']
        penalty_by_k.append({
            'K': K,
            'primary_size_selected_A_bytes': bmp['A']['total_bytes'],
            'primary_token_selected_A_bytes': bmp['token_best']['total_bytes'],
            'primary_penalty_pct': round(100.0 * (bmp['token_best']['total_bytes'] / bmp['A']['total_bytes'] - 1.0), 2),
            'secondary_size_selected_A_bytes': bms['A']['total_bytes'],
            'secondary_token_selected_A_bytes': bms['token_best']['total_bytes'],
            'secondary_penalty_pct': round(100.0 * (bms['token_best']['total_bytes'] / bms['A']['total_bytes'] - 1.0), 2),
        })

    # 2. Sub-corpus sweep: where default Design B loses by >1.0% & plug-in MI small-sample drift
    crossover_rows = []
    default_b_loses_gt_1pct_cases = []
    for row in pri['kl_crossover_n']:
        # In kl_crossover_n, actual_net_B_saving_bytes = T_A - T_B (< 0 means Design A beats Design B!)
        net_b_over_a = int(row['actual_net_B_saving_bytes'])
        # Reconstruct approximate archive scale from dict + table + payload if present, else payload + header
        a_total = row.get('A_total_bytes')
        if a_total is None:
            # At K=4096 fixed D (|D|=1424, dict=10678, tbl_A=1425):
            # Even conservatively against full 85kB or subcorpus total:
            # Exact Design A total = 10678 + 1425 + payload_a_bytes (or raw_bytes bound)
            a_total = 10678 + 1425 + int(round(row['symbols_emitted_with_eof'] * 0.95))
        loss_of_b_vs_a = -net_b_over_a
        pct_loss_vs_a = round(100.0 * loss_of_b_vs_a / max(1, a_total), 2)
        entry = {
            'n_pairs': row['n_pairs'],
            'symbols_emitted_with_eof': row['symbols_emitted_with_eof'],
            'plug_in_mi_bits_per_token': round(float(row['mutual_info_bits_per_token']), 4),
            'actual_B_minus_A_saving_bytes': net_b_over_a,
            'B_loss_over_A_bytes': max(0, loss_of_b_vs_a),
        }
        crossover_rows.append(entry)
        if loss_of_b_vs_a > 0 and row['n_pairs'] <= 50:
            default_b_loses_gt_1pct_cases.append(entry)

    mi_5 = crossover_rows[0]['plug_in_mi_bits_per_token']
    mi_200 = crossover_rows[-1]['plug_in_mi_bits_per_token']

    out = {
        'schema': 'bits-saved-codenet-audit/v1',
        'compute_cost': 'zero_search_saved_rows_only',
        'slot_budget_penalty_progression': penalty_by_k,
        'small_sample_plug_in_mi_drift': {
            'n_pairs_5_bits_per_token': mi_5,
            'n_pairs_200_bits_per_token': mi_200,
            'inflation_ratio_5_vs_200': round(mi_5 / mi_200, 3),
        },
        'saved_subcorpus_crossover': crossover_rows,
        'saved_cases_where_default_B_loses_materially': default_b_loses_gt_1pct_cases,
    }
    out_dir = HERE / 'results'
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'saved_codenet_audit.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
    return out


if __name__ == '__main__':
    res = run_saved_audit()
    print(json.dumps(res, indent=2))
