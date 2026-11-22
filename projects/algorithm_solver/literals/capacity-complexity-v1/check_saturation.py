#!/usr/bin/env python3
"""Check Theorem 3 (SATURATION.md) by exhaustive search on small graphs. Python 3.8+; no solver.

    python3 -B check_saturation.py        writes results-saturation.json; exits 1 on any mismatch
"""
import json
import os
import sys

from evaluate import HERE, eligible, minimum, terminator_corpus, vertex_cover_number

VERTEX, MIDDLE, FRESH, GATE = 'ABCDEFGH', 'abcdefgh', '12345678', 'wxyz'
GRAPHS = {
    'edge': [(0, 1)],
    'path3': [(0, 1), (1, 2)],
    'triangle': [(0, 1), (1, 2), (0, 2)],
    'path4': [(0, 1), (1, 2), (2, 3)],
    'star3': [(0, 1), (0, 2), (0, 3)],
    'cycle4': [(0, 1), (1, 2), (2, 3), (0, 3)],
}


def words(edges, gates):
    vertices = sorted({v for e in edges for v in e})
    out = []
    for n, (u, v) in enumerate(edges):
        a, b, c, one, two = VERTEX[u], MIDDLE[n], VERTEX[v], FRESH[2 * n], FRESH[2 * n + 1]
        out += [a + b + c, a + b + one, two + b + c, two + b + one]
    for j in range(gates):
        x = GATE[j]
        out += [x, x + ''.join(VERTEX[v] + x for v in vertices)]
    return out, len(vertices)


rows, failures = [], []
for name, edges in GRAPHS.items():
    cover = vertex_cover_number(edges)
    for gates in range(0, min(len({v for e in edges for v in e}), len(GATE) + 1)):
        x, vertices = words(edges, gates)
        alphabet = len(set(''.join(x)))
        predicted = min(3 * len(edges) + vertices + gates, 3 * len(edges) + cover + 2 * gates)
        rank = minimum(x, eligible(x, 'R'))[0]
        corpus = terminator_corpus(x, 2)
        witness = minimum(corpus, eligible(corpus, 'W2'))[0]
        corpus_alphabet = len(set(''.join(corpus)))
        saturated = witness == corpus_alphabet
        row = {'graph': name, 'vertices': vertices, 'edges': len(edges), 'cover': cover, 'gateWords': gates, 'words': len(x),
               'alphabet': alphabet, 'rankPredicted': predicted, 'rank': rank, 'witnessMinimum': witness,
               'corpusAlphabet': corpus_alphabet, 'saturated': saturated, 'saturatedPredicted': cover + gates >= vertices}
        rows.append(row)
        if alphabet != 3 * len(edges) + vertices + gates or rank != predicted or witness != 2 * len(x) + rank or saturated != row['saturatedPredicted']:
            failures.append(row)
        print(f"{name:9} c={gates} alphabet {alphabet:2} rank {rank:2} (predicted {predicted:2}) "
              f"witness minimum {witness:3} of {corpus_alphabet:3} characters: {'saturated' if saturated else 'not saturated'}")
with open(os.path.join(HERE, 'results-saturation.json'), 'w') as f:
    json.dump({'schema': 'capacity-complexity-saturation/v1', 'rows': rows, 'failures': failures}, f, indent=1)
    f.write('\n')
print(f'{len(rows)} instances, {len(failures)} mismatches')
sys.exit(1 if failures else 0)
