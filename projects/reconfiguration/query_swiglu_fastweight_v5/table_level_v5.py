"""Table-level comparison for v5 receipts: questions that share one support table are not independent,
so the unit here is the table. For each pair of arms it reports the per-table difference in the number
of correct answers and an exact two-sided sign-flip permutation p-value on those differences.

Usage: python -I table_level_v5.py RECEIPT_JSON [RECEIPT_JSON ...]   (receipts are grouped by model)
"""
import collections, itertools, json, random, sys

PAIRS = [('top2_ctx', 'base_ctx'), ('top2_ctx', 'knn_ctx'), ('shuf_ctx', 'base_ctx'), ('top2_ctx', 'shuf_ctx'), ('top2_bare', 'shuf_bare'), ('top2_ctx', 'cad_ctx'), ('knn_ctx', 'base_ctx'), ('cad_ctx', 'base_ctx'), ('top2_bare', 'base_ctx'), ('v5_ctx', 'base_ctx'), ('v5_bare', 'base_ctx')]

def sign_flip_p(diffs):
    d = [x for x in diffs if x != 0]
    if not d: return 1.0
    obs = abs(sum(d))
    if len(d) <= 20:
        hits = sum(1 for signs in itertools.product((1, -1), repeat=len(d)) if abs(sum(s * x for s, x in zip(signs, d))) >= obs)
        return hits / 2 ** len(d)
    rng = random.Random(0); n = 200000
    return sum(1 for _ in range(n) if abs(sum(x if rng.random() < 0.5 else -x for x in d)) >= obs) / n

by_model = collections.defaultdict(list)
for f in sys.argv[1:]:
    d = json.load(open(f))
    per = collections.defaultdict(lambda: collections.Counter())
    size = collections.Counter()
    for r in d['rows']:
        per[r['specialty_id']][r['arm']] += r['correct']
        if r['arm'] == 'base_ctx': size[r['specialty_id']] += 1
    for sid, c in per.items():
        by_model[d['model']].append({'table': f"{sid}", 'shots': d['shots_per_group'], 'n': size[sid], **c})

for model, tables in by_model.items():
    print(f"{model}: {len(tables)} tables, {sum(t['n'] for t in tables)} questions")
    for shots in sorted({t['shots'] for t in tables}) + ['all']:
        sub = [t for t in tables if shots == 'all' or t['shots'] == shots]
        for a, b in PAIRS:
            if not all(a in t and b in t for t in sub): continue
            diffs = [t[a] - t[b] for t in sub]
            up = sum(x > 0 for x in diffs); down = sum(x < 0 for x in diffs)
            print(f"  examples/group={shots!s:>3}  {a:9s} vs {b}: {sum(t[a] for t in sub):3d} vs {sum(t[b] for t in sub):3d}  tables better/worse/equal {up}/{down}/{len(sub)-up-down}  sign-flip p = {sign_flip_p(diffs):.3g}")
