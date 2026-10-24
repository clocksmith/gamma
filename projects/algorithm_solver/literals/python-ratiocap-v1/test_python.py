"""Synthetic checks: capped model optimum (flat, lexicographic, and lexicographic with the aggregate ratio row), canonical order, -O guard."""
import itertools, os, random, subprocess, sys, unittest
from pathlib import Path
HERE = Path(__file__).resolve().parent; LIT = HERE.parent
sys.path[:0] = [str(HERE)] + [str(LIT / d) for d in ('breadth-lns-v1', 'lagrange-select-v2', 'cost-decomposition-v1', '.', 'pass2/working')]
import capped, run
analyze = capped.analyze
costs = lambda texts, v: {p: len(analyze.shortest_encode(t, v)) for p, t in texts.items()}


class PythonTests(unittest.TestCase):
    def test_capped_matches_exhaustive(self):
        rng = random.Random(65)
        for _ in range(30):
            texts = {i: ''.join(rng.choice('abc') for _ in range(rng.randint(4, 12))) for i in range(rng.randint(2, 4))}
            subs = sorted({t[i:j] for t in texts.values() for i in range(len(t)) for j in range(i + 2, min(len(t), i + 4) + 1)})
            fixed = list('abc'); pool = rng.sample(subs, min(len(subs), 7)); capacity = rng.randint(1, 3)
            incumbent = fixed + pool[:min(capacity, 2)]; caps = costs(texts, incumbent)
            best = min(sum(cc.values()) for r in range(capacity + 1) for sub in itertools.combinations(pool, r)
                       for cc in [costs(texts, fixed + list(sub))] if all(cc[p] <= caps[p] for p in texts))
            chosen, rec = capped.solve(capped.build(texts, fixed, pool, capacity, incumbent, caps), pool, True, 30.)
            got = costs(texts, fixed + chosen)
            self.assertTrue(rec['optimal'] and all(got[p] <= caps[p] for p in texts)); self.assertEqual(sum(got.values()), best)

    def test_lexicographic_matches_exhaustive(self):
        rng = random.Random(67)
        def min_c(text, vocab, n):
            s = set(vocab); L = len(text); INF = 10 ** 9; f = [[INF] * (n + 1) for _ in range(L + 1)]; f[0][0] = 0
            for i in range(L):
                for k in range(n):
                    if f[i][k] == INF: continue
                    for j in range(i + 1, L + 1):
                        if text[i:j] in s: f[j][k + 1] = min(f[j][k + 1], f[i][k] + (j - i == 1))
            return min(f[L][k] for k in range(n + 1))
        for _ in range(25):
            texts = {i: ''.join(rng.choice('abc') for _ in range(rng.randint(4, 12))) for i in range(rng.randint(2, 4))}
            subs = sorted({t[i:j] for t in texts.values() for i in range(len(t)) for j in range(i + 2, min(len(t), i + 4) + 1)})
            fixed = list('abc'); pool = rng.sample(subs, min(len(subs), 7)); capacity = rng.randint(1, 3)
            incumbent = fixed + pool[:min(capacity, 2)]; caps = costs(texts, incumbent); M = 1000
            best = min(M * sum(cc.values()) + sum(min_c(texts[p], fixed + list(sub), cc[p]) for p in texts)
                       for r in range(capacity + 1) for sub in itertools.combinations(pool, r)
                       for cc in [costs(texts, fixed + list(sub))] if all(cc[p] <= caps[p] for p in texts))
            chosen, rec = capped.solve(capped.build(texts, fixed, pool, capacity, incumbent, caps, None, M), pool, True, 30.)
            self.assertTrue(rec['optimal']); self.assertEqual(round(rec['objective']), best)

    def test_ratio_row_matches_exhaustive(self):
        rng = random.Random(69)
        def segs(text, vocab, cap):  # every segmentation with at most cap pieces, as (N, C)
            out = set(); s = set(vocab)
            def go(i, n, c):
                if n > cap: return
                if i == len(text): out.add((n, c)); return
                for j in range(i + 1, len(text) + 1):
                    if text[i:j] in s: go(j, n + 1, c + (j - i == 1))
            go(0, 0, 0); return out
        checked = 0
        for _ in range(40):
            texts = {i: ''.join(rng.choice('ab') for _ in range(rng.randint(3, 7))) for i in range(rng.randint(2, 3))}
            subs = sorted({t[i:j] for t in texts.values() for i in range(len(t)) for j in range(i + 2, min(len(t), i + 3) + 1)})
            fixed = list('ab'); pool = rng.sample(subs, min(len(subs), 5)); capacity = rng.randint(1, 2)
            incumbent = fixed + pool[:min(capacity, 1)]; caps = costs(texts, incumbent); M = 1000
            nr = sum(caps.values()); cr = sum(sum(len(incumbent[i]) == 1 for i in analyze.shortest_encode(t, incumbent)) for t in texts.values())
            best = None
            for r in range(capacity + 1):
                for sub in itertools.combinations(pool, r):
                    per = [segs(texts[p], fixed + list(sub), caps[p]) for p in sorted(texts)]
                    if any(not s for s in per): continue
                    for combo in itertools.product(*per):
                        n = sum(x[0] for x in combo); c = sum(x[1] for x in combo)
                        if nr * c <= cr * n:
                            v = M * n + c; best = v if best is None or v < best else best
            m = capped.build(texts, fixed, pool, capacity, incumbent, caps, None, M, ratio=(nr, cr))
            chosen, rec = capped.solve(m, pool, True, 30.)
            self.assertTrue(rec['optimal']); self.assertEqual(round(rec['objective']), best); checked += 1
        self.assertGreater(checked, 30)

    def test_canonical_order_is_set_determined(self):
        cm = run.common()
        a = cm.ordered(['zz', 'b', 'abc', 'a', 'ab']); b = cm.ordered(['ab', 'a', 'zz', 'abc', 'b'])
        self.assertEqual(a, b)
        self.assertEqual(a[:2], [s for s in cm.ALPHABET if s in {'a', 'b'}])  # characters first, in alphabet order
        self.assertEqual(a[2:], ['ab', 'abc', 'zz'])                      # then learned entries, sorted

    def test_optimized_python_is_refused(self):
        code = "import sys; sys.path.insert(0, '.'); import run; run.contract()"
        for flags, env in ((['-O'], {}), ([], {'PYTHONOPTIMIZE': '1'})):
            r = subprocess.run([sys.executable, *flags, '-B', '-c', code], cwd=HERE, capture_output=True, text=True, env={**os.environ, **env})
            self.assertNotEqual(r.returncode, 0); self.assertIn('assertions must stay enabled', r.stderr)


if __name__ == '__main__':
    unittest.main()
