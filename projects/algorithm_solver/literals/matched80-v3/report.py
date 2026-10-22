"""Rebuild results.json and RESULTS.md from run-v1 artifacts. Reads only; safe to rerun."""
import json
import math
import statistics
from pathlib import Path

import run

ROOT = Path(__file__).resolve().parent
RUN = ROOT / 'run-v1'
LIT = ROOT.parent
LIVE = {128: {'version': 'bits-literal-joint80-7-v2', 'selections': 9910, 'package_bytes': 12798,
              'manifest': LIT / 'matched80-v2/run-v1/polish-128/manifest.json'},
        256: {'version': 'bits-literal-joint80-8-v1', 'selections': 6413, 'package_bytes': 11781,
              'manifest': LIT / 'scale-v2/search-v2/compact-marginal-256/manifest.json'}}
BAR = {size: {'selections': math.floor(live['selections'] * 0.98), 'package_bytes': math.floor(live['package_bytes'] * 1.05)}
       for size, live in LIVE.items()}
EMPTY_SLOT_PRESSES = 6413 * 9


def per_problem(path):
    return {row['id']: row['selections'] for row in json.loads(Path(path).read_text())['programs']}


def distribution(counts, reference):
    values = sorted(counts.values())
    deltas = [counts[pid] - reference[pid] for pid in sorted(counts)]
    return {'min': values[0], 'median': statistics.median(values), 'p90': values[math.ceil(.9 * len(values)) - 1], 'max': values[-1],
            'better': sum(d < 0 for d in deltas), 'same': sum(d == 0 for d in deltas), 'worse': sum(d > 0 for d in deltas),
            'largest_increase': max(deltas), 'largest_decrease': min(deltas)}


def baseline_alignment(texts, folder):
    """Token-aligned fraction of a matched80-v1 arm, from its stored dictionary and sequences."""
    vocab = json.loads((folder / 'dictionary.json').read_text())
    aligned = total = 0
    for row in json.loads((folder / 'manifest.json').read_text())['programs']:
        parts = [vocab[i] for i in row['sequence']]
        aligned += run.units.aligned_fraction(texts[str(row['id'])], parts) * len(parts)
        total += len(parts)
    return aligned / total


