"""Pure next-five definition tests; no candidate or external reference loading.

Parser fixtures reproduce the reviewed public-example values in synthetic text.
They are not official statement bytes or evidence of candidate qualification.
"""
import copy
from itertools import permutations
import json
from math import prod
import unittest
from unittest.mock import patch

from . import imported_qualification as q
from . import request_next5_oracles as oracle


EXAMPLES = {
    3514: [([[1, 3]], 2), ([[6, 7, 8, 9]], 4)],
    3528: [([[[0, 1, 2], [1, 2, 3]]], [1, 2, 6]),
           ([[[0, 1, 2], [0, 2, 3], [1, 3, 4], [1, 4, 5], [2, 5, 2], [4, 6, 3], [5, 7, 4]]],
            [1, 2, 3, 8, 10, 6, 30, 24])],
    3566: [([[3, 1, 6, 8, 4], 24], True), ([[2, 5, 3, 7], 15], False)],
    3578: [([[9, 4, 1, 3, 7], 4], 6), ([[3, 3, 4], 0], 2)],
    3607: [([5, [[1, 2], [2, 3], [3, 4], [4, 5]],
             [[1, 3], [2, 1], [1, 1], [2, 2], [1, 2]]], [3, 2, 3]),
           ([3, [], [[1, 1], [2, 1], [1, 1]]], [1, -1])],
}


def fixture(pid):
    return '\n'.join(
        'Input: ' + ', '.join(f'{name} = {value!r}' for name, value in zip(oracle.PARAMETERS[pid], args))
        + '\nOutput: ' + json.dumps(answer) + '\nExplanation: synthetic parser fixture.'
        for args, answer in EXAMPLES[pid]).encode()


