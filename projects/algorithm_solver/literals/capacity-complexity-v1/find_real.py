#!/usr/bin/env python3
"""Find a potential certificate and search for a small dictionary, for the corpora of PREREGISTRATION-REAL.md.
Needs scipy. Nothing here is trusted: evaluate_real.py re-checks the certificate and replays the dictionary.
The integer program is a search tool with a time limit; its claim of optimality is recorded and not used.

    python3 -B find_real.py
"""
import json
import os
import time
from fractions import Fraction

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, milp
from scipy.sparse import coo_matrix

from evaluate_real import HERE, certificate_value, dictionary_spells, load_corpora, occurrences

DENOMINATORS = list(range(1, 61)) + [120, 360, 2520]


def solve(programs):
    arcs = list(occurrences(programs))
    tokens = {}
    for n, i, j in arcs:
        tokens.setdefault(programs[n][i:j], len(tokens))
    offsets, nodes = [], 0
    for p in programs:
        offsets.append(nodes)
        nodes += len(p) + 1
    cost = np.zeros(nodes + len(arcs))
    bounds = [(None, None)] * nodes + [(0, None)] * len(arcs)
    for n, p in enumerate(programs):
        cost[offsets[n] + len(p)] -= 1
        bounds[offsets[n]] = (0, 0)
    r, c, v = [], [], []
    for a, (n, i, j) in enumerate(arcs):
        r += [a, a, a, len(arcs) + tokens[programs[n][i:j]]]
        c += [offsets[n] + j, offsets[n] + i, nodes + a, nodes + a]
        v += [1, -1, -1, 1]
    rows = coo_matrix((v, (r, c)), shape=(len(arcs) + len(tokens), nodes + len(arcs))).tocsr()
    limit = np.r_[np.zeros(len(arcs)), np.ones(len(tokens))]
    result = linprog(cost, A_ub=rows, b_ub=limit, bounds=bounds, method='highs')
    assert result.status == 0, result.message
    floats = [list(result.x[offsets[n]: offsets[n] + len(p) + 1]) for n, p in enumerate(programs)]
    amounts = -result.ineqlin.marginals[len(arcs):]          # how much of each entry the fractional dictionary uses
    return -result.fun, floats, dict(zip(tokens, amounts))


def as_fractions(programs, floats, optimum):
    for d in DENOMINATORS:
        candidate = [[str(Fraction(round(x * d), d)) for x in row] for row in floats]
        valid, value = certificate_value(programs, candidate)
        if valid and value >= optimum - 1e-7:
            return candidate
    exact = [[Fraction(round(x * 5040), 5040) for x in row] for row in floats]
    charge = {}
    for n, i, j in occurrences(programs):
        if exact[n][j] > exact[n][i]:
            s = programs[n][i:j]
            charge[s] = charge.get(s, 0) + exact[n][j] - exact[n][i]
    worst = max(charge.values(), default=Fraction(1))
    if worst > 1:
        exact = [[x / worst for x in row] for row in exact]
    return [[str(x) for x in row] for row in exact]


SEARCH_SECONDS = 300


def search_dictionary(programs):
    """Smallest dictionary an integer program finds within the time limit: choose entries, route one path per program."""
    arcs = list(occurrences(programs))
    tokens = {}
    for n, i, j in arcs:
        tokens.setdefault(programs[n][i:j], len(tokens))
    offsets, nodes = [], 0
    for p in programs:
        offsets.append(nodes)
        nodes += len(p) + 1
    width = len(tokens) + len(arcs)
    r, c, v, low, high = [], [], [], [], []
    for a, (n, i, j) in enumerate(arcs):                      # flow out of a node minus flow into it
        r += [offsets[n] + i, offsets[n] + j]
        c += [len(tokens) + a, len(tokens) + a]
        v += [1, -1]
    for n, p in enumerate(programs):
        for k in range(len(p) + 1):
            balance = 1 if k == 0 else -1 if k == len(p) else 0
            low.append(balance)
            high.append(balance)
    for a, (n, i, j) in enumerate(arcs):                      # an occurrence is used only if its entry is chosen
        r += [nodes + a, nodes + a]
        c += [len(tokens) + a, tokens[programs[n][i:j]]]
        v += [1, -1]
        low.append(-np.inf)
        high.append(0)
    rows = coo_matrix((v, (r, c)), shape=(nodes + len(arcs), width)).tocsr()
    cost = np.r_[np.ones(len(tokens)), np.zeros(len(arcs))]
    integrality = np.r_[np.ones(len(tokens)), np.zeros(len(arcs))]
    result = milp(cost, constraints=LinearConstraint(rows, low, high), integrality=integrality,
                  bounds=Bounds(0, 1), options={'time_limit': SEARCH_SECONDS})
    if result.x is None:
        return None, result.message
    names = list(tokens)
    dictionary = sorted(names[t] for t in range(len(names)) if result.x[t] > 0.5)
    for entry in sorted(dictionary, key=len, reverse=True):   # drop entries the spelling does not need
        rest = [d for d in dictionary if d != entry]
        if dictionary_spells(programs, rest):
            dictionary = rest
    return (dictionary if dictionary_spells(programs, dictionary) else None), result.message


def main():
    out, notes = {}, {}
    for name, programs in load_corpora().items():
        started = time.time()
        optimum, floats, amounts = solve(programs)
        entry = {'potentials': as_fractions(programs, floats, optimum)}
        lp_seconds = round(time.time() - started, 1)
        started = time.time()
        dictionary, message = search_dictionary(programs)
        if dictionary is not None:
            entry['dictionary'] = dictionary
        out[name] = entry
        notes[name] = {'linearProgramOptimum': round(optimum, 6), 'linearProgramSeconds': lp_seconds,
                       'entriesUsedFractionally': sum(1 for a in amounts.values() if 1e-6 < a < 1 - 1e-6),
                       'searchSeconds': round(time.time() - started, 1), 'searchLimitSeconds': SEARCH_SECONDS, 'searchMessage': message}
        print(name, notes[name], 'dictionary stored' if 'dictionary' in entry else 'no dictionary')
    with open(os.path.join(HERE, 'certificates-real.json'), 'w') as f:
        json.dump({'schema': 'capacity-complexity-certificates-real/v1',
                   'note': 'potentials and dictionary are checked by evaluate_real.py; solver is floating-point output, not checked and not used',
                   'corpora': out, 'solver': notes}, f, separators=(',', ':'))
        f.write('\n')


if __name__ == '__main__':
    main()
