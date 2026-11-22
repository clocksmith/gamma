#!/usr/bin/env python3
"""Write instances.json for capacity-complexity-v1. Builds strings and copies hand-derived numbers; solves nothing.

    python3 -B freeze_instances.py
"""
import hashlib
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
THEOREMS = os.path.join(HERE, '..', 'capacity-theorems-v1')
VERTEX, MIDDLE, FRESH = 'ABCDEFGH', 'abcdefghijklmnop', '123456789'


def graph_words(edges):
    """Neraud's words: one per edge, the two vertex letters around a middle letter used by that edge only."""
    return [VERTEX[u] + MIDDLE[n] + VERTEX[v] for n, (u, v) in enumerate(edges)]


def slices(words):
    """Neraud's slices: for w = abc, the four words abc, ab1, 2bc, 2b1 with 1 and 2 fresh for that word."""
    out = []
    for n, (a, b, c) in enumerate(words):
        one, two = FRESH[2 * n], FRESH[2 * n + 1]
        out += [a + b + c, a + b + one, two + b + c, two + b + one]
    return out


K4 = [(u, v) for u in range(4) for v in range(u + 1, 4)]
K5 = [(u, v) for u in range(5) for v in range(u + 1, 5)]
HALF = '1/2'
# name: (edges, minimum vertex cover, a fractional vertex cover of minimum weight). All derived by hand.
GRAPHS = {
    'edge': ([(0, 1)], 1, ['1', '0']),
    'path3': ([(0, 1), (1, 2)], 1, ['0', '1', '0']),
    'path4': ([(0, 1), (1, 2), (2, 3)], 2, ['0', '1', '1', '0']),
    'star3': ([(0, 1), (0, 2), (0, 3)], 1, ['1', '0', '0', '0']),
    'triangle': ([(0, 1), (1, 2), (0, 2)], 2, [HALF] * 3),
    'cycle4': ([(0, 1), (1, 2), (2, 3), (0, 3)], 2, ['1', '0', '1', '0']),
    'cycle5': ([(0, 1), (1, 2), (2, 3), (3, 4), (0, 4)], 3, [HALF] * 5),
    'paw': ([(0, 1), (1, 2), (0, 2), (2, 3)], 2, ['1', '0', '1', '0']),
    'diamond': ([(0, 1), (0, 2), (1, 2), (1, 3), (2, 3)], 2, ['0', '1', '1', '0']),
    'K4': (K4, 3, [HALF] * 4),
    'bowtie': ([(0, 1), (0, 2), (1, 2), (0, 3), (0, 4), (3, 4)], 3, [HALF] * 5),
    'K5': (K5, 4, [HALF] * 5),
    'K33': ([(u, v) for u in range(3) for v in range(3, 6)], 3, ['1', '1', '1', '0', '0', '0']),
    'prism': ([(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5), (0, 3), (1, 4), (2, 5)], 4, [HALF] * 6),
}
# name: (words, rank r(X) = fewest words Y with X inside Y*). All derived by hand.
WORD_SETS = {
    'N1': (['a', 'abc', 'bca'], 2),
    'N2': (['aba', 'bba', 'abb', 'baa'], 2),
    'N3': (['a', 'abc', 'cba'], 3),
    'E1': (['abc', 'bca'], 2),
    'R1': (['ab', 'abab', 'ababab'], 1),
    'R2': (['ab', 'ba', 'abab'], 2),
    'R3': (['a', 'aa', 'b'], 2),
    'R4': (['abc', 'abd', 'cd', 'ab'], 3),
    'Zedge': (slices(graph_words(GRAPHS['edge'][0])), 4),
    'Zpath3': (slices(graph_words(GRAPHS['path3'][0])), 7),
    'Ztriangle': (slices(graph_words(GRAPHS['triangle'][0])), 11),
}


def half_units(weights):
    return sum(2 if w == '1' else 1 if w == HALF else 0 for w in weights)


def sha256(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


graphs = {}
for name, (edges, cover, weights) in GRAPHS.items():
    twice = half_units(weights)
    graphs[name] = {
        'edges': [list(e) for e in edges], 'programs': graph_words(edges), 'fractionalCover': weights,
        'predicted': {
            'minimumVertexCover': cover,
            'unrestrictedMinimum': len(edges) + cover,
            'linearProgramTwice': 2 * len(edges) + twice,        # twice the value, to stay in integers
            'certificateReachesMinimum': (twice + 1) // 2 == cover,
        }}

rng = random.Random(20261122)
random_sets = []
while len(random_sets) < 60:
    words = sorted({''.join(rng.choice('abc') for _ in range(rng.randint(1, 4))) for _ in range(rng.choice((2, 3, 4)))})
    if len(words) >= 2 and words not in random_sets:
        random_sets.append(words)

out = {
    'schema': 'capacity-complexity-instances/v1',
    'graphs': graphs,
    'wordSets': {name: {'words': words, 'predicted': {'rank': rank, 'witnessMinimum': {'2': 2 * len(words) + rank, '3': 3 * len(words) + rank}}}
                 for name, (words, rank) in WORD_SETS.items()},
    'randomWordSets': random_sets,
    'frozenFamilies': {
        'capacity-theorems-v1/instances.json': sha256(os.path.join(THEOREMS, 'instances.json')),
        'capacity-theorems-v1/instances-round2.json': sha256(os.path.join(THEOREMS, 'instances-round2.json')),
    },
    'counterexamples': {
        'blockGrid': ['axby', 'byax', 'aybx', 'bxay'],
        'union': ['abd', 'abe', 'fbd', 'pxqy', 'qypx', 'pyqx', 'qxpy'],
        'sixProgramConnected': ['abd', 'fbd', 'abpxqy', 'qypx', 'pyqx', 'qxpy'],
        'fiveProgramConnected': ['abd', 'abpxqy', 'qypxbd', 'abpyqx', 'qxpybd'],
    },
    # Linear-program values seen in an exploratory run before this file was written (floating point, not checked).
    'seenBeforeFreezing': {
        'C1': {'U': 2.0, 'W2': 2.0}, 'C2': {'U': 3.0, 'W2': 3.0}, 'C4': {'U': 4.0, 'W2': 4.0}, 'O1': {'U': 4.0, 'W2': 4.5},
        'blockGrid': {'U': 4.0, 'W2': 4.0}, 'union': {'U': 8.0, 'W2': 8.5},
        'sixProgramConnected': {'U': 7.0, 'W2': 7.5}, 'fiveProgramConnected': {'U': 6.0, 'W2': 6.5},
    },
}
with open(os.path.join(HERE, 'instances.json'), 'w') as f:
    json.dump(out, f, indent=1)
    f.write('\n')
print(f"wrote instances.json: {len(graphs)} graphs, {len(WORD_SETS)} word sets, {len(random_sets)} random word sets")
