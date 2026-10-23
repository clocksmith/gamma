"""Synthetic checks for capped.py: exhaustive optimum with and without caps, warm/cold agreement, incumbent validity, and measure_safe."""
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

    def test_incumbent_violating_cap_is_rejected(self):
        texts = {1: 'abab', 2: 'abc'}; fixed = list('abc'); cand = ['ab']
        caps = {1: 1, 2: 3}  # 'abab' needs 2 selections with 'ab'; a cap below the incumbent's cost must fail closed
        with self.assertRaises(AssertionError):
            capped.build(texts, fixed, cand, 1, fixed + ['ab'], caps)


if __name__ == '__main__':
    unittest.main()
