"""Cross-check reference oracles and verify verdict boundaries for batch 03."""
from collections import deque
import copy
from itertools import combinations, combinations_with_replacement, permutations, product
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

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


class ComparatorRepairs(unittest.TestCase):
    def test_gray_code_range_types_and_cycle_are_all_required(self):
        self.assertTrue(o.matches(89, [1], [0, 1], [0, 1]))
        self.assertTrue(o.matches(89, [2], [0, 2, 3, 1], [0, 1, 3, 2]))
        for value in ([0, 2], [0, -1], [False, 1], [0, True], [0, 1.0], [0, 0],
                      [1, 0], [0], (0, 1), [0, 1, 5, 4]):
            with self.subTest(value=value):
                self.assertFalse(o.matches(89, [1 if len(value) <= 2 else 2], value, []))
        for args in ([], [True], [1.0], [-1], [0], [1000000000], [1, 2], (1,)):
            with self.subTest(args=args):
                self.assertFalse(o.matches(89, args, [0, 1], []))

    def test_published_boolean_subset_counterexample_is_rejected(self):
        args, want = [[0]], [[], [0]]
        self.assertFalse(o.matches(78, args, [[], [False]], want))
        record = {'result': [[], [False]], 'result_type': 'list',
                  'args_before': args, 'args_after': args, 'alias_edges': []}
        self.assertEqual(o.compare(78, args, want, record, 'python'), (False, 'result_value'))
        record['result_type'] = 'object'
        self.assertEqual(o.compare(78, args, want, record, 'javascript'), (False, 'result_value'))

    def test_nested_unordered_routes_preserve_types_shape_and_multiplicity(self):
        for pid in (15, 39, 40, 77, 78, 90, 216):
            with self.subTest(pid=pid):
                self.assertTrue(o.matches(pid, [], [[2, 1], []], [[], [1, 2]]))
                for value in ([[True]], [[1.0]], [(1,)], [1], [[1], [1]], {'x': [1]}):
                    self.assertFalse(o.matches(pid, [], value, [[1]]))
        self.assertTrue(o.matches(49, [], [['eat', 'tea'], ['bat']], [['bat'], ['tea', 'eat']]))
        self.assertFalse(o.matches(49, [], [['eat', 'eat']], [['eat', 'tea']]))

    def test_outer_unordered_routes_keep_recursive_types_and_inner_order(self):
        for pid in (46, 56, 57):
            self.assertTrue(o.matches(pid, [], [[3, 4], [1, 2]], [[1, 2], [3, 4]]))
            self.assertFalse(o.matches(pid, [], [[1, True]], [[1, 1]]))
            self.assertFalse(o.matches(pid, [], [[1, 2.0]], [[1, 2]]))
            self.assertFalse(o.matches(pid, [], [[2, 1]], [[1, 2]]))
        self.assertFalse(o.matches(46, [], [[[False]]], [[[0]]]))
        self.assertFalse(o.matches(131, [], [['b', 'a']], [['a', 'b']]))
        for pid in (241, 310, 347):
            self.assertTrue(o.matches(pid, [], [2, 1], [1, 2]))
            self.assertFalse(o.matches(pid, [], [True, 2], [1, 2]))
            self.assertFalse(o.matches(pid, [], [1.0, 2], [1, 2]))
        for pid in (22, 93, 187):
            self.assertTrue(o.matches(pid, [], ['b', 'a'], ['a', 'b']))
            self.assertFalse(o.matches(pid, [], ['a', 'a'], ['a', 'b']))

    def test_published_overused_pair_counterexample_is_rejected(self):
        args = [[1, 2], [1, 2], 3]
        want = [[1, 1], [1, 2], [2, 1]]
        self.assertFalse(o.matches(373, args, [[1, 1], [1, 2], [1, 2]], want))
        self.assertTrue(o.matches(373, args, [[2, 1], [1, 1], [1, 2]], want))

    def test_pair_threshold_accepts_real_ties_and_index_multiplicity(self):
        args = [[1, 2], [1, 2], 2]
        self.assertTrue(o.matches(373, args, [[1, 1], [2, 1]], [[1, 1], [1, 2]]))
        self.assertFalse(o.matches(373, args, [[1, 2], [2, 1]], [[1, 1], [1, 2]]))
        self.assertFalse(o.matches(373, args, [[1, 1], [2, 2]], [[1, 1], [1, 2]]))
        self.assertTrue(o.matches(373, [[1, 1], [2, 2], 3], [[1, 2]] * 3, None))
        self.assertTrue(o.matches(373, [[1, 1], [2, 2], 9], [[1, 2]] * 4, None))
        self.assertFalse(o.matches(373, [[1, 1], [2, 2], 3], [[1, 2]] * 4, None))
        self.assertTrue(o.matches(373, [[-3, -1], [-2, 4], 2], [[-3, -2], [-1, -2]], None))

    def test_pair_output_types_and_unknown_values_fail_closed(self):
        args = [[0, 1], [1, 2], 1]
        for value in ([[False, 1]], [[0.0, 1]], [(0, 1)], [[0, 1, 2]],
                      [[0]], [[0, 3]], None, [0], {'pair': [0, 1]}):
            with self.subTest(value=value):
                self.assertFalse(o.matches(373, args, value, [[0, 1]]))
        self.assertFalse(o.matches(373, [[1], [1], True], [[1, 1]], None))
        self.assertTrue(o.matches(373, [[1], [1], 0], [], None))
        self.assertTrue(o.matches(373, [[], [1], 1], [], None))

    def test_pair_witnesses_against_exhaustive_distinct_index_subsets(self):
        arrays = [list(a) for size in range(1, 4)
                  for a in combinations_with_replacement((-1, 1), size)]
        for left, right in product(arrays, repeat=2):
            index_pairs = [(a, b) for a in left for b in right]
            values = sorted(set(index_pairs))
            for k in range(min(3, len(index_pairs)) + 1):
                choices = list(combinations(range(len(index_pairs)), k))
                optimum = min(sum(sum(index_pairs[i]) for i in choice) for choice in choices)
                admitted = {tuple(sorted(index_pairs[i] for i in choice)) for choice in choices
                            if sum(sum(index_pairs[i]) for i in choice) == optimum}
                for candidate in combinations_with_replacement(values, k):
                    self.assertEqual(o.matches(373, [left, right, k], [list(p) for p in candidate], None),
                                     candidate in admitted, (left, right, k, candidate))


