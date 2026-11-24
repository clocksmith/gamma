#!/usr/bin/env python3
"""Total encoded size, including the dictionary, for every verified v3 dictionary.

Each file is parsed into the fewest tokens and written with a canonical Huffman code
over the entries plus one end-of-file symbol. Total bytes are the dictionary, one
code-length byte per table symbol, the payload, and 4 routing bytes when two tables
are used. Three designs share one accounting:

  A  one dictionary, one code table
  B  one dictionary, one code table per language
  C  two dictionaries, with one code table each

Search floors keep heuristic noise out of the comparison. A looser policy also scores
the dictionaries of its stricter policies, which are legal under it. Each shared cell
also scores the union of its best separate dictionaries, which fits the same budget.

    encoded.py <v1 private folder> <side folder> <run folder> [workers]
"""
import heapq
import json
import math
import multiprocessing
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify as V

ROUTING = 4
STEP = 16
LENGTHS = (8, 16, 32, 64)
SLOTS = (128, 256, 512, 1024, 2048, 4096)
CAPS = (4096, 8192, 16384, 32768, 65536, None)
TOKEN_ARMS = ('greedy-entry', 'greedy-byte', 'greedtok', 'freq-occ', 'freq-doc', 'bpe', 'pathpiece')
SINGLE = ('lp-det', 'lp-bias')
EOF = b'\0EOF'
CORPUS, VIEWS = {}, {}


def huffman_bits(counts):
    """Total payload bits of an optimal prefix code for positive symbol counts."""
    values = [c for c in counts if c > 0]
    if not values:
        return 0
    if len(values) == 1:
        return values[0]
    heapq.heapify(values)
    total = 0
    while len(values) > 1:
        merged = heapq.heappop(values) + heapq.heappop(values)
        total += merged
        heapq.heappush(values, merged)
    return total


def fixed_bits(tokens, symbols):
    return tokens * max(1, math.ceil(math.log2(symbols)))


def histogram(docs, segments, root):
    counts, tokens = Counter(), 0
    for raw, parts in zip(docs, segments):
        pieces = []
        for part in parts:
            found = V.parse(part, root)
            if found is None:
                return None, None
            pieces += found
        if b''.join(pieces) != raw:
            raise V.Rejected('a parse did not reconstruct its file')
        counts.update(pieces)
        tokens += len(pieces)
    return counts, tokens


def one_table(counts, files, entries):
    symbols = entries + 1
    return huffman_bits(list(counts.values()) + [files]), symbols


def measure_shared(job):
    scenario, limit, arm, path, budget = job
    entries = V.read_chain(path)[1]
    py, js = CORPUS['python'], CORPUS['javascript']
    segments, _ = VIEWS[(scenario, 'both')]
    py_seg, js_seg = segments[:400], segments[400:]
    sizes = [budget] if budget else prefix_sizes(entries)
    out, root, at = [], {}, 0
    for size in sizes:
        size = min(size, len(entries))
        while at < size:
            V.insert(root, entries[at][4])
            at += 1
        hp, tp = histogram(py, py_seg, root)
        if hp is None:
            continue
        hj, tj = histogram(js, js_seg, root)
        if hj is None:
            continue
        stored = entries[size - 1][1]
        joined = hp + hj
        bits_a, symbols = one_table(joined, 800, size)
        bits_p, _ = one_table(hp, 400, size)
        bits_j, _ = one_table(hj, 400, size)
        total = tp + tj
        out.append({'arm': arm, 'entries': size, 'stored': stored, 'tokens': total,
                    'A': stored + symbols + math.ceil(bits_a / 8),
                    'B': stored + 2 * symbols + ROUTING + math.ceil(bits_p / 8) + math.ceil(bits_j / 8),
                    'A_fixed': stored + math.ceil(fixed_bits(total + 800, symbols) / 8)})
    return scenario, limit, 'both', arm, out


