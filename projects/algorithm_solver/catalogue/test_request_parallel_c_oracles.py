"""Pure fixed batch C tests: synthetic fixtures, no source or file acquisition."""
import copy
import json
from math import factorial
import unittest
from unittest.mock import patch

from . import imported_qualification as q
from . import request_parallel_c_oracles as o

EXAMPLES = {
    3524: [([[1, 2, 3, 4, 5], 3], [9, 2, 4]),
           ([[1, 2, 4, 8, 16, 32], 4], [18, 1, 2, 0]), ([[1, 1, 2, 1, 1], 2], [9, 6])],
    3551: [([[37, 100]], 1), ([[22, 14, 33, 7]], 0), ([[18, 43, 34, 16]], 2)],
    3587: [([[2, 4, 6, 5, 7]], 3), ([[2, 4, 5, 7]], 1), ([[1, 2, 3]], 0), ([[4, 5, 6, 8]], -1)],
    3608: [([2, [[0, 1, 3]], 2], 3), ([3, [[0, 1, 2], [1, 2, 4]], 3], 4), ([3, [[0, 2, 5]], 2], 0)],
    3619: [([[[0, 2, 1, 0, 0], [0, 5, 0, 0, 5], [0, 0, 1, 0, 0], [0, 1, 4, 7, 0], [0, 2, 0, 0, 8]], 5], 2),
           ([[[3, 0, 3, 0], [0, 3, 0, 3], [3, 0, 3, 0]], 3], 6)],
}


def fixture(pid):
    return '\n'.join('Input: ' + ', '.join(f'{key} = {value!r}' for key, value in zip(o.PARAMETERS[pid], args))
                     + '\nOutput: ' + json.dumps(answer) + '\nExplanation: synthetic fixture.'
                     for args, answer in EXAMPLES[pid]).encode()


def frozen(pid):
    raw = fixture(pid)
    with patch.dict(o.STATEMENT_SHA256, {pid: q.sha(raw)}):
        return o.build_cases(pid, raw)


class DomainTests(unittest.TestCase):
    def test_fixed_identity_arity_and_exact_types(self):
        for pid, args in [(True, [[1], 1]), ('3524', [[1], 1]), (1, [[1], 1]),
                          (3524, ([1], 1)), (3524, [[1]]), (3551, [[1], 2]), (3619, [])]:
            with self.subTest(pid=pid), self.assertRaises(ValueError):
                o.validate(pid, args)

    def test_positive_array_bounds(self):
        for pid in (3524, 3551, 3587):
            tail = [1] if pid == 3524 else []
            for nums in ([], [0], [10**9 + 1], [True], [1.0], (1,), [1] * 100001):
                with self.subTest(pid=pid), self.assertRaises(ValueError):
                    o.validate(pid, [nums, *tail])
            o.validate(pid, [[1, 10**9], *tail])

    def test_distinctness_only_where_normative(self):
        o.validate(3524, [[7, 7, 7], 5])
        for pid in (3551, 3587):
            with self.assertRaises(ValueError):
                o.validate(pid, [[7, 7]])
            o.validate(pid, [list(range(1, 100001))])

    def test_moduli_are_exact_integers(self):
        for k in (0, 6, True, 1.0, '2'):
            with self.assertRaises(ValueError):
                o.validate(3524, [[1], k])
        for k in (0, 10**6 + 1, False, 1.0, '2'):
            with self.assertRaises(ValueError):
                o.validate(3619, [[[1]], k])

    def test_graph_identity_shape_and_bounds(self):
        invalid = [[0, [], 1], [100001, [], 1], [True, [], 1], [2, [], 0], [2, [], 3],
                   [2, [], True], [2, [[0, 0, 1]], 1], [2, [[0, 2, 1]], 1],
                   [2, [[False, 1, 1]], 1], [2, [[0, 1, 0]], 1], [2, [[0, 1, 10**9 + 1]], 1],
                   [2, [[0, 1, True]], 1], [2, [[0, 1, 1.0]], 1], [2, [(0, 1, 1)], 1],
                   [2, [[0, 1]], 1], [2, [[0, 1, 1, 1]], 1], [2, (), 1],
                   [2, [[0, 1, 1]] * 100001, 1]]
        for args in invalid:
            with self.subTest(n=args[0]), self.assertRaises(ValueError):
                o.validate(3608, args)
        o.validate(3608, [100000, [], 100000])
        o.validate(3608, [2, [[1, 0, 10**9]], 2])

    def test_duplicate_edges_are_unordered_and_time_independent(self):
        for edges in ([[0, 1, 1], [0, 1, 1]], [[0, 1, 1], [1, 0, 2]]):
            with self.assertRaises(ValueError):
                o.validate(3608, [2, edges, 1])
        o.validate(3608, [4, [[2, 3, 2], [1, 0, 2]], 2])

    def test_rectangular_grid_domain(self):
        invalid = [[], [[]], [[1], []], [[1], [1, 2]], [(1,)], [[-1]], [[True]], [[1.0]],
                   [[10**6 + 1]], [[0] * 1001], [[0]] * 1001, [[0] * 101 for _ in range(1000)]]
        for grid in invalid:
            with self.subTest(height=len(grid)), self.assertRaises(ValueError):
                o.validate(3619, [grid, 1])
        o.validate(3619, [[[0] * 1000 for _ in range(100)], 10**6])
        o.validate(3619, [[[10**6] * 100 for _ in range(1000)], 1])

    def test_full_domain_is_distinct_from_reference_budget(self):
        values = {3524: [[1] * 13, 1], 3551: [list(range(1, 9))],
                  3587: [list(range(1, 12))], 3608: [8, [], 1], 3619: [[[1] * 26], 1]}
        for pid, args in values.items():
            o.validate(pid, args)
            with self.subTest(pid=pid), self.assertRaisesRegex(ValueError, 'reference budget'):
                o.expected(pid, args)


