#!/usr/bin/env python3
"""Run the methods of PREREGISTRATION.md on every frozen corpus and store what they return. Needs scipy.
Nothing here is trusted: evaluate.py recomputes the cheap checks and re-checks every certificate and dictionary.

    python3 -B run_benchmark.py              all corpora, one child process per corpus; writes measurements.json
    python3 -B run_benchmark.py --one KEY    one corpus; prints its measurement as JSON

Methods, all under the witness rule with threshold 2:
- cheap checks: forced single characters and the rank of the forced blocks (evaluate.py);
- the shipped diagnostic: capacity-diagnostic-v1/diagnostic.py at budget 64, as a subprocess;
- the flow method: the flow formulation of Canzar et al. on the graph of eligible substring intervals,
  a linear program for the lower bound and an integer program for a dictionary, on a general solver (HiGHS).
  This is a reimplementation of the formulation, not the authors' software.
"""
import json
import os
import platform
import resource
import subprocess
import sys
import tempfile
import time
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
DIAGNOSTIC = os.path.join(HERE, '..', 'capacity-diagnostic-v1', 'diagnostic.py')
BUDGET, LIMIT_SECONDS, DIAGNOSTIC_SECONDS = 64, 600, 900
SIZE_LIMIT, RESTRICTED_LENGTH = 500_000, 40          # above SIZE_LIMIT occurrences: no linear program, short entries only
DENOMINATORS = list(range(1, 61)) + [120, 360, 2520]


def cheap_checks(programs):
    import evaluate
    best = None
    for _ in range(3):
        started = time.perf_counter()
        forced, blocks = len(evaluate.forced_singletons(programs)), evaluate.block_rank(programs)
        elapsed = time.perf_counter() - started
        best = elapsed if best is None else min(best, elapsed)
    return {'forcedSingletons': forced, 'blockRank': blocks, 'seconds': round(best, 4)}


def shipped_diagnostic(programs):
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, 'corpus.json')
        json.dump({'programs': programs}, open(path, 'w'))
        started = time.perf_counter()
        try:
            run = subprocess.run([sys.executable, '-B', DIAGNOSTIC, '--corpus', path, '--rule', 'W2', '--budget', str(BUDGET), '--json'],
                                 capture_output=True, text=True, timeout=DIAGNOSTIC_SECONDS)
        except subprocess.TimeoutExpired:
            return {'status': None, 'wallSeconds': None, 'note': f'no answer within {DIAGNOSTIC_SECONDS} s'}
        wall = time.perf_counter() - started
    if run.returncode != 0:
        return {'status': None, 'wallSeconds': round(wall, 2), 'note': 'exit ' + str(run.returncode)}
    out = json.loads(run.stdout)
    return {'status': out['status'], 'certifiedLowerBound': out['certifiedLowerBound'], 'wallSeconds': round(wall, 2),
            'peakMiB': round(out['measuredCost']['peakAllocKiB'] / 1024, 1)}


def flow_graph(programs, arcs):
    tokens = {}
    for n, i, j in arcs:
        tokens.setdefault(programs[n][i:j], len(tokens))
    offsets, nodes = [], 0
    for p in programs:
        offsets.append(nodes)
        nodes += len(p) + 1
    return tokens, offsets, nodes


def flow_matrices(programs, arcs, tokens, offsets, nodes):
    import numpy as np
    from scipy.sparse import coo_matrix
    width = len(tokens) + len(arcs)
    r, c, v = [], [], []
    for a, (n, i, j) in enumerate(arcs):                       # flow out of a node minus flow into it
        r += [offsets[n] + i, offsets[n] + j]
        c += [len(tokens) + a, len(tokens) + a]
        v += [1, -1]
    balance = coo_matrix((v, (r, c)), shape=(nodes, width)).tocsr()
    supply = np.zeros(nodes)
    for n, p in enumerate(programs):
        supply[offsets[n]], supply[offsets[n] + len(p)] = 1, -1
    r, c, v = [], [], []
    for a, (n, i, j) in enumerate(arcs):                       # an occurrence is used only as far as its entry is chosen
        r += [a, a]
        c += [len(tokens) + a, tokens[programs[n][i:j]]]
        v += [1, -1]
    link = coo_matrix((v, (r, c)), shape=(len(arcs), width)).tocsr()
    cost = np.r_[np.ones(len(tokens)), np.zeros(len(arcs))]
    return cost, balance, supply, link


def certificate_from_duals(programs, duals, offsets, optimum, certificate_value):
    """Turn the node duals into potentials and store them as fractions. Checked exactly before it is kept."""
    best = None
    for sign in (1, -1):
        floats = [[sign * (duals[offsets[n]] - duals[offsets[n] + k]) for k in range(len(p) + 1)] for n, p in enumerate(programs)]
        for d in DENOMINATORS:
            candidate = [[str(Fraction(round(x * d), d)) for x in row] for row in floats]
            valid, value = certificate_value(programs, candidate)
            if valid and (best is None or value > best[0]):
                best = (value, candidate)
            if valid and value >= optimum - 1e-7:
                return candidate
    return None if best is None or best[0] <= 0 else best[1]


