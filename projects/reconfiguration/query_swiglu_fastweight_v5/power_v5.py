"""Table-level effect sizes in the v5 development receipts, and the power of a confirmation of a given size.

The unit is the support table. Each table contributes the difference in accuracy between two arms (correct
answers divided by the table's question count, so 8-question and 16-question tables weigh the same). Power is
estimated by resampling the observed per-table differences with replacement and applying a two-sided sign-flip
test at 0.05 that must also point the right way. It assumes the true effect equals the development effect,
which development data tends to overstate.

Usage: python -I power_v5.py RECEIPT_JSON [RECEIPT_JSON ...]
"""
import collections, json, random, statistics, sys

PAIRS = [('top2_ctx', 'base_ctx'), ('top2_ctx', 'knn_ctx'), ('knn_ctx', 'base_ctx'), ('top2_bare', 'base_ctx')]
TABLES = (48, 96, 192)

def sign_flip_p(diffs, rng, reps):
    observed = abs(sum(diffs))
    return sum(abs(sum(x if rng.random() < 0.5 else -x for x in diffs)) >= observed for _ in range(reps)) / reps

def power(diffs, tables, rng, sims=400):
    passed = 0
    for _ in range(sims):
        sample = [rng.choice(diffs) for _ in range(tables)]
        passed += sum(sample) > 0 and sign_flip_p(sample, rng, 600) < 0.05
    return passed / sims

rows = []
for path in sys.argv[1:]:
    receipt = json.load(open(path))
    correct = collections.defaultdict(collections.Counter); questions = collections.Counter()
    for row in receipt['rows']:
        correct[row['specialty_id']][row['arm']] += int(bool(row['correct']))
        questions[row['specialty_id']] += row['arm'] == 'base_ctx'
    rows += [{'n': questions[table], **arms} for table, arms in correct.items() if questions[table]]

rng = random.Random(7)
for a, b in PAIRS:
    diffs = [(t[a] - t[b]) / t['n'] for t in rows if a in t and b in t]
    if len(diffs) < 6: continue
    better, worse = sum(x > 0 for x in diffs), sum(x < 0 for x in diffs)
    print(f"{a} minus {b}: {len(diffs)} tables, mean {100 * statistics.mean(diffs):+.1f} points, SD {100 * statistics.pstdev(diffs):.1f}, "
          f"better/worse/equal {better}/{worse}/{len(diffs) - better - worse}, sign-flip p {sign_flip_p(diffs, rng, 20000):.3f}")
    if statistics.mean(diffs) > 0:
        print('   power at this effect: ' + ', '.join(f"{n} tables {100 * power(diffs, n, rng):.0f}%" for n in TABLES))
