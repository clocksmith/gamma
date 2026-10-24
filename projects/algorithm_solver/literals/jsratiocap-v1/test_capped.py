"""Synthetic checks for jsratiocap-v1: capped model optima (flat, lexicographic, lexicographic with the aggregate ratio row and
binary arcs), the fractional-mixture and shorter-canonical regressions, the fixed universe order, measure_safe, the evidence
invariants and replacement binding, and the -O guard."""
import itertools, os, random, subprocess, sys, types, unittest
from pathlib import Path
HERE = Path(__file__).resolve().parent; LIT = HERE.parent
sys.path[:0] = [str(HERE)] + [str(LIT / d) for d in ('breadth-lns-v1', 'lagrange-select-v2', 'cost-decomposition-v1', '.', 'pass2/working')]
import capped, run, evidence
analyze = capped.analyze
costs = lambda texts, v: {p: len(analyze.shortest_encode(t, v)) for p, t in texts.items()}


def instance(rng, alphabet='abc', lo=4, hi=12, longest=4, pool_size=7, cap_hi=3):
    texts = {i: ''.join(rng.choice(alphabet) for _ in range(rng.randint(lo, hi))) for i in range(rng.randint(2, 4))}
    subs = sorted({t[i:j] for t in texts.values() for i in range(len(t)) for j in range(i + 2, min(len(t), i + longest) + 1)})
    fixed = list(alphabet); pool = rng.sample(subs, min(len(subs), pool_size)); capacity = rng.randint(1, cap_hi)
    incumbent = fixed + pool[:min(capacity, 2)]
    return texts, fixed, pool, capacity, incumbent, costs(texts, incumbent)


