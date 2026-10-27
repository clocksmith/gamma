"""Independent source-free checks for queue01 subset02; standard library only."""
from collections import Counter
from itertools import product
import unittest

from . import imported_qualification as q
from . import request_git_queue01_subset02_oracles as o


class DefinitionReferences(unittest.TestCase):
    def test_pinned_example_values_and_corner_rules(self):
        cases = [
            (1943, [[[1, 4, 5], [4, 7, 7], [1, 7, 9]]], [[1, 4, 14], [4, 7, 16]]),
            (1943, [[[1, 4, 5], [1, 4, 7], [4, 7, 1], [4, 7, 11]]], [[1, 4, 12], [4, 7, 12]]),
            (1943, [[[1, 2, 1], [3, 4, 2]]], [[1, 2, 1], [3, 4, 2]]),
            (1959, [[10, 20], 0], 10), (1959, [[10, 20, 30], 1], 10),
            (1959, [[10, 20, 15, 30, 20], 2], 15), (1959, [[1], 0], 0),
            (1977, ['327'], 2), (1977, ['094'], 0), (1977, ['0'], 0),
            (1977, ['11'], 2), (1977, ['10'], 1), (1977, ['101'], 1),
            (1997, [[0, 0]], 2), (1997, [[0, 0, 2]], 6), (1997, [[0, 1, 2, 0]], 6),
            (2049, [[-1, 2, 0, 2, 0]], 3), (2049, [[-1, 2, 0]], 2),
            (2056, [['rook'], [[1, 1]]], 15), (2056, [['queen'], [[1, 1]]], 22),
            (2056, [['bishop'], [[4, 3]]], 12),
        ]
        for pid, args, answer in cases:
            with self.subTest(pid=pid, args=args):
                self.assertTrue(q.exact(o.expected(pid, args), answer))

    def test_full_domain_invalid_controls(self):
        invalid = [
            (1943, [[]]), (1943, [[[1, 1, 1]]]), (1943, [[[0, 2, 1]]]),
            (1943, [[[1, 2, 1], [2, 3, 1]]]), (1943, [[[1, 2, True]]]),
            (1943, [[[1, 100001, 1]]]), (1943, [[[1, 2, 1000000001]]]),
            (1959, [[], 0]), (1959, [[1], 1]), (1959, [[1], -1]),
            (1959, [[1000001], 0]), (1959, [[True], 0]), (1959, [[1], False]),
            (1977, ['']), (1977, ['１']), (1977, ['1a']), (1977, ['1'*3501]),
            (1997, [[0]]), (1997, [[1, 1]]), (1997, [[0, 2]]), (1997, [[0, True]]),
            (2049, [[-1]]), (2049, [[0, 0]]), (2049, [[-1, 0, 0, 0]]),
            (2049, [[-1, 2, 1]]), (2049, [[-1, -1]]), (2049, [[-1, True]]),
            (2056, [[], []]), (2056, [['king'], [[1, 1]]]),
            (2056, [['queen', 'queen'], [[1, 1], [8, 8]]]),
            (2056, [['rook', 'bishop'], [[1, 1], [1, 1]]]),
            (2056, [['rook'], [[True, 1]]]), (2056, [['rook'], [[1, 9]]]),
        ]
        for pid, args in invalid:
            with self.subTest(pid=pid, args=args), self.assertRaises(ValueError):
                o.validate(pid, args)
        for pid, args in [(True, []), (1943, ([],)), (1959, [[1]]), (9999, [])]:
            with self.assertRaises(ValueError):
                o.validate(pid, args)

    def test_admission_is_not_reference_bound(self):
        large = [(1943, [[[1, 100000, i+1] for i in range(20000)]]),
                 (1959, [[1000000]*200, 199]), (1977, ['9'*3500]),
                 (1997, [list(range(100000))]), (2049, [[-1]+list(range(99999))])]
        for pid, args in large:
            o.validate(pid, args)
            with self.assertRaisesRegex(ValueError, 'budget'):
                o.expected(pid, args)

    def test_resize_reference_against_capacity_assignment(self):
        for n in range(1, 5):
            for values in product((1, 3), repeat=n):
                for k in range(n):
                    feasible = []
                    for capacities in product((1, 3), repeat=n):
                        if (all(a <= b for a, b in zip(values, capacities))
                                and sum(a != b for a, b in zip(capacities, capacities[1:])) <= k):
                            feasible.append(sum(b-a for a, b in zip(values, capacities)))
                    self.assertEqual(o.expected(1959, [list(values), k]), min(feasible))

    def test_partition_uniform_and_zero_families(self):
        for n in range(1, 13):
            self.assertEqual(o.expected(1977, ['1'*n]), o.integer_partition_count(n))
            self.assertEqual(o.expected(1977, ['9'*n]), o.integer_partition_count(n))
            self.assertEqual(o.expected(1977, ['1'+'0'*(n-1)]), 1)
            self.assertEqual(o.expected(1977, ['0'*n]), 0)

    def test_room_analytic_families_against_days(self):
        for n in range(2, 15):
            self.assertEqual(o.expected(1997, [[0]*n]), 2**n-2)
            self.assertEqual(o.expected(1997, [list(range(n))]), 2*(n-1))
            self.assertEqual(o.expected(1997, [[max(0, i-1) for i in range(n)]]), n*(n-1))
            values = list(range(n)); values[-1] = 0
            self.assertEqual(o.expected(1997, [values]), 2*(n-1))

    def test_tree_analytic_families_and_arbitrary_label_order(self):
        for n in range(6, 100):
            self.assertEqual(o.expected(2049, [[-1]+list(range(n-1))]), 1 if n % 2 else 2)
        for n in (15, 31, 63):
            self.assertEqual(o.expected(2049, [[-1]+[(i-1)//2 for i in range(1, n)]]), 2)
        self.assertEqual(o.expected(2049, [[-1, 0, 1, 2, 3]]), 3)
        self.assertEqual(o.expected(2049, [[-1, 0, 0, 1, 1, 2, 2]]), 1)
        o.validate(2049, [[-1, 3, 0, 2]])

    def test_chess_destinations_and_instantaneous_swaps(self):
        for r in range(1, 9):
            for c in range(1, 9):
                bishop = 1 + min(r-1, c-1)+min(r-1, 8-c)+min(8-r, c-1)+min(8-r, 8-c)
                self.assertEqual(o.expected(2056, [['rook'], [[r, c]]]), 15)
                self.assertEqual(o.expected(2056, [['bishop'], [[r, c]]]), bishop)
                self.assertEqual(o.expected(2056, [['queen'], [[r, c]]]), 14+bishop)
        swap = (((1, 1),)+((1, 2),)*7, ((1, 2),)+((1, 1),)*7)
        self.assertTrue(o.valid_motion_combination(swap))
        stop_collision = (((1, 1),)+((1, 2),)*7, ((1, 3),)+((1, 2),)*7)
        self.assertFalse(o.valid_motion_combination(stop_collision))
        noncollision = (((1, 1),)*8, ((2, 2),)*8)
        self.assertTrue(o.valid_motion_combination(noncollision))

    def test_order_independent_painting_compare_preserves_strict_effects(self):
        args = [[[1, 2, 1], [3, 4, 2]]]
        case = {'args': args, 'expected': [[1, 2, 1], [3, 4, 2]], 'compare': 'return'}
        record = {'result': [[3, 4, 2], [1, 2, 1]], 'result_type': 'list',
                  'args_before': args, 'args_after': args, 'alias_edges': []}
        self.assertIsNone(o.compare_observation(1943, case, record, 'python'))
        for bad in [dict(record, result=[[1, 4, 3]]), dict(record, result=[[1, 2, True], [3, 4, 2]]),
                    dict(record, result=[[1, 2, 1], [1, 2, 1], [3, 4, 2]]),
                    dict(record, alias_edges=[['result', 'arg0']]), dict(record, args_after=[]),
                    dict(record, result_type='tuple')]:
            self.assertIsNotNone(o.compare_observation(1943, case, bad, 'python'))
        self.assertEqual(o.compare_observation(1943, case, {'error': 'bad'}, 'python'), 'candidate_error')

    def test_no_source_or_unpinned_statement_reads(self):
        with self.assertRaises(ValueError):
            o.public_examples(1943, b'unpinned')
        packet = q.packet([{'args': ['327'], 'expected': 2, 'compare': 'return'}])
        self.assertEqual(packet['calls'], [{'args': ['327']}])
        self.assertNotIn('expected', packet)


if __name__ == '__main__':
    unittest.main()
