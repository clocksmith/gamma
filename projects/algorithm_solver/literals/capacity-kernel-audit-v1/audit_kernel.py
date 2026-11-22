#!/usr/bin/env python3
"""Audit of nullspace_kernel_certificate alone (no other tier, no fallback) against exhaustive search.
For rule U (k=1) and W2 (k=2): RANK_ATTAINED must come with a legal dictionary of size rank and the true
minimum must equal rank; RANK_UNATTAINABLE must mean minimum >= rank + 1; in the claimed exact class
(deltaDetStar == 0, search not aborted) the status must be decisive and correct."""
import collections, importlib.util, json, os, random, sys, time
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m); return m
sys.path.insert(0, os.path.join(ROOT, 'capacity-complexity-v1'))
ev = load('cx_evaluate', os.path.join(ROOT, 'capacity-complexity-v1', 'evaluate.py'))
dg = load('diag', os.path.join(ROOT, 'capacity-diagnostic-v1', 'diagnostic.py'))
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1

def corpora():
    rng = random.Random(seed)
    for _ in range(1200):
        a = rng.choice(['ab', 'abc', 'abcd', 'abcde', 'abcdef'])
        yield 'random', sorted({''.join(rng.choice(a) for _ in range(rng.randint(2, 7))) for _ in range(rng.randint(2, 5))})
    for _ in range(2500):                       # shared blocks with stray characters: produces minimum below alphabet
        a = 'abcdefghij'[:rng.randint(4, 10)]
        blocks = [''.join(rng.choice(a) for _ in range(rng.randint(1, 4))) for _ in range(rng.randint(2, 5))]
        yield 'blocks', sorted({''.join(rng.choice(blocks) for _ in range(rng.randint(1, 3))) + rng.choice(['', rng.choice(a)]) for _ in range(rng.randint(2, 6))})
    for _ in range(1500):                       # rare characters that only ever appear inside shared fragments
        a = 'abcd'; rare = 'XYZW'
        frags = [''.join(rng.choice(a + rare[:rng.randint(1, 4)]) for _ in range(rng.randint(2, 5))) for _ in range(rng.randint(1, 3))]
        yield 'rare', sorted({rng.choice(['', rng.choice(a)]) + rng.choice(frags) + ''.join(rng.choice(a) for _ in range(rng.randint(0, 2))) + rng.choice(['', rng.choice(frags)]) for _ in range(rng.randint(2, 6))})
    for _ in range(1200):                       # mutations of the published counterexamples
        a = 'abcdefpqxy'
        base = rng.choice([['abd', 'abe', 'fbd'], ['axby', 'byax', 'aybx', 'bxay'], ['abd', 'abpxqy', 'qypxbd', 'abpyqx', 'qxpybd'], ['aaa', 'aab']])
        out = set(base)
        for _ in range(rng.randint(0, 3)):
            w = list(rng.choice(base)); i = rng.randrange(len(w)); op = rng.choice('smd')
            if op == 's': w[i] = rng.choice(a)
            elif op == 'm' and len(w) > 2: del w[i]
            else: w.insert(i, rng.choice(a))
            out.add(''.join(w))
        yield 'mutated', sorted(out)
    for _ in range(400):                        # graph words with doubled ends
        n = rng.randint(3, 5); edges = {tuple(sorted(rng.sample(range(n), 2))) for _ in range(rng.randint(2, 5))}
        words = ['ABCDE'[u] + 'abcdefg'[i] + 'ABCDE'[v] for i, (u, v) in enumerate(sorted(edges))]
        yield 'graph', sorted({w + t for w in words for t in '12'})

stats, bugs, seen, t0 = collections.defaultdict(collections.Counter), [], set(), time.time()
for family, programs in corpora():
    if len(programs) < 2 or any(len(p) < 2 for p in programs) or tuple(programs) in seen: continue
    seen.add(tuple(programs))
    for k, rule in ((2, 'W2'), (1, 'U')):
        tokens = ev.eligible(programs, rule)
        opt = ev.minimum(programs, tokens)[0]
        if opt is None: continue
        try:
            c = dg.nullspace_kernel_certificate(programs, k)
        except Exception as e:
            bugs.append({'kind': 'crash', 'rule': rule, 'programs': programs, 'error': f'{type(e).__name__}: {e}'}); continue
        s = stats[(family, rule)]; s['corpora'] += 1; s[c['status']] += 1
        rank, status = c['rank'], c['status']
        s['minimum==rank'] += opt == rank
        if rank > opt:
            bugs.append({'kind': 'rank above minimum', 'rule': rule, 'programs': programs, 'rank': rank, 'minimum': opt})
        if status == 'RANK_ATTAINED':
            d = (c.get('attainingConstruction') or {}).get('dictionary')
            ok = d is not None and len(d) == rank and set(d) <= set(tokens) and ev.minimum(programs, sorted(set(d)))[0] is not None
            if opt != rank or not ok:
                bugs.append({'kind': 'false RANK_ATTAINED', 'rule': rule, 'programs': programs, 'rank': rank, 'minimum': opt, 'dictionary': d})
        elif status == 'RANK_UNATTAINABLE':
            if opt <= rank:
                bugs.append({'kind': 'UNSOUND +1 lift', 'rule': rule, 'programs': programs, 'rank': rank, 'minimum': opt, 'cert': {x: c[x] for x in ('nullity', 'sFree', 'kFree', 'deltaDetStar')}})
        elif status == 'SATURATED':
            if opt != rank: s['saturated-rank-but-minimum-differs'] += 1      # only a bug if rank > opt, caught above
        elif status == 'UNRESOLVED':
            s['unresolved deltaDetStar=%d' % c['deltaDetStar']] += 1
            if c['deltaDetStar'] == 0:
                bugs.append({'kind': 'exact class left UNRESOLVED', 'rule': rule, 'programs': programs, 'rank': rank, 'minimum': opt, 'cert': {x: c[x] for x in ('nullity', 'sFree', 'kFree', 'deltaDetStar')}})
print('seed', seed, 'seconds', round(time.time() - t0, 1))
for key in sorted(stats): print(key, dict(stats[key]))
kinds = collections.Counter(b['kind'] for b in bugs); print('findings', dict(kinds))
shown = set()
for b in bugs:
    if b['kind'] not in shown or len(shown) > 8:
        if sum(1 for x in shown if x == b['kind']) < 1: print(json.dumps(b)[:600])
        shown.add(b['kind'])
if bugs:                                     # a findings file is written only when there is something in it
    json.dump(bugs, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f'audit-kernel-findings-{seed}.json'), 'w'), indent=1)
sys.exit(1 if bugs else 0)
