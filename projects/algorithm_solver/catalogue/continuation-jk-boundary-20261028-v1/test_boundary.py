"""Boundary references against the cohorts' own references, and lane plumbing; never loads candidates."""
from __future__ import annotations
import random
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import boundary_cases as B  # noqa: E402
import protocol as P  # noqa: E402


class ReferenceAgreement(unittest.TestCase):
    def test_tree_closed_forms_match_cohort_reference(self):
        rng = random.Random(1)
        for n in range(4, 14):
            for _ in range(10):
                args, expected = B.path_case(n, rng, rng.sample(range(n), 3), True)
                self.assertEqual(B.J_ORACLES.reference(3820, args), expected)
                legs = [rng.randint(1, 4) for _ in range(rng.randint(2, 4))]
                spots = [(leg, depth) for leg, length in enumerate(legs) for depth in range(1, length+1)]
                if len(spots) >= 3:
                    args, expected = B.spider_case(legs, rng, rng.sample(spots, 3))
                    self.assertEqual(B.J_ORACLES.reference(3820, args), expected)

    def test_counting_unrank_matches_cohort_reference(self):
        for k in range(1, 8):
            for n in range(1, 10):
                self.assertEqual(B.nth_with_k_ones(n, k), B.J_ORACLES.reference(3821, [n, k]))
        self.assertEqual(B.nth_with_k_ones(B.comb(50, 25), 25), 2**50-2**25)

    def test_fenwick_lis_matches_cohort_reference(self):
        rng = random.Random(2)
        for _ in range(200):
            nums = [min(rng.randrange(2**30), 10**9) if rng.random() < .5 else rng.randrange(16) for _ in range(rng.randint(1, 9))]
            self.assertEqual(B.longest_and_lis(nums), B.J_ORACLES.reference(3825, [nums]))

    def test_window_counts_match_cohort_reference_and_closed_forms(self):
        rng = random.Random(3)
        for _ in range(200):
            nums = [rng.choice((1, 2, 4, 10**9)) for _ in range(rng.randint(1, 4))]; k = rng.choice((0, 1, 4, 10, 10**9, 3*10**9))
            self.assertEqual(B.count_windows_brute(nums, k), B.J_ORACLES.reference(3835, [nums, k]))
        for n in range(1, 25):
            for spike in range(n):
                nums = [1]*n; nums[spike] = 10**9
                for m in (1, 2, 5):
                    self.assertEqual(B.spike_count(n, spike, (10**9-1)*m), B.count_windows_brute(nums, (10**9-1)*m))
        for n in range(1, 20):
            for spike in range(n):
                nums = [1]*n; nums[spike] = 10**9
                for k in (0, 5, 10**9-2):
                    self.assertEqual(B.spike_count(n, spike, k), B.count_windows_brute(nums, k))
                    inverted = [10**9]*n; inverted[spike] = 1
                    self.assertEqual(B.spike_count(n, spike, k, base=10**9, peak=1), B.count_windows_brute(inverted, k))
        for n in range(2, 30, 2):
            for k in (0, 7, 10**9-2, (10**9-1)*2, (10**9-1)*5-1, (10**9-1)*n):
                self.assertEqual(B.alternating_count(n, k), B.count_windows_brute([1, 10**9]*(n//2), k))
        for _ in range(200):
            nums = [rng.choice((1, 2, 5, 10**9, rng.randrange(1, 10**9))) for _ in range(rng.randint(1, 40))]
            k = rng.choice((0, 1, 10**9, 5*10**9, rng.randrange(10**11)))
            self.assertEqual(B.count_windows_sparse(nums, k), B.count_windows_brute(nums, k))

    def test_net_count_combinatorics_match_cohort_enumeration(self):
        rng = random.Random(4)
        for _ in range(150):
            nums = [rng.randint(1, 6) for _ in range(rng.randint(1, 8))]; k = rng.choice((1, 2, 3, 4, 6, 7, 8, 12, 16, 30, 36))
            self.assertEqual(B.count_sequences(nums, k), B.K_ORACLES.expected(3850, [nums, k]))
        # Net +17 over nineteen 6s: 17 plus and 2 zeros (171 ways) or 18 plus and 1 minus (19 ways).
        self.assertEqual(B.count_sequences([6]*19, 6**17), 190)


class LanePlumbing(unittest.TestCase):
    def test_population_cases_and_plans(self):
        pop = P.population(); data, owners = P.cases_and_owners(pop)
        self.assertEqual(set(data), {pid for ids in P.IDS.values() for pid in ids})
        for pid, rows in data.items():
            self.assertEqual(len({repr(r['args']) for r in rows}), len(rows), pid)
            plan = P.batch_plan(pid, rows)
            self.assertEqual(plan['blocked_cases'], [], pid)
            self.assertEqual(plan['admitted_distinct_cases'], len(rows))
            self.assertGreater(sum(r.get('category') == 'boundary-independent-reference' for r in rows), 0)

    def test_comparison_is_exact_for_every_cohort(self):
        case = {'args': [[4]*19, 4**19], 'expected': 1}
        base = {'i': 0, 'result_type': 'int', 'args_before': case['args'], 'args_after': case['args'], 'alias_edges': []}
        self.assertIsNone(P.compare(3850, 'python', case, dict(base, result=1), None))
        self.assertEqual(P.compare(3850, 'python', case, dict(base, result=0), None), 'result_value')


if __name__ == '__main__':
    unittest.main()
