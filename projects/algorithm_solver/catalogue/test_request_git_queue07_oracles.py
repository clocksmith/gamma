"""Independent mathematical checks; no candidate imports or executions."""
import copy
import itertools
import unittest
from . import request_git_queue07_oracles as oracle


def mountain(heights):
    return any(all(heights[j] <= heights[j + 1] for j in range(p))
               and all(heights[j] >= heights[j + 1] for j in range(p, len(heights) - 1))
               for p in range(len(heights)))


def history_scan(nums):
    result = []
    for i, value in enumerate(nums):
        if value != -1:
            continue
        k, j = 1, i - 1
        while j >= 0 and nums[j] == -1:
            k += 1
            j -= 1
        positives = [x for x in reversed(nums[:i]) if x > 0]
        result.append(positives[k - 1] if k <= len(positives) else -1)
    return result


def triples(nums):
    candidates = [nums[i] + nums[j] + nums[k]
                  for i, j, k in itertools.combinations(range(len(nums)), 3)
                  if nums[i] < nums[j] and nums[k] < nums[j]]
    return min(candidates, default=-1)


def topo_exists(n, edges):
    for order in itertools.permutations(range(n)):
        rank = {v: i for i, v in enumerate(order)}
        if all(rank[u] < rank[v] for u, v in edges):
            return True
    return False


def changed_position_cover(word):
    bad = [i for i in range(len(word) - 1) if abs(ord(word[i]) - ord(word[i + 1])) <= 1]
    return min(mask.bit_count() for mask in range(1 << len(word))
               if all((mask >> i & 1) or (mask >> (i + 1) & 1) for i in bad))


class DifferentialTests(unittest.TestCase):
    def test_all_tiny_tower_height_assignments(self):
        for n in range(1, 6):
            for caps in itertools.product(range(1, 4), repeat=n):
                expected = max(sum(h) for h in itertools.product(*(range(1, c + 1) for c in caps)) if mountain(h))
                self.assertEqual(oracle.reference(2865, [list(caps)]), expected)

    def test_all_short_integer_history_streams(self):
        for n in range(1, 7):
            for values in itertools.product((-1, 1, 2), repeat=n):
                nums = list(values)
                self.assertEqual(oracle.reference(2899, [nums]), history_scan(nums))

    def test_exhaustive_mountain_index_triples(self):
        for n in range(3, 7):
            for values in itertools.product(range(1, 4), repeat=n):
                nums = list(values)
                self.assertEqual(oracle.reference(2909, [nums]), triples(nums))

    def test_all_small_directed_graphs_with_independent_topological_orders(self):
        accepted = 0
        for n in range(1, 5):
            possible = [(u, v) for u in range(n) for v in range(n) if u != v]
            for mask in range(1 << len(possible)):
                edges = [list(e) for bit, e in enumerate(possible) if mask >> bit & 1]
                valid = len(edges) <= n * (n - 1) // 2 and topo_exists(n, edges)
                if not valid:
                    with self.assertRaises(ValueError):
                        oracle.validate(2924, [n, edges])
                    continue
                accepted += 1
                targets = {v for _, v in edges}
                undefeated = [v for v in range(n) if v not in targets]
                self.assertEqual(oracle.reference(2924, [n, edges]), undefeated[0] if len(undefeated) == 1 else -1)
        self.assertEqual(accepted, 572)

    def test_full_letter_dp_against_changed_position_subsets(self):
        for n in range(1, 6):
            for letters in itertools.product('abcz', repeat=n):
                word = ''.join(letters)
                self.assertEqual(oracle.reference(2957, [word]), changed_position_cover(word))