class UnexecutedEvidenceChecks(unittest.TestCase):
    def test_preparation_verifier_does_not_promote_unexecuted_delivery(self):
        # Exercise the existing verifier's metadata path with wholly synthetic
        # records. No private snapshots, raw streams or candidates are loaded.
        import verify as verifier
        from qualify import encoded, sha
        import json
        data = {11: [{'args': [[1, 1]], 'expected': 1}]}
        artifacts = {'synthetic-helper.py': '0' * 64}
        contract = {'artifact_hashes': artifacts, 'cases_sha256': sha(encoded(data)),
                    'statement_pins': [{'id': 11}]}
        raw = json.dumps(contract).encode()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            freeze = root / 'freeze.json'; freeze.write_bytes(raw)
            output = root / 'delivery'; output.mkdir()
            for name, value in {
                'run-identity.json': {'freeze_sha256': sha(raw)},
                'report.json': {'freeze_sha256': sha(raw), 'execution_status': 'unexecuted', 'passed': False},
                'unexecuted-receipt.json': {'freeze_sha256': sha(raw), 'execution_status': 'unexecuted',
                                           'judge_binary_required': '/usr/bin/bwrap'},
            }.items():
                (output / name).write_text(json.dumps(value))
            with patch.object(verifier, 'artifacts', return_value=artifacts), \
                    patch.object(verifier, 'load_cases', return_value=data), \
                    patch.object(verifier, 'verdict', side_effect=AssertionError('no execution replay allowed')):
                result = verifier.verify(freeze, root / 'unused-statements', output)
        self.assertEqual(result['execution_status'], 'unexecuted')
        self.assertEqual(result['cases_regenerated'], 1)
        self.assertTrue(result['unexecuted_receipt_verified'])
        self.assertNotIn('programs_passed', result)
        self.assertNotIn('programs_qualified', result)
        self.assertNotIn('all_observations_match_report', result)


if __name__ == '__main__':
    unittest.main()
