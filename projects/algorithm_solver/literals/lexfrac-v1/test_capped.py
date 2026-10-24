"""Synthetic checks for capped.py: exhaustive optimum with and without caps and with tail weights, warm/cold agreement, incumbent validity, measure_safe, caps and the -O guard."""
import itertools, random, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import capped

analyze = capped.analyze


def costs(texts, vocab):
    return {p: len(analyze.shortest_encode(t, vocab)) for p, t in texts.items()}


def brute(texts, fixed, cand, capacity, caps):
    best = None
    for r in range(capacity + 1):
        for sub in itertools.combinations(cand, r):
            c = costs(texts, list(fixed) + list(sub))
            if all(c[p] <= caps[p] for p in texts):
                v = sum(c.values()); best = v if best is None or v < best else best
    return best


def min_c(text, vocab, n):
    # fewest single-character pieces among segmentations of text into exactly n pieces from vocab
    s = set(vocab); L = len(text); INF = 10 ** 9; f = [[INF] * (n + 1) for _ in range(L + 1)]; f[0][0] = 0
    for i in range(L):
        for k in range(n):
            if f[i][k] == INF: continue
            for j in range(i + 1, L + 1):
                if text[i:j] in s: f[j][k + 1] = min(f[j][k + 1], f[i][k] + (j - i == 1))
    return min(f[L][k] for k in range(n + 1))


