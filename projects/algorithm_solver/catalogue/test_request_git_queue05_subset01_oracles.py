"""Focused source-free unittest checks; no candidate or statement file reads."""
from itertools import combinations, product
import unittest

from . import imported_qualification as q
from . import request_git_queue05_subset01_oracles as o


class Queue05Subset01Tests(unittest.TestCase):
    def test_official_examples(self):
        examples = [
            (2508, [5, [[1, 2], [2, 3], [3, 4], [4, 2], [1, 4], [2, 5]]], True),
            (2508, [4, [[1, 2], [3, 4]]], True),
            (2508, [4, [[1, 2], [1, 3], [1, 4]]], False),
            (2567, [[1, 4, 7, 8, 5]], 3), (2567, [[1, 4, 3]], 0),
            (2640, [[2, 3, 7, 5, 10]], [4, 10, 24, 36, 56]),
            (2640, [[1, 1, 2, 4, 8, 16]], [2, 4, 8, 16, 32, 64]),
            (2672, [4, [[0, 2], [1, 2], [3, 1], [1, 1], [2, 1]]], [0, 1, 1, 0, 2]),
            (2672, [1, [[0, 100000]]], [0]),
        ]
        for pid, args, expected in examples:
            with self.subTest(pid=pid, args=args):
                self.assertTrue(q.exact(o.expected(pid, args), expected))

    def test_domain_negative_controls(self):
        invalid = [
            (2508, [True, [[1, 2], [2, 3]]]), (2508, [2, [[1, 2], [2, 1]]]),
            (2508, [3, []]), (2508, [3, [[1, 2]]]),
            (2508, [3, [[1, 2], [2, 1]]]), (2508, [3, [[1, 1], [2, 3]]]),
            (2508, [3, [[0, 1], [2, 3]]]), (2508, [3, [[1, True], [2, 3]]]),
            (2508, [3, [[1, 4], [2, 3]]]), (2508, [100001, [[1, 2], [2, 3]]]),
            (2567, [[1, 2]]), (2567, [[1, 2, 0]]), (2567, [[1, 2, True]]),
            (2567, [[1, 2, 1000000001]]), (2567, [[1]*100001]),
            (2640, [[]]), (2640, [[0]]), (2640, [[1.0]]), (2640, [[False]]),
            (2672, [0, [[0, 1]]]), (2672, [2, []]), (2672, [2, [[2, 1]]]),
            (2672, [2, [[0, 0]]]), (2672, [2, [[0, 100001]]]),
            (2672, [2, [[False, 1]]]), (2672, [2, [[0, True]]]),
            (2672, [2, [[0, 1, 2]]]), (2672, [2, [[0, 1]]*100001]),
            (True, [[1]]), (9999, []), (2640, ([1],)), (2640, [[1], 2]),
        ]
        for pid, args in invalid:
            with self.subTest(pid=pid):
                with self.assertRaises(ValueError):
                    o.validate(pid, args)

    def test_full_domains_are_not_reference_budgets(self):
        for pid, args in [(2508, [100000, [[1, 2], [2, 3]]]),
                          (2567, [[1000000000]*100000]),
                          (2640, [[1000000000]*100000]),
                          (2672, [100000, [[99999, 100000]]*100000])]:
            o.validate(pid, args)
            with self.assertRaisesRegex(ValueError, 'budget'):
                o.expected(pid, args)

    def test_graph_reference_against_odd_degree_classification(self):
        for n in range(3, 6):
            pairs = list(combinations(range(1, n+1), 2))
            for mask in range(1 << len(pairs)):
                edges = [list(e) for k, e in enumerate(pairs) if mask >> k & 1]
                if len(edges) < 2:
                    continue
                present = {tuple(e) for e in edges}
                odd = [v for v in range(1, n+1) if sum(v in e for e in edges) % 2]
                def absent(a, b):
                    return a != b and tuple(sorted((a, b))) not in present
                if not odd:
                    result = True
                elif len(odd) == 2:
                    a, b = odd
                    result = absent(a, b) or any(absent(a, c) and absent(b, c) for c in range(1, n+1))
                elif len(odd) == 4:
                    a, b, c, d = odd
                    result = any(absent(x, y) and absent(z, w) for x, y, z, w in
                                 [(a, b, c, d), (a, c, b, d), (a, d, b, c)])
                else:
                    result = False
                self.assertIs(o.expected(2508, [n, edges]), result)

    def test_pair_index_reference_against_literal_value_assignments(self):
        for n in range(3, 6):
            for values in product((1, 2, 3), repeat=n):
                best = 100
                for i, j in combinations(range(n), 2):
                    for x, y in product(range(1, 4), repeat=2):
                        changed = list(values)
                        changed[i], changed[j] = x, y
                        differences = [abs(changed[a]-changed[b]) for a, b in combinations(range(n), 2)]
                        best = min(best, min(differences)+max(differences))
                self.assertEqual(o.expected(2567, [list(values)]), best)

    def test_prefix_reference_against_incremental_conversion(self):
        for n in range(1, 7):
            for values in product((1, 4), repeat=n):
                total = largest = 0
                answer = []
                for x in values:
                    largest = max(largest, x)
                    total += x + largest
                    answer.append(total)
                self.assertEqual(o.expected(2640, [list(values)]), answer)
        self.assertEqual(o.expected(2640, [[1000000000]*40])[-1], 80000000000)

    def test_repaint_rescan_against_local_edge_updates(self):
        for n in range(1, 4):
            for stream in product(list(product(range(n), (1, 2))), repeat=3):
                colors = [0]*n
                count = 0
                answer = []
                for index, color in stream:
                    for other in (index-1, index+1):
                        if 0 <= other < n and colors[index] != 0 and colors[index] == colors[other]:
                            count -= 1
                    colors[index] = color
                    for other in (index-1, index+1):
                        if 0 <= other < n and colors[index] == colors[other]:
                            count += 1
                    answer.append(count)
                self.assertEqual(o.expected(2672, [n, [list(x) for x in stream]]), answer)

    def test_packet_and_statement_contracts(self):
        case = dict(args=[[1, 2, 3]], expected=[2, 6, 12], compare='return')
        packet = q.packet([case])
        self.assertEqual(packet['calls'], [dict(args=[[1, 2, 3]])])
        self.assertNotIn('expected', str(packet))
        for language in ('javascript', 'python'):
            self.assertLess(o.expected_observation_bytes([case], language), q.LIMITS['max_output_bytes'])
        with self.assertRaises(ValueError):
            o.expected_observation_bytes([case], 'other')
        for pid in o.IDS:
            with self.assertRaisesRegex(ValueError, 'pinned'):
                o.public_examples(pid, b'not a pinned official definition')


if __name__ == '__main__':
    unittest.main()