class OracleTests(unittest.TestCase):
    def test_every_public_example_typed_and_read_only(self):
        for pid, rows in EXAMPLES.items():
            for args, answer in rows:
                before = copy.deepcopy(args)
                with self.subTest(pid=pid):
                    self.assertTrue(q.exact(o.expected(pid, args), answer))
                    self.assertEqual(args, before)

    def test_interval_multiplicity_exact_products_and_all_moduli(self):
        self.assertEqual(o.expected(3524, [[2, 2, 2], 4]), [3, 0, 3, 0])
        self.assertEqual(o.expected(3524, [[10**9] * 12, 3]), [0, 78, 0])
        for k in range(1, 6):
            result = o.expected(3524, [[1, 2, 3, 4], k])
            self.assertEqual(sum(result), 10)
            self.assertEqual(len(result), k)

    def test_arbitrary_swaps_and_tie_break_are_not_adjacent_distance(self):
        self.assertEqual(o.expected(3551, [[3, 2, 1]]), 1)
        self.assertEqual(o.expected(3551, [[10, 1]]), 1)
        self.assertEqual(o.expected(3551, [[1, 10]]), 0)
        self.assertEqual(o.expected(3551, [[10**9, 1, 10, 100]]), 3)
        for n in range(1, 8):
            distances = o._swap_distances(n)
            self.assertEqual(len(distances), factorial(n))
            self.assertEqual(distances[tuple(range(n))], 0)
            self.assertLessEqual(max(distances.values()), n - 1)

    def test_adjacent_parity_all_singletons_and_impossible_counts(self):
        self.assertEqual(o.expected(3587, [[2]]), 0)
        self.assertEqual(o.expected(3587, [[3]]), 0)
        self.assertEqual(o.expected(3587, [[2, 4]]), -1)
        self.assertEqual(o.expected(3587, [[2, 4, 6, 1, 3, 5]]), 3)
        self.assertEqual(o.expected(3587, [[1, 3, 5, 2, 4, 6]]), 3)
        self.assertEqual(o.expected(3587, [[2, 4, 6, 8, 1, 3]]), -1)

    def test_time_zero_threshold_equality_and_parallel_removals(self):
        self.assertEqual(o.expected(3608, [5, [], 5]), 0)
        self.assertEqual(o.expected(3608, [4, [[0, 1, 7], [1, 2, 7], [2, 3, 7]], 3]), 7)
        self.assertEqual(o.expected(3608, [3, [[0, 1, 1], [1, 2, 2], [0, 2, 3]], 2]), 2)
        self.assertEqual(o.expected(3608, [4, [[0, 1, 10**9], [2, 3, 1]], 3]), 1)
        self.assertEqual(o.expected(3608, [2, [[0, 1, 10**9]], 2]), 10**9)

    def test_island_zero_water_diagonal_separation_and_exact_sums(self):
        self.assertEqual(o.expected(3619, [[[0, 0], [0, 0]], 1]), 0)
        self.assertEqual(o.expected(3619, [[[2, 0], [0, 2]], 2]), 2)
        self.assertEqual(o.expected(3619, [[[2, 1], [0, 3]], 3]), 1)
        self.assertEqual(o.expected(3619, [[[10**6] * 5 for _ in range(5)], 999983]), 0)

    def test_oracles_do_not_open_files(self):
        with patch('builtins.open', side_effect=AssertionError('No payload file opens')):
            for pid, rows in EXAMPLES.items():
                self.assertTrue(q.exact(o.expected(pid, rows[0][0]), rows[0][1]))


