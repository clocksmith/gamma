"""Cross-check the new host reference algorithms and rejection boundaries."""
import copy
from itertools import combinations, permutations, product
import math
import unittest

import oracles as o


def stack_outputs(n):
    result = set()

    def visit(next_input, stack, output):
        if len(output) == n:
            result.add(tuple(output))
        if next_input < n:
            visit(next_input + 1, stack + [next_input], output)
        if stack:
            visit(next_input, stack[:-1], output + [stack[-1]])
    visit(0, [], [])
    return result


def all_pairings(xs):
    if not xs:
        return 0
    return max(min(xs[0], xs[i]) + all_pairings(xs[1:i] + xs[i + 1:])
               for i in range(1, len(xs)))


class Oracles(unittest.TestCase):
    def test_stack_pattern_against_every_operation_path(self):
        for n in range(1, 7):
            reachable = stack_outputs(n)
            for p in permutations(range(n)):
                self.assertEqual(o.expected(946, [list(range(n)), list(p)]), p in reachable)

    def test_product_against_every_triple(self):
        for n in (3, 4, 5):
            for xs in product((-2, 0, 3), repeat=n):
                self.assertEqual(o.maximum_product(xs), max(math.prod(c) for c in combinations(xs, 3)))

    def test_partition_against_every_pairing(self):
        for n in (2, 4, 6):
            for xs in product((-2, 0, 3), repeat=n):
                self.assertEqual(o.expected(561, [list(xs)]), all_pairings(list(xs)))

    def test_palindrome_dp_against_all_substrings(self):
        for n in range(1, 8):
            for chars in product('aB', repeat=n):
                s = ''.join(chars)
                want = max(j - i for i in range(n) for j in range(i + 1, n + 1)
                           if s[i:j] == s[i:j][::-1])
                self.assertEqual(o.longest_length(s), want)

    def test_domain_rejections(self):
        for pid, args in [(1, [[1, 1, 1], 2]), (1, [[1, 2], True]), (5, ['']),
                          (125, ['é']), (338, [True]), (496, [[2], [1]]),
                          (500, [['a1']]), (557, ['a  b']), (561, [[1, 2, 3]]),
                          (693, [0]), (852, [[1, 1, 0]]), (946, [[1, 2], [1, 1]]),
                          (953, [['abc'], 'a' * 26])]:
            with self.subTest(pid=pid, args=args), self.assertRaises(ValueError):
                o.expected(pid, args)

    def test_value_and_effect_negative_controls(self):
        args = [[30, 31]]
        record = {'result': [1, 0], 'result_type': 'list', 'args_before': args,
                  'args_after': args, 'alias_edges': []}
        self.assertEqual(o.compare(739, args, [1, 0], record, 'python'), (True, None))
        for field, value, reason in [('result', [True, 0], 'result_value'),
                                     ('result_type', 'tuple', 'result_type'),
                                     ('args_after', [[31, 30]], 'input_effects'),
                                     ('alias_edges', [['result', 'args.0']], 'mutable_return_alias')]:
            altered = copy.deepcopy(record)
            altered[field] = value
            self.assertEqual(o.compare(739, args, [1, 0], altered, 'python'), (False, reason))
        self.assertTrue(o.matches(5, ['babad'], 'aba', 3))
        self.assertTrue(o.matches(5, ['babad'], 'bab', 3))
        self.assertFalse(o.matches(5, ['babad'], 'bad', 3))
        self.assertTrue(o.matches(1, [[2, 7], 9], [1, 0], [0, 1]))
        self.assertFalse(o.matches(1, [[2, 7], 9], [False, 1], [0, 1]))
        self.assertTrue(o.matches(500, [['a', 'A', 'a']], ['A', 'a', 'a'], ['a', 'A', 'a']))
        self.assertFalse(o.matches(500, [['a', 'A', 'a']], ['a', 'A'], ['a', 'A', 'a']))


if __name__ == '__main__':
    unittest.main()
