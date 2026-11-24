#!/usr/bin/env python3
"""Read-only post-hoc checks on fixed-source-v3-r1. Not part of the frozen scoring.

Added after the freeze because a review raised three accounting questions:

1. Does greedy still beat BPE and PathPiece when BPE stores merge pairs instead of raw
   strings, and when every arm's dictionary is compressed the same way?
2. Does BPE's own segmentation change that comparison?
3. Does the objective-inversion finding survive when token-best gets the same union
   floor as byte-best?

    posthoc.py <v1 private folder> <side folder> <run folder> [workers]
"""
import json
import math
import multiprocessing
import os
import statistics
import sys
import zlib
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import encoded as X
import verify as V

SCENARIOS = ('s1-whole', 's2-nowhole', 'p2-nowhole')
ARMS = ('greedy-entry', 'greedy-byte', 'bpe', 'pathpiece')
CODINGS = ('raw', 'merge', 'deflate')
SAMPLE = 64
BAR = 0.25


def sizes_for(entries):
    total = len(entries)
    wanted = set(range(SAMPLE, total + 1, SAMPLE)) | {total}
    wanted |= {V.prefix_for(entries, k, b) for k in V.GRID_K for b in V.GRID_B}
    return sorted(size for size in wanted if size > 0)


def parents(entries, merges):
    found = {}
    for added, left, right in merges:
        if added < len(entries) and entries[added][4] == left + right and entries[added][4] not in found:
            found[entries[added][4]] = (left, right)
    return found


def dictionary_bytes(entries, size, pairs):
    head = [row[4] for row in entries[:size]]
    raw = entries[size - 1][1]
    packed = len(zlib.compress(b''.join(bytes([len(e)]) + e for e in head), 9))
    if pairs is None:
        return raw, raw, packed
    seen, singles = set(), 0
    for entry in head:
        if len(entry) == 1:
            singles += 1
        else:
            left, right = pairs[entry]
            if left not in seen or right not in seen:
                raise SystemExit('a merge parent is outside its prefix')
        seen.add(entry)
    width = max(1, math.ceil(math.log2(max(2, size))))
    return raw, singles + math.ceil((size - singles) * 2 * width / 8), packed


def point(arm, entries, size, counts, tokens, pairs):
    raw, merge, packed = dictionary_bytes(entries, size, pairs)
    bits = X.huffman_bits(list(counts.values()) + [800])
    payload = size + 1 + math.ceil(bits / 8)
    return {'arm': arm, 'entries': size, 'tokens': tokens, 'payload': payload, 'raw': raw, 'merge': merge, 'deflate': packed}


def measure_parsed(job):
    scenario, limit, arm, path = job
    _, entries, merges, _, _, _ = V.read_chain(path)
    docs = X.CORPUS['both']
    segments, _ = X.VIEWS[(scenario, 'both')]
    pairs = parents(entries, merges) if arm == 'bpe' else None
    out, root, at = [], {}, 0
    for size in sizes_for(entries):
        while at < size:
            V.insert(root, entries[at][4])
            at += 1
        counts, tokens = X.histogram(docs, segments, root)
        if counts is not None:
            out.append(point(arm, entries, size, counts, tokens, pairs))
    return scenario, limit, out


def measure_ordinary(job):
    """BPE's own left-to-right merge segmentation, decoded back to the source bytes."""
    scenario, limit, _, path = job
    _, entries, merges, _, _, _ = V.read_chain(path)
    docs = X.CORPUS['both']
    pairs = parents(entries, merges)
    ids = {}

    def token(value):
        if value not in ids:
            code = len(ids) + 0x100
            ids[value] = chr(code if code < 0xD800 else code + 0x800)
        return ids[value]

    streams = [''.join(token(bytes([b])) for b in raw) for raw in docs]
    wanted, place, out = sizes_for(entries), 0, []

    def record(prefix):
        nonlocal place
        while place < len(wanted) and wanted[place] <= prefix:
            size = wanted[place]
            back = {code: value for value, code in ids.items()}
            for raw, stream in zip(docs, streams):
                if b''.join(back[c] for c in stream) != raw:
                    raise SystemExit('BPE segmentation did not reconstruct a file')
            counts = Counter()
            for stream in streams:
                counts.update(stream)
            out.append(point('bpe-ordinary', entries, size, counts, sum(map(len, streams)), pairs))
            place += 1

    for added, left, right in merges:
        if added < len(entries) and entries[added][4] == left + right:
            record(added)
        pair, merged = token(left) + token(right), token(left + right)
        streams = [s.replace(pair, merged) if pair in s else s for s in streams]
    record(len(entries))
    return scenario, limit, out


def best(points, arms, coding, budget, cap):
    values = [p['payload'] + p[coding] for p in points if p['arm'] in arms and p['entries'] <= budget and (cap is None or p[coding] <= cap)]
    return min(values) if values else None


