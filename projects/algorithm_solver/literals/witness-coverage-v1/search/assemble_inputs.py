#!/usr/bin/env python3
"""Freeze the figure inputs for the witness-rule coverage curve.

Merges every dictionary found so far, keeps for each budget the one that spells the most programs, replays
it against the pinned source bytes to record exactly which programs it spells, and writes:

  coverage.json       one row per budget: verified lower end, proven upper end, single-character value
  search-effort.json  the solver runs, kept apart from the bounds: they are search records, not proofs

    assemble_inputs.py GAMMA_CHECKOUT CURVE.json MILP.jsonl OUT_DIR
"""
import collections
import json
import os
import subprocess
import sys

REPO, CURVE, MILP, OUT = sys.argv[1:5]
PIN, ROOT = '59ff04415ff2afd04ff2ed451340f4f02852bf18', 'projects/algorithm_solver/literals/'


def blob(path):
    return subprocess.check_output(['git', '-C', REPO, 'show', f'{PIN}:{ROOT}{path}'])


ids = sorted(json.loads(blob('matched80-v1/labels/ids.json')))
wanted = set(ids)
src = {r['id']: blob('scale-v2/generated/' + r['file']) for r in json.loads(blob('scale-v2/generated/manifest.json'))['rows']
       if r['variant'] == 'compact' and r['id'] in wanted}
whole = set(src.values())
assert len(src) == 80 and all(max(s) < 128 for s in whole)
need = {p: frozenset(s) for p, s in src.items()}
TOP = len(frozenset().union(*need.values()))


def legal(words):
    return all(w and w not in whole and (len(w) == 1 or sum(w in s for s in whole) >= 2) for w in words)


def spelled(words):
    by_first = collections.defaultdict(list)
    for w in words:
        by_first[w[0]].append(w)
    out = []
    for p in ids:
        s = src[p]
        reach = [False] * (len(s) + 1)
        reach[0] = True
        for i in range(len(s)):
            if reach[i]:
                for w in by_first.get(s[i], ()):
                    if s.startswith(w, i):
                        reach[i + len(w)] = True
        if reach[len(s)]:
            out.append(p)
    return out


def unrestricted(k):
    return 0 if k == 0 else k - 1 if k <= 60 else k if k <= 67 else k + 1 if k <= 79 else 80


# ---- candidates: (entries, how it was found)
candidates = []
curve = json.load(open(CURVE))
for row in curve['rows']:
    if row['dictionary']:
        candidates.append(([e.encode('latin-1') for e in row['dictionary']], row['floorSource']))
effort = []
if os.path.exists(MILP):
    for line in open(MILP):
        rec = json.loads(line)
        if rec.get('vocabulary'):
            candidates.append(([e.encode('latin-1') for e in rec['vocabulary']], 'frozen model, incumbent at the time limit' if rec['status'] != 0 else 'frozen model, solved'))
        effort.append({'slots': rec['budget'], 'model': 'sixbit-v1/model.py at the pinned commit, kind B1, witness rule', 'timeLimitSeconds': 1500,
                       'seconds': rec['seconds'],
                       'outcome': 'time limit reached' if rec['status'] == 1 else 'the solver reports its dictionary as optimal; not independently certified',
                       'programsInBestDictionaryFound': rec.get('covered'),
                       'solverBoundAtStop': None if rec.get('mip_dual_bound') is None else -rec['mip_dual_bound'],
                       'usedAsCeiling': False})

best = {}
for words, source in candidates:
    words = sorted(set(words))
    assert legal(words), source
    covers = spelled(words)
    k = len(words)
    if len(covers) > best.get(k, (-1,))[0]:
        best[k] = (len(covers), words, covers, source)

# ---- single characters: the recorded optimum and its character set, rechecked here
single = {}
for row in curve['rows']:
    single[row['budget']] = row['singleCharacters']
single_sets = {}
for (count, words, covers, source) in best.values():
    if all(len(w) == 1 for w in words) and source == 'single characters':
        single_sets[len(words)] = (words, covers)