class JsRatioTests(unittest.TestCase):
    def test_capped_matches_exhaustive_both_arc_types(self):
        rng = random.Random(72)
        for _ in range(25):
            texts, fixed, pool, capacity, incumbent, caps = instance(rng)
            best = min(sum(cc.values()) for r in range(capacity + 1) for sub in itertools.combinations(pool, r)
                       for cc in [costs(texts, fixed + list(sub))] if all(cc[p] <= caps[p] for p in texts))
            for integral in (False, True):
                chosen, rec = capped.solve(capped.build(texts, fixed, pool, capacity, incumbent, caps), pool, True, 30., integral_arcs=integral)
                got = costs(texts, fixed + chosen)
                self.assertTrue(rec['optimal'] and all(got[p] <= caps[p] for p in texts)); self.assertEqual(sum(got.values()), best)

    def test_ratio_row_matches_exhaustive(self):
        rng = random.Random(721)
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
            texts, fixed, pool, capacity, incumbent, caps = instance(rng, 'ab', 3, 7, 3, 5, 2)
            M = 1000; nr = sum(caps.values())
            cr = sum(sum(len(incumbent[i]) == 1 for i in analyze.shortest_encode(t, incumbent)) for t in texts.values())
            best = None
            for r in range(capacity + 1):
                for sub in itertools.combinations(pool, r):
                    per = [segs(texts[p], fixed + list(sub), caps[p]) for p in sorted(texts)]
                    if any(not s for s in per): continue
                    for combo in itertools.product(*per):
                        n = sum(x[0] for x in combo); c = sum(x[1] for x in combo)
                        if nr * c <= cr * n:
                            v = M * n + c; best = v if best is None or v < best else best
            chosen, rec = capped.solve(capped.build(texts, fixed, pool, capacity, incumbent, caps, None, M, ratio=(nr, cr)), pool, True, 30., integral_arcs=True)
            self.assertTrue(rec['optimal']); self.assertEqual(round(rec['objective']), best); checked += 1
        self.assertGreater(checked, 30)

    def test_fractional_mixture_and_shorter_canonical(self):
        # python-ratiocap-v1 AMENDMENT-1's instance: seed path a|bc|de|fg|hi (N 5, C 1)
        texts = {1: 'abcdefghi'}; fixed = list('abcdefghi') + ['bc', 'de', 'fg', 'hi']
        cand = ['bcde', 'fghi', 'ab', 'cd', 'ef', 'ghi']; M = 1000; caps = {1: 5}
        m = capped.build(texts, fixed, cand, len(cand), fixed, caps, None, M, ratio=(5, 1))
        _, cont = capped.solve(m, cand, True, 30., integral_arcs=False)
        _, integ = capped.solve(m, cand, True, 30., integral_arcs=True)
        self.assertTrue(integ['optimal']); self.assertEqual(round(integ['objective']), 4 * M)
        self.assertLess(cont['objective'], 4 * M - 1)  # continuous arcs mix paths under the ratio row
        self.assertFalse(run.trial_check(3, 1, 4, True, (5, 1), 0.25))  # shorter canonical breaking the ratio: rejected, not aborted
        self.assertTrue(run.trial_check(4, 0, 4, True, (5, 1), 0.25))
        with self.assertRaises(AssertionError): run.trial_check(3, 1, 4, True, None, 0.25)   # no ratio row: optimal equality holds
        with self.assertRaises(AssertionError): run.trial_check(5, 1, 4, False, (5, 1), 0.25)  # canonical N never exceeds the path

    def test_fixed_universe_order(self):
        text = 'abcd'; v1 = ['a', 'b', 'c', 'd', 'abc', 'ab', 'cd']; v2 = ['a', 'b', 'c', 'd', 'ab', 'cd', 'abc']
        chars = lambda v: sum(len(v[i]) == 1 for i in analyze.shortest_encode(text, v))
        self.assertNotEqual(chars(v1), chars(v2))  # the hazard the fixed order removes
        uidx = {s: i for i, s in enumerate(['a', 'b', 'c', 'd', 'abc', 'zz'] + sorted(['ab', 'cd', 'qq']))}
        self.assertEqual(run.ordered(uidx, v1), run.ordered(uidx, v2))
        self.assertEqual(run.ordered(uidx, ['qq', 'ab', 'a']), ['a', 'ab', 'qq'])
        with self.assertRaises(AssertionError): run.ordered(uidx, ['a', 'outside'])

    def test_measure_safe_retains_unencodable(self):
        rows, _, _ = run.measure_safe({1: 'abab', 2: 'abz'}, list('ab') + ['ab'], 8, set())
        self.assertTrue(rows['1']['encodable']); self.assertEqual(rows['1']['selections'], 2); self.assertEqual(rows['2'], {'encodable': False})

    def test_evidence_invariants_and_binding(self):
        ok = {'fit_programs_worse_than_start': 0, 'final_fit': 100, 'final_characters': 50}
        self.assertIsNone(evidence.invariant_violations(ok, True, (100, 50)))
        self.assertEqual(evidence.invariant_violations({**ok, 'final_characters': 51}, True, (100, 50)), {'fit_fraction_rose': True})
        self.assertIsNone(evidence.invariant_violations({**ok, 'final_characters': 51}, False, (100, 50)))  # lex controls: no ratio invariant
        self.assertIn('fit_programs_worse_than_start', evidence.invariant_violations({**ok, 'fit_programs_worse_than_start': 1}, False, (100, 50)))
        none = types.SimpleNamespace(record_time_best=None, record_time_arm=None, record_time_sha256=None)
        r = evidence.replacement(none, ['k40ratio'], {}, {}, [], lambda k: k)
        self.assertEqual((r['resolved'], r['replacement_allowed']), (False, False))  # no binding never defaults to a pass
        bad = types.SimpleNamespace(record_time_best='/nonexistent.json', record_time_arm='flat', record_time_sha256='0' * 64)
        self.assertFalse(evidence.replacement(bad, ['k40ratio'], {}, {}, [], lambda k: k)['resolved'])

    def test_incumbent_violating_cap_is_rejected(self):
        with self.assertRaises(AssertionError):
            capped.build({1: 'abab', 2: 'abc'}, list('abc'), ['ab'], 1, list('abc') + ['ab'], {1: 1, 2: 3})

    def test_optimized_python_is_refused(self):
        code = ("import sys; sys.path[:0]=['.','../breadth-lns-v1','../lagrange-select-v2','../cost-decomposition-v1','..','../pass2/working']; "
                "import run; run.contract()")
        for flags, env in ((['-O'], {}), ([], {'PYTHONOPTIMIZE': '1'})):
            r = subprocess.run([sys.executable, *flags, '-B', '-c', code], cwd=HERE, capture_output=True, text=True, env={**os.environ, **env})
            self.assertNotEqual(r.returncode, 0); self.assertIn('assertions must stay enabled', r.stderr)


if __name__ == '__main__':
    unittest.main()