def compare(points):
    report = {}
    for coding in CODINGS:
        rows = {'bpe': [], 'pathpiece': []}
        for (scenario, limit), items in points.items():
            for budget in X.SLOTS:
                for cap in X.CAPS:
                    greedy = best(items, ('greedy-entry', 'greedy-byte'), coding, budget, cap)
                    if greedy is None:
                        continue
                    other = best(items, ('bpe', 'bpe-ordinary'), coding, budget, cap)
                    if other is not None:
                        rows['bpe'].append((scenario, other / greedy - 1))
                    other = best(items, ('pathpiece',), coding, budget, cap)
                    if other is not None:
                        rows['pathpiece'].append((scenario, other / greedy - 1))
        report[coding] = {}
        for name, values in rows.items():
            for scenario in SCENARIOS:
                part = [v for s, v in values if s == scenario]
                if part:
                    report[coding].setdefault(name, {})[scenario] = {
                        'cells': len(part), 'greedy_smaller': sum(v > 0 for v in part), 'tied': sum(v == 0 for v in part),
                        'baseline_smaller': sum(v < 0 for v in part), 'median_baseline_excess': statistics.median(part),
                        'min_baseline_excess': min(part), 'max_baseline_excess': max(part)}
    return report


def equal_floor(run):
    cells = json.loads((run / 'out' / 'encoded.json').read_text())['cells']
    folder = run / 'chains'
    cache, result, carried = {}, {}, Counter()
    for scenario in SCENARIOS:
        usable = changed = frozen = equal = 0
        for cell in (c for c in cells if c['scenario'] == scenario):
            for arm in ('lp-det', 'lp-bias'):
                row = cell['by_arm'].get(arm)
                if row and cell['K'] not in (256, 1024, 4096):
                    carried[arm] += 1
            if cell['A'] is None or cell['B_design'] is None or cell['C'] is None:
                continue
            usable += 1
            byte_best, token_best = cell['A']['A'], cell['token_best']
            frozen += token_best['A'] >= 1.01 * byte_best
            c = cell['C']
            key = (scenario, cell['L'], cell['K'], c['python_arm'], c['javascript_arm'], c['python_entries'], c['javascript_entries'],
                   c['python_scenario'], c['javascript_scenario'])
            if key not in cache:
                cache[key] = X.union_point(scenario, cell['L'], c, folder, cell['K'])
            floor = cache[key]
            tokens, bytes_at = token_best['tokens'], token_best['A']
            if floor is not None and (cell['B'] is None or floor['stored'] <= cell['B']) and floor['tokens'] < tokens:
                tokens, bytes_at = floor['tokens'], floor['A']
                changed += 1
            equal += bytes_at >= 1.01 * byte_best
        result[scenario] = {'feasible': usable, 'token_best_replaced_by_union': changed, 'k2_frozen': frozen / usable if usable else None,
                            'k2_equal_floor': equal / usable if usable else None}
    return result, dict(carried)


def main():
    private, side, run = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 8
    X.CORPUS.update(V.load_corpus(private))
    for scenario in SCENARIOS:
        policy, use_cuts = V.SCENARIOS[scenario]
        docs = X.CORPUS['both']
        groups = [int(x) for x in (side / 'both.groups').read_text().split()]
        X.VIEWS[(scenario, 'both')] = V.build_views(docs, groups, b'', use_cuts, policy)
    jobs, ordinary = [], []
    for scenario in SCENARIOS:
        for limit in X.LENGTHS:
            for arm in ARMS:
                path = run / 'chains' / scenario / f'both-L{limit}-{arm}.txt'
                if not path.exists():
                    raise SystemExit(f'missing chain: {path.name}')
                jobs.append((scenario, limit, arm, path))
                if arm == 'bpe':
                    ordinary.append((scenario, limit, arm, path))
    os.nice(19)
    with multiprocessing.get_context('fork').Pool(workers) as pool:
        results = pool.map(measure_parsed, jobs, chunksize=1) + pool.map(measure_ordinary, ordinary, chunksize=1)
    points = {}
    for scenario, limit, rows in results:
        points.setdefault((scenario, limit), []).extend(rows)
    floors, carried = equal_floor(run)
    score = json.loads((run / 'out' / 'score.json').read_text())
    k1 = score['kill_bar']['k1_design_inversion']
    k2 = all(floors[s]['k2_equal_floor'] >= BAR for s in SCENARIOS)
    report = {'schema': 'gamma.fixed-source-posthoc.v3', 'label': 'post-hoc, read-only, not part of the frozen scoring',
              'codings': {'raw': 'one length byte plus the entry', 'merge': 'BPE stores two parent IDs per merged entry; other arms stay raw',
                          'deflate': 'zlib level 9 of the serialized dictionary, for every arm'},
              'comparison': compare(points), 'equal_floor': floors, 'lp_rows_carried_from_a_smaller_solved_K': carried,
              'frozen_decision': score['kill_bar']['decision'], 'k1_frozen': k1, 'k2_with_equal_floor': k2,
              'survives_equal_floor': bool(k1 or k2)}
    (run / 'out' / 'posthoc.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({k: report[k] for k in ('equal_floor', 'lp_rows_carried_from_a_smaller_solved_K', 'frozen_decision', 'k1_frozen', 'k2_with_equal_floor', 'survives_equal_floor')}))
    for coding, row in report['comparison'].items():
        for name, part in row.items():
            print(coding, name, {s: (v['greedy_smaller'], v['tied'], v['baseline_smaller'], round(v['median_baseline_excess'], 4)) for s, v in part.items()})


if __name__ == '__main__':
    main()