def measure_language(job):
    scenario, limit, corpus, arm, path = job
    entries = V.read_chain(path)[1]
    docs = CORPUS[corpus]
    segments, _ = VIEWS[(scenario, corpus)]
    out, root, at = [], {}, 0
    for size in prefix_sizes(entries):
        while at < size:
            V.insert(root, entries[at][4])
            at += 1
        counts, tokens = histogram(docs, segments, root)
        if counts is None:
            continue
        bits, symbols = one_table(counts, len(docs), size)
        out.append({'arm': arm, 'entries': size, 'stored': entries[size - 1][1], 'tokens': tokens,
                    'cost': entries[size - 1][1] + symbols + math.ceil(bits / 8),
                    'fixed': entries[size - 1][1] + math.ceil(fixed_bits(tokens + len(docs), symbols) / 8)})
    return scenario, limit, corpus, arm, out


def prefix_sizes(entries):
    total = len(entries)
    wanted = {size for size in range(STEP, total + 1, STEP)} | {total}
    wanted |= {V.prefix_for(entries, k, b) for k in V.GRID_K for b in V.GRID_B}
    return sorted(size for size in wanted if size > 0)


def pareto(points, key):
    """Keeps points not dominated in entries, stored bytes and the key."""
    points = sorted(points, key=lambda p: (p['entries'], p['stored'], p[key]))
    kept, best = [], []
    for point in points:
        if any(s <= point['stored'] and c <= point[key] for s, c in best):
            continue
        kept.append(point)
        best.append((point['stored'], point[key]))
    return kept


def best_shared(points, budget, cap, key):
    routed = ROUTING if key == 'B' else 0
    usable = [p for p in points if p['entries'] <= budget and (cap is None or p['stored'] + routed <= cap)]
    return min(usable, key=lambda p: (p[key], p['tokens'], p['arm'], p['entries'])) if usable else None


def best_separate(python, javascript, budget, cap, key='cost'):
    best = None
    for a in python:
        if a['entries'] >= budget:
            continue
        for b in javascript:
            if a['entries'] + b['entries'] > budget:
                continue
            stored = a['stored'] + b['stored'] + ROUTING
            if cap is not None and stored > cap:
                continue
            total = a[key] + b[key] + ROUTING
            row = (total, a['tokens'] + b['tokens'], a['arm'], b['arm'], a['entries'], b['entries'], stored, a['scenario'], b['scenario'])
            if best is None or row < best:
                best = row
    if best is None:
        return None
    return dict(zip(('bytes', 'tokens', 'python_arm', 'javascript_arm', 'python_entries', 'javascript_entries', 'stored',
                     'python_scenario', 'javascript_scenario'), best))


def stricter(scenario):
    return {'s1-whole': ('s2-nowhole', 'p2-nowhole'), 's2-nowhole': ('p2-nowhole',)}.get(scenario, ())


def union_point(scenario, limit, split, folder, budget):
    """The shared dictionary made from the best separate pair, under the same accounting."""
    if scenario == 's1-whole-cuts':
        return None
    seen, order = set(), []
    for corpus, arm, size, source in (('python', split['python_arm'], split['python_entries'], split['python_scenario']),
                                      ('javascript', split['javascript_arm'], split['javascript_entries'], split['javascript_scenario'])):
        for row in V.read_chain(folder / source / f'{corpus}-L{limit}-{arm}.txt')[1][:size]:
            if row[4] not in seen:
                seen.add(row[4])
                order.append(row[4])
    if len(order) > budget:
        return None
    policy = V.SCENARIOS[scenario][0]
    _, units = VIEWS[(scenario, 'both')]
    try:
        V.check_entries([(0, 0, 0, 0, entry) for entry in order], CORPUS['both'], units, limit, policy)
    except V.Rejected:
        return None
    root = {}
    for entry in order:
        V.insert(root, entry)
    segments, _ = VIEWS[(scenario, 'both')]
    hp, tp = histogram(CORPUS['python'], segments[:400], root)
    hj, tj = histogram(CORPUS['javascript'], segments[400:], root)
    if hp is None or hj is None:
        return None
    stored = sum(1 + len(entry) for entry in order)
    bits_a, symbols = one_table(hp + hj, 800, len(order))
    bits_p, _ = one_table(hp, 400, len(order))
    bits_j, _ = one_table(hj, 400, len(order))
    return {'arm': 'union', 'entries': len(order), 'stored': stored, 'tokens': tp + tj,
            'A': stored + symbols + math.ceil(bits_a / 8),
            'B': stored + 2 * symbols + ROUTING + math.ceil(bits_p / 8) + math.ceil(bits_j / 8)}


