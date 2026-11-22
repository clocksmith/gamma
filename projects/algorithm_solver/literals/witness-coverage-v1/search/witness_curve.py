#!/usr/bin/env python3
"""Witness-rule coverage curve for compact matched80: floors, ceilings, and where they meet.

For each budget K: how many of the 80 programs can a dictionary of at most K entries spell exactly, when
every multi-character entry must occur in at least two of the 80 programs and no entry is a whole program.

Floors are dictionaries, each rechecked by a separate legality and cover check:
  - single characters only (exact optimum by integer program; the witness is rechecked without the solver);
  - a greedy build that adds one program at a time using shared fragments and single characters;
  - the stored 64-entry witnessed dictionary, with entries removed one at a time.
Ceilings:
  - the unrestricted maximum (proved separately): a witnessed dictionary is also an unrestricted one;
  - 79 below 92 entries (all 80 need 92, by the rank of the forced blocks);
  - characters each program forces: if a program's forced blocks span the unit vector of a character,
    every dictionary spelling that program has that direction in its span. An integer program maximizes
    the number of programs whose forced characters fit in K. (Solver-dependent; reported as such.)

    witness_curve.py GAMMA_CHECKOUT OUT.json [SEEDS]
"""
import collections
import json
import random
import subprocess
import sys

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

REPO, OUT = sys.argv[1], sys.argv[2]
SEEDS = int(sys.argv[3]) if len(sys.argv) > 3 else 4
PIN, ROOT = '59ff04415ff2afd04ff2ed451340f4f02852bf18', 'projects/algorithm_solver/literals/'
P, B = 1_000_000_007, 2


def blob(path):
    return subprocess.check_output(['git', '-C', REPO, 'show', f'{PIN}:{ROOT}{path}'])


ids = sorted(json.loads(blob('matched80-v1/labels/ids.json')))
wanted = set(ids)
src = {r['id']: blob('scale-v2/generated/' + r['file']) for r in json.loads(blob('scale-v2/generated/manifest.json'))['rows']
       if r['variant'] == 'compact' and r['id'] in wanted}
assert len(src) == 80 and all(0 not in s for s in src.values())
whole = set(src.values())
alphabet = sorted(set(b''.join(whole)))
need = {p: frozenset(s) for p, s in src.items()}

# ---------------------------------------------------------------- legality and cover, used to recheck every floor
def occurrences(word):
    return sum(word in s for s in whole)


def legal(words):
    return all(w and w not in whole and (len(w) == 1 or occurrences(w) >= 2) for w in words)


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


best = {}                                   # budget -> (programs, source, frozenset of entries)


def offer(words, source):
    words = frozenset(words)
    if not legal(words):
        return
    count = len(spelled(words))
    k = len(words)
    if count > best.get(k, (-1,))[0]:
        best[k] = (count, source, words)


# ---------------------------------------------------------------- integer program: most programs whose sets fit in K items
def fit_curve(sets, universe):
    col = {c: len(ids) + j for j, c in enumerate(universe)}
    n = len(ids) + len(universe)
    pairs = [(i, col[c]) for i, p in enumerate(ids) for c in sets[p]]
    A = lil_matrix((len(pairs) + 1, n))
    for r, (i, j) in enumerate(pairs):
        A[r, i] = 1
        A[r, j] = -1
    A[len(pairs), len(ids):] = 1
    A = A.tocsr()
    cost = np.zeros(n)
    cost[:len(ids)] = -1
    curve = {}
    for k in range(0, len(alphabet) + 1):
        upper = np.zeros(len(pairs) + 1)
        upper[-1] = k
        res = milp(cost, constraints=LinearConstraint(A, -np.inf, upper), integrality=np.ones(n), bounds=Bounds(0, 1))
        assert res.status == 0, (k, res.message)
        chosen = frozenset(c for c in universe if res.x[col[c]] > 0.5)
        curve[k] = (round(-res.fun), chosen)
    return curve