def flow_method(programs, sibling):
    import numpy as np
    from scipy.optimize import Bounds, LinearConstraint, linprog, milp
    out, notes = {}, {}
    every = list(sibling.occurrences(programs))
    notes['overSizeLimit'] = len(every) > SIZE_LIMIT

    if notes['overSizeLimit']:
        notes['linearProgram'] = f'not attempted: more than {SIZE_LIMIT:,} eligible occurrences'
    else:
        tokens, offsets, nodes = flow_graph(programs, every)
        cost, balance, supply, link = flow_matrices(programs, every, tokens, offsets, nodes)
        started = time.perf_counter()
        result = linprog(cost, A_ub=link, b_ub=np.zeros(len(every)), A_eq=balance, b_eq=supply, bounds=(0, None),
                         method='highs-ds', options={'time_limit': LIMIT_SECONDS})
        out['linearProgramSeconds'] = round(time.perf_counter() - started, 2)
        notes['linearProgram'] = result.message
        if result.status == 0:
            notes['linearProgramOptimum'] = round(float(result.fun), 6)
            out['potentials'] = certificate_from_duals(programs, result.eqlin.marginals, offsets, result.fun, sibling.certificate_value)

    arcs = [a for a in every if a[2] - a[1] <= RESTRICTED_LENGTH] if notes['overSizeLimit'] else every
    if notes['overSizeLimit']:
        notes['search'] = f'entries of at most {RESTRICTED_LENGTH} characters only'
    tokens, offsets, nodes = flow_graph(programs, arcs)
    cost, balance, supply, link = flow_matrices(programs, arcs, tokens, offsets, nodes)
    from scipy.sparse import vstack
    rows = vstack([balance, link]).tocsr()
    low = np.r_[supply, np.full(len(arcs), -np.inf)]
    high = np.r_[supply, np.zeros(len(arcs))]
    started = time.perf_counter()
    result = milp(cost, constraints=LinearConstraint(rows, low, high), integrality=np.r_[np.ones(len(tokens)), np.zeros(len(arcs))],
                  bounds=Bounds(0, 1), options={'time_limit': LIMIT_SECONDS})
    out['searchSeconds'] = round(time.perf_counter() - started, 2)
    notes['searchMessage'] = result.message
    if result.x is not None:
        names = list(tokens)
        dictionary = sorted(names[t] for t in range(len(names)) if result.x[t] > 0.5)
        for entry in sorted(dictionary, key=len, reverse=True):          # drop entries the spelling does not need
            rest = [d for d in dictionary if d != entry]
            if sibling.dictionary_spells(programs, rest):
                dictionary = rest
        if sibling.dictionary_spells(programs, dictionary):
            out['dictionary'] = dictionary
        dual_bound = getattr(result, 'mip_dual_bound', None)
        notes['searchReportedBound'] = None if dual_bound is None else round(float(dual_bound), 6)
    out['notes'] = notes
    return out, len(every)


def one(key):
    import evaluate
    sibling = evaluate.load_sibling()
    programs = evaluate.load_instances()[key]['programs']
    measurement = {'cheap': cheap_checks(programs), 'diagnostic': shipped_diagnostic(programs)}
    measurement['flow'], measurement['eligibleOccurrences'] = flow_method(programs, sibling)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    measurement['flow']['peakMemoryMiB'] = round(peak / (1 << 20 if sys.platform == 'darwin' else 1 << 10), 1)
    return measurement


def main():
    import evaluate
    import scipy
    keys = sorted(evaluate.load_instances(), key=lambda k: evaluate.load_instances()[k]['bytes'])
    corpora = {}
    for key in keys:
        started = time.time()
        run = subprocess.run([sys.executable, '-B', os.path.abspath(__file__), '--one', key], capture_output=True, text=True)
        if run.returncode != 0:
            raise SystemExit(f'{key} failed:\n{run.stderr[-2000:]}')
        corpora[key] = json.loads(run.stdout)
        print(key, 'done in', round(time.time() - started), 's', flush=True)
    out = {'schema': 'capacity-boundary-measurements/v1',
           'environment': {'python': platform.python_version(), 'scipy': scipy.__version__, 'machine': platform.machine(),
                           'cores': os.cpu_count(), 'note': 'one laptop, other work running; times are single runs except the cheap checks (best of 3)'},
           'limits': {'secondsPerSolve': LIMIT_SECONDS, 'diagnosticSeconds': DIAGNOSTIC_SECONDS, 'sizeLimitOccurrences': SIZE_LIMIT,
                      'restrictedEntryLength': RESTRICTED_LENGTH},
           'corpora': {key: corpora[key] for key in sorted(corpora)}}
    with open(os.path.join(HERE, 'measurements.json'), 'w') as f:
        json.dump(out, f, separators=(',', ':'))
        f.write('\n')


if __name__ == '__main__':
    if '--one' in sys.argv:
        print(json.dumps(one(sys.argv[sys.argv.index('--one') + 1])))
    else:
        main()
