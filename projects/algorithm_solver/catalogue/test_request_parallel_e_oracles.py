"""Synthetic source-free regression tests for the fixed batch E owner."""
from copy import deepcopy
import json
from math import factorial
import unittest
from unittest.mock import patch

from . import imported_qualification as q
from . import request_parallel_e_oracles as o

EXAMPLES = {
    3227: [(['leetcoder'], True), (['bbcd'], False)],
    3234: [(['00011'], 5), (['101101'], 16)],
    3556: [(['12234'], 1469), (['111'], 11)],
    3577: [([[1, 2, 3]], 2), ([[3, 3, 3, 4, 4, 4]], 0)],
    3584: [([[-1, -9, 2, 3, -2, -3, 1], 1], 81),
           ([[1, 3, -5, 5, 6, -4], 3], 20), ([[2, -1, 2, -6, 5, 2, -5, 7], 2], 35)],
}


def fixture(pid):
    return ''.join('Input: ' + ', '.join(f'{name} = {value!r}' for name, value in zip(o.PARAMETERS[pid], args)) +
                   '\n\nOutput: ' + json.dumps(answer) + '\nExplanation: Synthetic example transcription.\n'
                   for args, answer in EXAMPLES[pid]).encode()


class ParallelEOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = {pid: fixture(pid) for pid in o.IDS}
        cls.pins = {pid: q.sha(raw) for pid, raw in cls.raw.items()}
        with patch.dict(o.STATEMENT_SHA256, cls.pins):
            cls.built = {pid: o.build_cases(pid, cls.raw[pid]) for pid in o.IDS}

    def test_public_examples_exact_types(self):
        for pid, rows in EXAMPLES.items():
            for args, answer in rows:
                with self.subTest(pid=pid):
                    self.assertTrue(q.exact(o.expected(pid, args), answer))

    def test_identity_and_ordered_shape(self):
        for pid, args in [(True, ['a']), (3227.0, ['a']), (3223, ['a']), (3227, ('a',)),
                          (3227, []), (3227, ['a', 0]), (3584, [[1]])]:
            with self.subTest(pid=pid, args=args), self.assertRaises(ValueError):
                o.validate(pid, args)

    def test_exact_ascii_string_domains(self):
        for pid, maximum, good, bad in [(3227, 100000, 'z', '0'), (3234, 40000, '1', '2'), (3556, 10, '9', 'a')]:
            for value in ('', 'é', '\n', bad, None, 1, good * (maximum + 1)):
                with self.subTest(pid=pid, value=str(value)[:50]), self.assertRaises(ValueError):
                    o.validate(pid, [value])
            o.validate(pid, [good * maximum])
        for value in ('A', '*', 'a b'):
            with self.assertRaises(ValueError):
                o.validate(3227, [value])

    def test_unlock_array_domain(self):
        for values in ([], [1], [1] * 100001, [0, 1], [1, 10**9 + 1], [False, 1], [1, 2.0], (1, 2)):
            with self.subTest(value=str(values)[:50]), self.assertRaises(ValueError):
                o.validate(3577, [values])
        o.validate(3577, [[10**9] * 100000])

    def test_subsequence_full_domain(self):
        invalid = [[[], 1], [[0] * 100001, 1], [[True], 1], [[1.0], 1], [[100001], 1],
                   [[-100001], 1], [[1], 0], [[1], 2], [[1], True], [[1], 1.0], [(1,), 1]]
        for args in invalid:
            with self.subTest(args=str(args)[:50]), self.assertRaises(ValueError):
                o.validate(3584, args)
        o.validate(3584, [[-100000] * 100000, 100000])

    def test_reference_budgets_do_not_shrink_domains(self):
        for pid, args in [(3227, ['a' * 13]), (3234, ['0' * 65]), (3577, [[1] * 9]), (3584, [[0] * 13, 1])]:
            o.validate(pid, args)
            with self.subTest(pid=pid), self.assertRaisesRegex(ValueError, 'budget'):
                o.expected(pid, args)
        self.assertIsInstance(o.expected(3556, ['9999999967']), int)

    def test_budget_before_game_search(self):
        with patch.object(o, '_game_win', side_effect=AssertionError('must not search')):
            with self.assertRaisesRegex(ValueError, 'budget'):
                o.expected(3227, ['a' * 100000])

    def test_game_empty_moves_and_alternation(self):
        self.assertFalse(o._game_win('', 0)); self.assertFalse(o._game_win('', 1))
        self.assertFalse(o._game_win('0', 0)); self.assertTrue(o._game_win('0', 1))
        for value in ('a', 'aa', 'bab', 'baba', 'aeiou', 'yey'):
            self.assertIs(o.expected(3227, [value]), True)
        self.assertIs(o.expected(3227, ['xyz']), False)

    def test_game_projection_preserves_all_vowels(self):
        for vowel in 'aeiou':
            self.assertIs(o.expected(3227, ['by' + vowel + 'z']), True)
        self.assertIs(o.expected(3227, ['y']), False)

    def test_dominance_boundary_is_square_and_inclusive(self):
        self.assertEqual(o.expected(3234, ['0']), 0)
        self.assertEqual(o.expected(3234, ['1']), 1)
        self.assertEqual(o.expected(3234, ['01']), 2)
        self.assertEqual(o.expected(3234, ['001111']), 15)

    def test_large_interval_formula_small_homologues(self):
        for n in range(4, 20):
            self.assertEqual(o.expected(3234, ['0' + '1' * (n - 1)]), n * (n + 1) // 2 - 1)
            t = n - 2
            answer = t * (t + 1) // 2 + t + max(0, t - 3)
            self.assertEqual(o.expected(3234, ['00' + '1' * t]), answer)
            expected = n * (n + 1) // 2 + sum(max(0, n - z*z + 1) for z in range(1, n + 1))
            self.assertEqual(o.expected(3234, ['0' * n + '1' * n]), expected)

    def test_prime_values_unique_and_leading_zeroes_ignored(self):
        for value, answer in [('0', 0), ('1', 0), ('0002', 2), ('222', 2), ('111', 11), ('023', 28)]:
            self.assertEqual(o.expected(3556, [value]), answer)

    def test_primality_squares_and_large_integer_boundaries(self):
        for value in (0, 1, 4, 9, 25, 9999800001, 10**9):
            self.assertFalse(o._trial_prime(value))
        for value in (2, 3, 97, 2147483647, 4294967291, 9999999967):
            self.assertTrue(o._trial_prime(value))
        self.assertGreater(o.expected(3556, ['9999999967']), 2**32)
        self.assertEqual(o._trial_prime.cache_info().maxsize, 32768)

    def test_unlock_root_fixed_and_witness_strict(self):
        for values, answer in [([1, 2], 1), ([1, 1], 0), ([2, 1, 3], 0), ([1, 3, 2], 2), ([3, 4, 5, 6], 6)]:
            self.assertEqual(o.expected(3577, [values]), answer)
        self.assertEqual(o.expected(3577, [[1, 2, 3]]), factorial(2))
        self.assertNotEqual(o.expected(3577, [[1, 2, 3]]), factorial(3))

    def test_subsequence_order_size_and_negative_results(self):
        for args, answer in [([[-2], 1], 4), ([[-1, 1], 2], -1), ([[-5, 0, -4], 3], 20),
                             ([[-100000, 100000], 2], -10**10), ([[100000], 1], 10**10)]:
            self.assertEqual(o.expected(3584, args), answer)

    def test_sources_are_not_needed_and_arguments_not_mutated(self):
        for pid, rows in EXAMPLES.items():
            for args, _ in rows:
                before = deepcopy(args); o.expected(pid, args); self.assertEqual(args, before)

    def test_statement_pin_precedes_reference_work(self):
        with patch.object(o, 'expected', side_effect=AssertionError('must not run')):
            with self.assertRaisesRegex(ValueError, 'pinned statement'):
                o.public_examples(3227, b'not pinned')

    def test_missing_examples_and_wrong_argument_order(self):
        for raw in (b'Constraints only', b'Input: m = 1, nums = [1]\nOutput: 1\n'):
            with patch.dict(o.STATEMENT_SHA256, {3584: q.sha(raw)}), self.assertRaises(ValueError):
                o.public_examples(3584, raw)

    def test_boolean_example_cannot_be_integer(self):
        raw = self.raw[3227].replace(b'Output: true', b'Output: 1')
        with patch.dict(o.STATEMENT_SHA256, {3227: q.sha(raw)}), self.assertRaisesRegex(ValueError, 'disagrees'):
            o.public_examples(3227, raw)

    def test_frozen_populations_and_exact_case_bytes(self):
        for pid, (cases, categories) in self.built.items():
            self.assertEqual(len(cases), o.CASE_COUNT[pid]); self.assertEqual(len(categories), len(cases))
            self.assertEqual(q.sha(q.encoded(cases)), o.CASES_SHA256[pid])
        self.assertEqual(sum(len(cases) for cases, _ in self.built.values()), 3370)
        self.assertEqual(sum(len({q.encoded(c['args']) for c in cases}) for cases, _ in self.built.values()), 3366)

    def test_population_or_missing_hash_fails_closed(self):
        for target, change in [(o.CASE_COUNT, {3556: 1}), (o.CASES_SHA256, {3556: None})]:
            with patch.dict(o.STATEMENT_SHA256, self.pins), patch.dict(target, change):
                with self.assertRaisesRegex(ValueError, 'frozen batch'):
                    o.build_cases(3556, self.raw[3556])

    def test_file_packet_and_projected_output_caps(self):
        count = 0
        for cases, _ in self.built.values():
            self.assertLessEqual(len(q.encoded(cases)), 8388608)
            for _, batch in q.batches(cases):
                count += 1; self.assertLessEqual(len(batch), 32)
                self.assertLessEqual(len(q.encoded(q.packet(batch))), 1100000)
                for language in ('javascript', 'python'):
                    self.assertLessEqual(o.expected_observation_bytes(batch, language), 8388608)
        self.assertEqual(count, 117)

    def test_valid_ten_digit_maximum_shape_exceeds_packet(self):
        args = [[10**9] * 100000]; o.validate(3577, args)
        with self.assertRaisesRegex(ValueError, 'packet cap'):
            list(q.batches([{'args': args, 'expected': 0, 'compare': 'return'}]))

    def test_projection_language_and_output_cap_fail_closed(self):
        with self.assertRaises(ValueError):
            o.expected_observation_bytes([], 'unknown')
        with patch.dict(o.STATEMENT_SHA256, self.pins), patch.dict(q.LIMITS, {'max_output_bytes': 1}):
            with self.assertRaisesRegex(ValueError, 'output cap'):
                o.build_cases(3556, self.raw[3556])


if __name__ == '__main__':
    unittest.main()
