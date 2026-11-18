"""Counts for one v5 receipt. Usage: python -I tally_v5.py RECEIPT_JSON [--layers]"""
import collections, json, math, statistics, sys

d = json.load(open(sys.argv[1]))
rows = d['rows']
print(f"{d['model']}  split={d['split']} seed={d['seed']}  tables={d['specialties']} shots/group={d['shots_per_group']} tasks={d['task_count']}")
arms = ['base_bare', 'base_ctx', 'v5_bare', 'v5_ctx', 'top2_bare', 'top2_ctx']
by = collections.defaultdict(dict)
for r in rows: by[r['arm']][r['task_id']] = r
n = len(by['base_bare'])
def cnt(arm, multi=None, key='correct'):
    return sum(r[key] for r in by[arm].values() if multi is None or r['multi_token'] == multi)
nm = sum(r['multi_token'] for r in by['base_bare'].values())
print(f"{'arm':10s} {'right':>8s} {'word':>8s} {'pair':>8s} {'valid code':>11s} {'ms/query':>9s} {'prompt tok':>10s}")
for a in arms:
    if a not in by: continue
    ms = statistics.mean(r['total_ms'] for r in by[a].values()); pt = statistics.mean(r['prompt_tokens'] for r in by[a].values())
    print(f"{a:10s} {cnt(a):3d}/{n:<4d} {cnt(a, False):3d}/{n-nm:<4d} {cnt(a, True):3d}/{nm:<4d} {cnt(a, key='valid_code'):6d}/{n:<4d} {ms:9.0f} {pt:10.0f}")
def mcn(a, b):
    w = sum(1 for t in by[a] if by[a][t]['correct'] and not by[b][t]['correct']); l = sum(1 for t in by[a] if by[b][t]['correct'] and not by[a][t]['correct'])
    m = w + l; k = min(w, l); p = 1.0 if m == 0 else min(1.0, 2 * sum(math.comb(m, j) for j in range(k + 1)) / 2 ** m)
    return f"{w} wins, {l} losses, p = {p:.3g}"
def tail(k, m, p): return sum(math.comb(m, j) * p**j * (1 - p)**(m - j) for j in range(k, m + 1))
print('v5_bare  vs base_ctx :', mcn('v5_bare', 'base_ctx'))
print('v5_ctx   vs base_ctx :', mcn('v5_ctx', 'base_ctx'))
print('v5_bare  vs top2_bare:', mcn('v5_bare', 'top2_bare'))
print(f"v5_bare vs guessing a valid code (1 in 4): {cnt('v5_bare')}/{n}, one-sided p = {tail(cnt('v5_bare'), n, 0.25):.3g}")
print('tables:')
for s in d['specialties_compiled']:
    sid = s['specialty_id']; q = [t for t, r in by['base_bare'].items() if r['specialty_id'] == sid]
    got = {a: sum(by[a][t]['correct'] for t in q) for a in arms if a in by}
    print(f"  {sid:22s} layer {s['layer']:2d} ridge {s['ridge_ratio']:<6} loo {s['loo_accuracy']:.2f} write {s['write_scale']:.2f} hit {s['train_first_token_hit']:.2f} {'ABSTAIN ' if s['abstain'] else ''}| of {len(q)}: " + ' '.join(f"{a}={v}" for a, v in got.items()))
    if '--layers' in sys.argv: print('     loo by layer:', ' '.join(f"{l}:{v:.2f}" for l, v in s['loo_by_layer'].items()))
