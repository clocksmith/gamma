"""Public evidence for roles-v1: aggregates, per-problem action counts, comparisons and the frozen verdicts.

  evidence.py --run DIR/roles/run-v1   writes evidence/results.json (IDs, counts, hashes and aggregates only)

Promotion and conditional-gain tests are the frozen rule in FREEZE.md and contract.json; this script applies them.
"""
import argparse, hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda b: hashlib.sha256(b).hexdigest()


def paired(x, y):
    """x against baseline y, per problem on actions."""
    a, b = x['per_problem_actions'], y['per_problem_actions']
    assert a.keys() == b.keys()
    d = {k: a[k] - b[k] for k in a}
    diffs = sorted(d.values())
    return {'arm': x['arm'], 'baseline': y['arm'], 'actions': x['devval']['actions'], 'baseline_actions': y['devval']['actions'],
            'change': x['devval']['actions'] - y['devval']['actions'],
            'relative': x['devval']['actions'] / y['devval']['actions'] - 1,
            'median': x['devval']['median'], 'baseline_median': y['devval']['median'],
            'p90': x['devval']['p90'], 'baseline_p90': y['devval']['p90'],
            'improved': sum(v < 0 for v in diffs), 'same': sum(v == 0 for v in diffs), 'worsened': sum(v > 0 for v in diffs),
            'per_problem_change_range': [diffs[0], diffs[-1]], 'per_problem_change_median': (diffs[49] + diffs[50]) / 2}


def passes(p, correct, rule):
    checks = {'P1_correct': correct,
              'P2_actions': p['actions'] <= (1 - rule['min_reduction']) * p['baseline_actions'],
              'P3_median_and_p90': p['median'] < p['baseline_median'] and p['p90'] < p['baseline_p90'],
              'P4_per_problem': p['improved'] >= rule['min_improved'] and p['worsened'] <= rule['max_worsened']}
    return all(checks.values()), checks


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', type=Path, required=True); a = ap.parse_args()
    contract = json.loads((HERE / 'contract.json').read_text())
    res = json.loads((a.run / 'results.json').read_text()); ex = json.loads((a.run / 'execution.json').read_text())
    assert res['contract_sha256'] == sha((HERE / 'contract.json').read_bytes()) and not res['smoke_trials']
    assert ex['results_sha256'] == sha((a.run / 'results.json').read_bytes())
    arms = {r['arm']: r for r in res['arms']}
    correct = {k: ex['arms'][k]['passed'] == ex['arms'][k]['programs'] == arms[k]['packets_verified'] == 100 for k in arms}
    rule = contract['promotion']
    out = {'schema': 'gamma.roles-v1.evidence.v1', 'contract_sha256': res['contract_sha256'], 'results_sha256': sha((a.run / 'results.json').read_bytes()),
           'execution_sha256': sha((a.run / 'execution.json').read_bytes()), 'seconds': res['seconds'], 'arms': {}, 'widths': {}}
    for k, r in arms.items():
        out['arms'][k] = {key: r[key] for key in ('pool', 'rep', 'width', 'stop', 'trials', 'seconds', 'entries', 'slots_in_dictionary',
                                                 'end_in_dictionary', 'entries_with_slots', 'dictionary_bytes', 'package_bytes', 'decoder_bytes',
                                                 'package_bytes_with_decoder', 'packets_verified', 'dictionary_sha256', 'devval',
                                                 'per_problem_actions')}
        out['arms'][k]['execution'] = ex['arms'][k]
    for w in (128, 256):
        g = lambda name: arms[f'{name}-{w}']
        pairs = {f'{x} vs {y}': paired(g(x), g(y)) for x, y in (('B-Om', 'L-Om'), ('B-Om', 'L-R'), ('B-R', 'L-R'), ('N-Om', 'L-Om'),
                                                              ('N-Om', 'L-R'), ('N-R', 'L-R'), ('B-Om', 'N-Om'), ('B-R', 'N-R'))}
        tests = {}
        for x in ('B-Om', 'B-R'):
            for y in ('L-R', 'L-Om'):
                ok, checks = passes(pairs.get(f'{x} vs {y}') or paired(g(x), g(y)), correct[f'{x}-{w}'], rule)
                tests[f'{x} vs {y}'] = {'passes': ok, **checks}
        eligible = [x for x in ('B-Om', 'B-R') if tests[f'{x} vs L-R']['passes'] and tests[f'{x} vs L-Om']['passes']]
        promoted = min(eligible, key=lambda x: (g(x)['devval']['actions'], g(x)['package_bytes_with_decoder'])) if eligible else None
        lom, nom, bom = (g(x)['devval']['actions'] for x in ('L-Om', 'N-Om', 'B-Om'))
        out['widths'][str(w)] = {
            'pairs': pairs, 'tests': tests, 'promoted': promoted,
            'conditional_gain': {x: tests[f'{x} vs {y}']['passes'] for x, y in (('B-Om', 'L-Om'), ('B-R', 'L-R'))},
            'attribution_Om': {'L_to_N_naming': nom - lom, 'N_to_B_declarations': bom - nom, 'L_to_B_total': bom - lom},
            'control_reproduced': g('L-Om')['devval']['selections'] == contract['controls'][f'L-Om-{w}']
                                  and g('L-R')['devval']['selections'] == contract['controls'][f'L-R-{w}'],
            'm1_indicator_devval': {k: (g(k)['devval']['median'] <= 32 and g(k)['devval']['p95'] <= 96
                                        and g(k)['devval']['fallback_selection_fraction'] <= .10)
                                    for k in ('L-Om', 'B-Om', 'N-Om', 'L-R', 'B-R', 'N-R')}}
    W = out['widths']
    out['predictions'] = {
        'R1': all(W[w]['control_reproduced'] for w in W),
        'R2': all(W[w]['pairs']['B-Om vs L-Om']['relative'] <= -.15 and W[w]['pairs']['B-Om vs L-Om']['improved'] > 80 for w in W),
        'R3': all(W[w]['pairs']['B-R vs L-R']['relative'] > -.01 for w in W),
        'R4': all(W[w]['promoted'] is None for w in W),
        'R5': all(W[w]['attribution_Om']['N_to_B_declarations'] > 0 and W[w]['pairs']['N-Om vs L-R']['relative'] > 0 for w in W),
        'R6': all(correct.values()),
        'R7': not any(v for w in W for v in W[w]['m1_indicator_devval'].values())}
    (HERE / 'evidence').mkdir(exist_ok=True)
    (HERE / 'evidence/results.json').write_text(json.dumps(out, indent=1, sort_keys=True) + '\n')
    for w, v in W.items():
        print(w, 'promoted', v['promoted'], 'conditional', v['conditional_gain'], 'attribution', v['attribution_Om'])
        for k, p in v['pairs'].items():
            print(f"   {k:14} {p['actions']:6} vs {p['baseline_actions']:6} {100 * p['relative']:+6.1f}%  med {p['median']} vs {p['baseline_median']}  "
                  f"p90 {p['p90']} vs {p['baseline_p90']}  better/same/worse {p['improved']}/{p['same']}/{p['worsened']}")
    print(out['predictions'])


if __name__ == '__main__':
    main()
