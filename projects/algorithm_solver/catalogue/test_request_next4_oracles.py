"""Focused pure-oracle/domain tests; never load or execute a candidate."""
import copy
import unittest
from unittest.mock import patch

from catalogue import imported_qualification as q
from catalogue import request_next4_oracles as oracle


EXAMPLES = {
    3228: [(['1001101'], 4), (['00111'], 0)],
    3523: [([[4, 2, 5, 3, 5]], 3), ([[1, 2, 3]], 3)],
    3558: [([[[1, 2]]], 1), ([[[1, 2], [1, 3], [3, 4], [3, 5]]], 2)],
    3597: [(['abbccccd'], ['a', 'b', 'bc', 'c', 'cc', 'd']), (['aaaa'], ['a', 'aa'])],
}


def fixture(pid):
    name = oracle.PARAMETERS[pid][0]
    return '\n'.join(
        f'Input: {name} = {args[0]!r}\nOutput: {answer!r}\nExplanation: synthetic parser fixture.'
        for args, answer in EXAMPLES[pid]).encode()


class DomainTests(unittest.TestCase):
    def test_problem_and_argument_shape(self):
        for pid, args in [(True, ['0']), ('3228', ['0']), (0, ['0']),
                          (3228, ('0',)), (3228, []), (3228, ['0', '1'])]:
            with self.subTest(pid=pid, args=args), self.assertRaises(ValueError):
                oracle.validate(pid, args)

    def test_string_ascii_and_length(self):
        for pid, values in [(3228, ['', '2', '01a', '\u0661', True, ['0'], '0' * 100001]),
                            (3597, ['', 'A', 'a0', '\u00e9', True, ['a'], 'a' * 100001])]:
            for value in values:
                with self.subTest(pid=pid, kind=type(value)), self.assertRaises(ValueError):
                    oracle.validate(pid, [value])
        oracle.validate(3228, ['01' * 50000])
        oracle.validate(3597, ['z' * 100000])

    def test_array_domain(self):
        for values in [[], [0], [200001], [True], [1.0], (1,), [1] * 200001]:
            with self.subTest(kind=type(values)), self.assertRaises(ValueError):
                oracle.validate(3523, [values])
        oracle.validate(3523, [[1, 200000]])
        oracle.validate(3523, [[1] * 200000])

    def test_tree_domain(self):
        invalid = [[], [[1, 1]], [[1, 3]], [[True, 2]], [[1.0, 2]], [(1, 2)],
                   [[1]], [[1, 2, 3]], [[1, 2], [2, 1]],
                   [[1, 2], [2, 3], [3, 1]], [[1, 2]] * 100000]
        for edges in invalid:
            with self.subTest(edge_count=len(edges)), self.assertRaises(ValueError):
                oracle.validate(3558, [edges])
        oracle.validate(3558, [[[2, 1]]])
        oracle.validate(3558, [[[1, 3], [2, 3]]])

    def test_budget_checked_before_combinatorial_work(self):
        cases = [(3228, ['0' * 13], '_maximum_moves'),
                 (3523, [[1] * 11], '_partition_maxima'),
                 (3558, [[[1, i] for i in range(2, 12)]], '_path_weight_assignments'),
                 (3597, ['a' * 13], '_valid_cut_partition')]
        for pid, args, name in cases:
            oracle.validate(pid, args)
            with self.subTest(pid=pid), patch.object(oracle, name) as function:
                with self.assertRaisesRegex(ValueError, 'budget'):
                    oracle.expected(pid, args)
                function.assert_not_called()


