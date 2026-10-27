"""Synthetic focused tests; no candidate, statement file or historical case reads."""
from copy import deepcopy
from itertools import permutations
import json
import unittest
from unittest.mock import patch

from . import imported_qualification as q
from . import request_parallel_d_oracles as o

EXAMPLES = {
    3513: [([[1, 2]], 2), ([[3, 1, 2]], 4)],
    3522: [([['jump', 'add', 'add', 'jump', 'add', 'jump'], [2, 1, 3, 1, -2, -3]], 1),
           ([['jump', 'add', 'add'], [3, 1, 1]], 0), ([['jump'], [0]], 0)],
    3527: [([[['good', 'ok', 'good', 'ok'], ['ok', 'bad', 'good', 'ok', 'ok'], ['good'], ['bad']]], 'good'),
           ([[['good', 'ok', 'good'], ['ok', 'bad'], ['bad', 'notsure'], ['great', 'good']]], 'bad')],
    3546: [([[[1, 4], [2, 3]]], True), ([[[1, 3], [2, 4]]], False)],
    3572: [([[1, 2, 1, 3, 2], [5, 3, 4, 6, 2]], 14), ([[1, 2, 1, 2], [4, 5, 6, 7]], -1)],
}


def fixture(pid):
    return ''.join('Input: ' + ', '.join(f'{name} = {value!r}' for name, value in zip(o.PARAMETERS[pid], args)) +
                   '\nOutput: ' + json.dumps(answer) + '\nExplanation: Synthetic example transcription.\n'
                   for args, answer in EXAMPLES[pid]).encode()


class ParallelDTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = {pid: fixture(pid) for pid in o.IDS}
        cls.pins = {pid: q.sha(raw) for pid, raw in cls.raw.items()}
        with patch.dict(o.STATEMENT_SHA256, cls.pins):
            cls.built = {pid: o.build_cases(pid, raw) for pid, raw in cls.raw.items()}

    def reject(self, pid, arguments):
        for args in arguments:
            with self.subTest(pid=pid, args=str(args)[:100]), self.assertRaises(ValueError):
                o.validate(pid, args)

    def test_fixed_identity_and_ordered_arguments(self):
        for pid, args in [(True, [[1]]), (3513.0, [[1]]), (0, [[1]]), (3513, ([1],)),
                          (3513, []), (3513, [[1], [1]]), (3522, [['add']])]:
            with self.assertRaises(ValueError):
                o.validate(pid, args)

    def test_permutation_is_exact_one_through_length(self):
        self.reject(3513, [[[]], [[1, 1]], [[2, 3]], [[0, 1]], [[True]], [[1.0]], [(1,)], [[1] * 100001]])
        o.validate(3513, [list(range(100000, 0, -1))])

    def test_instruction_domain_and_equal_lengths(self):
        self.reject(3522, [[[], []], [['add'], []], [['jump'], [0, 1]],
                           [['ADD'], [1]], [['jump '], [1]], [[True], [1]],
                           [('add',), [1]], [['add'], [True]], [['add'], [1.0]],
                           [['add'], [100001]], [['jump'], [-100001]],
                           [['add'] * 100001, [0] * 100001]])
        o.validate(3522, [['add'] * 100000, [-100000] * 100000])

    def test_response_domain_has_no_hidden_total_item_cap(self):
        o.validate(3527, [[['abcdefghij'] * 1000 for _ in range(1000)]])
        self.reject(3527, [[[]], [[[]]], [[['a']] * 1001], [[['a'] * 1001]],
                           [[['']]], [[['a' * 11]]], [[['A']]], [[['é']]], [[['a\na']]],
                           [[['a', 1]]], [[('a',)]], [(('a',),)]])

    def test_grid_rectangular_area_and_positive_values(self):
        self.reject(3546, [[[]], [[[]]], [[[1]]], [[[1], [1, 2]]],
                           [[[0, 1]]], [[[-1, 1]]], [[[True, 1]]], [[[1.0, 1]]],
                           [[[100001, 1]]], [[(1, 1)]], [[[1] * 100001]],
                           [[[1] * 1000 for _ in range(101)]]])
        o.validate(3546, [[[100000] * 100000]])
        o.validate(3546, [[[100000] for _ in range(100000)]])

    def test_triplet_arrays_allow_repeated_labels_but_not_zero_weights(self):
        o.validate(3572, [[1, 1, 1], [1, 1, 1]])
        self.reject(3572, [[[1, 2], [1, 2]], [[1, 2, 3], [1, 2]],
                           [[1, 2, 3], [1, 2, 3, 4]], [[0, 1, 2], [1, 1, 1]],
                           [[1, 2, 3], [0, 1, 1]], [[1, 2, 3], [-1, 1, 1]],
                           [[1000001, 2, 3], [1, 1, 1]], [[1, 2, 3], [1, 1, 1000001]],
                           [[True, 2, 3], [1, 1, 1]], [[1, 2, 3], [1.0, 1, 1]]])

    def test_small_budgets_do_not_narrow_domain(self):
        inputs = [(3513, [list(range(1, 66))]), (3522, [['add'] * 65, [0] * 65]),
                  (3527, [[['a'] * 101]]), (3546, [[[1] * 37]]),
                  (3572, [[1] * 19, [1] * 19])]
        for pid, args in inputs:
            o.validate(pid, args)
            with self.assertRaisesRegex(ValueError, 'enumeration budget'):
                o.expected(pid, args)

    def test_large_rejection_precedes_expensive_reference(self):
        with patch.object(o, '_positional_xor_triples', side_effect=AssertionError('must not run')):
            with self.assertRaisesRegex(ValueError, 'enumeration budget'):
                o.expected(3513, [list(range(1, 100001))])

    def test_public_examples_exact_types(self):
        for pid, examples in EXAMPLES.items():
            for args, answer in examples:
                self.assertTrue(q.exact(o.expected(pid, args), answer))

    def test_xor_repeated_positions_and_permutation_orders(self):
        self.assertEqual(o.expected(3513, [[1]]), 1)
        self.assertEqual(o.expected(3513, [[2, 1]]), 2)
        for nums in permutations(range(1, 5)):
            self.assertEqual(o.expected(3513, [list(nums)]), 8)

    def test_constructive_xor_witnesses_match_small_enumeration(self):
        for n in range(1, 65):
            self.assertEqual(o._xor_span_witness_count(n), o.expected(3513, [list(range(1, n + 1))]))
        self.assertEqual(o._xor_span_witness_count(100000), 131072)
        for n in (0, 100001, True, 3.0):
            with self.assertRaises(ValueError):
                o._xor_span_witness_count(n)

    def test_instruction_revisit_is_not_executed(self):
        self.assertEqual(o.expected(3522, [['add', 'jump'], [5, -1]]), 5)
        self.assertEqual(o.expected(3522, [['jump'], [0]]), 0)
        self.assertEqual(o.expected(3522, [['jump', 'add'], [-1, 100000]]), 0)
        self.assertEqual(o.expected(3522, [['add'], [-100000]]), -100000)

    def test_response_day_membership_not_occurrence_count(self):
        self.assertEqual(o.expected(3527, [[['a'] * 10, ['b'], ['b']]]), 'b')
        self.assertEqual(o.expected(3527, [[['aa'], ['a']]]), 'a')
        self.assertEqual(o.expected(3527, [[['z', 'a'], ['z', 'a']]]), 'a')

    def test_grid_requires_nonempty_sections_and_checks_both_orientations(self):
        self.assertIs(o.expected(3546, [[[1, 1]]]), True)
        self.assertIs(o.expected(3546, [[[1, 2]]]), False)
        self.assertIs(o.expected(3546, [[[1, 1], [2, 2]]]), True)
        self.assertIs(o.expected(3546, [[[1, 3], [2, 4]]]), False)

    def test_distinct_x_not_distinct_y_and_not_three_best_occurrences(self):
        self.assertEqual(o.expected(3572, [[1, 1, 2, 3], [100, 99, 4, 5]]), 109)
        self.assertEqual(o.expected(3572, [[1, 1, 2, 2], [100, 1, 3, 4]]), -1)
        self.assertEqual(o.expected(3572, [[1, 2, 3], [1000000] * 3]), 3000000)

    def test_oracles_do_not_mutate_input_containers(self):
        for pid, examples in EXAMPLES.items():
            for args, _ in examples:
                before = deepcopy(args)
                o.expected(pid, args)
                self.assertEqual(args, before)

    def test_statement_pin_checked_before_parsing(self):
        with patch.object(o, 'expected', side_effect=AssertionError('must not run')):
            for pid, raw in ((3513, b''), (True, b''), (3513, '')):
                with self.assertRaises(ValueError):
                    o.public_examples(pid, raw)

    def test_wrong_example_parameters_or_count_fail_closed(self):
        for raw in (b'Input: values = [1]\nOutput: 1\n', b'Input: nums = [1]\nOutput: 1\n'):
            with patch.dict(o.STATEMENT_SHA256, {3513: q.sha(raw)}), self.assertRaises(ValueError):
                o.public_examples(3513, raw)

    def test_boolean_example_not_numeric_equivalent(self):
        raw = self.raw[3546].replace(b'true', b'1')
        with patch.dict(o.STATEMENT_SHA256, {3546: q.sha(raw)}), self.assertRaisesRegex(ValueError, 'disagrees'):
            o.public_examples(3546, raw)

    def test_frozen_case_populations_and_hashes(self):
        for pid, (cases, categories) in self.built.items():
            self.assertEqual(len(cases), o.CASE_COUNT[pid])
            self.assertEqual(len(categories), len(cases))
            self.assertEqual(q.sha(q.encoded(cases)), o.CASES_SHA256[pid])
        self.assertEqual(sum(len(c) for c, _ in self.built.values()), 2128)
        self.assertEqual(sum(len({q.encoded(row['args']) for row in c}) for c, _ in self.built.values()), 2123)

    def test_missing_hash_and_wrong_count_fail_closed(self):
        for constants, changed in ((o.CASE_COUNT, {3513: 1}), (o.CASES_SHA256, {3513: None})):
            with patch.dict(o.STATEMENT_SHA256, self.pins), patch.dict(constants, changed), \
                    self.assertRaisesRegex(ValueError, 'frozen case'):
                o.build_cases(3513, self.raw[3513])

    def test_retained_file_packet_and_output_caps(self):
        batches = 0
        for cases, _ in self.built.values():
            self.assertLessEqual(len(q.encoded(cases)), q.MAX_FILE)
            for _, batch in q.batches(cases):
                batches += 1
                self.assertLessEqual(len(q.encoded(q.packet(batch))), q.MAX_PACKET)
                for language in ('javascript', 'python'):
                    self.assertLessEqual(o.expected_observation_bytes(batch, language), q.LIMITS['max_output_bytes'])
        self.assertEqual(batches, 83)

    def test_valid_over_cap_shapes_are_transport_not_domain_failures(self):
        examples = [(3522, [['add'] * 100000, [100000] * 100000]),
                    (3527, [[['a'] * 1000 for _ in range(1000)]]),
                    (3572, [[1000000] * 100000, [1000000] * 100000])]
        for pid, args in examples:
            o.validate(pid, args)
            with self.assertRaisesRegex(ValueError, 'packet cap'):
                list(q.batches([{'args': args, 'expected': 0, 'compare': 'return'}]))

    def test_file_and_output_limit_failures_are_explicit(self):
        with patch.dict(o.STATEMENT_SHA256, self.pins):
            with patch.object(q, 'MAX_FILE', 1), self.assertRaisesRegex(ValueError, 'reader cap'):
                o.build_cases(3513, self.raw[3513])
            with patch.dict(q.LIMITS, {'max_output_bytes': 1}), self.assertRaisesRegex(ValueError, 'output cap'):
                o.build_cases(3513, self.raw[3513])

    def test_output_projection_language_validation(self):
        with self.assertRaises(ValueError):
            o.expected_observation_bytes([], 'other')


if __name__ == '__main__':
    unittest.main()
