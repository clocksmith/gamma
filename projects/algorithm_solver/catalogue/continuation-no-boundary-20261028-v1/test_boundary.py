"""Boundary references against the cohorts' own references, and lane plumbing; never loads candidates."""
from __future__ import annotations
from itertools import permutations, product
import random
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import boundary_cases as B  # noqa: E402
import protocol as P  # noqa: E402

REFERENCES = {3891: lambda a: B.min_increase(a[0]), 3896: lambda a: B.alternating_prime_ops(a[0]),
              3897: lambda a: B.concatenated_max(*a), 3901: lambda a: B.good_subsequence_queries(*a),
              3905: lambda a: B.flood_fill(*a), 3915: lambda a: B.max_alternating_sum(*a),
              3919: lambda a: B.move_costs(*a), 3926: lambda a: B.word_counts(*a),
              3932: lambda a: B.kth_roots(*a), 3934: lambda a: B.smallest_unique_sam(a[0]),
              3937: lambda a: B.residue_alternating(*a), 3942: lambda a: B.dihedral_sort(a[0])}


def side_comparison(nums):
    peak = nums.index(max(nums)); left = sum(nums[:peak]); right = sum(nums[peak+1:])
    return 0 if left > right else 1 if right > left else -1


REFERENCES[3909] = lambda a: side_comparison(a[0])