# ---------------------------------------------------------------- floor 1: single characters
singles = fit_curve(need, alphabet)
single_curve = {}
for k, (optimum, chosen) in singles.items():
    words = frozenset(bytes([c]) for c in chosen)
    got = len(spelled(words)) if words else 0
    assert got == optimum, (k, got, optimum)
    single_curve[k] = got
    if words:
        offer(words, 'single characters')

# ---------------------------------------------------------------- shared fragments: longest match in another program
shared_len = {}
for p in ids:
    s = src[p]
    others = b'\x00'.join(src[q] for q in ids if q != p)
    L, prev = [0] * len(s), 0
    for i in range(len(s)):
        l = max(prev - 1, 0)
        while i + l < len(s) and s[i:i + l + 1] in others:
            l += 1
        L[i] = prev = l
    shared_len[p] = L


def parse_cost(p, by_first, have, bias_single, bias_multi):
    """Cheapest way to spell p: entries already held are free, each new entry costs one."""
    s, L = src[p], shared_len[p]
    n = len(s)
    inf = float('inf')
    f, back = [inf] * (n + 1), [0] * (n + 1)
    f[0] = 0.0
    for i in range(n):
        fi = f[i]
        if fi == inf:
            continue
        for w in by_first.get(s[i], ()):
            if s.startswith(w, i) and fi < f[i + len(w)]:
                f[i + len(w)], back[i + len(w)] = fi, i
        c1 = fi + 1 + bias_single
        if c1 < f[i + 1]:
            f[i + 1], back[i + 1] = c1, i
        cm = fi + 1 + bias_multi
        for j in range(i + 2, min(n, i + L[i]) + 1):
            if cm < f[j]:
                f[j], back[j] = cm, i
    pieces, j = [], n
    while j > 0:
        pieces.append(s[back[j]:j])
        j = back[j]
    return {w for w in pieces if w not in have}


def greedy(bias_single, bias_multi, rng, label):
    have, group = set(), set()
    by_first = collections.defaultdict(list)
    while len(group) < len(ids):
        options = []
        for p in ids:
            if p in group:
                continue
            new = parse_cost(p, by_first, have, bias_single, bias_multi)
            options.append((len(new), rng.random() if rng else 0, p, new))
        size, _, p, new = min(options)
        if any(w in whole for w in new):
            new = {w for w in new if w not in whole} | {bytes([c]) for w in new if w in whole for c in w}
        for w in new:
            have.add(w)
            by_first[w[0]].append(w)
        group.add(p)
        offer(have, label)


greedy(0.0, 0.001, None, 'greedy build, single characters preferred')
greedy(0.001, 0.0, None, 'greedy build, shared fragments preferred')
for seed in range(SEEDS):
    greedy(0.0, 0.0, random.Random(seed), 'greedy build, random ties')
    greedy(0.0, 0.001, random.Random(100 + seed), 'greedy build, single characters preferred, random ties')
    greedy(0.001, 0.0, random.Random(200 + seed), 'greedy build, shared fragments preferred, random ties')

# ---------------------------------------------------------------- floor 3: the stored witnessed dictionary, shrunk
stored = {w.encode() for w in json.loads(blob('sixbit-v1/run-v1/b-w-compact/manifest.json'))['vocabulary']}
offer(stored, 'stored 64-entry witnessed dictionary')
current = set(stored)
while len(current) > 1:
    kept = len(spelled(current))
    choice = min(current, key=lambda w: (kept - len(spelled(current - {w})), -len(w), w))
    current.discard(choice)
    offer(current, 'stored 64-entry witnessed dictionary, entries removed')

# ---------------------------------------------------------------- ceilings
def unrestricted(k):
    return 0 if k == 0 else k - 1 if k <= 60 else k if k <= 67 else k + 1 if k <= 79 else 80


