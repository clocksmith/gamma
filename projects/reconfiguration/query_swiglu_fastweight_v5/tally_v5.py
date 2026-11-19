"""Counts for one v5 receipt. Usage: python -I tally_v5.py RECEIPT_JSON [--layers]"""
import collections, json, math, statistics, sys

d = json.load(open(sys.argv[1]))
rows = d['rows']
print(f"{d['model']}  split={d['split']} seed={d['seed']}  tables={d['specialties']} shots/group={d['shots_per_group']} tasks={d['task_count']}")
arms = ['base_bare', 'base_ctx', 'top2_bare', 'top2_ctx', 'knn_ctx', 'cad_ctx', 'kv_ctx', 'shuf_bare', 'shuf_ctx', 'mfc_bare', 'probe_bare', 'nn_bare', 'ra_bare', 'ra_ctx', 'ra_kv', 'v5_bare', 'v5_ctx']
by = collections.defaultdict(dict)
for r in rows: by[r['arm']][r['task_id']] = r
n = len(by['base_bare'])
def cnt(arm, multi=None, key='correct'):
    return sum(r[key] for r in by[arm].values() if multi is None or r['multi_token'] == multi)
nm = sum(r['multi_token'] for r in by['base_bare'].values())
print(f"{'arm':11s} {'right':>8s} {'word':>8s} {'pair':>8s} {'valid code':>11s} {'ms/query':>9s} {'prompt tok':>10s}")
for a in arms:
    if a not in by: continue
    ms = statistics.mean(r['total_ms'] for r in by[a].values()); pt = statistics.mean(r['prompt_tokens'] for r in by[a].values())
    print(f"{a:11s} {cnt(a):3d}/{n:<4d} {cnt(a, False):3d}/{n-nm:<4d} {cnt(a, True):3d}/{nm:<4d} {cnt(a, key='valid_code'):6d}/{n:<4d} {ms:9.0f} {pt:10.0f}")
def mcn(a, b):
    w = sum(1 for t in by[a] if by[a][t]['correct'] and not by[b][t]['correct']); l = sum(1 for t in by[a] if by[b][t]['correct'] and not by[a][t]['correct'])
    m = w + l; k = min(w, l); p = 1.0 if m == 0 else min(1.0, 2 * sum(math.comb(m, j) for j in range(k + 1)) / 2 ** m)
    return f"{w} wins, {l} losses, p = {p:.3g}"
def tail(k, m, p): return sum(math.comb(m, j) * p**j * (1 - p)**(m - j) for j in range(k, m + 1))
for a, b in [('top2_ctx', 'base_ctx'), ('top2_ctx', 'knn_ctx'), ('top2_ctx', 'cad_ctx'), ('top2_bare', 'base_ctx'), ('ra_bare', 'kv_ctx'), ('ra_bare', 'base_ctx'), ('ra_bare', 'top2_bare'), ('ra_bare', 'probe_bare'), ('ra_kv', 'kv_ctx'), ('top2_bare', 'probe_bare'), ('top2_bare', 'nn_bare'), ('probe_bare', 'base_ctx'), ('top2_bare', 'mfc_bare'), ('kv_ctx', 'base_ctx'), ('v5_ctx', 'base_ctx'), ('v5_bare', 'base_ctx')]:
    if a in by and b in by: print(f"{a:10s} vs {b:10s}:", mcn(a, b))
print(f"top2_bare vs guessing a valid code (1 in 4): {cnt('top2_bare')}/{n}, one-sided p = {tail(cnt('top2_bare'), n, 0.25):.3g}")
print('tables:')
for s in d['specialties_compiled']:
    sid = s['specialty_id']; q = [t for t, r in by['base_bare'].items() if r['specialty_id'] == sid]
    got = {a: sum(by[a][t]['correct'] for t in q) for a in arms if a in by}
    sel = f"selected layer {s['layer']} ridge {s['ridge_ratio']} loo {s['loo_accuracy']:.2f} " if 'layer' in s else ''
    fc = f"fixed compile {s['fixed_compile_ms']/1000:.1f}s " if s.get('fixed_compile_ms') else ''
    print(f"  {sid:22s} {fc}{sel}| of {len(q)}: " + ' '.join(f"{a}={v}" for a, v in got.items()))
    if '--layers' in sys.argv and 'loo_by_layer' in s: print('     loo by layer:', ' '.join(f"{l}:{v:.2f}" for l, v in s['loo_by_layer'].items()))