class CappedTests(unittest.TestCase):
    def test_exhaustive_optimum_warm_and_cold(self):
        rng = random.Random(37)
        for trial in range(40):
            texts = {i: ''.join(rng.choice('abc') for _ in range(rng.randint(4, 12))) for i in range(rng.randint(2, 4))}
            subs = sorted({t[i:j] for t in texts.values() for i in range(len(t)) for j in range(i + 2, min(len(t), i + 4) + 1)})
            fixed = list('abc'); pool = rng.sample(subs, min(len(subs), 7)); capacity = rng.randint(1, 3)
            incumbent = fixed + pool[:min(capacity, 2)]; cand = [s for s in pool]  # incumbent's learned entries stay candidates
            caps = costs(texts, incumbent)
            want = brute(texts, fixed, cand, capacity, caps)
            m = capped.build(texts, fixed, cand, capacity, incumbent, caps)
            self.assertEqual(m['initial'], sum(caps.values()))
            for warm in (True, False):
                chosen, rec = capped.solve(m, cand, warm, 30.)
                self.assertTrue(rec['optimal'] and rec['feasible'], rec)
                got = costs(texts, fixed + chosen)
                self.assertTrue(all(got[p] <= caps[p] for p in texts))
                self.assertEqual(sum(got.values()), want)
                self.assertEqual(round(rec['objective']), want)

    def test_fixed_universe_order_preserves_canonical_ties(self):
        sys.path[:0] = [str(Path(__file__).resolve().parent.parent / d) for d in ('breadth-lns-v1', 'lagrange-select-v2', 'cost-decomposition-v1', '.', 'pass2/working')]
        import run
        # Regression: the same entry set in two orders gives different canonical C, because ID order breaks equal-N ties.
        text = 'abcd'
        v1 = ['a', 'b', 'c', 'd', 'abc', 'ab', 'cd']; v2 = ['a', 'b', 'c', 'd', 'ab', 'cd', 'abc']
        chars = lambda v: sum(len(v[i]) == 1 for i in analyze.shortest_encode(text, v))
        self.assertNotEqual(chars(v1), chars(v2))  # the hazard the fixed order removes
        universe = ['a', 'b', 'c', 'd', 'abc', 'zz'] + sorted(['ab', 'cd', 'qq'])  # seed order, then sorted non-seed entries
        uidx = {s: i for i, s in enumerate(universe)}
        # A freed-and-reselected entry, or a different construction order, still serializes identically.
        self.assertEqual(run.ordered(uidx, v1), run.ordered(uidx, v2))
        self.assertEqual(run.ordered(uidx, ['cd', 'a', 'abc', 'b', 'ab', 'd', 'c']), ['a', 'b', 'c', 'd', 'abc', 'ab', 'cd'])
        # New (non-seed) entries follow the seed entries in sorted order.
        self.assertEqual(run.ordered(uidx, ['qq', 'ab', 'a']), ['a', 'ab', 'qq'])
        with self.assertRaises(AssertionError):
            run.ordered(uidx, ['a', 'outside'])

    def test_lexicographic_n_then_c_matches_exhaustive(self):
        rng = random.Random(51)
        for trial in range(30):
            texts = {i: ''.join(rng.choice('abc') for _ in range(rng.randint(4, 12))) for i in range(rng.randint(2, 4))}
            subs = sorted({t[i:j] for t in texts.values() for i in range(len(t)) for j in range(i + 2, min(len(t), i + 4) + 1)})
            fixed = list('abc'); pool = rng.sample(subs, min(len(subs), 7)); capacity = rng.randint(1, 3)
            incumbent = fixed + pool[:min(capacity, 2)]; caps = costs(texts, incumbent); M = 1000
            best = None  # exhaustive lexicographic optimum of (total N, min total C over min-N paths) under the caps
            for r in range(capacity + 1):
                for sub in itertools.combinations(pool, r):
                    cc = costs(texts, fixed + list(sub))
                    if all(cc[p] <= caps[p] for p in texts):
                        v = M * sum(cc.values()) + sum(min_c(texts[p], fixed + list(sub), cc[p]) for p in texts)
                        best = v if best is None or v < best else best
            m = capped.build(texts, fixed, pool, capacity, incumbent, caps, None, M)
            chosen, rec = capped.solve(m, pool, True, 30.)
            self.assertTrue(rec['optimal'])
            self.assertEqual(round(rec['objective']), best)
            got = costs(texts, fixed + chosen)
            self.assertTrue(all(got[p] <= caps[p] for p in texts)); self.assertEqual(sum(got.values()), best // M)

    def test_weighted_capped_matches_exhaustive(self):
        rng = random.Random(48)
        for trial in range(30):
            texts = {i: ''.join(rng.choice('abc') for _ in range(rng.randint(4, 12))) for i in range(rng.randint(2, 4))}
            subs = sorted({t[i:j] for t in texts.values() for i in range(len(t)) for j in range(i + 2, min(len(t), i + 4) + 1)})
            fixed = list('abc'); pool = rng.sample(subs, min(len(subs), 7)); capacity = rng.randint(1, 3)
            incumbent = fixed + pool[:min(capacity, 2)]; caps = costs(texts, incumbent)
            weights = {p: rng.choice((1, 10)) for p in texts}
            best = None
            for r in range(capacity + 1):
                for sub in itertools.combinations(pool, r):
                    cc = costs(texts, fixed + list(sub))
                    if all(cc[p] <= caps[p] for p in texts):
                        v = sum(weights[p] * cc[p] for p in texts); best = v if best is None or v < best else best
            m = capped.build(texts, fixed, pool, capacity, incumbent, caps, weights)
            self.assertEqual(m['initial'], sum(weights[p] * caps[p] for p in texts))
            chosen, rec = capped.solve(m, pool, True, 30.)
            got = costs(texts, fixed + chosen)
            self.assertTrue(rec['optimal'] and all(got[p] <= caps[p] for p in texts))
            self.assertEqual(sum(weights[p] * got[p] for p in texts), best)

    def test_uncapped_matches_exhaustive(self):
        rng = random.Random(43)
        for trial in range(30):
            texts = {i: ''.join(rng.choice('abc') for _ in range(rng.randint(4, 12))) for i in range(rng.randint(2, 4))}
            subs = sorted({t[i:j] for t in texts.values() for i in range(len(t)) for j in range(i + 2, min(len(t), i + 4) + 1)})
            fixed = list('abc'); pool = rng.sample(subs, min(len(subs), 7)); capacity = rng.randint(1, 3)
            incumbent = fixed + pool[:min(capacity, 2)]
            big = {p: 10 ** 6 for p in texts}
            want = brute(texts, fixed, pool, capacity, big)
            m = capped.build(texts, fixed, pool, capacity, incumbent, None)
            chosen, rec = capped.solve(m, pool, True, 30.)
            self.assertTrue(rec['optimal'])
            self.assertEqual(sum(costs(texts, fixed + chosen).values()), want)

    def test_measure_safe_retains_unencodable(self):
        sys.path[:0] = [str(Path(__file__).resolve().parent.parent / d) for d in ('breadth-lns-v1', 'lagrange-select-v2', 'cost-decomposition-v1', '.', 'pass2/working')]
        import run
        rows, illegal, db = run.measure_safe({1: 'abab', 2: 'abz'}, list('ab') + ['ab'], 8, set())
        self.assertTrue(rows['1']['encodable']); self.assertEqual(rows['1']['selections'], 2)
        self.assertEqual(rows['2'], {'encodable': False})

    def test_timeout_kill_after_bounds_a_term_ignoring_child(self):
        import subprocess, time
        code = 'import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)'
        t0 = time.monotonic()
        r = subprocess.run(['timeout', '--kill-after=2', '1', sys.executable, '-c', code])
        self.assertEqual(r.returncode, 137)  # SIGKILL after the grace period, not an unbounded wait
        self.assertLess(time.monotonic() - t0, 10)

    def test_optimized_python_is_refused(self):
        import subprocess
        here = Path(__file__).resolve().parent
        code = ("import sys; sys.path[:0]=['.','../breadth-lns-v1','../lagrange-select-v2','../cost-decomposition-v1','..','../pass2/working']; "
                "import run; run.contract()")
        for flags, env in ((['-O'], {}), ([], {'PYTHONOPTIMIZE': '1'})):
            r = subprocess.run([sys.executable, *flags, '-B', '-c', code], cwd=here, capture_output=True, text=True,
                               env={**__import__('os').environ, **env})
            self.assertNotEqual(r.returncode, 0)
            self.assertIn('assertions must stay enabled', r.stderr)

    def test_evidence_rejects_nonregression_violation_and_unresolved_comparator(self):
        sys.path[:0] = [str(Path(__file__).resolve().parent.parent / d) for d in ('breadth-lns-v1', 'lagrange-select-v2', 'cost-decomposition-v1', '.', 'pass2/working')]
        import evidence
        self.assertIsNone(evidence.invariant_violation({'fit_programs_worse_than_start': 0}))
        self.assertEqual(evidence.invariant_violation({'fit_programs_worse_than_start': 3}), {'fit_programs_worse_than_start': 3})
        r = evidence.record_time_comparison('/nonexistent.json', 'x', {}, {}, [], '0' * 64)
        self.assertFalse(r['resolved'])  # a missing comparator leaves replacement unresolved, never a default pass
        import types
        none = types.SimpleNamespace(record_time_best=None, record_time_arm=None, record_time_sha256=None)
        r = evidence.replacement(none, ['tail'], {}, {}, [], lambda k: k)
        self.assertEqual((r['resolved'], r['replacement_allowed']), (False, False))  # no binding: never defaults to item 43
        # every candidate is checked before ranking: the first-ranked failing the comparator must not hide a passing one
        orig = evidence.record_time_comparison
        evidence.record_time_comparison = lambda path, arm, s, rows, ids, h: {'resolved': True, 'passes': s['ok']}
        try:
            bound = types.SimpleNamespace(record_time_best='x', record_time_arm='y', record_time_sha256='z')
            out = {'arms': {'a': {'validation': {'ok': False}}, 'b': {'validation': {'ok': True}}}}
            r = evidence.replacement(bound, ['a', 'b'], out, {'a': {}, 'b': {}}, [], lambda k: k)
            self.assertEqual((r['selected'], r['eligible']), ('b', ['b']))
        finally:
            evidence.record_time_comparison = orig

    def test_incumbent_violating_cap_is_rejected(self):
        texts = {1: 'abab', 2: 'abc'}; fixed = list('abc'); cand = ['ab']
        caps = {1: 1, 2: 3}  # 'abab' needs 2 selections with 'ab'; a cap below the incumbent's cost must fail closed
        with self.assertRaises(AssertionError):
            capped.build(texts, fixed, cand, 1, fixed + ['ab'], caps)


if __name__ == '__main__':
    unittest.main()
