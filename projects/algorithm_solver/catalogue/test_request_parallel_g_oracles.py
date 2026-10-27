"""Focused source-free G domain, reference and byte-freeze regressions."""
import copy
from itertools import product
import unittest
from unittest.mock import patch

from . import request_parallel_g_oracles as o
from . import imported_qualification as q


class GOraclesTests(unittest.TestCase):
    def rejected(self, pid, values):
        for args in values:
            with self.subTest(pid=pid, args=str(args)[:80]), self.assertRaises(ValueError):
                o.validate(pid, args)

    def test_fixed_ids_and_argument_order(self):
        for pid, args in [(True, ['a']), (3231, [[1]]), ('3561', ['a']), (3561, ('a',)), (3561, []), (3561, ['a', 0])]:
            with self.assertRaises(ValueError):
                o.validate(pid, args)

    def test_query_full_domain_boundaries(self):
        o.validate(3525, [[1]*100000, 5, [[99999, 10**9, 99999, 4]]*20000])
        o.validate(3525, [[10**9], 1, [[0, 1, 0, 0]]])

    def test_query_invalid_values_and_rows(self):
        self.rejected(3525, [[[], 1, [[0, 1, 0, 0]]], [[True], 1, [[0, 1, 0, 0]]], [[0], 1, [[0, 1, 0, 0]]],
                             [[10**9+1], 1, [[0, 1, 0, 0]]], [[1], 0, [[0, 1, 0, 0]]], [[1], 6, [[0, 1, 0, 0]]],
                             [[1], True, [[0, 1, 0, 0]]], [[1], 1, []], [[1], 1, [[0, 1, 0]]], [[1], 1, [(0, 1, 0, 0)]],
                             [[1], 1, [[1, 1, 0, 0]]], [[1], 1, [[0, 0, 0, 0]]], [[1], 1, [[0, 1, -1, 0]]],
                             [[1], 1, [[0, 1, 0, 1]]], [[1], 1, [[False, 1, 0, 0]]], [[1], 1, [[0, 1, 0, 0]]*20001]])

    def test_query_persistence_and_temporary_prefix(self):
        args = [[1, 2, 3], 3, [[0, 2, 1, 2], [2, 1, 0, 1], [0, 1, 2, 1]]]
        before = copy.deepcopy(args)
        self.assertEqual(o.expected(3525, args), [1, 2, 1])
        self.assertEqual(args, before)

    def test_query_modulus_one_and_large_exact_product(self):
        self.assertEqual(o.expected(3525, [[10**9]*16, 1, [[0, 1, 0, 0], [0, 1, 15, 0]]]), [16, 1])
        self.assertEqual(o.expected(3525, [[10**9-1]*16, 5, [[0, 10**9-1, 0, 1]]]), [8])

    def test_grid_full_domain_and_blocked_goal(self):
        for matrix in [['.'], ['A'], ['.#'], ['.'*1000]*1000, ['A']*1000]:
            o.validate(3552, [matrix])
        self.assertEqual(o.expected(3552, [['.#']]), -1)

    def test_grid_rejects_domain_not_just_budget(self):
        self.rejected(3552, [[[]], [['']], [['#']], [['..', '.']], [['a']], [['é']], [['.']*1001], [['.'*1001]], [[['.']]]])

    def test_grid_start_portal_and_zero_distance(self):
        self.assertEqual(o.expected(3552, [['A..', '.A.', '...']]), 2)
        self.assertEqual(o.expected(3552, [['A#A']]), 0)
        self.assertEqual(o.expected(3552, [['A']]), 0)

    def test_grid_optional_portals_and_multiple_letters(self):
        self.assertEqual(o.expected(3552, [['AB', 'BA']]), 0)
        self.assertEqual(o.expected(3552, [['.#.', '.#.', '...']]), 4)
        self.assertEqual(o.expected(3552, [['.#', '#.']]), -1)

    def test_deletion_examples_and_leftmost_requirement(self):
        for s, want in [('abc', 'c'), ('adcb', ''), ('zadb', 'db'), ('abcd', ''), ('bca', 'a')]:
            self.assertEqual(o.expected(3561, [s]), want)

    def test_circular_adjacency_both_directions(self):
        self.assertEqual(o.expected(3561, ['za']), '')
        self.assertEqual(o.expected(3561, ['az']), '')
        self.assertEqual(o.expected(3561, ['ac']), 'ac')

    def test_string_full_domain_and_rejections(self):
        o.validate(3561, ['z'*100000])
        self.rejected(3561, [[''], ['a'*100001], ['A'], ['é'], ['a b'], [True]])

    def test_doubling_at_most_once_and_at_most_k(self):
        self.assertEqual(o.expected(3574, [[2, 4], 1]), 8)
        self.assertEqual(o.expected(3574, [[3, 5, 7], 2]), 14)
        self.assertEqual(o.expected(3574, [[5, 5, 5], 1]), 15)
        self.assertEqual(o.expected(3574, [[10**9], 1]), 2*10**9)

    def test_doubling_full_domain_and_rejections(self):
        o.validate(3574, [[10**9]*1500, 1500])
        self.rejected(3574, [[[], 1], [[0], 1], [[True], 1], [[10**9+1], 1], [[1], 0], [[1], 2], [[1], True], [[1]*1501, 1]])

    def test_doubling_uniform_analytic_formula_on_small_exhaustive(self):
        for n in range(1, 7):
            for k in range(1, n+1):
                for value in (1, 3, 10**9):
                    self.assertEqual(o.expected(3574, [[value]*n, k]), value*max(n, 2*k))

    def test_xor_exactly_k_nonempty_intervals(self):
        self.assertEqual(o.expected(3599, [[1, 2, 3], 2]), 1)
        self.assertEqual(o.expected(3599, [[2, 3, 3, 2], 3]), 2)
        self.assertEqual(o.expected(3599, [[1, 1, 2, 3, 1], 2]), 0)
        self.assertEqual(o.expected(3599, [[1, 1], 2]), 1)

    def test_xor_full_domain_and_rejections(self):
        o.validate(3599, [[10**9]*250, 250])
        self.rejected(3599, [[[], 1], [[0], 1], [[10**9+1], 1], [[True], 1], [[1], 0], [[1], 2], [[1], True], [[1]*251, 1]])

    def test_xor_constant_analytic_condition(self):
        for n in range(1, 10):
            for k in range(1, n+1):
                want = 0 if n % 2 == 0 and n >= 2*k else 7
                self.assertEqual(o.expected(3599, [[7]*n, k]), want)

    def test_reference_budget_not_domain(self):
        probes = [(3525, [[1]*17, 1, [[0, 1, 0, 0]]]), (3525, [[1], 1, [[0, 1, 0, 0]]*161]),
                  (3552, [['.'*7]*6]), (3552, [['ABCD']]), (3561, ['a'*65]), (3574, [[1]*9, 1]), (3599, [[1]*13, 1])]
        for pid, args in probes:
            o.validate(pid, args)
            with self.assertRaisesRegex(ValueError, 'budget'):
                o.expected(pid, args)

    def test_references_preserve_all_input_shapes(self):
        for pid, args in [(3525, [[1, 2], 2, [[1, 1, 0, 1]]]), (3552, [['A.', '.A']]),
                          (3561, ['abc']), (3574, [[2, 4], 1]), (3599, [[1, 2, 3], 2])]:
            before = copy.deepcopy(args)
            o.expected(pid, args)
            self.assertEqual(args, before)

    def test_pinned_statement_required(self):
        for pid in o.IDS:
            with self.assertRaises(ValueError):
                o.build_cases(pid, b'unpinned content')
        with self.assertRaises(ValueError):
            o.public_examples(3231, b'')

    def test_public_example_parser_and_wrong_output(self):
        raw = b'Input: nums = [2,4], k = 1\n\nOutput: 8\n'
        with patch.dict(o.STATEMENT_SHA256, {3574: q.sha(raw)}), patch.dict(o.EXAMPLE_COUNT, {3574: 1}):
            self.assertEqual(o.public_examples(3574, raw)[0]['expected'], 8)
        wrong = raw.replace(b'Output: 8', b'Output: 9')
        with patch.dict(o.STATEMENT_SHA256, {3574: q.sha(wrong)}), patch.dict(o.EXAMPLE_COUNT, {3574: 1}), self.assertRaises(ValueError):
            o.public_examples(3574, wrong)

    def test_fixed_population_hash_and_count_fail_closed(self):
        cases = [{'args': ['a'], 'expected': 'a', 'compare': 'return'}]
        with patch.object(o, '_generate_cases', return_value=(cases, ['synthetic'])), self.assertRaises(ValueError):
            o.build_cases(3561, b'')
        with patch.object(o, '_generate_cases', return_value=(cases, ['synthetic'])), patch.dict(o.CASE_COUNT, {3561: 1}), patch.dict(o.CASES_SHA256, {3561: q.sha(q.encoded(cases))}):
            self.assertEqual(o.build_cases(3561, b'')[0], cases)

    def test_valid_but_over_cap_query_shape_is_rejected_not_truncated(self):
        args = [[10**9]*100000, 5, [[99999, 10**9, 99999, 4]]*20000]
        o.validate(3525, args)
        with self.assertRaisesRegex(ValueError, 'packet cap'):
            list(q.batches([{'args': args, 'expected': [0]*20000, 'compare': 'return'}]))

    def test_output_projection_and_language_rejection(self):
        case = {'args': ['abc'], 'expected': 'c', 'compare': 'return'}
        for lang in ('javascript', 'python'):
            self.assertGreater(o.expected_observation_bytes([case], lang), len(q.encoded(case)))
        with self.assertRaises(ValueError):
            o.expected_observation_bytes([case], 'ruby')


if __name__ == '__main__':
    unittest.main()
