#!/usr/bin/env python3
"""Addendum to the witness-rule coverage curve of matched80 (witness-coverage-v1): more budgets where the value is
exact. Python 3.10+, numpy and Git; no solver. The frozen curve and its figure are not changed.

Upper ends. Under the witness rule every legal parse cuts where a two-character window occurs in fewer than two
of the 80 programs, so the blocks of any subset of programs are spelled by the dictionary, and a dictionary that
spells the subset has at least as many entries as the rank of that subset's blocks. This script computes that
rank for every subset of 79, 78 and (with --deep) 77 programs.

Lower ends. dictionaries.json holds dictionaries found by the rank-tight parsing test; each is checked here for
legality (single characters; longer entries of at most 160 bytes in at least two of the 80 programs; no whole
program) and replayed against the pinned bytes.

    python3 -B check_addendum.py /path/to/gamma [--deep]
"""
import collections
import itertools
import json
import os
import subprocess
import sys

import numpy as np

REPO = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
P, B = 1_000_000_007, 2
PIN, ROOT = '59ff04415ff2afd04ff2ed451340f4f02852bf18', 'projects/algorithm_solver/literals/'


def check(value, message):
    if not value:
        raise SystemExit('FAILED: ' + message)


def blob(path):
    return subprocess.check_output(['git', '-C', REPO, 'show', f'{PIN}:{ROOT}{path}'])


ids = sorted(json.loads(blob('matched80-v1/labels/ids.json')))
wanted = set(ids)
src = {r['id']: blob('scale-v2/generated/' + r['file']) for r in json.loads(blob('scale-v2/generated/manifest.json'))['rows']
       if r['variant'] == 'compact' and r['id'] in wanted}
check(len(src) == 80 and len(set(src.values())) == 80, 'cohort is not 80 distinct sources')
letters = sorted(set(b''.join(src.values())))
column, width = {c: i for i, c in enumerate(letters)}, len(letters)
owners = {}
for n, p in enumerate(ids):
    for i in range(len(src[p]) - 1):
        owners.setdefault(src[p][i:i + 2], set()).add(n)


def blocks(s):
    out, start = [], 0
    for i in range(len(s) - 1):
        if len(owners[s[i:i + 2]]) < 2:
            out.append(s[start:i + 1])
            start = i + 1
    out.append(s[start:])
    return out


def reduce(rows):
    m = np.array(rows, dtype=np.int64) % P
    r = 0
    for c in range(m.shape[1]):
        nonzero = np.nonzero(m[r:, c])[0]
        if len(nonzero) == 0:
            continue
        pivot = r + int(nonzero[0])
        m[[r, pivot]] = m[[pivot, r]]
        m[r] = m[r] * pow(int(m[r, c]), P - 2, P) % P
        factor = m[:, c].copy()
        factor[r] = 0
        m = (m - factor[:, None] * m[r][None, :]) % P
        r += 1
        if r == m.shape[0]:
            break
    return m[:r]


def vector(block):
    v, weight = [0] * width, 1
    for ch in block:
        v[column[ch]] = (v[column[ch]] + weight) % P
        weight = weight * B % P
    return v


basis = {p: reduce([vector(b) for b in set(blocks(src[p]))]) for p in ids}


def rank_without(dropped):
    return len(reduce(np.vstack([basis[p] for p in ids if p not in dropped])))


def spelled(words):
    by_first = collections.defaultdict(list)
    for w in words:
        by_first[w[0]].append(w)
    out = []
    for p in ids:
        s = src[p]
        reach = [True] + [False] * len(s)
        for i in range(len(s)):
            if reach[i]:
                for w in by_first.get(s[i], ()):
                    if s.startswith(w, i):
                        reach[i + len(w)] = True
        if reach[-1]:
            out.append(p)
    return out


def legal(words):
    whole = set(src.values())
    return len(set(words)) == len(words) and all(
        w and w not in whole and (len(w) == 1 or (len(w) <= 160 and sum(1 for s in src.values() if w in s) >= 2)) for w in words)


check(rank_without(()) == 92 == width, 'all 80 programs: rank is not 92')
need = {80: 92}
for size, count in ((79, 1), (78, 2)) + (((77, 3),) if '--deep' in sys.argv else ()):
    need[size] = min(rank_without(set(drop)) for drop in itertools.combinations(ids, count))
    print(f'every set of {size} programs needs at least {need[size]} entries (minimum block rank over all such sets)', flush=True)
data = json.load(open(os.path.join(HERE, 'dictionaries.json')))
check(need[79] == data['need']['79'] and need[78] == data['need']['78'], 'the subset ranks differ from the recorded ones')
if 77 in need:
    check(need[77] == data['need']['77'], 'the rank for 77 programs differs from the recorded one')
have = {}
for name, d in data['dictionaries'].items():
    words = [w.encode('utf-8') for w in d['entries']]
    check(legal(words), name + ': an entry is not legal under the witness rule')
    got = spelled(words)
    check(len(words) == d['entryCount'] and got == d['spells'], name + ': does not replay as recorded')
    have[len(words)] = max(have.get(len(words), 0), len(got))
    print(f"{name}: {len(words)} entries spell {len(got)} programs; longer entries {[w.decode() for w in words if len(w) > 1]}")
# A dictionary of k entries also serves every larger budget. need[m] never decreases with m, so with k slots the
# number of programs is below the smallest m whose need exceeds k.
exact = []
for slots in range(70, 92):
    lower = max([programs for entries, programs in have.items() if entries <= slots] or [0])
    above = [size for size in need if need[size] > slots]
    if above and lower == min(above) - 1:
        exact.append((slots, lower))
print('exact from this addendum:', exact)
expected = data['newExactSlotsDeep'] if 77 in need else data['newExactSlots']
check([s for s, _ in exact if s < 85] == expected, 'the list of newly exact budgets differs from the recorded one')
print(f"ok: {len(expected)} budgets become exact, {24 + len(expected)} of 93 with the 24 of the frozen curve" + ('' if 77 in need else '; --deep adds 76 slots'))
