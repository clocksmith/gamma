"""Boundary references against the cohorts' own references, and lane plumbing; never loads candidates."""
from __future__ import annotations
import importlib.util
import itertools
import random
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import boundary_cases as B  # noqa: E402
import protocol as P  # noqa: E402

L, M = B.L_ORACLES, B.M_ORACLES


class ReferenceAgreement(unittest.TestCase):
    def test_3855_doubling_matches_tuple_enumeration(self):
        for l in range(10):
            for r in range(l, 10):
                for k in range(1, 9):
                    if (r-l+1)**k <= 100000:
                        self.assertEqual(B.digit_tuple_total(l, r, k), L.reference(3855, [l, r, k]), (l, r, k))

    def test_3859_left_sweep_matches_interval_counters(self):
        rng = random.Random(1)
        for _ in range(1500):
            n = rng.randint(1, 45); top = rng.randint(1, 8)
            nums = [rng.randint(1, top) for _ in range(n)]; k = rng.randint(1, n); m = rng.randint(1, min(n, 5))
            self.assertEqual(B.count_k_distinct_m(nums, k, m), L.reference(3859, [nums, k, m]), (nums, k, m))
        self.assertEqual(B.count_k_distinct_m([1, 1, 2, 2, 3, 3], 2, 2), 2)

    def test_3862_scan_matches_literal_suffix_products(self):
        rng = random.Random(2)
        for values in itertools.product([1, 2, 3, 4], repeat=6):
            self.assertEqual(B.balanced_scan(list(values)), L.reference(3862, [list(values)]))
        for _ in range(3000):
            nums = [rng.choice((1, 1, 2, 3, 6, 10**9, rng.randint(1, 10**9))) for _ in range(rng.randint(1, 100))]
            self.assertEqual(B.balanced_scan(nums), L.reference(3862, [nums]))
        # Planted large balance and an int32-wrap decoy, checked literally.
        for nums in ([10**9]*60+[7, 60, 10**9], [10**9]*4+[294967302, 5, 2, 3]):
            self.assertEqual(B.balanced_scan(nums), L.reference(3862, [nums]))

    def test_3869_inclusion_exclusion_matches_enumeration(self):
        rng = random.Random(3)
        for _ in range(250):
            l = rng.choice((1, rng.randint(1, 10**6), rng.randint(1, 10**15-10000))); r = l+rng.randint(0, 10000)
            self.assertEqual(B.count_fancy(l, r), L.reference(3869, [l, r]), (l, r))
        # A wider brute force than the cohort budget, including every 6-digit monotone number.
        good = L.good
        running = 0
        for v in range(1, 300001):
            running += good(v) or good(sum(map(int, str(v))))
            if v % 25000 == 0 or v in (98765, 123456, 210000):
                self.assertEqual(B.fancy_to(v), running, v)
        self.assertEqual(len(B.MONOTONE), len(set(B.MONOTONE)))
        self.assertTrue(all(B._monotone(x) for x in B.MONOTONE))

    def test_3872_window_feasibility_matches_interpolation(self):
        rng = random.Random(4)
        for _ in range(3000):
            n = rng.randint(4, 12); a = [rng.randint(1, rng.choice((3, 6, 20))) for _ in range(n)]
            if rng.random() < .4:
                d = rng.randint(-3, 3); s = rng.randint(40, 60); a = [s+d*i for i in range(n)]
                for _ in range(rng.randint(1, 2)):
                    a[rng.randrange(n)] = rng.randint(1, 100)
            self.assertEqual(B.longest_one_change(a), M.expected(3872, [a]), a)

    def test_3873_bipartite_components_match_activation_search(self):
        rng = random.Random(5)
        for _ in range(2000):
            g = rng.choice((3, 4, 6, 10)); n = rng.randint(1, 12)
            points = rng.sample([(x, y) for x in range(g) for y in range(g)], min(n, g*g))
            self.assertEqual(B.activation_by_components(points), M.expected(3873, [[list(p) for p in points]]))
        for _ in range(200):
            sizes = [rng.randint(1, 5) for _ in range(rng.randint(1, 3))]
            if sum(sizes) <= 12:
                args, expected = B._components_case(rng, sizes)
                self.assertEqual(M.expected(3873, args), expected)

    def test_3876_closed_form_matches_parity_options(self):
        rng = random.Random(6)
        for _ in range(4000):
            nums = rng.sample(range(1, rng.choice((10, 30, 300, 10**9))), rng.randint(1, 9))
            self.assertEqual(B.uniform_parity(nums), M.expected(3876, [nums]), nums)

    def test_3877_meet_in_middle_matches_subset_enumeration(self):
        rng = random.Random(7)
        for _ in range(1500):
            n = rng.randint(1, 16); top = rng.choice((3, 15, 1024, 10000))
            nums = [rng.randint(0, top) for _ in range(n)]; target = rng.randint(0, min(top, 10000))
            self.assertEqual(B.min_removals_xor(nums, target), M.expected(3877, [nums, target]), (nums, target))
        self.assertEqual(B.min_removals_xor([5]*40, 5), M.expected(3877, [[5]*40, 5]))

    def test_3878_submask_spans_match_literal_or(self):
        rng = random.Random(8)
        for _ in range(2000):
            nums = [rng.choice((0, 1, 2, 3, 4, 5, 7, 8, rng.randint(0, 10**9))) for _ in range(rng.randint(1, 40))]
            self.assertEqual(B.count_or_member(nums), M.expected(3878, [nums]), nums)

    def test_3881_exact_binomial_matches_direction_enumeration(self):
        for n in range(1, 17):
            for pos in range(n):
                for k in range(n):
                    self.assertEqual(B.visible_assignments(n, pos, k), M.expected(3881, [n, pos, k]))
        for n in (17, 1000, 100000):  # the cohort shortcuts at its budget edge
            for k in (0, 1, n-2, n-1):
                self.assertEqual(B.visible_assignments(n, n//2, k), M.expected(3881, [n, n//2, k]))

    def test_3885_segment_tree_matches_event_scan(self):
        rng = random.Random(9)
        for _ in range(1500):
            args = B._event_trace_case(rng, rng.randint(1, 12), rng.randint(1, 30), (1, rng.choice((2, 5, 10**9))),
                                       rng.random(), reuse_share=rng.random(), distinct_ids=rng.random() < .5)
            M.validate(3885, args)
            self.assertEqual(B.event_trace(args), M.expected(3885, args))
        for args, expected in M.PUBLIC_EXAMPLES[3885]:
            self.assertEqual(B.event_trace(args), expected)


class LanePlumbing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pop = P.population(); cls.data, cls.owners = P.cases_and_owners(cls.pop)

    def test_population_cases_and_plans(self):
        self.assertEqual(set(self.data), {pid for ids in P.IDS.values() for pid in ids})
        for pid, rows in self.data.items():
            self.assertEqual(len({repr(r['args']) for r in rows}), len(rows), pid)
            plan = P.batch_plan(pid, rows)
            self.assertEqual(plan['blocked_cases'], [], pid)
            self.assertEqual(plan['admitted_distinct_cases'], len(rows))
            self.assertGreater(sum(r.get('category') == 'boundary-independent-reference' for r in rows), 0)
            for entry in plan['batches']:
                self.assertLessEqual(entry['input_bytes'], P.MAX_INPUT_BYTES)
                self.assertLessEqual(max(entry['projected_output_bytes'].values()), P.LIMITS.max_output_bytes)

    def test_original_cases_are_all_kept(self):
        for pid in P.IDS['l']:
            original = B.L_CASES.build_cases(pid, include_maximum=True)
            self.assertEqual(self.data[pid][:len(original)], original)
        for pid in P.IDS['m']:
            original = M.build_cases(pid)
            rows = [{k: v for k, v in row.items() if k != '_native_problem_id'} for row in self.data[pid][:len(original)]]
            self.assertEqual(rows, original)

    def test_owner_comparison_accepts_expected_and_rejects_changes(self):
        for pid, rows in self.data.items():
            for language in P.LANGUAGES:
                for row in (rows[0], rows[-1]):
                    if pid == 3885:
                        record = P.native_owner().projected_record(pid, row['args'], row['expected'], language, 0)
                        self.assertIsNone(P.compare(pid, language, row, record, self.owners[pid]))
                        wrong = dict(record, result=record['result'][:-1]+[-2])
                        self.assertEqual(P.compare(pid, language, row, wrong, self.owners[pid]), 'wrong_answer')
                        continue
                    record = {'i': 0, 'result': row['expected'], 'result_type': P.return_type(pid, row, language),
                              'args_before': row['args'], 'args_after': row['args'], 'alias_edges': []}
                    self.assertIsNone(P.compare(pid, language, row, record, self.owners[pid]))
                    if type(row['expected']) is bool:
                        wrong = not row['expected']
                    else:
                        wrong = row['expected']+1
                    self.assertEqual(P.compare(pid, language, row, dict(record, result=wrong), self.owners[pid]), 'result_value')

    def test_owner_recheck_uses_independent_reference_beyond_cohort_budget(self):
        args = next(r['args'] for r in self.data[3878] if r.get('isolate'))
        with self.assertRaises(ValueError):
            M.expected(3878, args)
        self.assertTrue(B.matches(3878, args, B.count_or_member(args[0])))
        self.assertFalse(B.matches(3878, args, B.count_or_member(args[0])+1))

    def test_settings_match_the_lm_lane(self):
        spec = importlib.util.spec_from_file_location('lm_lane_protocol', HERE.parent/'continuation-lm-qualification-20261028-v1'/'protocol.py')
        base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
        for name in ('LIMITS', 'ARGV', 'NATIVE_ARGV', 'MAX_INPUT_BYTES', 'BATCH_POLICY', 'REVIEW_FLAGS', 'NATIVE_REVIEW_FLAGS',
                     'TRANSPORT', 'FUNCTION_TRANSPORT', 'DIRECTORIES'):
            if name == 'DIRECTORIES':
                self.assertEqual(getattr(P, name), getattr(base, name))
            else:
                self.assertEqual(getattr(P, name), getattr(base, name), name)
        for key, ids in P.IDS.items():
            self.assertTrue(set(ids) <= set(base.IDS[key]))

    def test_no_candidate_module_loaded(self):
        for module in list(sys.modules.values()):
            path = str(getattr(module, '__file__', '') or '')
            self.assertFalse('/continuation-l-20261028-v1/python/' in path or '/continuation-m-20261028-v1/python/' in path, path)
            self.assertFalse(path.endswith('.js') or path.endswith('.cjs'), path)


if __name__ == '__main__':
    unittest.main()
