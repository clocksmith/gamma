"""Synthetic focused checks; no candidate, historical case or statement reads."""
import copy
import unittest
from unittest import mock

from . import imported_qualification as q
from . import request_parallel_b_oracles as o


class DomainTests(unittest.TestCase):
    def reject(self, pid, arguments):
        for args in arguments:
            with self.subTest(pid=pid, args=str(args)[:100]), self.assertRaises(ValueError):
                o.validate(pid, args)

    def test_fixed_identity_and_ordered_shape(self):
        for pid in (True, '3517', 3518, None):
            with self.assertRaises(ValueError):
                o.validate(pid, ['a'])
        self.reject(3517, [None, ('a',), [], ['a', 'a']])

    def test_palindrome_requirement_is_not_rearrangeability(self):
        self.reject(3517, [['aabb'], ['ab'], [''], ['A'], ['é'], ['a\na'], [1]])
        for s in ('a', 'abba', 'z' * 100000):
            o.validate(3517, [s])

    def test_palindrome_length_limit(self):
        self.reject(3517, [['a' * 100001]])

    def test_building_integer_bounds(self):
        self.reject(3531, [[1, [[1, 1]]], [100001, [[1, 1]]], [True, [[1, 1]]],
                           [3.0, [[1, 1]]], [3, [[0, 1]]], [3, [[4, 1]]],
                           [3, [[True, 1]]], [3, [[1.0, 1]]]])

    def test_buildings_unique_and_shaped(self):
        self.reject(3531, [[3, []], [3, [[1, 1], [1, 1]]], [3, [[1]]],
                           [3, [[1, 1, 1]]], [3, [(1, 1)]], [3, 'x'],
                           [100000, [[1, 1]] * 100001]])
        o.validate(3531, [2, [[1, 1], [1, 2], [2, 1], [2, 2]]])
        o.validate(3531, [100000, [[100000, 1], [1, 100000]]])

    def test_grid_rectangular_and_dimensions(self):
        self.reject(3567, [[[], 1], [[[]], 1], [[[1], [1, 2]], 1],
                           [[[0] * 31], 1], [[[0]] * 31, 1], [('x',), 1],
                           [[(1,)], 1]])

    def test_grid_integer_and_window_bounds(self):
        self.reject(3567, [[[[True]], 1], [[[-100001]], 1], [[[100001]], 1],
                           [[[0.0]], 1], [[[0]], 0], [[[0]], 2], [[[0]], True]])
        o.validate(3567, [[[-100000, 100000]], 1])
        o.validate(3567, [[[0] * 30 for _ in range(30)], 30])

    def test_word_individual_total_and_count_bounds(self):
        self.reject(3598, [[[]], [['']], [['a' * 10001]], [['a' * 10000] * 11],
                           [['a'] * 100001], [('a',)], [['a', 1]], [['A']], [['é']]])
        o.validate(3598, [['a' * 10000] * 10])
        o.validate(3598, [['a'] * 100000])

    def test_prime_array_full_integer_domain(self):
        self.reject(3618, [[[]], [[0] * 100001], [[True]], [[1.0]],
                           [[10**9 + 1]], [[-10**9 - 1]], [(1,)]])
        o.validate(3618, [[-10**9, 0, 10**9]])
        o.validate(3618, [[10**9] * 100000])

    def test_domain_validity_is_not_packet_acceptance(self):
        args = [[10**9] * 100000]
        o.validate(3618, args)
        with self.assertRaisesRegex(ValueError, 'packet cap'):
            list(q.batches([{'args': args, 'expected': 0, 'compare': 'return'}]))

    def test_small_enumeration_budget_is_separate(self):
        cases = [(3517, ['a' * 9]),
                 (3531, [100, [[1, i] for i in range(1, 66)]]),
                 (3567, [[[0] * 7 for _ in range(6)], 1]),
                 (3598, [['a'] * 17]), (3598, [['a' * 1001]])]
        for pid, args in cases:
            with self.subTest(pid=pid):
                o.validate(pid, args)
                with self.assertRaisesRegex(ValueError, 'enumeration budget'):
                    o.expected(pid, args)


