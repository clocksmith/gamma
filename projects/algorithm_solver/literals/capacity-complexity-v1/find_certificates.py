#!/usr/bin/env python3
"""Find a potential certificate for every corpus named in PREREGISTRATION.md and store it as fractions.
Needs scipy. Nothing here is trusted: evaluate.py re-checks every stored certificate without a solver.

    python3 -B find_certificates.py
"""
import json
import os
from fractions import Fraction

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import lil_matrix

from evaluate import HERE, THEOREMS, certificate_value, eligible

DENOMINATORS = list(range(1, 61)) + [120, 360, 2520]


def solve(programs, tokens):
    """Maximise the total rise subject to: every occurrence is charged at least its rise, and the charges of
    all occurrences of one entry sum to at most 1. Returns (optimum, potentials) in floating point."""
    allowed = {t: n for n, t in enumerate(tokens)}
    offsets, nodes = [], 0
    for p in programs:
        offsets.append(nodes)
        nodes += len(p) + 1
    arcs = [(n, i, j, allowed[p[i:j]]) for n, p in enumerate(programs)
            for i in range(len(p)) for j in range(i + 1, len(p) + 1) if p[i:j] in allowed]
    cost = np.zeros(nodes + len(arcs))
    bounds = [(None, None)] * nodes + [(0, None)] * len(arcs)
    for n, p in enumerate(programs):
        cost[offsets[n] + len(p)] -= 1
        bounds[offsets[n]] = (0, 0)
    rows = lil_matrix((len(arcs) + len(tokens), nodes + len(arcs)))
    limit = np.zeros(len(arcs) + len(tokens))
    for a, (n, i, j, t) in enumerate(arcs):
        rows[a, offsets[n] + j], rows[a, offsets[n] + i], rows[a, nodes + a] = 1, -1, -1
        rows[len(arcs) + t, nodes + a] = 1
    limit[len(arcs):] = 1
    r = linprog(cost, A_ub=rows.tocsr(), b_ub=limit, bounds=bounds, method='highs')
    assert r.status == 0, r.message
    return -r.fun, [list(r.x[offsets[n]: offsets[n] + len(p) + 1]) for n, p in enumerate(programs)]


def worst_charge(programs, tokens, potentials):
    allowed, charge = set(tokens), {}
    for p, phi in zip(programs, potentials):
        for i in range(len(p)):
            for j in range(i + 1, len(p) + 1):
                if p[i:j] in allowed and phi[j] > phi[i]:
                    charge[p[i:j]] = charge.get(p[i:j], 0) + phi[j] - phi[i]
    return max(charge.values(), default=Fraction(0))


def as_fractions(programs, tokens, floats, optimum):
    for d in DENOMINATORS:
        candidate = [[str(Fraction(round(x * d), d)) for x in row] for row in floats]
        valid, value = certificate_value(programs, tokens, candidate)
        if valid and value >= optimum - 1e-7:
            return candidate
    exact = [[Fraction(round(x * 5040), 5040) for x in row] for row in floats]       # round finely, then shrink until valid
    worst = worst_charge(programs, tokens, exact)
    if worst > 1:
        exact = [[x / worst for x in row] for row in exact]
    return [[str(x) for x in row] for row in exact]


def main():
    frozen = json.load(open(os.path.join(HERE, 'instances.json')))
    first = json.load(open(os.path.join(THEOREMS, 'instances.json')))
    second = json.load(open(os.path.join(THEOREMS, 'instances-round2.json')))
    jobs = [(f'graph/{name}', g['programs'], ('U',)) for name, g in frozen['graphs'].items()]
    jobs += [(f'instance/{name}', v['programs'], ('U', 'W2')) for name, v in first['instances'].items()]
    jobs += [(f'counterexample/{name}', programs, ('U', 'W2')) for name, programs in frozen['counterexamples'].items()]
    jobs += [(f'random/{n}', programs, ('U', 'W2')) for n, programs in enumerate(first['randomSearchFamily'])]
    jobs += [(f'round2/{n}', programs, ('U', 'W2')) for n, programs in enumerate(second['corpora'])]
    certificates, solver = {}, {}
    for key, programs, rules in jobs:
        for rule in rules:
            tokens = eligible(programs, rule)
            optimum, floats = solve(programs, tokens)
            certificates[f'{key}/{rule}'] = as_fractions(programs, tokens, floats, optimum)
            solver[f'{key}/{rule}'] = round(optimum, 6)
    out = {'schema': 'capacity-complexity-certificates/v1',
           'note': 'certificates: one potential per position boundary of each program, as fractions; checked by evaluate.py. '
                   'solverOptimum: what the linear-programming solver reported, in floating point; not checked and not used.',
           'certificates': certificates, 'solverOptimum': solver}
    with open(os.path.join(HERE, 'certificates.json'), 'w') as f:
        json.dump(out, f, indent=0, separators=(',', ':'))
        f.write('\n')
    print(f'wrote certificates.json: {len(certificates)} certificates')


if __name__ == '__main__':
    main()