dictionaries, rows, holder = {}, [], None
floor = 0
for k in range(0, TOP + 1):
    if k in best and best[k][0] > floor:
        floor = best[k][0]
        key = f'd{k}'
        dictionaries[key] = {'entries': [w.decode('latin-1') for w in best[k][1]], 'entryCount': k, 'spells': best[k][2],
                             'multiCharacterEntries': sum(len(w) > 1 for w in best[k][1]), 'foundBy': best[k][3]}
        holder = key
    upper = min(unrestricted(k), 80 if k >= TOP else 79)
    upper_source = ('all 80 need 92 entries (rank of the forced blocks)' if k < TOP and unrestricted(k) > 79 else
                    'single characters spell all 80' if k >= TOP else 'unrestricted exact maximum')
    rows.append({'slots': k, 'lower': floor, 'lowerDictionary': holder, 'upper': upper, 'upperSource': upper_source,
                 'exact': floor == upper, 'singleCharacters': single[k], 'unrestrictedMaximum': unrestricted(k)})
    assert floor <= upper and single[k] <= floor, k

# ---- single characters at every budget: the optimum from an integer program, stored with its character set
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix
letters = sorted(frozenset().union(*need.values()))
col = {c: len(ids) + j for j, c in enumerate(letters)}
nvar = len(ids) + len(letters)
pairs = [(i, col[c]) for i, p in enumerate(ids) for c in need[p]]
A = lil_matrix((len(pairs) + 1, nvar))
for r_, (i, j) in enumerate(pairs):
    A[r_, i] = 1
    A[r_, j] = -1
A[len(pairs), len(ids):] = 1
A = A.tocsr()
cost = np.zeros(nvar)
cost[:len(ids)] = -1
single_sets = {}
for k in range(0, TOP + 1):
    upper_row = np.zeros(len(pairs) + 1)
    upper_row[-1] = k
    res = milp(cost, constraints=LinearConstraint(A, -np.inf, upper_row), integrality=np.ones(nvar), bounds=Bounds(0, 1))
    assert res.status == 0
    chosen = [c for c in letters if res.x[col[c]] > 0.5]
    got = [p for p in ids if need[p] <= frozenset(chosen)]
    assert len(chosen) <= k and len(got) == round(-res.fun) == single[k], (k, len(got), single[k])
    single_sets[k] = {'characters': bytes(chosen).decode('latin-1'), 'spells': len(got)}

os.makedirs(OUT, exist_ok=True)
json.dump({'schema': 'witness-coverage/v1', 'pin': PIN, 'corpus': '80 compact JavaScript programs (matched80), original trailing newlines',
           'rule': 'single characters are eligible; a longer entry must occur in at least two of the 80 programs; no entry is a whole program',
           'lowerMeans': 'programs spelled exactly by a stored dictionary of at most that many entries, replayed against the pinned bytes',
           'upperMeans': 'a proven ceiling; its source is named per row',
           'singleCharactersMeans': 'most programs whose characters all fit in that many single-character entries; each value is attained by the stored character set, and its optimality is from an integer program',
           'rows': rows, 'dictionaries': dictionaries, 'singleCharacterSets': single_sets}, open(os.path.join(OUT, 'coverage.json'), 'w'), indent=1)
json.dump({'schema': 'witness-coverage-search/v1', 'note': 'Search records. A run that stops at its time limit proves nothing about the maximum. A run the solver reports as optimal is a solver claim, not a checked proof. None of these is used as a ceiling; each dictionary found is used as a lower end only after it is replayed.',
           'runs': sorted(effort, key=lambda r: r['slots'])}, open(os.path.join(OUT, 'search-effort.json'), 'w'), indent=1)
exact = [r['slots'] for r in rows if r['exact']]
print('exact budgets:', len(exact), '| dictionaries stored:', len(dictionaries))
print('intervals at 8, 16, 24, 32, 40, 48, 56:', [(r['slots'], r['lower'], r['upper'], dictionaries[r['lowerDictionary']]['foundBy'] if r['lowerDictionary'] else None) for r in rows if r['slots'] in (8, 16, 24, 32, 40, 48, 56)])