def main():
    private, side, run = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 12
    CORPUS.update(V.load_corpus(private))
    for scenario, (policy, use_cuts) in V.SCENARIOS.items():
        for corpus, docs in CORPUS.items():
            groups = [int(x) for x in (side / f'{corpus}.groups').read_text().split()]
            cuts = (side / f'{corpus}.cuts').read_bytes() if use_cuts else b''
            VIEWS[(scenario, corpus)] = V.build_views(docs, groups, cuts, use_cuts, policy)
    folder = run / 'chains'
    shared_jobs, language_jobs = [], []
    for scenario in V.SCENARIOS:
        for limit in LENGTHS:
            for arm in TOKEN_ARMS:
                path = folder / scenario / f'both-L{limit}-{arm}.txt'
                if path.exists():
                    shared_jobs.append((scenario, limit, arm, path, None))
                for corpus in ('python', 'javascript'):
                    path = folder / scenario / f'{corpus}-L{limit}-{arm}.txt'
                    if path.exists():
                        language_jobs.append((scenario, limit, corpus, arm, path))
            for arm in SINGLE:
                for path in sorted((folder / scenario).glob(f'both-L{limit}-{arm}-K*.txt')):
                    shared_jobs.append((scenario, limit, arm, path, int(path.stem.rsplit('-K', 1)[1])))
    os.nice(19)
    with multiprocessing.get_context('fork').Pool(workers) as pool:
        shared = pool.map(measure_shared, shared_jobs, chunksize=1)
        language = pool.map(measure_language, language_jobs, chunksize=1)
    own = {}
    for scenario, limit, corpus, _, rows in shared + language:
        own.setdefault((scenario, limit, corpus), []).extend({**row, 'scenario': scenario} for row in rows)
    points = {}
    for (scenario, limit, corpus), rows in own.items():
        points.setdefault((scenario, limit, corpus), []).extend(rows)
        for source in stricter(scenario):
            points[(scenario, limit, corpus)].extend(own.get((source, limit, corpus), []))
    cells = []
    for scenario in V.SCENARIOS:
        for limit in LENGTHS:
            both = points.get((scenario, limit, 'both'), [])
            py = pareto(points.get((scenario, limit, 'python'), []), 'cost')
            js = pareto(points.get((scenario, limit, 'javascript'), []), 'cost')
            for budget in SLOTS:
                for cap in CAPS:
                    a, b = best_shared(both, budget, cap, 'A'), best_shared(both, budget, cap, 'B')
                    c = best_separate(py, js, budget, cap)
                    if c is not None:
                        floor = union_point(scenario, limit, c, folder, budget)
                        if floor is not None and (cap is None or floor['stored'] <= cap):
                            pool = both + [floor]
                            a, b = best_shared(pool, budget, cap, 'A'), best_shared(pool, budget, cap, 'B')
                    tokens_best = best_shared(both, budget, cap, 'tokens')
                    by_arm = {}
                    for arm in TOKEN_ARMS + SINGLE:
                        found = best_shared([p for p in both if p['arm'] == arm], budget, cap, 'A')
                        if found:
                            by_arm[arm] = {'bytes': found['A'], 'tokens': found['tokens'], 'entries': found['entries'], 'stored': found['stored']}
                    cells.append({'scenario': scenario, 'L': limit, 'K': budget, 'B': cap,
                                  'A': None if a is None else {k: a[k] for k in ('arm', 'entries', 'stored', 'tokens', 'A')},
                                  'B_design': None if b is None else {k: b[k] for k in ('arm', 'entries', 'stored', 'tokens', 'B')},
                                  'C': c, 'token_best': None if tokens_best is None else {k: tokens_best[k] for k in ('arm', 'entries', 'stored', 'tokens', 'A')},
                                  'by_arm': by_arm})
    (run / 'out' / 'encoded.json').write_text(json.dumps({'schema': 'gamma.fixed-source-encoded.v3', 'cells': cells}, separators=(',', ':')) + '\n')
    print(f'encoded {len(shared_jobs)} shared and {len(language_jobs)} language chains into {len(cells)} cells')


if __name__ == '__main__':
    main()