class DomainTests(unittest.TestCase):
    def test_fixed_identity_and_ordered_argument_shape(self):
        invalid = [(True, [[1]]), ('3514', [[1]]), (1, [[1]]), (3514, ([1],)),
                   (3514, []), (3514, [[1], 0]), (3566, [[1, 2, 3]]),
                   (3607, [1, []]), (3607, [1, [], [[1, 1]], 0])]
        for pid, args in invalid:
            with self.subTest(pid=pid, args=args), self.assertRaises(ValueError):
                oracle.validate(pid, args)

    def test_array_domains_are_exact_integers_and_inclusive_bounds(self):
        rows = [(3514, [], [[], [0], [1501], [True], [1.0], (1,), [1] * 1501]),
                (3566, [1], [[], [1, 2], [1, 2, 101], [1, True, 3], [1, 2.0, 3],
                             (1, 2, 3), [1, 2, 2], list(range(1, 14))]),
                (3578, [0], [[], [1], [0, 1], [1, 10**9 + 1], [True, 2], [1, 2.0],
                             (1, 2), [1] * 50001])]
        for pid, rest, invalid in rows:
            for values in invalid:
                with self.subTest(pid=pid, kind=type(values)), self.assertRaises(ValueError):
                    oracle.validate(pid, [values, *rest])
        oracle.validate(3514, [[1] * 1499 + [1500]])
        oracle.validate(3514, [[7, 7, 7]])  # Repeated values are allowed here.
        oracle.validate(3566, [list(range(89, 101)), 10**15])
        oracle.validate(3578, [[1] * 49999 + [10**9], 10**9])

    def test_target_and_threshold_do_not_accept_bool_float_or_out_of_range(self):
        for pid, values, invalid in [(3566, [1, 2, 3], [0, 10**15 + 1, True, 6.0, '6']),
                                     (3578, [1, 2], [-1, 10**9 + 1, False, 0.0, '0'])]:
            for value in invalid:
                with self.subTest(pid=pid, value=value), self.assertRaises(ValueError):
                    oracle.validate(pid, [values, value])

    def test_conversion_shape_endpoints_and_factors(self):
        invalid = [[], [[0, 0, 1]], [[0, 2, 1]], [[True, 1, 2]], [[0, 1.0, 2]],
                   [[0, 1, True]], [[0, 1, 1.0]], [[0, 1, 0]], [[0, 1, 10**9 + 1]],
                   [(0, 1, 1)], [[0, 1]], [[0, 1, 1, 1]], [[0, 1, 1]] * 100000]
        for edges in invalid:
            with self.subTest(edge_count=len(edges)), self.assertRaises(ValueError):
                oracle.validate(3528, [edges])
        oracle.validate(3528, [[[0, 1, 1]]])
        oracle.validate(3528, [[[0, 1, 10**9]]])

    def test_conversion_root_indegree_uniqueness_and_reachability(self):
        invalid = [
            [[1, 0, 2]],  # Wrong root orientation.
            [[0, 1, 2], [0, 1, 3]],  # Duplicate incoming edge, absent vertex.
            [[0, 1, 1], [2, 3, 1], [3, 2, 1]],  # Disconnected directed cycle.
            [[0, 1, 1], [1, 2, 1], [2, 0, 1]],  # Root has an incoming edge.
        ]
        for edges in invalid:
            with self.subTest(edges=edges), self.assertRaises(ValueError):
                oracle.validate(3528, [edges])
        oracle.validate(3528, [[[3, 1, 2], [0, 3, 5], [3, 2, 7]]])

    def test_station_cable_query_domains_and_parallel_cables(self):
        valid = [3, [[1, 2], [1, 2], [2, 1]], [[2, 1], [2, 1], [1, 1]]]
        oracle.validate(3607, valid)
        oracle.validate(3607, [1, [], [[2, 1]]])
        invalid = [[True, [], [[1, 1]]], [0, [], [[1, 1]]], [100001, [], [[1, 1]]],
                   [1.0, [], [[1, 1]]], [1, [[1, 1]], [[1, 1]]],
                   [2, [[1, 2], [1, 2]], [[1, 1]]],  # Stated cable-count cap still applies.
                   [3, [[0, 2]], [[1, 1]]], [3, [[1, 4]], [[1, 1]]],
                   [3, [[1, True]], [[1, 1]]], [3, [(1, 2)], [[1, 1]]],
                   [3, [[1, 2, 3]], [[1, 1]]], [3, [], []],
                   [3, [], [[0, 1]]], [3, [], [[3, 1]]], [3, [], [[True, 1]]],
                   [3, [], [[1.0, 1]]], [3, [], [[1, 0]]], [3, [], [[1, 4]]],
                   [3, [], [[1, False]]], [3, [], [(1, 1)]], [3, [], [[1, 1, 1]]],
                   [1, [], [[1, 1]] * 200001]]
        for args in invalid:
            with self.subTest(stations=args[0], queries=len(args[-1])), self.assertRaises(ValueError):
                oracle.validate(3607, args)

    def test_enumeration_budget_precedes_combinatorial_helpers(self):
        rows = [(3514, [[1] * 15], '_xor_triples'),
                (3528, [[[i, i + 1, 1] for i in range(10)]], '_directed_path_products'),
                (3578, [[1] * 13, 0], '_cut_partitions'),
                (3607, [9, [], [[1, 1]]], '_search_each_maintenance'),
                (3607, [2, [], [[1, 1]] * 17], '_search_each_maintenance')]
        for pid, args, helper in rows:
            oracle.validate(pid, args)
            with self.subTest(pid=pid), patch.object(oracle, helper) as work:
                with self.assertRaisesRegex(ValueError, 'budget'): oracle.expected(pid, args)
                work.assert_not_called()
        # The whole declared 3566 length domain fits the fixed subset budget;
        # lengths beyond that domain must fail before its exponential helper.
        with patch.object(oracle, '_complementary_products') as work:
            with self.assertRaises(ValueError): oracle.expected(3566, [list(range(1, 14)), 1])
            work.assert_not_called()