def main():
    contract = json.loads((ROOT / 'contract.json').read_text())
    arms = {}
    for folder in sorted(p for p in RUN.iterdir() if p.is_dir()):
        metrics = json.loads((folder / 'manifest.json').read_text())['metrics']
        arms[folder.name] = {**metrics, 'resources': json.loads((RUN / f'{folder.name}-resources.json').read_text()),
                             'per_problem': per_problem(folder / 'manifest.json')}
    texts, _, _ = run.inputs()
    for name, a in arms.items():
        if a['kind'] == 'readable':
            ref = LIT / f"matched80-v1/run-v1/fixed-designed-{a['style']}-{a['size']}"
            a['reference'] = {'arm': f"matched80-v1 fixed-designed-{a['style']}-{a['size']}",
                              **{k: json.loads((ref / 'manifest.json').read_text())['metrics'][k] for k in ('selections', 'package_bytes')},
                              'token_aligned_selection_fraction': baseline_alignment(texts[a['style']], ref)}
            a['distribution'] = distribution(a['per_problem'], per_problem(ref / 'manifest.json'))
        else:
            live = LIVE[a['size']]
            a['reference'] = {'arm': live['version'], 'selections': live['selections'], 'package_bytes': live['package_bytes']}
            a['distribution'] = distribution(a['per_problem'], per_problem(live['manifest']))
    sel = lambda n: arms[n]['selections']
    literal = {size: sorted((n for n, a in arms.items() if a['kind'] != 'readable' and a['size'] == size),
                            key=lambda n: (sel(n), arms[n]['package_bytes'], n)) for size in LIVE}
    seeds = {size: [arms[f'ils-{size}-s{s}']['selections'] for s in contract['ils']['seeds']] for size in LIVE}
    ils_start = {size: arms[f'ils-{size}-s{contract["ils"]["seeds"][0]}']['start_selections'] for size in LIVE}
    promotion = {}
    for size, live in LIVE.items():
        a = arms[literal[size][0]]
        promotion[str(size)] = {'live': {k: live[k] for k in ('version', 'selections', 'package_bytes')}, 'bar': BAR[size],
                                'candidate': literal[size][0], 'selections': a['selections'], 'package_bytes': a['package_bytes'],
                                'selection_change': (a['selections'] - live['selections']) / live['selections'],
                                'package_change': (a['package_bytes'] - live['package_bytes']) / live['package_bytes'],
                                'meets_selection_rule': a['selections'] <= BAR[size]['selections'],
                                'meets_package_rule': a['package_bytes'] <= BAR[size]['package_bytes']}
    readable = [n for n, a in arms.items() if a['kind'] == 'readable']
    r = lambda pool, style, size: arms[f'readable-{pool}-{style}-{size}']
    styles = contract['readable']['styles']
    predictions = {
        'L1 wide-v2polish beats its start': {str(s): sel(f'wide-v2polish-{s}') < arms[f'wide-v2polish-{s}']['start_selections'] for s in LIVE},
        'L2 best 8-bit arm meets the bar': {'256': promotion['256']['meets_selection_rule'] and promotion['256']['meets_package_rule']},
        'L3 ILS: >=4/5 seeds improve and spread <= 1% of median': {str(s): sum(x < ils_start[s] for x in seeds[s]) >= 4 and
                                                                   max(seeds[s]) - min(seeds[s]) <= 0.01 * statistics.median(seeds[s]) for s in LIVE},
        'L4 wide-scalev2 within 1% of wide-v2polish': {str(s): abs(sel(f'wide-scalev2-{s}') - sel(f'wide-v2polish-{s}')) <= 0.01 * sel(f'wide-v2polish-{s}') for s in LIVE},
        'R1 units-designed < designed-only': {f'{st}-{s}': r('units-designed', st, s)['selections'] < r('units-designed', st, s)['reference']['selections'] for st in styles for s in LIVE},
        'R2 units-designed <= units': {f'{st}-{s}': r('units-designed', st, s)['selections'] <= r('units', st, s)['selections'] for st in styles for s in LIVE},
        'R3 units-designed more token-aligned than designed-only': {f'{st}-{s}': r('units-designed', st, s)['token_aligned_selection_fraction'] >
                                                                   r('units-designed', st, s)['reference']['token_aligned_selection_fraction'] for st in styles for s in LIVE},
    }
    empty_slot = {n: {'presses': arms[n]['selections'] * (arms[n]['size'].bit_length()), 'meets': arms[n]['selections'] * arms[n]['size'].bit_length() < EMPTY_SLOT_PRESSES}
                  for n in readable}
    run_info = json.loads((RUN / 'run.json').read_text())
    results = {'schema': 'gamma.matched80.results.v3', 'run': {k: run_info[k] for k in ('complete', 'host', 'python', 'elapsed_seconds', 'parallel', 'contract_sha256')},
               'frozen_at': contract['frozen_at'], 'bars': {str(k): v for k, v in BAR.items()}, 'predictions': predictions, 'promotion': promotion,
               'ils_seeds': {str(s): {'selections': seeds[s], 'start': ils_start[s], 'min': min(seeds[s]), 'median': statistics.median(seeds[s]), 'max': max(seeds[s])} for s in LIVE},
               'readable_empty_slot_rule': {'cheapest_existing_presses': EMPTY_SLOT_PRESSES, 'arms': empty_slot}, 'arms': arms}
    (ROOT / 'results.json').write_text(json.dumps(results, indent=2, sort_keys=True) + '\n')

    def row(name, a):
        d, res = a['distribution'], a['resources']
        flag = ' (time limit)' if res['stop'] == 'time_limit' else ''
        return (f"| {name} | {a['selections']:,} | {(a['selections'] - a['reference']['selections']) / a['reference']['selections']:+.2%} | "
                f"{a['dictionary_bytes']:,} | {a['packet_bytes']:,} | {a['package_bytes']:,} | {d['min']} / {d['median']} / {d['p90']} / {d['max']} | "
                f"{d['better']} / {d['same']} / {d['worse']} ({d['largest_increase']:+d}) | {res['trials']:,} | {res['search_seconds']:.0f}{flag} |")
    head = ('| Arm | Selections | vs reference | Dictionary B | Packets B | Package B | Per problem min / median / p90 / max | '
            'Problems better / same / worse (largest increase) | Trials | Seconds |')
    lines = ['# Matched 80, iteration 3 results', '',
             f"Generated by `report.py` (run complete: {run_info['complete']}, {run_info['elapsed_seconds']:.0f} s wall on {run_info['host']}, "
             f"{run_info['parallel']} parallel jobs). Package bytes are the LTD1 dictionary plus every LTV1 packet with its 41-byte header; "
             'the shared decoder is unchanged and not included.', '',
             '## Literal scorecard (80 compact sources)', '',
             'Reference: the live BITS profile of each size (7-bit `bits-literal-joint80-7-v2`, 9,910; 8-bit `bits-literal-joint80-8-v1`, 6,413).', '',
             head, '| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |']
    for size in LIVE:
        lines += [row(n, arms[n]) for n in sorted(literal[size])]
    lines += ['', '### Seeds', '', '| Size | Start | Seeds (selections) | Min / median / max | Spread |', '| --- | ---: | --- | --- | ---: |']
    for s in LIVE:
        lines.append(f"| {s} | {ils_start[s]:,} | {', '.join(f'{x:,}' for x in seeds[s])} | {min(seeds[s]):,} / {statistics.median(seeds[s]):,} / {max(seeds[s]):,} | "
                     f"{(max(seeds[s]) - min(seeds[s])) / statistics.median(seeds[s]):.2%} |")
    lines += ['', '## Promotion check (BITS_PROMOTION.md, unchanged)', '',
              '| Size | Live | Bar (selections / bytes) | Candidate | Selections | Change | Package B | Change | Promote |', '| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |']
    for size, p in promotion.items():
        lines.append(f"| {size} | {p['live']['version']} ({p['live']['selections']:,}) | <= {p['bar']['selections']:,} / <= {p['bar']['package_bytes']:,} | {p['candidate']} | "
                     f"{p['selections']:,} | {p['selection_change']:+.2%} | {p['package_bytes']:,} | {p['package_change']:+.2%} | "
                     f"{'yes' if p['meets_selection_rule'] and p['meets_package_rule'] else 'no'} |")
    lines += ['', '## Readable scorecard (readable-units-v1; separate from the literal scorecard)', '',
              'Reference: the matched80-v1 designed-only arm of the same style and size.', '',
              head.replace('| Trials', '| Token-aligned (reference) | Entries by class | Trials'),
              '| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | ---: | ---: |']
    for name in readable:
        a = arms[name]
        classes = ', '.join(f'{k} {v}' for k, v in sorted(a['entries_by_provenance'].items()))
        base_row = row(name, a).rsplit('|', 3)
        lines.append(f"{base_row[0]}| {a['token_aligned_selection_fraction']:.1%} ({a['reference']['token_aligned_selection_fraction']:.1%}) | {classes} |{base_row[1]}|{base_row[2]}|")
    lines += ['', f"Empty-slot rule: no joint80 readable slot is live; a first readable profile would need fewer total presses than {EMPTY_SLOT_PRESSES:,} "
              f"(the live 8-bit profile). Arms meeting it: {', '.join(n for n, v in empty_slot.items() if v['meets']) or 'none'}.", '', '## Predictions', '']
    lines += [f"- **{k}**: " + ', '.join(f"{kk} {'holds' if vv else 'fails'}" for kk, vv in v.items()) for k, v in predictions.items()]
    (ROOT / 'RESULTS.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk in ('candidate', 'selections', 'package_bytes', 'selection_change', 'meets_selection_rule', 'meets_package_rule')}
                      for k, v in promotion.items()}))


if __name__ == '__main__':
    main()
