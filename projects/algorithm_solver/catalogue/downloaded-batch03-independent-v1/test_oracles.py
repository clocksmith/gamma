"""Cross-check reference oracles and verify verdict boundaries for batch 03."""
from collections import deque
import copy
from itertools import combinations, permutations, product
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oracles as o


class ReferenceChecks(unittest.TestCase):
    def test_catalan_structures_against_combinatorics(self):
        for n in range(1, 7):
            catalan = math.comb(2 * n, n) // (n + 1)
            self.assertEqual(o.expected(96, [n]), catalan)
            parens = o.expected(22, [n])
            self.assertEqual(len(parens), catalan)
            for p in parens:
                # verify well-formed parentheses
                bal = 0
                for ch in p:
                    bal += 1 if ch == '(' else -1
                    self.assertGreaterEqual(bal, 0)
                self.assertEqual(bal, 0)

    def test_permutations_and_subsets_counts(self):
        for n in range(1, 5):
            nums = list(range(1, n + 1))
            self.assertEqual(len(o.expected(46, [nums])), math.factorial(n))
            self.assertEqual(len(o.expected(78, [nums])), 1 << n)

    def test_unique_paths_against_grid_dp(self):
        for m in range(1, 6):
            for n in range(1, 6):
                dp = [[1] * n for _ in range(m)]
                for r in range(1, m):
                    for c in range(1, n):
                        dp[r][c] = dp[r - 1][c] + dp[r][c - 1]
                self.assertEqual(o.expected(62, [m, n]), dp[m - 1][n - 1])

    def test_gray_code_cycle_and_bit_transitions(self):
        for n in range(1, 6):
            seq = o.expected(89, [n])
            self.assertTrue(o.matches(89, [n], seq, seq))
            self.assertEqual(len(seq), 1 << n)
            self.assertEqual(seq[0], 0)
            self.assertEqual(len(set(seq)), 1 << n)
            for i in range(len(seq)):
                diff = seq[i] ^ seq[(i + 1) % len(seq)]
                self.assertEqual(diff & (diff - 1), 0)
                self.assertGreater(diff, 0)

    def test_course_schedule_topological_validity(self):
        prereqs = [[1, 0], [2, 0], [3, 1], [3, 2]]
        order = o.expected(210, [4, prereqs])
        self.assertTrue(o.matches(210, [4, prereqs], order, order))
        pos = {c: i for i, c in enumerate(order)}
        for dest, src in prereqs:
            self.assertLess(pos[src], pos[dest])

    def test_basic_calculator_truncation_and_precedence(self):
        self.assertEqual(o.expected(227, ['14-3/2']), 13)
        self.assertEqual(o.expected(227, [' 3/2 ']), 1)
        self.assertEqual(o.expected(227, [' 3+5 / 2 ']), 5)

    def test_fraction_recurring_decimal(self):
        self.assertEqual(o.expected(166, [1, 2]), '0.5')
        self.assertEqual(o.expected(166, [2, 1]), '2')
        self.assertEqual(o.expected(166, [4, 333]), '0.(012)')
        self.assertEqual(o.expected(166, [1, 5]), '0.2')
        self.assertEqual(o.expected(166, [-50, 8]), '-6.25')

    def test_nth_digit_against_direct_concatenation(self):
        big_str = ''.join(str(i) for i in range(1, 1000))
        for n in (1, 3, 9, 10, 11, 15, 100, 250, 500):
            self.assertEqual(o.expected(400, [n]), int(big_str[n - 1]))

    def test_result_freedom_and_negative_controls(self):
        # 3Sum: ordering freedom
        self.assertTrue(o.matches(15, [[-1, 0, 1]], [[1, 0, -1]], [[-1, 0, 1]]))
        self.assertFalse(o.matches(15, [[-1, 0, 1]], [[0, 0, 0]], [[-1, 0, 1]]))

        # Pow(x, n): float tolerance
        self.assertTrue(o.matches(50, [2.0, 10], 1024.000001, 1024.0))
        self.assertFalse(o.matches(50, [2.0, 10], 1025.0, 1024.0))

        # Compare verdict checks
        args = [[1, 2, 3]]
        record = {'result': [1, 2, 3], 'result_type': 'list', 'args_before': args,
                  'args_after': args, 'alias_edges': []}
        self.assertEqual(o.compare(26, args, [1, 2, 3], record, 'python'), (True, None))

        # Check negative controls
        altered_type = copy.deepcopy(record)
        altered_type['result_type'] = 'tuple'
        self.assertEqual(o.compare(26, args, [1, 2, 3], altered_type, 'python'), (False, 'result_type'))

        altered_effect = copy.deepcopy(record)
        altered_effect['args_after'] = [[1, 2]]
        self.assertEqual(o.compare(26, args, [1, 2, 3], altered_effect, 'python'), (False, 'input_effects'))

        altered_alias = copy.deepcopy(record)
        altered_alias['alias_edges'] = [['result', 'args.0']]
        self.assertEqual(o.compare(26, args, [1, 2, 3], altered_alias, 'python'), (False, 'mutable_return_alias'))

    def test_mandatory_failures_registry(self):
        self.assertIn((41, 'python'), o.MANDATORY_FAILURES)
        self.assertIn((41, 'javascript'), o.MANDATORY_FAILURES)
        self.assertIn((164, 'python'), o.MANDATORY_FAILURES)
        self.assertIn((164, 'javascript'), o.MANDATORY_FAILURES)
        self.assertIn((373, 'python'), o.MANDATORY_FAILURES)
        self.assertIn((373, 'javascript'), o.MANDATORY_FAILURES)


if __name__ == '__main__':
    unittest.main()
