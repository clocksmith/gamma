"""Synthetic checks: capped model optimum (flat, lexicographic, and lexicographic with the aggregate ratio row), related removal, canonical order, -O guard."""
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
            chosen, rec = capped.solve(m, pool, True, 30., integral_arcs=True)
            self.assertTrue(rec['optimal']); self.assertEqual(round(rec['objective']), best); checked += 1
        self.assertGreater(checked, 30)

    def test_ratio_row_fractional_mixture_and_shorter_canonical(self):
        # codex's constructed case (LOG 04:53Z): one source, seed path a|bc|de|fg|hi (N 5, C 1, ratio 1/5)
        texts = {1: 'abcdefghi'}; fixed = list('abcdefghi') + ['bc', 'de', 'fg', 'hi']
        cand = ['bcde', 'fghi', 'ab', 'cd', 'ef', 'ghi']; M = 1000; caps = {1: 5}
        self.assertEqual(costs(texts, fixed), {1: 5})
        m = capped.build(texts, fixed, cand, len(cand), fixed, caps, None, M, ratio=(5, 1))
        _, cont = capped.solve(m, cand, True, 30., integral_arcs=False)   # item 26's continuous arcs
        chosen, integ = capped.solve(m, cand, True, 30., integral_arcs=True)
        self.assertTrue(integ['optimal']); self.assertEqual(round(integ['objective']), 4 * M)      # ab|cd|ef|ghi: N 4, C 0
        self.assertLess(cont['objective'], 4 * M - 1)                                              # fractional mixture is cheaper
        # canonical decode of the chosen dictionary may be shorter than the solver path and break the ratio: reject, never abort
        trial = fixed + chosen; seq = analyze.shortest_encode(texts[1], trial)
        n_c, c_c = len(seq), sum(len(trial[i]) == 1 for i in seq)
        ok = run.trial_check(n_c, c_c, round(integ['objective']) // M, True, (5, 1), 0.25)
        if 'bcde' in chosen and 'fghi' in chosen:
            self.assertEqual((n_c, c_c), (3, 1)); self.assertFalse(ok)
        self.assertFalse(run.trial_check(3, 1, 4, True, (5, 1), 0.25))   # shorter canonical, ratio fails -> rejected, no assertion
        self.assertTrue(run.trial_check(4, 0, 4, True, (5, 1), 0.25))
        with self.assertRaises(AssertionError):
            run.trial_check(3, 1, 4, True, None, 0.25)                    # without a ratio row the optimal equality must hold
        with self.assertRaises(AssertionError):
            run.trial_check(5, 1, 4, False, (5, 1), 0.25)                 # canonical N can never exceed the path

    def test_adjacency_counts_consecutive_learned_selections(self):
        vocab = list('abcd') + ['ab', 'cd', 'abcd']
        w = run.adjacency({1: 'abcdab', 2: 'cdab'}, ['a', 'b', 'c', 'd', 'ab', 'cd'], analyze, ['ab', 'cd'])
        self.assertEqual(w, {'ab': {'cd': 3}, 'cd': {'ab': 3}})        # ab|cd|ab and cd|ab: three consecutive learned pairs
        self.assertEqual(run.adjacency({1: 'abcd'}, vocab, analyze, ['ab', 'cd', 'abcd']), {})  # one selection: no pairs

    def test_related_removal(self):
        learned = ['e%d' % i for i in range(10)]
        w = {'e0': {'e1': 5}, 'e1': {'e0': 5, 'e2': 1}, 'e2': {'e1': 1}}
        for seed in range(20):
            r1 = run.related_removal(random.Random(seed), learned, 4, w); r2 = run.related_removal(random.Random(seed), learned, 4, w)
            self.assertEqual(r1, r2); self.assertEqual(len(set(r1)), 4); self.assertTrue(set(r1) <= set(learned))
            if r1[0] == 'e0': self.assertEqual(r1[1:3], ['e1', 'e2'])     # follows adjacency greedily from the seed
            if r1[0] in ('e1', 'e2'): self.assertIn('e1' if r1[0] == 'e2' else 'e0', r1[1:2])
        self.assertEqual(sorted(run.related_removal(random.Random(1), learned[:3], 9, w)), learned[:3])  # k capped at |learned|
        isolated = run.related_removal(random.Random(3), learned, 3, {})  # no adjacency: random distinct entries
        self.assertEqual(len(set(isolated)), 3)

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
