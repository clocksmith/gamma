#!/usr/bin/env python3
"""Paired closeout of fixed-source-v2, written after the frozen endpoints were scored.

Compares each primary cell with its matched control and with v1, measures whether
single-file entries help broadly or through a few files, and reads the rechecked
bounds. Everything here is descriptive and changes no frozen endpoint.

    closeout.py <v1 private folder> <run folder>
"""
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify as V

PRIMARY, CONTROL = 's1-whole', 's2-nowhole'
BEST = ('greedy-entry', 'greedy-byte', 'greedy-polish')
CORPORA = ('python', 'javascript', 'both')
FILE_CELLS = [(16, 256), (16, 1024), (16, 4096), (32, 4096), (64, 1024), (64, 4096)]


def quantile(values, q):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(q * len(ordered)))]


def describe(values):
    if not values:
        return None
    return {'n': len(values), 'min': min(values), 'median': statistics.median(values), 'p90': quantile(values, .9), 'max': max(values)}


def tokens_by_file(run, policy, corpus, limit, budget, arm, docs):
    if arm == 'greedy-polish':
        entries = V.read_chain(run / 'chains' / policy / f'{corpus}-L{limit}-polish-K{budget}.txt')[1]
    else:
        entries = V.read_chain(run / 'chains' / policy / f'{corpus}-L{limit}-{arm}.txt')[1]
        entries = entries[:V.prefix_for(entries, budget, None)]
    root = {}
    for row in entries:
        V.insert(root, row[4])
    counts = []
    for raw in docs:
        pieces = V.parse(raw, root)
        if pieces is None or b''.join(pieces) != raw:
            raise SystemExit('a closeout parse failed')
        counts.append(len(pieces))
    return counts


