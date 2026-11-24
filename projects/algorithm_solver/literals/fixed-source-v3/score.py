#!/usr/bin/env python3
"""Scores the frozen v3 predictions and kill bar from verified encoded sizes.

    score.py <run folder>
"""
import json
import sys
from collections import Counter
from pathlib import Path

PRIMARY = 's1-whole'
CONTROLS = ('s2-nowhole', 'p2-nowhole')
GREEDY = ('greedy-entry', 'greedy-byte')
BASELINES = ('bpe', 'pathpiece', 'freq-occ', 'freq-doc', 'greedtok', 'lp-det', 'lp-bias')
BAR = 0.25


def size(cell, design):
    item = cell[design]
    if item is None:
        return None
    return item['bytes'] if design == 'C' else item['A'] if design == 'A' else item['B']


def feasible(cell):
    return all(size(cell, d) is not None for d in ('A', 'B_design', 'C'))


def metrics(cells):
    usable = [c for c in cells if feasible(c)]
    winners, design_wins, objective_wins, a_beats_c, close = Counter(), 0, 0, 0, 0
    for cell in usable:
        a, b, c = size(cell, 'A'), size(cell, 'B_design'), size(cell, 'C')
        winners[min((a, 0, 'A'), (b, 1, 'B'), (c, 2, 'C'))[2]] += 1
        design_wins += min(b, c) <= 0.99 * a
        objective_wins += cell['token_best']['A'] >= 1.01 * a
        a_beats_c += a < c
        arms = cell['by_arm']
        baseline = [arms[x]['bytes'] for x in BASELINES if x in arms]
        overall = [v['bytes'] for v in arms.values()]
        close += bool(baseline) and min(baseline) <= 1.02 * min(overall)
    n = len(usable)
    share = lambda value: value / n if n else None
    return {'cells': len(cells), 'feasible': n, 'lowest_total': dict(winners),
            'k1_other_design_at_least_1pct_smaller': share(design_wins),
            'k2_token_best_at_least_1pct_larger': share(objective_wins),
            'a_beats_c': share(a_beats_c), 'b_lowest': share(winners['B']),
            'best_baseline_within_2pct_of_best_arm': share(close)}


def main():
    run = Path(sys.argv[1])
    out = run / 'out'
    cells = json.loads((out / 'encoded.json').read_text())['cells']
    by_scenario = {s: metrics([c for c in cells if c['scenario'] == s]) for s in (PRIMARY, *CONTROLS, 's1-whole-cuts')}
    first = by_scenario[PRIMARY]

    def at(scenario):
        return next(c for c in cells if c['scenario'] == scenario and c['L'] == 16 and c['K'] == 1024 and c['B'] is None)

    base, cut = size(at(PRIMARY), 'A'), size(at('s1-whole-cuts'), 'A')
    predictions = {
        'V1': {'text': 'Design A is smaller than C in at least 75% of feasible primary cells', 'value': first['a_beats_c'], 'held': first['a_beats_c'] >= .75},
        'V2': {'text': 'Design B is lowest in fewer than 25% of feasible primary cells', 'value': first['b_lowest'], 'held': first['b_lowest'] < .25},
        'V3': {'text': 'The token-best dictionary is within 1% of the byte-best in at least 75% of feasible primary cells',
               'value': 1 - first['k2_token_best_at_least_1pct_larger'], 'held': first['k2_token_best_at_least_1pct_larger'] <= .25},
        'V4': {'text': 'The best baseline is within 2% of the best arm in at least 50% of feasible primary cells',
               'value': first['best_baseline_within_2pct_of_best_arm'], 'held': first['best_baseline_within_2pct_of_best_arm'] >= .5},
        'V5': {'text': 'Forbidding boundary crossing raises design A bytes by at least 3% at K=1024, L=16, uncapped',
               'primary': base, 'forbidden': cut, 'value': cut / base - 1, 'held': cut >= 1.03 * base},
    }
    scenarios = (PRIMARY, *CONTROLS)
    k1 = all(by_scenario[s]['k1_other_design_at_least_1pct_smaller'] >= BAR for s in scenarios)
    k2 = all(by_scenario[s]['k2_token_best_at_least_1pct_larger'] >= BAR for s in scenarios)
    lp = []
    for path in sorted((run / 'lp').glob('*.json')):
        row = json.loads(path.read_text())
        lp.append({k: row[k] for k in ('policy', 'corpus', 'L', 'K', 'status', 'objective', 'columns', 'rows', 'solve_seconds', 'label')})
    failures = (run / 'lp' / 'failures.txt')
    summary = {'schema': 'gamma.fixed-source-score.v3', 'by_scenario': by_scenario, 'predictions': predictions,
               'kill_bar': {'threshold': BAR, 'k1_design_inversion': k1, 'k2_objective_inversion': k2,
                            'decision': 'full paper allowed' if k1 or k2 else 'benchmark note and close'},
               'lp': lp, 'lp_failures': failures.read_text().splitlines() if failures.exists() else []}
    (out / 'score.json').write_text(json.dumps(summary, indent=1) + '\n')
    for key, item in predictions.items():
        print(key, 'HELD' if item['held'] else 'FAILED', round(item['value'], 4))
    print(json.dumps(summary['kill_bar']))


if __name__ == '__main__':
    main()
