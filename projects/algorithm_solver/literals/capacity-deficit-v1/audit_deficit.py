#!/usr/bin/env python3
"""Audit of the deficit hierarchy (deficit.py) against exhaustive search on small corpora, under both rules.
The lower bound must never exceed the true minimum, every dictionary it builds must be legal and spell every
program, and the table shows how often the answer is exact. Python 3.8+; no solver.

    python3 -B audit_deficit.py [SEED]      exits 1 on any unsound answer
"""
import collections
import importlib.util
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


exhaustive = load('cx_evaluate', os.path.join(ROOT, 'capacity-complexity-v1', 'evaluate.py'))
import deficit                                          # noqa: E402

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1


def corpora():
    rng = random.Random(seed)
    for _ in range(800):
        a = rng.choice(['ab', 'abc', 'abcd', 'abcde', 'abcdef'])
        yield 'random', sorted({''.join(rng.choice(a) for _ in range(rng.randint(2, 7))) for _ in range(rng.randint(2, 5))})
    for _ in range(1800):
        a = 'abcdefghij'[:rng.randint(4, 10)]
        blocks = [''.join(rng.choice(a) for _ in range(rng.randint(1, 4))) for _ in range(rng.randint(2, 5))]
        yield 'blocks', sorted({''.join(rng.choice(blocks) for _ in range(rng.randint(1, 3))) + rng.choice(['', rng.choice(a)]) for _ in range(rng.randint(2, 6))})
    for _ in range(1200):
        a, rare = 'abcd', 'XYZW'
        frags = [''.join(rng.choice(a + rare[:rng.randint(1, 4)]) for _ in range(rng.randint(2, 5))) for _ in range(rng.randint(1, 3))]
        yield 'rare', sorted({rng.choice(['', rng.choice(a)]) + rng.choice(frags) + ''.join(rng.choice(a) for _ in range(rng.randint(0, 2))) + rng.choice(['', rng.choice(frags)]) for _ in range(rng.randint(2, 6))})
    for _ in range(1000):
        a = 'abcdefpqxy'
        base = rng.choice([['abd', 'abe', 'fbd'], ['axby', 'byax', 'aybx', 'bxay'], ['abd', 'abpxqy', 'qypxbd', 'abpyqx', 'qxpybd'], ['aaa', 'aab']])
        out = set(base)
        for _ in range(rng.randint(0, 3)):
            w = list(rng.choice(base))
            i = rng.randrange(len(w))
            op = rng.choice('smd')
            if op == 's':
                w[i] = rng.choice(a)
            elif op == 'm' and len(w) > 2:
                del w[i]
            else:
                w.insert(i, rng.choice(a))
            out.add(''.join(w))
        yield 'mutated', sorted(out)
    for _ in range(400):
        n = rng.randint(3, 5)
        edges = {tuple(sorted(rng.sample(range(n), 2))) for _ in range(rng.randint(2, 5))}
        words = ['ABCDE'[u] + 'abcdefg'[i] + 'ABCDE'[v] for i, (u, v) in enumerate(sorted(edges))]
        yield 'graph', sorted({w + t for w in words for t in '12'})


stats, unsound, seen, started = collections.defaultdict(collections.Counter), [], set(), time.time()
for family, programs in corpora():
    if len(programs) < 2 or any(len(p) < 2 for p in programs) or tuple(programs) in seen:
        continue
    seen.add(tuple(programs))
    for rule in ('W2', 'U'):
        tokens = exhaustive.eligible(programs, rule)
        minimum = exhaustive.minimum(programs, tokens)[0]
        if minimum is None:
            continue
        r = deficit.analyze(programs, rule)
        s = stats[(family, rule)]
        s['corpora'] += 1
        d = r['dictionary']
        legal = d is None or (len(set(d)) == len(d) and set(d) <= set(tokens) and exhaustive.minimum(programs, sorted(d))[0] is not None)
        if r['lowerBound'] > minimum or not legal or (d is not None and len(d) < minimum):
            unsound.append({'rule': rule, 'programs': programs, 'minimum': minimum, 'lowerBound': r['lowerBound'], 'dictionary': d, 'note': r['note']})
            continue
        upper = len(d) if d is not None else len(set(''.join(programs)))
        excess = minimum - r['rank']
        s[f'minimum is rank + {excess}' if excess <= 2 else 'minimum is rank + 3 or more'] += 1
        exact = r['lowerBound'] == minimum and (upper == minimum)
        s['exact'] += exact
        if excess == 1:
            s['rank + 1 cases exact'] += exact
        if r['lowerBound'] == r['rank'] + 2:
            s['proved rank + 2'] += 1
print('seed', seed, 'seconds', round(time.time() - started, 1))
for key in sorted(stats):
    print(key, dict(stats[key]))
total = sum(s['corpora'] for s in stats.values())
print('audits', total, 'exact', sum(s['exact'] for s in stats.values()), 'unsound', len(unsound))
for u in unsound[:6]:
    print('UNSOUND', u)
sys.exit(1 if unsound else 0)