def main():
    private, run = Path(sys.argv[1]), Path(sys.argv[2])
    out = run / 'out'
    summary = json.loads((out / 'summary.json').read_text())
    files = V.load_corpus(private)
    cells = defaultdict(dict)
    for cell in summary['table']:
        cells[(cell['policy'], cell['corpus'], cell['L'], cell['K'], cell['B'])] = cell['arms']

    def best(policy, corpus, limit, budget, cap):
        rows = [(cells[(policy, corpus, limit, budget, cap)][arm]['emissions'], order, arm)
                for order, arm in enumerate(BEST) if arm in cells[(policy, corpus, limit, budget, cap)]
                and cells[(policy, corpus, limit, budget, cap)][arm]['emissions'] is not None]
        return min(rows) if rows else None

    paired, by_budget = [], defaultdict(list)
    for corpus in CORPORA:
        for limit in (2, 4, 8, 16, 32, 64):
            for budget in V.GRID_K:
                for cap in V.GRID_B:
                    a, b = best(PRIMARY, corpus, limit, budget, cap), best(CONTROL, corpus, limit, budget, cap)
                    if a is None or b is None:
                        continue
                    change = 1 - a[0] / b[0]
                    arms = cells[(PRIMARY, corpus, limit, budget, cap)][a[2]]
                    row = {'corpus': corpus, 'L': limit, 'K': budget, 'B': cap, 'primary': a[0], 'control': b[0], 'reduction': change,
                           'primary_stored': arms['stored'], 'one_file_entries': arms['one_file_entries'],
                           'whole_file_entries': arms['whole_file_entries']}
                    paired.append(row)
                    by_budget[(limit, budget)].append(change)
    counts = Counter('primary lower' if r['primary'] < r['control'] else 'primary higher' if r['primary'] > r['control'] else 'equal' for r in paired)
    grid = [{'L': limit, 'K': budget, **describe(values)} for (limit, budget), values in sorted(by_budget.items())]
    corpus_bytes = {name: sum(map(len, docs)) for name, docs in files.items()}
    memorizing = [r for r in paired if r['primary_stored'] >= 0.5 * corpus_bytes[r['corpus']]]

    per_file = {}
    for limit, budget in FILE_CELLS:
        a, b = best(PRIMARY, 'both', limit, budget, None), best(CONTROL, 'both', limit, budget, None)
        first = tokens_by_file(run, PRIMARY, 'both', limit, budget, a[2], files['both'])
        second = tokens_by_file(run, CONTROL, 'both', limit, budget, b[2], files['both'])
        deltas = [y - x for x, y in zip(first, second)]
        gains = sorted((d for d in deltas if d > 0), reverse=True)
        total = sum(deltas)
        positive = sum(gains)
        per_file[f'L{limit}-K{budget}'] = {
            'files': len(deltas), 'improved': sum(d > 0 for d in deltas), 'unchanged': sum(d == 0 for d in deltas),
            'worse': sum(d < 0 for d in deltas), 'net_tokens_saved': total, 'gross_tokens_saved': positive,
            'top_1pct_share_of_gross': sum(gains[:max(1, len(deltas) // 100)]) / positive if positive else 0,
            'top_10pct_share_of_gross': sum(gains[:len(deltas) // 10]) / positive if positive else 0,
            'median_file_change': statistics.median(deltas), 'primary_stored': cells[(PRIMARY, 'both', limit, budget, None)][a[2]]['stored'],
            'control_stored': cells[(CONTROL, 'both', limit, budget, None)][b[2]]['stored']}

    v1 = json.loads((private / 'run-v1' / 'out' / 'summary.json').read_text())
    v1_cells = {(c['corpus'], c['L'], c['K'], c['B']): c['arms'] for c in v1['table']}
    v1_compare = Counter()
    for (corpus, limit, budget, cap), arms in v1_cells.items():
        if limit == 1:
            continue
        values = [arms[a]['emissions'] for a in BEST if a in arms and arms[a]['emissions'] is not None]
        control = best(CONTROL, corpus, limit, budget, cap)
        if values and control:
            v1_compare['equal' if min(values) == control[0] else 'v2 control lower' if control[0] < min(values) else 'v2 control higher'] += 1

    bounds = []
    for path in sorted(out.glob('bound-*.jsonl')):
        for line in path.read_text().splitlines():
            row = json.loads(line)
            found = best(row['policy'], row['corpus'], 16, row['K'], None)[0]
            bounds.append({'policy': row['policy'], 'corpus': row['corpus'], 'K': row['K'], 'best': found, 'lower_bound': row['lower_bound'],
                           'gap': (found - row['lower_bound']) / found, 'certificate_sha256': row['certificate_sha256']})
    losses = [{k: r[k] for k in ('L', 'K', 'B', 'shared', 'separate')} for r in summary['sharing']
              if r['policy'] == PRIMARY and r['shared'] is not None and r['separate'] is not None and r['shared'] >= r['separate']]
    report = {'schema': 'gamma.fixed-source-closeout.v2', 'run': summary['run'], 'paired_cells': len(paired), 'paired_outcomes': dict(counts),
              'reduction_when_lower': describe([r['reduction'] for r in paired if r['primary'] < r['control']]),
              'increase_when_higher': describe([-r['reduction'] for r in paired if r['primary'] > r['control']]),
              'budget_grid': grid, 'primary_higher_cells': [r for r in paired if r['primary'] > r['control']],
              'cells_storing_at_least_half_the_corpus': {'n': len(memorizing), 'reduction': describe([r['reduction'] for r in memorizing])},
              'cells_storing_less_than_half': describe([r['reduction'] for r in paired if r['primary_stored'] < 0.5 * corpus_bytes[r['corpus']]]),
              'per_file': per_file, 'v1_vs_v2_control_best': dict(v1_compare), 'bounds': bounds, 'primary_sharing_losses': losses}
    (out / 'closeout.json').write_text(json.dumps(report, indent=1) + '\n')
    printable = {k: v for k, v in report.items() if k not in ('budget_grid', 'primary_higher_cells', 'bounds')}
    print(json.dumps(printable, indent=1))
    print('L/K with the largest median reduction:', [(g['L'], g['K'], round(g['median'], 3)) for g in sorted(grid, key=lambda g: -g['median'])[:8]])
    print('cells where primary is higher:', [(r['corpus'], r['L'], r['K'], r['B'], r['primary'], r['control']) for r in report['primary_higher_cells']][:14])


if __name__ == '__main__':
    main()
