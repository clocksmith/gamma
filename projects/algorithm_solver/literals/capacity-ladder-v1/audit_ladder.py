#!/usr/bin/env python3
"""Audit of the deficit ladder (ladder.py) against exhaustive search on small corpora, under both rules. The
lower bound must never exceed the true minimum and every dictionary must be legal and spell every program.
The table shows, by how far the minimum lies above the rank, how often the answer is exact. Python 3.10+, numpy.

    python3 -B audit_ladder.py [SEED] [MAX_LEVEL]      exits 1 on any unsound answer
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
import check_certificate                                # noqa: E402
import ladder                                           # noqa: E402

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
max_level = int(sys.argv[2]) if len(sys.argv) > 2 else 3
GADGETS = (['axby', 'byax', 'aybx', 'bxay'], ['ax', 'ay', 'bx', 'by'], ['abd', 'abe', 'fbd'], ['pxqy', 'qypx', 'pyqx', 'qxpy'])


def rename(words, shift):
    return [''.join(chr(ord(c) + shift) if c.isalpha() else c for c in w) for w in words]


def corpora():
    rng = random.Random(seed)
    for _ in range(600):
        a = rng.choice(['ab', 'abc', 'abcd', 'abcde', 'abcdef'])
        yield 'random', sorted({''.join(rng.choice(a) for _ in range(rng.randint(2, 7))) for _ in range(rng.randint(2, 5))})
    for _ in range(1200):
        a = 'abcdefghij'[:rng.randint(4, 10)]
        blocks = [''.join(rng.choice(a) for _ in range(rng.randint(1, 4))) for _ in range(rng.randint(2, 5))]
        yield 'blocks', sorted({''.join(rng.choice(blocks) for _ in range(rng.randint(1, 3))) + rng.choice(['', rng.choice(a)]) for _ in range(rng.randint(2, 6))})
    for _ in range(900):
        a, rare = 'abcd', 'XYZW'
        frags = [''.join(rng.choice(a + rare[:rng.randint(1, 4)]) for _ in range(rng.randint(2, 5))) for _ in range(rng.randint(1, 3))]
        yield 'rare', sorted({rng.choice(['', rng.choice(a)]) + rng.choice(frags) + ''.join(rng.choice(a) for _ in range(rng.randint(0, 2))) + rng.choice(['', rng.choice(frags)]) for _ in range(rng.randint(2, 6))})
    for _ in range(800):
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
    for _ in range(500):                                   # two or three gadgets on separate alphabets, some mutated or glued
        parts, out = rng.randint(2, 3), set()
        for k in range(parts):
            words = rename(rng.choice(GADGETS), 0)
            words = [''.join(chr(ord('a') + (ord(c) - ord('a')) % 26) for c in w) for w in words]
            words = [''.join(c.upper() if k == 1 else (c if k == 0 else chr(ord('0') + (ord(c) - ord('a')) % 10)) for c in w) for w in words]
            out.update(words)
        out = sorted(out)
        for _ in range(rng.randint(0, 2)):
            i, j = rng.randrange(len(out)), rng.randrange(len(out))
            if i != j and rng.random() < 0.5:
                out.append(out[i] + out[j])
        yield 'unions', sorted(set(out))


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
        r = ladder.analyze(programs, rule, max_level=max_level)
        d = r['dictionary']
        if rule == 'W2' and r.get('certificate') is not None:
            try:
                certified = check_certificate.check(programs, r['certificate'])
            except ValueError as problem:
                certified = str(problem)
            stats['certificates']['checked'] += 1
            if certified != r['lowerBound'] or certified > minimum:
                unsound.append({'rule': rule, 'programs': programs, 'minimum': minimum, 'lowerBound': r['lowerBound'], 'certificateCheck': certified})
                continue
            stats['certificates']['valid'] += 1
        legal = d is None or (len(set(d)) == len(d) and set(d) <= set(tokens) and exhaustive.minimum(programs, sorted(d))[0] is not None)
        if r['lowerBound'] > minimum or not legal or (d is not None and len(d) < minimum):
            unsound.append({'rule': rule, 'programs': programs, 'minimum': minimum, 'lowerBound': r['lowerBound'], 'dictionary': d, 'note': r['note']})
            continue
        upper = len(d) if d is not None else len(set(''.join(programs)))
        upper = min(upper, len(set(''.join(programs)))) if rule == 'W2' else upper
        excess = min(minimum - r['rank'], 4)
        s = stats[excess]
        s['checks'] += 1
        s['bound exact'] += r['lowerBound'] == minimum
        s['exact'] += r['lowerBound'] == minimum and upper == minimum
        stats['family ' + family + ' ' + rule]['checks'] += 1
print('seed', seed, 'max level', max_level, 'seconds', round(time.time() - started, 1))
for key in sorted(k for k in stats if isinstance(k, int)):
    print(f"minimum is rank + {key}{' or more' if key == 4 else ''}:", dict(stats[key]))
print('certificates', dict(stats.pop('certificates', {})))
for key in sorted(k for k in stats if isinstance(k, str)):
    print(key, dict(stats[key]))
total = sum(s['checks'] for k, s in stats.items() if isinstance(k, int))
print('checks', total, 'exact', sum(s['exact'] for k, s in stats.items() if isinstance(k, int)), 'unsound', len(unsound))
for u in unsound[:6]:
    print('UNSOUND', u)
sys.exit(1 if unsound else 0)
