"""Source-free tests for the fixed batch A oracle owner."""
from copy import deepcopy
from itertools import product
import json
from math import comb
import unittest
from unittest.mock import patch

from . import imported_qualification as q
from . import request_parallel_a_oracles as o

EXAMPLES = {
    3223: [(['abaacbcbb'], 5), (['aa'], 2)],
    3232: [([[1, 2, 3, 4, 10]], False), ([[1, 2, 3, 4, 5, 14]], True), ([[5, 5, 5, 25]], True)],
    3532: [([2, [1, 3], 1, [[0, 0], [0, 1]]], [True, False]),
           ([4, [2, 5, 6, 8], 2, [[0, 1], [0, 2], [1, 3], [2, 3]]], [False, False, True, True])],
    3583: [([[6, 3, 6]], 1), ([[0, 1, 0, 0]], 1), ([[8, 4, 2, 8, 4]], 2)],
    3612: [(['a#b%*'], 'ba'), (['z*#'], '')],
}


def fixture(pid):
    return ''.join('Input: ' + ', '.join(f'{name} = {value!r}' for name, value in zip(o.PARAMETERS[pid], args)) +
                   '\nOutput: ' + json.dumps(answer) + '\nExplanation: Synthetic public-example transcription.\n'
                   for args, answer in EXAMPLES[pid]).encode()


class ParallelAOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = {pid: fixture(pid) for pid in o.IDS}
        cls.pins = {pid: q.sha(raw) for pid, raw in cls.raw.items()}
        with patch.dict(o.STATEMENT_SHA256, cls.pins):
            cls.built = {pid: o.build_cases(pid, cls.raw[pid]) for pid in o.IDS}

    def test_exact_examples_and_result_types(self):
        for pid, examples in EXAMPLES.items():
            for args, answer in examples:
                with self.subTest(pid=pid, args=args):
                    self.assertTrue(q.exact(o.expected(pid, args), answer))

    def test_identity_and_ordered_argument_shape(self):
        for pid, args in [(True, ['a']), (3223.0, ['a']), (3215, ['a']), (3223, ('a',)),
                          (3223, []), (3223, ['a', 1]), (3532, [1, [0], 0])]:
            with self.subTest(pid=pid, args=args), self.assertRaises(ValueError):
                o.validate(pid, args)

    def test_string_domains(self):
        for pid in (3223, 3612):
            for s in ('', 'A', 'é', 'a\n', 1, None):
                with self.subTest(pid=pid, value=s), self.assertRaises(ValueError):
                    o.validate(pid, [s])
        for pid, s in [(3223, '*'), (3223, 'a' * 200001), (3612, 'a' * 21)]:
            with self.assertRaises(ValueError):
                o.validate(pid, [s])
        o.validate(3223, ['z' * 200000]); o.validate(3612, ['*#%' * 6 + '*#'])

    def test_numeric_array_domains(self):
        invalid = {3232: [[], [0], [100], [True], [1.0], [1] * 101, (1,)],
                   3583: [[], [0, 0], [0, 0, -1], [0, 0, 100001], [0, 0, False], [0, 0, 1.0], [0] * 100001]}
        for pid, arrays in invalid.items():
            for values in arrays:
                with self.subTest(pid=pid, length=len(values)), self.assertRaises(ValueError):
                    o.validate(pid, [values])
        o.validate(3232, [[99] * 100]); o.validate(3583, [[100000] * 100000])

    def test_graph_domain_rejects_malformed_and_unsorted(self):
        invalid = [[True, [0], 0, [[0, 0]]], [0, [], 0, [[0, 0]]], [2, [0], 0, [[0, 0]]],
                   [2, [1, 0], 0, [[0, 0]]], [1, [False], 0, [[0, 0]]],
                   [1, [0], False, [[0, 0]]], [1, [0], -1, [[0, 0]]],
                   [1, [0], 100001, [[0, 0]]], [1, [0], 0, []], [1, [0], 0, [[0, 1]]],
                   [1, [0], 0, [[False, 0]]], [1, [0], 0, [[0]]], [1, [0], 0, [(0, 0)]],
                   [1, [0], 0, [[0, 0]] * 100001]]
        for args in invalid:
            with self.subTest(args=str(args)[:100]), self.assertRaises(ValueError):
                o.validate(3532, args)
        o.validate(3532, [100000, [100000] * 100000, 100000, [[0, 99999]] * 100000])

    def test_reference_budgets_are_not_domain_restrictions(self):
        for pid, args in [(3223, ['a' * 13]), (3532, [13, [0] * 13, 0, [[0, 0]]]),
                          (3532, [1, [0], 0, [[0, 0]] * 145]), (3583, [[0] * 13]), (3612, ['a' * 13])]:
            o.validate(pid, args)
            with self.subTest(pid=pid), self.assertRaisesRegex(ValueError, 'budget'):
                o.expected(pid, args)

    def test_budget_rejection_before_expensive_reference(self):
        with patch.object(o, '_minimum_remaining', side_effect=AssertionError('must not run')):
            with self.assertRaisesRegex(ValueError, 'budget'):
                o.expected(3223, ['a' * 200000])

    def test_deletions_keep_center_and_need_both_sides(self):
        for s, expected in [('a', 1), ('aa', 2), ('aba', 3), ('aaa', 1), ('aaaa', 2),
                            ('abaca', 3), ('abcabcabc', 3), ('abccba', 6)]:
            self.assertEqual(o.expected(3223, [s]), expected)

    def test_digit_choices_strict_tie_and_empty_class(self):
        for values, answer in [([5, 5, 10], False), ([1], True), ([99], True), ([9, 10], True)]:
            self.assertIs(o.expected(3232, [values]), answer)

    def test_graph_reflexivity_duplicates_and_transitivity(self):
        self.assertEqual(o.expected(3532, [4, [0, 0, 2, 4], 2, [[0, 3], [1, 0], [2, 2]]]), [True] * 3)
        self.assertEqual(o.expected(3532, [4, [0, 0, 2, 4], 0, [[0, 3], [1, 0], [2, 2]]]), [False, True, True])

    def test_positional_triplets_and_numeric_boundary(self):
        self.assertEqual(o.expected(3583, [[0] * 12]), comb(12, 3))
        self.assertEqual(o.expected(3583, [[100000, 50000, 100000]]), 1)
        self.assertEqual(o.expected(3583, [[50000, 100000, 50000]]), 0)

    def test_reverse_index_against_small_forward_traces(self):
        for length in range(1, 6):
            for tokens in product('ab*#%', repeat=length):
                value = ''
                for token in tokens:
                    value = value[:-1] if token == '*' else value * 2 if token == '#' else value[::-1] if token == '%' else value + token
                self.assertEqual(o.expected(3612, [''.join(tokens)]), value)

    def test_no_argument_mutation(self):
        for pid, examples in EXAMPLES.items():
            for args, _ in examples:
                before = deepcopy(args); o.expected(pid, args); self.assertEqual(args, before)

    def test_statement_identity_checked_before_example_work(self):
        with patch.object(o, 'expected', side_effect=AssertionError('must not run')):
            with self.assertRaisesRegex(ValueError, 'pinned statement'):
                o.public_examples(3223, b'not a statement')

    def test_missing_examples_and_wrong_parameter_order_fail(self):
        for raw in (b'Constraints: no examples', b'Input: values = [1]\nOutput: true\nExplanation: x'):
            with patch.dict(o.STATEMENT_SHA256, {3232: q.sha(raw)}), self.assertRaises(ValueError):
                o.public_examples(3232, raw)

    def test_boolean_output_not_numeric_equivalent(self):
        raw = self.raw[3532].replace(b'[true, false]', b'[1, 0]')
        with patch.dict(o.STATEMENT_SHA256, {3532: q.sha(raw)}), self.assertRaisesRegex(ValueError, 'disagrees'):
            o.public_examples(3532, raw)

    def test_frozen_population_and_hashes(self):
        for pid, (cases, cats) in self.built.items():
            self.assertEqual(len(cases), o.CASE_COUNT[pid]); self.assertEqual(len(cats), len(cases))
            self.assertEqual(q.sha(q.encoded(cases)), o.CASES_SHA256[pid])
        self.assertEqual(sum(len(c) for c, _ in self.built.values()), 2553)
        self.assertEqual(sum(len({q.encoded(x['args']) for x in c}) for c, _ in self.built.values()), 2551)

    def test_missing_hash_and_changed_population_fail_closed(self):
        for constants, change in [(o.CASES_SHA256, {3232: None}), (o.CASE_COUNT, {3232: 1})]:
            with patch.dict(o.STATEMENT_SHA256, self.pins), patch.dict(constants, change):
                with self.assertRaisesRegex(ValueError, 'frozen batch'):
                    o.build_cases(3232, self.raw[3232])

    def test_unchanged_file_packet_and_output_caps(self):
        total_batches = 0
        for cases, _ in self.built.values():
            self.assertLessEqual(len(q.encoded(cases)), 8 * 1024**2)
            for _, batch in q.batches(cases):
                total_batches += 1; self.assertLessEqual(len(batch), 32)
                self.assertLessEqual(len(q.encoded(q.packet(batch))), 1100000)
                for language in ('python', 'javascript'):
                    self.assertLessEqual(o.expected_observation_bytes(batch, language), 8 * 1024**2)
        self.assertEqual(total_batches, 87)

    def test_fitting_maximum_output_retained(self):
        cases, _ = self.built[3612]
        self.assertEqual(max(len(c['expected']) for c in cases), 524288)
        self.assertEqual(sum(len(c['expected']) == 524288 for c in cases), 2)

    def test_valid_dense_maximum_graph_exceeds_transport_not_domain(self):
        args = [100000, [100000] * 100000, 100000, [[99999, 99999]] * 100000]
        o.validate(3532, args)
        case = {'args': args, 'expected': [True] * 100000, 'compare': 'return'}
        with self.assertRaisesRegex(ValueError, 'packet cap'):
            list(q.batches([case]))

    def test_projection_tracks_python_done_space_and_language(self):
        case = {'args': ['a'], 'expected': 'a'}
        self.assertGreater(o.expected_observation_bytes([case], 'javascript'), 0)
        with self.assertRaises(ValueError):
            o.expected_observation_bytes([case], 'unknown')

    def test_output_cap_rejection(self):
        with patch.dict(o.STATEMENT_SHA256, self.pins), patch.dict(q.LIMITS, {'max_output_bytes': 1}):
            with self.assertRaisesRegex(ValueError, 'output cap'):
                o.build_cases(3232, self.raw[3232])


if __name__ == '__main__':
    unittest.main()
