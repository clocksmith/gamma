"""Synthetic checks for holdout-gate-v1: capped model optima (flat and lexicographic, continuous and binary arcs), the fixed
universe order, the gate split and gate rule, measure_safe, the evidence invariants and replacement binding, and the -O guard."""
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

    def test_lexicographic_matches_exhaustive(self):
        rng = random.Random(75)
        def min_c(text, vocab, n):
            s = set(vocab); L = len(text); INF = 10 ** 9; f = [[INF] * (n + 1) for _ in range(L + 1)]; f[0][0] = 0
            for i in range(L):
                for k in range(n):
                    if f[i][k] == INF: continue
                    for j in range(i + 1, L + 1):
                        if text[i:j] in s: f[j][k + 1] = min(f[j][k + 1], f[i][k] + (j - i == 1))
            return min(f[L][k] for k in range(n + 1))
        for _ in range(25):
            texts, fixed, pool, capacity, incumbent, caps = instance(rng); M = 1000
            best = min(M * sum(cc.values()) + sum(min_c(texts[p], fixed + list(sub), cc[p]) for p in texts)
                       for r in range(capacity + 1) for sub in itertools.combinations(pool, r)
                       for cc in [costs(texts, fixed + list(sub))] if all(cc[p] <= caps[p] for p in texts))
            chosen, rec = capped.solve(capped.build(texts, fixed, pool, capacity, incumbent, caps, None, M), pool, True, 30.)
            self.assertTrue(rec['optimal']); self.assertEqual(round(rec['objective']), best)

    def test_split_and_gate_rule(self):
        ids = list(range(1000, 1300))
        search, gate = run.split(ids, 60, 'holdout-gate-v1')
        self.assertEqual(len(gate), 60); self.assertEqual(sorted(search + gate), ids); self.assertFalse(set(search) & set(gate))
        self.assertEqual(run.split(list(reversed(ids)), 60, 'holdout-gate-v1'), (search, gate))  # order-independent, fixed
        self.assertNotEqual(run.split(ids, 60, 'other')[1], gate)
        self.assertTrue(run.gate_ok((100, 50), (100, 50))); self.assertTrue(run.gate_ok((99, 60), (100, 50)))
        self.assertTrue(run.gate_ok((100, 49), (100, 50)))
        self.assertFalse(run.gate_ok((101, 0), (100, 50))); self.assertFalse(run.gate_ok((100, 51), (100, 50)))

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
        ok = {'search_programs_worse_than_start': 0, 'start_gate': [100, 50], 'final_gate': [100, 50]}
        self.assertIsNone(evidence.invariant_violations(ok, True))
        self.assertEqual(evidence.invariant_violations({**ok, 'final_gate': [100, 51]}, True), {'gate_rose': True})
        self.assertIsNone(evidence.invariant_violations({**ok, 'final_gate': [101, 0]}, False))  # free arms: no gate invariant
        self.assertIn('search_programs_worse_than_start', evidence.invariant_violations({**ok, 'search_programs_worse_than_start': 1}, False))
        none = types.SimpleNamespace(record_time_best=None, record_time_arm=None, record_time_sha256=None)
        r = evidence.replacement(none, ['gate24'], {}, {}, [], lambda k: k)
        self.assertEqual((r['resolved'], r['replacement_allowed']), (False, False))  # no binding never defaults to a pass
        bad = types.SimpleNamespace(record_time_best='/nonexistent.json', record_time_arm='flat', record_time_sha256='0' * 64)
        self.assertFalse(evidence.replacement(bad, ['gate24'], {}, {}, [], lambda k: k)['resolved'])

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
