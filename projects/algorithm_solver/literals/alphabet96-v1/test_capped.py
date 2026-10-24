"""Synthetic checks for alphabet96-v1 (inherited from jsratiocap-v1, plus the uncapped exact drop): capped model optima (flat, lexicographic, lexicographic with the aggregate ratio row and
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

    def test_uncapped_lex_drop_matches_exhaustive(self):
        # the drop step: all characters fixed, candidates = the incumbent's learned entries, capacity = |learned| - d, no caps
        rng = random.Random(77)
        for _ in range(25):
            texts, fixed, pool, capacity, incumbent, caps = instance(rng, pool_size=6)
            learned = pool[:]; d = rng.randint(1, 2); cap = len(learned) - d; M = 10 ** 4
            def lexcost(sub):
                v = fixed + list(sub); n = 0; cc = 0
                for t in texts.values():
                    seq = analyze.shortest_encode(t, v); n += len(seq)
                return n
            best_n = min(lexcost(sub) for sub in itertools.combinations(learned, cap))
            warm = fixed + learned[:cap]
            chosen, rec = capped.solve(capped.build(texts, fixed, learned, cap, warm, None, None, M), learned, True, 30.)
            self.assertTrue(rec['optimal']); self.assertLessEqual(len(chosen), cap)
            self.assertEqual(round(rec['objective']) // M, best_n)
            self.assertEqual(sum(costs(texts, fixed + chosen).values()), best_n)

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

    def test_replacement_binding_refusal(self):
        none = types.SimpleNamespace(record_time_best=None, record_time_arm=None, record_time_sha256=None)
        r = evidence.replacement(none, ['repair'], {}, {}, [], lambda k: k)
        self.assertEqual((r['resolved'], r['replacement_allowed']), (False, False))
        bad = types.SimpleNamespace(record_time_best='/nonexistent.json', record_time_arm='flat', record_time_sha256='0' * 64)
        self.assertFalse(evidence.replacement(bad, ['repair'], {}, {}, [], lambda k: k)['resolved'])

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