class ReferenceAgreement(unittest.TestCase):
    def agree(self, pid, args):
        self.assertEqual(REFERENCES[pid](args), B.cohort_reference(pid, args), (pid, args))

    def test_peak_sets_match_cohort_enumeration(self):
        for n in range(3, 7):
            for nums in product(range(1, 5), repeat=n):
                if n < 6 or sum(nums) % 7 == 0:
                    self.agree(3891, [list(nums)])
        rng = random.Random(1)
        for _ in range(300):
            self.agree(3891, [[rng.randint(1, 8) for _ in range(6)]])

    def test_miller_rabin_primes_match_trial_division_and_cohort(self):
        sieve = bytearray([1])*100200; sieve[0] = sieve[1] = 0
        for i in range(2, 317):
            if sieve[i]:
                sieve[i*i::i] = bytearray(len(sieve[i*i::i]))
        self.assertEqual(B.PRIMES, [i for i in range(100200) if sieve[i]])
        rng = random.Random(2)
        for _ in range(300):
            self.agree(3896, [[rng.randint(1, 1000) for _ in range(rng.randint(1, 100))]])

    def test_exchange_order_matches_cohort_permutations(self):
        rng = random.Random(3)
        for _ in range(400):
            n = rng.randint(1, 7)
            pairs = [(rng.randint(0, 6), rng.randint(0, 6)) for _ in range(n)]
            pairs = [(a, b) if a+b else (1, 0) for a, b in pairs]
            self.agree(3897, [[a for a, b in pairs], [b for a, b in pairs]])

    def test_block_gcd_witness_matches_cohort_subsequences(self):
        rng = random.Random(4)
        for _ in range(250):
            n = rng.randint(2, 12); p = rng.choice((1, 2, 3, 6, 5))
            pool = [p*v for v in (1, 2, 3, 5, 6, 10, 15, 7)]+[rng.randint(1, 60)]
            queries = [[rng.randrange(n), rng.choice(pool)] for _ in range(rng.randint(1, 40))]
            self.agree(3901, [[rng.choice(pool) for _ in range(n)], p, queries])
        self.agree(3901, [[30, 42, 70, 105], 1, [[0, 30], [3, 105], [3, 7]]])

    def test_separable_transform_matches_cohort_nearest_source(self):
        rng = random.Random(5)
        for _ in range(250):
            n = rng.randint(1, 12); m = rng.randint(1, 12)
            count = rng.randint(1, n*m)
            sources = [[c//m, c % m, rng.choice((1, 2, 3, 10**6))] for c in rng.sample(range(n*m), count)]
            self.agree(3905, [n, m, sources])

    def test_designed_side_sums_hold_and_match_cohort(self):
        for row in B.boundary_rows(3909):
            nums = row['args'][0]
            self.assertEqual(side_comparison(nums), row['expected'])
            if len(nums) < 5000:
                self.assertEqual(B.cohort_reference(3909, row['args']), row['expected'])

    def test_value_tree_matches_cohort_and_quadratic_dp(self):
        rng = random.Random(6)
        for _ in range(300):
            n = rng.randint(1, 13); nums = [rng.randint(1, 5) if rng.random() < .7 else rng.randint(1, 100000) for _ in range(n)]
            self.agree(3915, [nums, rng.randint(1, n)])
        for _ in range(40):
            n = rng.randint(50, 300); nums = [rng.randint(1, 30) for _ in range(n)]; k = rng.randint(1, 20)
            self.assertEqual(B.max_alternating_sum(nums, k), B.alternating_quadratic(nums, k))

    def test_dijkstra_matches_cohort_floyd(self):
        rng = random.Random(7)
        for _ in range(150):
            n = rng.randint(2, 30); step = rng.choice((3, 5))
            nums = sorted(rng.sample(range(-60, 61), n)) if rng.random() < .5 else [-10**9+step*i for i in range(n)]
            self.agree(3919, [nums, [[i, j] for i in range(n) for j in range(n)]])

    def test_split_tokenizer_matches_cohort_classifier(self):
        rng = random.Random(8)
        for _ in range(400):
            text = ''.join(rng.choice('ab -') for _ in range(rng.randint(1, 60)))
            cuts = sorted(set([0, len(text)]+[rng.randrange(len(text)+1) for _ in range(5)]))
            self.agree(3926, [[text[a:b] for a, b in zip(cuts, cuts[1:])], ['a', 'b', 'a-b', 'ab', 'b-a-b', 'aa-b']])

    def test_root_counts_match_cohort_and_integer_roots(self):
        rng = random.Random(9)
        for k in range(1, 31):
            for _ in range(15):
                r = rng.randint(0, 10000); self.agree(3932, [rng.randint(0, r), r, k])
        for _ in range(200):
            l, r = sorted(rng.randint(0, 10**9) for _ in range(2))
            self.assertEqual(B.kth_roots(l, r, 2), B.isqrt(r)-(B.isqrt(l-1) if l else -1))

    def test_suffix_automaton_matches_cohort_and_closed_form(self):
        rng = random.Random(10)
        for _ in range(300):
            n = rng.randint(1, 80); self.agree(3934, [[rng.randint(1, rng.choice((1, 2, 3, 9))) for _ in range(n)]])
        for n in range(1, 60):
            for period in range(1, 30):
                self.assertEqual(B.smallest_unique_sam([i % period for i in range(n)]), B.periodic_unique(n, period))

    def test_large_unique_lengths_hold_under_rolling_hash_certificate(self):
        # Equal windows hash equally, so a window that is unique by hash is unique; no
        # window of length L-1 being unique is checked with a 61-bit modulus.
        mod = (1 << 61)-1; base = 1000003
        def unique_exists(nums, length):
            power = pow(base, length, mod); h = 0; seen = {}
            for i, v in enumerate(nums):
                h = (h*base+v) % mod
                if i >= length:
                    h = (h-nums[i-length]*power) % mod
                if i >= length-1:
                    seen[h] = seen.get(h, 0)+1
            return 1 in seen.values()
        for row in B.boundary_rows(3934):
            nums, length = row['args'][0], row['expected']
            self.assertTrue(unique_exists(nums, length))
            if length > 1:
                self.assertFalse(unique_exists(nums, length-1))

    def test_final_integer_windows_match_cohort_and_circular_distance(self):
        rng = random.Random(11)
        for k in range(2, 16):
            for _ in range(20):
                self.agree(3937, [[rng.randint(1, rng.choice((2*k, 10**9))) for _ in range(rng.randint(1, 30))], k])
        for row in B.boundary_rows(3937):
            self.assertEqual(B.circular_residue(*row['args']), row['expected'])

    def test_negative_finals_change_some_boundary_answers(self):
        # Under a non-negative-final reading, values below the target residue cannot wrap downward.
        def nonnegative(nums, k):
            def cost(v, t):
                down = (v-t) % k  # finals at or above zero only; the nearest one below v exists when v-down >= 0
                return min(down if v-down >= 0 else k, (k-down) % k)
            total = [[sum(cost(v, t) for v in nums[parity::2]) for t in range(k)] for parity in (0, 1)]
            return min(total[0][x]+total[1][y] for x in range(k) for y in range(k) if x != y)
        differing = sum(nonnegative(*row['args']) != row['expected'] for row in B.boundary_rows(3937))
        self.assertGreater(differing, 20)

    def test_dihedral_search_matches_cohort_bfs(self):
        for n in range(1, 8):
            for nums in permutations(range(n)):
                self.agree(3942, [list(nums)])

    def test_new_references_reproduce_every_original_row(self):
        for pid in REFERENCES:
            for row in B.CASES[B.COHORT[pid]].build_cases(pid, include_maximum=True):
                self.assertEqual(REFERENCES[pid](row['args']), row['expected'], pid)


class LanePlumbing(unittest.TestCase):
    def test_population_cases_and_plans(self):
        pop = P.population(); data, owners = P.cases_and_owners(pop)
        self.assertEqual(set(data), {pid for ids in P.IDS.values() for pid in ids})
        for pid, rows in data.items():
            self.assertEqual(len({repr(r['args']) for r in rows}), len(rows), pid)
            originals = {repr(r['args']) for r in B.CASES[B.COHORT[pid]].build_cases(pid, include_maximum=True)}
            self.assertLessEqual(originals, {repr(r['args']) for r in rows}, pid)
            plan = P.batch_plan(pid, rows)
            self.assertEqual(plan['blocked_cases'], [], pid)
            self.assertEqual(plan['admitted_distinct_cases'], len(rows))
            for entry in plan['batches']:
                self.assertLessEqual(entry['input_bytes'], P.MAX_INPUT_BYTES)
                self.assertLessEqual(max(entry['projected_output_bytes'].values()), P.LIMITS.max_output_bytes)
            self.assertGreater(sum(r.get('category') == 'boundary-independent-reference' for r in rows), 0)

    def test_comparison_is_exact(self):
        case = {'args': [[1, 2, 3]], 'expected': 0}
        base = {'i': 0, 'result_type': 'int', 'args_before': case['args'], 'args_after': case['args'], 'alias_edges': []}
        self.assertIsNone(P.compare(3909, 'python', case, dict(base, result=0), None))
        self.assertEqual(P.compare(3909, 'python', case, dict(base, result=-1), None), 'result_value')
        self.assertEqual(P.compare(3909, 'python', case, dict(base, result=0.0, result_type='float'), None), 'result_type')

    def test_no_candidate_source_loaded(self):
        for module in list(sys.modules.values()):
            path = str(getattr(module, '__file__', '') or '')
            if '/authored/' in path:
                self.assertNotIn('/python/', path); self.assertNotIn('/javascript/', path)


if __name__ == '__main__':
    unittest.main()