class ContractTests(unittest.TestCase):
    def test_official_examples(self):
        examples = {2865: [([[5, 3, 4, 1, 1]], 13), ([[6, 5, 3, 9, 2, 7]], 22), ([[3, 2, 5, 5, 2, 3]], 18)],
                    2899: [([[1, 2, -1, -1, -1]], [2, 1, -1]), ([[1, -1, 2, -1, -1]], [1, 2, 1])],
                    2909: [([[8, 6, 1, 5, 3]], 9), ([[5, 4, 8, 7, 10, 2]], 13), ([[6, 5, 4, 3, 4, 5]], -1)],
                    2924: [([3, [[0, 1], [1, 2]]], 0), ([4, [[0, 2], [1, 3], [1, 2]]], -1)],
                    2957: [(['aaaaa'], 2), (['abddez'], 2), (['zyxyxyz'], 3)]}
        for pid, rows in examples.items():
            for args, expected in rows:
                self.assertEqual(oracle.reference(pid, args), expected)

    def test_strict_complete_domain_rejections(self):
        bad = {2865: [[], [[True]], [[1.0]], [[]], [[0]], [[10**9 + 1]], [[1] * 1001], [(1, 2)], [[1], 2]],
               2899: [[[]], [[True]], [[0]], [[-2]], [[101]], [[1] * 101], [['1', 'prev']]],
               2909: [[[1, 2]], [[1, True, 1]], [[0, 1, 2]], [[1, 10**8 + 1, 1]], [[1] * 100001]],
               2924: [[True, []], [0, []], [101, []], [2, [[0, 0]]], [2, [[0, 2]]], [3, [[0, 1], [1, 2], [2, 0]]], [3, [[False, 1]]], [2, [[0, 1], [0, 1]]], [2, [(0, 1)]], [2, [], 1]],
               2957: [[''], ['a' * 101], ['A'], ['é'], ['a1'], [True], [['a']]]}
        for pid, rows in bad.items():
            for args in rows:
                with self.subTest(pid=pid, args=str(args)[:80]), self.assertRaises(ValueError):
                    oracle.validate(pid, args)
        for pid in (True, 2908, '2865', 0):
            with self.assertRaises(ValueError): oracle.validate(pid, [[1]])
        for pid in oracle.IDS:
            with self.assertRaises(ValueError): oracle.validate(pid, ())
            with self.assertRaises(ValueError): oracle.build_cases(pid, b'unpinned definition')

    def test_dag_duplicate_edges_and_nonclosed_chain_are_valid(self):
        self.assertEqual(oracle.reference(2924, [3, [[0, 1], [0, 1]]]), -1)
        self.assertEqual(oracle.reference(2924, [3, [[0, 1], [0, 1], [1, 2]]]), 0)
        self.assertEqual(oracle.reference(2924, [3, [[2, 1], [1, 0]]]), 2)

    def test_maximum_numeric_and_length_analytic_values(self):
        self.assertEqual(oracle.reference(2865, [[10**9] * 1000]), 10**12)
        self.assertEqual(oracle.reference(2899, [[-1] * 100]), [-1] * 100)
        self.assertEqual(oracle.reference(2909, [[10**8 - 1] * 49999 + [10**8] + [10**8 - 1] * 50000]), 3 * 10**8 - 2)
        self.assertEqual(oracle.reference(2924, [100, [[99, v] for v in range(99)]]), 99)
        self.assertEqual(oracle.reference(2957, ['a' * 100]), 50)
        self.assertEqual(oracle.reference(2957, ['az' * 50]), 0)

    def test_reference_preserves_arguments_and_returns_typed_values(self):
        examples = {2865: [[3, 1, 3]], 2899: [[1, -1, -1]], 2909: [[1, 2, 1]],
                    2924: [3, [[2, 1], [1, 0]]], 2957: ['abcz']}
        for pid, args in examples.items():
            before = copy.deepcopy(args)
            result = oracle.reference(pid, args)
            self.assertEqual(args, before)
            self.assertIs(type(result), list if pid == 2899 else int)
            if type(result) is list:
                self.assertIsNot(result, args[0])
                self.assertTrue(all(type(x) is int for x in result))


if __name__ == '__main__':
    unittest.main()