class FrozenInputTests(unittest.TestCase):
    def test_synthetic_examples_require_exact_pin_and_all_examples(self):
        for pid in o.IDS:
            raw = fixture(pid)
            with self.assertRaises(ValueError):
                o.public_examples(pid, raw)
            with patch.dict(o.STATEMENT_SHA256, {pid: q.sha(raw)}):
                self.assertEqual(len(o.public_examples(pid, raw)), o.EXAMPLE_COUNT[pid])
            first = raw.split(b'Explanation:')[0]
            with patch.dict(o.STATEMENT_SHA256, {pid: q.sha(first)}), self.assertRaises(ValueError):
                o.public_examples(pid, first)

    def test_parser_rejects_wrong_order_nonliteral_and_wrong_result(self):
        for raw in (b'Input: k = 2, nums = [1]\nOutput: [0,1]\n',
                    b'Input: nums = list([1]), k = 2\nOutput: [0,1]\n',
                    b'Input: nums = [1], k = 2\nOutput: [1,0]\n'):
            with patch.dict(o.STATEMENT_SHA256, {3524: q.sha(raw)}), self.assertRaises(ValueError):
                o.public_examples(3524, raw)

    def test_all_frozen_counts_hashes_domains_categories_and_packets(self):
        for pid in o.IDS:
            cases, categories = frozen(pid)
            with self.subTest(pid=pid):
                self.assertEqual(len(cases), o.CASE_COUNT[pid])
                self.assertEqual(q.sha(q.encoded(cases)), o.CASES_SHA256[pid])
                self.assertEqual(len(categories), len(cases))
                self.assertTrue(all(type(x) is str and x for x in categories))
                for case in cases:
                    o.validate(pid, case['args'])
                for _, batch in q.batches(cases):
                    self.assertLessEqual(len(batch), 32)
                    self.assertLessEqual(len(q.encoded(q.packet(batch))), q.MAX_PACKET)

    def test_hard_pins_cannot_be_missing_or_changed(self):
        raw = fixture(3608)
        for values in ({}, {3608: 1}):
            with patch.dict(o.STATEMENT_SHA256, {3608: q.sha(raw)}), patch.object(o, 'CASE_COUNT', values):
                with self.assertRaises((KeyError, ValueError)):
                    o.build_cases(3608, raw)
        for values in ({}, {3608: '0' * 64}):
            with patch.dict(o.STATEMENT_SHA256, {3608: q.sha(raw)}), patch.object(o, 'CASES_SHA256', values):
                with self.assertRaises((KeyError, ValueError)):
                    o.build_cases(3608, raw)

    def test_valid_oversized_inputs_are_explicitly_transport_rejected(self):
        for pid, args in ((3524, [[10**9] * 100000, 5]),
                          (3608, [100000, [[0, i, 1] for i in range(1, 100000)], 100000])):
            o.validate(pid, args)
            self.assertGreater(len(q.encoded(q.packet([{'args': args}]))), q.MAX_PACKET)
            with self.assertRaisesRegex(ValueError, 'no silent truncation'):
                list(q.batches([{'args': args}]))
            self.assertIn('cap', o.OMITTED_MAXIMUM_SHAPES[pid])

    def test_numeric_and_large_shape_diagnostics_are_retained(self):
        cases, categories = frozen(3524)
        self.assertTrue(any(max(case['expected']) > 2**32 for case in cases))
        self.assertEqual(categories.count('analytic_near_maximum_high_values'), 2)
        self.assertEqual({len(case['args'][0]) for case, category in zip(cases, categories)
                          if category == 'analytic_near_maximum_high_values'}, {99000})
        cases, categories = frozen(3587)
        for case, category in zip(cases, categories):
            if 'balanced_blocks' in category or 'reversed_blocks' in category:
                self.assertEqual(case['expected'], 50000 * 49999 // 2)
        cases, categories = frozen(3619)
        self.assertEqual(sum(len(case['args'][0]) * len(case['args'][0][0]) == 100000 for case in cases), 5)


if __name__ == '__main__':
    unittest.main()