class OracleTests(unittest.TestCase):
    def test_all_public_examples_and_no_mutation(self):
        for pid, examples in EXAMPLES.items():
            for args, answer in examples:
                before = copy.deepcopy(args)
                with self.subTest(pid=pid, args=args):
                    result = oracle.expected(pid, args)
                    self.assertEqual(result, answer)
                    self.assertIs(type(result), type(answer))
                    self.assertEqual(args, before)

    def test_whole_zero_run_is_one_move(self):
        for s, answer in [('10000', 1), ('111000', 3), ('1010', 3),
                          ('101010', 6), ('000111', 0)]:
            self.assertEqual(oracle.expected(3228, [s]), answer)

    def test_block_partition_contract(self):
        for values, answer in [([2, 2, 1, 2], 3), ([3, 1, 2], 1),
                               ([1, 3, 2, 4], 3), ([2, 1, 2], 2), ([4], 1)]:
            self.assertEqual(oracle.expected(3523, [values]), answer)

    def test_one_deepest_path_not_all_leaves_or_edges(self):
        for edges, answer in [([[1, 2], [1, 3], [1, 4]], 1),
                              ([[1, 2], [2, 3], [2, 4]], 2),
                              ([[1, 2], [2, 3], [3, 4], [3, 5]], 4)]:
            self.assertEqual(oracle.expected(3558, [edges]), answer)
            self.assertEqual(oracle.expected(3558, [[edge[::-1] for edge in edges[::-1]]]), answer)

    def test_seen_final_suffix_is_omitted(self):
        for s, answer in [('a', ['a']), ('aa', ['a']), ('aaa', ['a', 'aa']),
                          ('aba', ['a', 'b']), ('abac', ['a', 'b', 'ac']),
                          ('aaaaaa', ['a', 'aa', 'aaa'])]:
            self.assertEqual(oracle.expected(3597, [s]), answer)

    def test_statement_pin_before_oracle_work(self):
        for pid, raw in [(3228, fixture(3228)), (3228, 'text'), (True, b'text')]:
            with self.subTest(pid=pid), patch.object(oracle, 'expected') as function:
                with self.assertRaisesRegex(ValueError, 'pin'):
                    oracle._public_examples(pid, raw)
                function.assert_not_called()

    def test_examples_reject_wrong_names_count_answers_and_types(self):
        original = fixture(3228)
        invalid = [original.replace(b's =', b'x ='),
                   b'Input:' + original.split(b'Input:')[1],
                   original.replace(b'Output: 4', b'Output: 5'),
                   original.replace(b'Output: 4', b'Output: 4.0')]
        for raw in invalid:
            with patch.dict(oracle.STATEMENT_SHA256, {3228: oracle.sha(raw)}):
                with self.assertRaises(ValueError):
                    oracle._public_examples(3228, raw)


class FrozenCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.populations = {}
        for pid in oracle.IDS:
            raw = fixture(pid)
            with patch.dict(oracle.STATEMENT_SHA256, {pid: oracle.sha(raw)}):
                cls.populations[pid] = oracle.build_cases(pid, raw)

    def test_frozen_counts_hashes_categories_and_full_domains(self):
        for pid, (cases, categories) in self.populations.items():
            with self.subTest(pid=pid):
                self.assertEqual(len(cases), oracle.CASE_COUNT[pid])
                self.assertEqual(oracle.sha(oracle.encoded(cases)), oracle.CASES_SHA256[pid])
                self.assertEqual(len(categories), len(cases))
                self.assertEqual(categories.count('pinned_public_example'), 2)
                self.assertEqual(sum(c.startswith('analytic_') for c in categories), 5)
                for case in cases:
                    self.assertEqual(set(case), {'args', 'expected', 'compare'})
                    self.assertEqual(case['compare'], 'return')
                    oracle.validate(pid, case['args'])

    def test_existing_file_and_packet_caps_preserve_all_cases(self):
        for pid, (cases, _) in self.populations.items():
            with self.subTest(pid=pid):
                self.assertLessEqual(len(oracle.encoded(cases)), q.MAX_FILE)
                packets = list(q.batches(cases))
                self.assertEqual(sum(len(packet) for _, packet in packets), len(cases))
                for _, packet in packets:
                    self.assertLessEqual(len(packet), 32)
                    self.assertLessEqual(len(q.encoded(q.packet(packet))), q.MAX_PACKET)

    def test_explicitly_omitted_shapes_exceed_unchanged_packet_cap(self):
        for pid, args in [(3523, [[200000] * 200000]),
                          (3558, [[[i, i + 1] for i in range(1, 100000)]])]:
            oracle.validate(pid, args)
            with self.subTest(pid=pid), self.assertRaisesRegex(ValueError, 'packet cap'):
                list(q.batches([{'args': args, 'expected': 1, 'compare': 'return'}]))

    def test_frozen_population_rejects_changed_or_missing_case(self):
        cases, categories = self.populations[3228]
        changed = copy.deepcopy(cases)
        changed[0]['expected'] += 1
        for population in [changed, cases[:-1]]:
            with patch.object(oracle, '_generate_cases', return_value=(population, categories)):
                with self.assertRaisesRegex(ValueError, 'frozen'):
                    oracle.build_cases(3228, b'not read because generator is mocked')


if __name__ == '__main__':
    unittest.main()