owners = collections.defaultdict(set)
for p, s in src.items():
    for i in range(len(s) - 1):
        owners[s[i:i + 2]].add(p)
col_of = {c: i for i, c in enumerate(alphabet)}


def vec(word):
    v, weight = [0] * len(alphabet), 1
    for c in word:
        v[col_of[c]] = (v[col_of[c]] + weight) % P
        weight = weight * B % P
    return v


def forced_characters(s):
    """Characters whose unit vector lies in the span of this program's forced blocks."""
    blocks, start = [], 0
    for i in range(len(s) - 1):
        if len(owners[s[i:i + 2]]) < 2:
            blocks.append(s[start:i + 1])
            start = i + 1
    blocks.append(s[start:])
    rows, basis = [vec(b) for b in set(blocks)], []
    for v in rows:
        for pivot, r in basis:
            if v[pivot]:
                f = v[pivot]
                v = [(a - f * b) % P for a, b in zip(v, r)]
        pivot = next((j for j, x in enumerate(v) if x), None)
        if pivot is None:
            continue
        inv = pow(v[pivot], P - 2, P)
        v = [x * inv % P for x in v]
        basis = [(pj, [(a - r[pivot] * b) % P for a, b in zip(r, v)] if r[pivot] else r) for pj, r in basis]
        basis.append((pivot, v))
    out = set()
    for c in set(s):
        v = [0] * len(alphabet)
        v[col_of[c]] = 1
        for pivot, r in basis:
            if v[pivot]:
                f = v[pivot]
                v = [(a - f * b) % P for a, b in zip(v, r)]
        if not any(v):
            out.add(c)
    return frozenset(out), len(blocks), len(basis)


forced, block_facts = {}, {}
for p in ids:
    forced[p], n_blocks, block_rank = forced_characters(src[p])
    block_facts[p] = {'distinctCharacters': len(need[p]), 'forcedBlocks': n_blocks, 'blockRank': block_rank, 'forcedCharacters': len(forced[p])}
forced_curve = {k: v[0] for k, v in fit_curve(forced, alphabet).items()}

# ---------------------------------------------------------------- assemble
rows, floor = [], 0
top = len(alphabet)
for k in range(0, top + 1):
    if k in best and best[k][0] > floor:
        floor, source, words = best[k]
        holder = {'source': source, 'entries': sorted(w.decode('latin-1') for w in words)}
    elif k == 0:
        holder = {'source': 'empty dictionary', 'entries': []}
    ceiling = min(unrestricted(k), forced_curve[k], 80 if k >= top else 79)
    rows.append({'budget': k, 'floor': floor, 'ceiling': ceiling, 'exact': floor == ceiling,
                 'singleCharacters': single_curve[k], 'unrestrictedMaximum': unrestricted(k), 'forcedCharacterCeiling': forced_curve[k],
                 'floorSource': holder['source'], 'floorEntries': len(holder['entries']),
                 'multiCharacterEntriesInFloor': sum(len(e) > 1 for e in holder['entries']), 'dictionary': holder['entries']})
assert all(r['floor'] <= r['ceiling'] for r in rows), [r['budget'] for r in rows if r['floor'] > r['ceiling']]
json.dump({'pin': PIN, 'variant': 'compact', 'rule': 'multi-character entries occur in at least two of the 80 programs; no entry is a whole program',
           'field': {'prime': P, 'base': B}, 'greedySeeds': SEEDS, 'perProgram': block_facts, 'rows': rows}, open(OUT, 'w'), indent=1)
exact = [r['budget'] for r in rows if r['exact']]
print('budgets with an exact value:', len(exact), 'of', len(rows))
print('budgets where the floor beats single characters:', [(r['budget'], r['singleCharacters'], r['floor']) for r in rows if r['floor'] > r['singleCharacters']][:40])
print('widest gap:', max(rows, key=lambda r: r['ceiling'] - r['floor']))
