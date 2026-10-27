"""Focused source-free contract tests for the fixed F reference owner."""
import copy
import json
import unittest
from unittest.mock import patch

from . import imported_qualification as q
from . import request_parallel_f_oracles as m


class ParallelFOracleTests(unittest.TestCase):
    def reject(self, pid, args):
        with self.assertRaises(ValueError):
            m.validate(pid, args)

    def test_fixed_id_and_argument_shapes(self):
        for pid, args in ((True, [0]), (3537.0, [0]), (9999, [0]), (3537, (0,)), (3537, []), (3537, [0, 1])):
            self.reject(pid, args)

    def test_grid_integer_bounds(self):
        for n in (-1, 11, True, 1.0, '1'):
            self.reject(3537, [n])
        for n in range(11):
            m.validate(3537, [n])

    def test_grid_public_values(self):
        self.assertEqual(m.expected(3537, [0]), [[0]])
        self.assertEqual(m.expected(3537, [1]), [[3, 0], [2, 1]])
        self.assertEqual(m.expected(3537, [2]), [[15, 12, 3, 0], [14, 13, 2, 1], [11, 8, 7, 4], [10, 9, 6, 5]])

    def test_grid_recursive_quadrant_contract(self):
        def check(grid):
            n = len(grid)
            if n == 1:
                return
            half = n // 2
            quadrants = [[r[half:] for r in grid[:half]], [r[half:] for r in grid[half:]],
                         [r[:half] for r in grid[half:]], [r[:half] for r in grid[:half]]]
            for a, b in zip(quadrants, quadrants[1:]):
                self.assertLess(max(x for row in a for x in row), min(x for row in b for x in row))
            for quadrant in quadrants:
                check(quadrant)
        for n in range(7):
            grid = m.expected(3537, [n])
            self.assertEqual(sorted(x for row in grid for x in row), list(range(4**n)))
            self.assertEqual(len({id(row) for row in grid}), len(grid))
            check(grid)

    def test_zero_operation_public_values(self):
        for nums, answer in (([0, 2], 1), ([3, 1, 2, 1], 3), ([1, 2, 1, 2, 1, 2], 4)):
            self.assertEqual(m.expected(3542, [nums]), answer)

    def test_zero_is_barrier_not_ignored_minimum(self):
        self.assertEqual(m.expected(3542, [[1, 0, 1]]), 2)
        self.assertEqual(m.expected(3542, [[2, 1, 2]]), 3)
        self.assertEqual(m.expected(3542, [[0, 0]]), 0)

    def test_zero_domain(self):
        for nums in ([], [-1], [100001], [True], [1.0], (1,), [0] * 100001):
            self.reject(3542, [nums])
        m.validate(3542, [[100000] * 100000])

    def test_zero_budget_does_not_narrow_domain(self):
        args = [[1] * 10]
        m.validate(3542, args)
        with self.assertRaisesRegex(ValueError, 'budget'):
            m.expected(3542, args)

    def test_stock_public_values(self):
        self.assertEqual(m.expected(3573, [[1, 7, 9, 8, 2], 2]), 14)
        self.assertEqual(m.expected(3573, [[12, 16, 19, 19, 8, 1, 19, 13, 9], 3]), 36)

    def test_stock_no_same_day_reuse(self):
        self.assertEqual(m.expected(3573, [[1, 9, 1, 1], 2]), 8)
        self.assertEqual(m.expected(3573, [[1, 9, 1, 9], 2]), 16)
        self.assertEqual(m.expected(3573, [[9, 1], 1]), 8)

    def test_stock_domain(self):
        for args in (([1], 1), ([0, 1], 1), ([1, 10**9 + 1], 1), ([1, 1], 0), ([1, 1], 2), ([1, 1], True), ([True, 1], 1), ([1] * 1001, 1)):
            self.reject(3573, list(args))
        m.validate(3573, [[10**9] * 1000, 500])

    def test_stock_exact_large_integer(self):
        answer = m.expected(3573, [[1, 10**9] * 6, 6])
        self.assertIs(type(answer), int)
        self.assertEqual(answer, 6 * (10**9 - 1))
        self.assertGreater(answer, 2**32)

    def test_stock_budget(self):
        with self.assertRaisesRegex(ValueError, 'budget'):
            m.expected(3573, [[1] * 13, 6])

    def test_sign_public_values_and_exact_bool(self):
        self.assertIs(m.expected(3576, [[1, -1, 1, -1, 1], 3]), True)
        self.assertIs(m.expected(3576, [[-1, -1, -1, 1, 1, 1], 5]), False)

    def test_sign_singleton_and_parity(self):
        for sign in (-1, 1):
            self.assertIs(m.expected(3576, [[sign], 1]), True)
        self.assertIs(m.expected(3576, [[-1, 1], 2]), False)
        self.assertIs(m.expected(3576, [[-1, -1, 1, 1], 1]), True)

    def test_sign_domain(self):
        for args in (([], 1), ([0], 1), ([True], 1), ([1.0], 1), ([1], 0), ([1], 2), ([1], True)):
            self.reject(3576, list(args))
        m.validate(3576, [[-1] * 100000, 100000])

    def test_sign_budget(self):
        with self.assertRaisesRegex(ValueError, 'budget'):
            m.expected(3576, [[1] * 11, 1])

    def test_string_public_values(self):
        for args, answer in ((['a#b%*', 1], 'a'), (['cd%#*#', 3], 'd'), (['z*#', 0], '.')):
            self.assertEqual(m.expected(3614, args), answer)

    def test_string_zero_based_and_empty(self):
        self.assertEqual(m.expected(3614, ['ab', 0]), 'a')
        self.assertEqual(m.expected(3614, ['ab', 1]), 'b')
        self.assertEqual(m.expected(3614, ['ab', 2]), '.')
        self.assertEqual(m.expected(3614, ['*#%', 10**15]), '.')

    def test_string_domain(self):
        for args in (['', 0], ['a' * 100001, 0], ['A', 0], ['é', 0], ['a!', 0], ['a', -1], ['a', 10**15 + 1], ['a', True], ['a', 0.0], [[], 0]):
            self.reject(3614, args)

    def test_string_final_length_not_prefix_cap(self):
        program = m._homogeneous_program(10**15 + 1)
        self.reject(3614, [program, 0])
        m.validate(3614, [program + '*', 10**15])
        self.assertEqual(m.processed_length(program + '*'), 10**15)
        m.validate(3614, [m._homogeneous_program(10**15) + 'a*', 0])

    def test_string_impossible_huge_prefix_rejected_boundedly(self):
        self.reject(3614, ['a' + '#' * 99999, 0])
        m.validate(3614, ['#' * 100000, 0])

    def test_string_reference_budget_separate(self):
        args = ['a' * 21, 0]
        m.validate(3614, args)
        with self.assertRaisesRegex(ValueError, 'budget'):
            m.expected(3614, args)
        with self.assertRaisesRegex(ValueError, 'materialization'):
            m.expected(3614, ['a' + '#' * 19, 0])

    def test_constructive_length_builder(self):
        for n in (1, 2, 3, 7, 8, 1000, 10**15, 10**15 + 1):
            program = m._homogeneous_program(n)
            if n <= 1000:
                self.assertEqual(m._literal_result(program), 'a' * n)
            elif n <= 10**15:
                self.assertEqual(m.processed_length(program), n)
        for value in (0, True, 10**15 + 2):
            with self.assertRaises(ValueError):
                m._homogeneous_program(value)

    def test_references_preserve_input(self):
        vectors = {3537: [2], 3542: [[3, 1, 2, 1]], 3573: [[1, 3, 2, 4], 2], 3576: [[1, -1, -1], 2], 3614: ['ab#%', 1]}
        for pid, args in vectors.items():
            before = copy.deepcopy(args)
            m.expected(pid, args)
            self.assertEqual(args, before)

    def test_public_example_parser_requires_exact_statement(self):
        for pid in m.IDS:
            with self.assertRaises(ValueError):
                m.public_examples(pid, b'Input: n = 0\nOutput: [[0]]\n')
        with self.assertRaises(ValueError):
            m.public_examples(True, b'')

    def test_build_fails_closed_on_population_drift(self):
        with patch.object(m, '_generate_cases', return_value=([{'args': [0], 'expected': [[0]], 'compare': 'return'}], ['synthetic'])):
            with self.assertRaisesRegex(ValueError, 'frozen case'):
                m.build_cases(3537, b'')

    def test_observation_projection_has_metadata_and_done_record(self):
        batch = [{'args': [[1, 2]], 'expected': True, 'compare': 'return'}]
        base = {'i': 0, 'result': True, 'result_type': 'boolean', 'args_before': [[1, 2]], 'args_after': [[1, 2]], 'alias_edges': []}
        self.assertEqual(m.expected_observation_bytes(batch, 'javascript'), len(q.encoded(base)) + len(q.encoded({'done': 1})))
        self.assertGreater(m.expected_observation_bytes(batch, 'python'), len(json.dumps(True)))
        with self.assertRaises(ValueError):
            m.expected_observation_bytes(batch, 'ruby')


if __name__ == '__main__':
    unittest.main()