class ReferenceTests(unittest.TestCase):
    def test_permutation_oracle_even_and_odd(self):
        self.assertEqual(o.expected(3517, ['babab']), 'abbba')
        self.assertEqual(o.expected(3517, ['daccad']), 'acddca')
        self.assertEqual(o.expected(3517, ['zzayazz']), 'azzyzza')

    def test_directional_witnesses_not_diagonals(self):
        self.assertEqual(o.expected(3531, [3, [[1, 1], [2, 2], [3, 3]]]), 0)
        self.assertEqual(o.expected(3531, [5, [[1, 3], [3, 2], [3, 3], [3, 5], [5, 3]]]), 1)

    def test_distinct_values_not_occurrences(self):
        self.assertEqual(o.expected(3567, [[[1, 1], [5, 5]], 2]), [[4]])
        self.assertEqual(o.expected(3567, [[[5, 5], [5, 5]], 2]), [[0]])

    def test_window_positions_and_numeric_extremes(self):
        self.assertEqual(o.expected(3567, [[[1, -2, 3], [2, 3, 5]], 2]), [[1, 2]])
        self.assertEqual(o.expected(3567, [[[-100000, 100000], [-100000, 100000]], 2]), [[200000]])
        self.assertEqual(o.expected(3567, [[[3, -1]], 1]), [[0, 0]])

    def test_removals_are_independent_and_bridge_adjacency(self):
        self.assertEqual(o.expected(3598, [['ab', 'z', 'ac']]), [0, 1, 0])
        self.assertEqual(o.expected(3598, [['jump', 'run', 'run', 'jump', 'run']]), [3, 0, 0, 3, 3])

    def test_removals_zero_and_prefix_equality(self):
        self.assertEqual(o.expected(3598, [['a']]), [0])
        self.assertEqual(o.expected(3598, [['a', 'ab']]), [0, 0])
        self.assertEqual(o.expected(3598, [['a', 'ab', 'abc', 'ab']]), [2, 2, 2, 2])

    def test_zero_based_prime_indices(self):
        self.assertEqual(o.expected(3618, [[2, 3, 4]]), 1)
        self.assertEqual(o.expected(3618, [[-1, 5, 7, 0]]), 3)
        self.assertEqual(o.expected(3618, [[-10**9] * 10]), 2 * 10**9)

    def test_prime_squares_and_larger_prime(self):
        values = [0] * 50
        values[0], values[49] = 3, 5
        self.assertEqual(o.expected(3618, [values]), 8)
        values[49], values[47] = 0, 5
        self.assertEqual(o.expected(3618, [values]), 2)
        self.assertFalse(o._prime(0))
        self.assertFalse(o._prime(1))
        self.assertFalse(o._prime(121))

    def test_oracles_do_not_mutate_arguments(self):
        cases = [(3517, ['babab']), (3531, [3, [[1, 1], [2, 2]]]),
                 (3567, [[[1, 2], [2, 1]], 2]), (3598, [['a', 'b', 'a']]),
                 (3618, [[1, 2, 3]])]
        for pid, args in cases:
            original = copy.deepcopy(args)
            o.expected(pid, args)
            self.assertEqual(args, original)


class FreezeTests(unittest.TestCase):
    def test_example_identity_pin_fails_closed(self):
        for pid, raw in ((3517, b''), (3517, ''), (True, b''), (9999, b'')):
            with self.assertRaises(ValueError):
                o.public_examples(pid, raw)

    def test_examples_need_all_ordered_arguments(self):
        raw = b'Input: wrong = "a"\nOutput: "a"\n'
        with mock.patch.dict(o.STATEMENT_SHA256, {3517: q.sha(raw)}), self.assertRaises(ValueError):
            o.public_examples(3517, raw)

    def test_examples_validate_count_and_answers(self):
        for raw in (b'Input: s = "a"\nOutput: "a"\n',
                    b'Input: s = "a"\nOutput: "b"\n' * 3):
            with mock.patch.dict(o.STATEMENT_SHA256, {3517: q.sha(raw)}), self.assertRaises(ValueError):
                o.public_examples(3517, raw)

    def test_synthetic_example_extraction(self):
        raw = b'Input: s = "a"\nOutput: "a"\n' * 3
        with mock.patch.dict(o.STATEMENT_SHA256, {3517: q.sha(raw)}):
            self.assertEqual(len(o.public_examples(3517, raw)), 3)

    def test_frozen_population_and_hash_are_unconditional(self):
        case = {'args': ['a'], 'expected': 'a', 'compare': 'return'}
        with mock.patch.object(o, '_generate_cases', return_value=([case], ['synthetic'])):
            with self.assertRaises(ValueError):
                o.build_cases(3517, b'')
            with mock.patch.dict(o.CASE_COUNT, {3517: 1}), self.assertRaises(ValueError):
                o.build_cases(3517, b'')
            with mock.patch.dict(o.CASE_COUNT, {3517: 1}), mock.patch.dict(o.CASES_SHA256, {3517: q.sha(q.encoded([case]))}):
                self.assertEqual(o.build_cases(3517, b''), ([case], ['synthetic']))

    def test_frozen_packet_cannot_silently_drop_case(self):
        case = {'args': [[10**9] * 100000], 'expected': 0, 'compare': 'return'}
        with mock.patch.object(o, '_generate_cases', return_value=([case], ['synthetic'])), \
                mock.patch.dict(o.CASE_COUNT, {3618: 1}), \
                mock.patch.dict(o.CASES_SHA256, {3618: q.sha(q.encoded([case]))}), \
                self.assertRaisesRegex(ValueError, 'packet cap'):
            o.build_cases(3618, b'')


if __name__ == '__main__':
    unittest.main()