class DefinitionOracleTests(unittest.TestCase):
    def test_public_examples_exact_result_types_and_no_mutation(self):
        for pid, examples in EXAMPLES.items():
            for args, answer in examples:
                before = copy.deepcopy(args)
                with self.subTest(pid=pid):
                    result = oracle.expected(pid, args)
                    self.assertTrue(q.exact(result, answer))
                    self.assertIs(type(result), type(answer))
                    self.assertEqual(args, before)
                    if type(result) is list:
                        self.assertTrue(all(type(value) is int for value in result))
                        self.assertTrue(all(result is not value for value in args))

    def test_xor_repeated_positions_values_and_high_bits(self):
        for values, expected in [([7], 1), ([1, 2], 2), ([1, 1, 2], 2),
                                 ([1, 2, 4], 4), ([1024, 1500], 2)]:
            self.assertEqual(oracle.expected(3514, [values]), expected)

    def test_conversions_allow_arbitrary_labels_and_edge_order(self):
        edges = [[3, 1, 2], [0, 3, 5], [3, 2, 7]]
        for ordered in permutations(edges):
            args = [copy.deepcopy(list(ordered))]; before = copy.deepcopy(args)
            self.assertEqual(oracle.expected(3528, args), [1, 10, 35, 5])
            self.assertEqual(args, before)

    def test_high_factor_paths_use_exact_products_before_modulo(self):
        factor = 10**9
        self.assertGreater(factor**3, 2**53)
        edges = [[2, 1, factor], [0, 3, factor], [3, 2, factor]]
        answer = [1, factor**3 % oracle.MOD, factor**2 % oracle.MOD, factor]
        self.assertEqual(oracle.expected(3528, [edges]), answer)
        self.assertEqual(answer, [1, 999999664, 49, 1000000000])

    def test_subset_products_require_nonempty_disjoint_full_coverage(self):
        rows = [([2, 3, 6], 6, True), ([1, 2, 3, 6], 6, True),
                ([1, 2, 3], 6, False), ([1, 2, 4], 2, False),
                ([1, 2, 6], 12, False), ([1, 2, 3], 1, False)]
        for values, target, answer in rows:
            result = oracle.expected(3566, [values, target])
            self.assertIs(result, answer)
        with self.assertRaises(ValueError): oracle.expected(3566, [[2, 2, 3], 6])

    def test_twelve_number_exact_complementary_products(self):
        left = [99, 80, 88, 63, 84, 60]
        right = [90, 96, 72, 77, 70, 66]
        target = 221298739200
        values = left + right
        self.assertEqual(len(set(values)), 12)
        self.assertEqual(prod(left), target); self.assertEqual(prod(right), target)
        self.assertGreater(prod(values), 2**53)
        for order in (values, values[::-1], values[::2] + values[1::2]):
            for candidate, answer in [(target, True), (target - 1, False), (target + 1, False), (10**15, False)]:
                with self.subTest(target=candidate):
                    result = oracle.expected(3566, [order, candidate])
                    self.assertIs(result, answer)

    def test_exact_complement_products_do_not_use_rounded_total_product(self):
        values = [68, 76, 78, 80, 84, 85, 88, 90, 91, 95, 98, 99]
        target = 391091500800
        left = [68, 78, 80, 95, 98, 99]
        right = [76, 84, 85, 88, 90, 91]
        self.assertEqual(sorted(left + right), values)
        self.assertEqual(prod(left), target); self.assertEqual(prod(right), target)
        self.assertEqual(prod(values), target**2)
        # A binary64 total-product precheck can disagree despite exact witnesses.
        # This is pure numeric arithmetic, not candidate or JavaScript execution.
        self.assertNotEqual(prod(map(float, values)), float(target) * float(target))
        self.assertIs(oracle.expected(3566, [values, target]), True)

    def test_contiguous_cut_positions_and_inclusive_threshold(self):
        for values, k, answer in [([1, 2], 0, 1), ([1, 2], 1, 2),
                                  ([1, 2, 3], 1, 3), ([1, 2, 3], 2, 4),
                                  ([3, 3, 4], 0, 2), ([1, 10**9], 10**9 - 1, 2),
                                  ([1, 10**9], 10**9 - 2, 1)]:
            self.assertEqual(oracle.expected(3578, [values, k]), answer)

    def test_offline_bridges_and_repeated_shutdown_retain_connectivity(self):
        args = [4, [[1, 2], [2, 3], [3, 4]],
                [[2, 2], [1, 3], [2, 1], [1, 1], [2, 3], [1, 2],
                 [2, 4], [2, 4], [1, 3]]]
        before = copy.deepcopy(args)
        self.assertEqual(oracle.expected(3607, args), [3, 3, 4, -1])
        self.assertEqual(args, before)

    def test_online_station_is_self_not_component_minimum(self):
        args = [3, [[1, 2], [2, 3]], [[1, 3], [2, 3], [1, 3], [2, 1], [1, 3], [1, 2]]]
        self.assertEqual(oracle.expected(3607, args), [3, 1, 2, 2])

    def test_parallel_cables_disconnected_and_all_offline(self):
        args = [3, [[1, 2], [1, 2], [2, 1]],
                [[2, 1], [2, 1], [1, 1], [2, 2], [1, 1], [1, 3]]]
        self.assertEqual(oracle.expected(3607, args), [2, -1, 3])
        self.assertEqual(oracle.expected(3607, [1, [], [[2, 1], [1, 1]]]), [-1])
        self.assertEqual(oracle.expected(3607, [3, [], [[2, 3], [1, 3], [1, 1]]]), [-1, 1])

    def test_empty_output_and_fresh_per_invocation_state(self):
        args = [1, [], [[2, 1], [2, 1]]]
        before = copy.deepcopy(args)
        result = oracle.expected(3607, args)
        self.assertEqual(result, []); self.assertIs(type(result), list)
        result.append(99)
        self.assertEqual(oracle.expected(3607, args), [])
        self.assertEqual(oracle.expected(3607, [1, [], [[1, 1]]]), [1])
        self.assertEqual(args, before)


class PublicExampleParserTests(unittest.TestCase):
    def test_synthetic_text_preserves_exact_reviewed_example_values(self):
        for pid in oracle.IDS:
            raw = fixture(pid)
            with self.subTest(pid=pid), patch.dict(oracle.STATEMENT_SHA256, {pid: q.sha(raw)}):
                actual = oracle.public_examples(pid, raw)
            self.assertEqual(actual, [{'args': args, 'expected': answer, 'compare': 'return'} for args, answer in EXAMPLES[pid]])

    def test_statement_pin_rejected_before_oracle_work(self):
        for pid, raw in [(3514, fixture(3514)), (3514, 'text'), (True, b'text'), (9999, b'text')]:
            with self.subTest(pid=pid), patch.object(oracle, 'expected') as work:
                with self.assertRaisesRegex(ValueError, 'pin'): oracle.public_examples(pid, raw)
                work.assert_not_called()

    def test_wrong_names_order_count_value_and_return_types(self):
        rows = []
        raw = fixture(3566)
        rows += [(3566, raw.replace(b'nums =', b'values =')),
                 (3566, b'Input:' + raw.split(b'Input:')[1]),
                 (3566, raw.replace(b'Output: true', b'Output: false')),
                 (3566, raw.replace(b'Output: true', b'Output: 1'))]
        raw = fixture(3578)
        rows += [(3578, raw.replace(b'Output: 6', b'Output: 6.0'))]
        raw = fixture(3528)
        rows += [(3528, raw.replace(b'Output: [1, 2, 6]', b'Output: [1, 2.0, 6]'))]
        # Reversing valid parameter names is not an alternate call interface.
        raw = fixture(3566).replace(b'nums = [3, 1, 6, 8, 4], target = 24',
                                   b'target = 24, nums = [3, 1, 6, 8, 4]')
        rows.append((3566, raw))
        for pid, raw in rows:
            with self.subTest(pid=pid), patch.dict(oracle.STATEMENT_SHA256, {pid: q.sha(raw)}):
                with self.assertRaises(ValueError): oracle.public_examples(pid, raw)


class FrozenCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if set(oracle.CASE_COUNT) != set(oracle.IDS) or set(oracle.CASES_SHA256) != set(oracle.IDS):
            raise AssertionError('All five reviewed count/hash constants must be frozen before these checks')
        cls.populations = {}
        for pid in oracle.IDS:
            raw = fixture(pid)
            with patch.dict(oracle.STATEMENT_SHA256, {pid: q.sha(raw)}):
                cls.populations[pid] = oracle.build_cases(pid, raw)

    def test_counts_hashes_categories_and_domains(self):
        for pid, (cases, categories) in self.populations.items():
            with self.subTest(pid=pid):
                self.assertEqual(len(cases), oracle.CASE_COUNT[pid])
                self.assertEqual(q.sha(q.encoded(cases)), oracle.CASES_SHA256[pid])
                self.assertEqual(len(categories), len(cases))
                self.assertEqual(categories.count('pinned_public_example'), 2)
                if pid == 3566:
                    diagnostic = [[68, 76, 78, 80, 84, 85, 88, 90, 91, 95, 98, 99], 391091500800]
                    matches = [case for case in cases if case['args'] == diagnostic]
                    self.assertEqual(len(matches), 1)
                    self.assertIs(matches[0]['expected'], True)
                self.assertTrue(any(category.startswith('analytic_') or category == 'high_product_above_safe_number'
                                    for category in categories))
                for case in cases:
                    self.assertEqual(set(case), {'args', 'expected', 'compare'})
                    self.assertEqual(case['compare'], 'return')
                    oracle.validate(pid, case['args'])
                    answer = case['expected']
                    if pid == 3566:
                        self.assertIs(type(answer), bool)
                    elif pid in (3528, 3607):
                        self.assertIs(type(answer), list)
                        self.assertTrue(all(type(value) is int for value in answer))
                    else:
                        self.assertIs(type(answer), int)

    def test_file_and_packet_caps_preserve_every_generated_case(self):
        for pid, (cases, _) in self.populations.items():
            with self.subTest(pid=pid):
                self.assertLessEqual(len(q.encoded(cases)), q.MAX_FILE)
                groups = list(q.batches(cases))
                self.assertEqual(sum(len(batch) for _, batch in groups), len(cases))
                for _, batch in groups:
                    self.assertLessEqual(len(batch), 32)
                    self.assertLessEqual(len(q.encoded(q.packet(batch))), q.MAX_PACKET)

    def test_missing_count_or_hash_pin_fails_closed(self):
        raw = fixture(3514)
        for name in ('CASE_COUNT', 'CASES_SHA256'):
            with self.subTest(pin=name), patch.dict(getattr(oracle, name), {}, clear=True), \
                    patch.dict(oracle.STATEMENT_SHA256, {3514: q.sha(raw)}):
                with self.assertRaises((KeyError, ValueError)):
                    oracle.build_cases(3514, raw)

    def test_changed_or_missing_case_cannot_retain_frozen_hash(self):
        examples = copy.deepcopy(self.populations[3514][0][:2])
        changed = copy.deepcopy(examples); changed[0]['expected'] += 1
        for altered in (changed, examples[:1]):
            with patch.object(oracle, 'public_examples', return_value=altered):
                with self.assertRaisesRegex(ValueError, 'frozen'): oracle.build_cases(3514, b'synthetic mocked parser')


class DeclaredDomainTransportTests(unittest.TestCase):
    def test_valid_full_conversion_tree_exceeds_only_unchanged_packet_cap(self):
        # Shortest decimal root-zero star: validity must not be narrowed to fit.
        args = [[[0, i, 1] for i in range(1, 100000)]]
        oracle.validate(3528, args)
        self.assertGreater(len(q.encoded(q.packet([{'args': args}]))), q.MAX_PACKET)
        with self.assertRaisesRegex(ValueError, 'packet cap'):
            list(q.batches([{'args': args, 'expected': [1] * 100000, 'compare': 'return'}]))

    def test_valid_full_query_count_exceeds_only_unchanged_packet_cap(self):
        args = [1, [], [[1, 1]] * 200000]
        oracle.validate(3607, args)
        self.assertGreater(len(q.encoded(q.packet([{'args': args}]))), q.MAX_PACKET)
        with self.assertRaisesRegex(ValueError, 'packet cap'):
            list(q.batches([{'args': args, 'expected': [1] * 200000, 'compare': 'return'}]))


if __name__ == '__main__':
    unittest.main()
