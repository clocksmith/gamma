"""Pure stdlib oracle checks; no candidate execution or definition file access."""
from itertools import product
import unittest
from . import request_git_queue02_subset01_oracles as o


class Queue02Tests(unittest.TestCase):
    def test_public_examples_independently_transcribed(self):
        for pid, args, answer in [(2110, [[3, 2, 1, 4]], 7), (2110, [[8, 6, 7, 7]], 4),
                                  (2110, [[1]], 1), (2221, [[1, 2, 3, 4, 5]], 8), (2221, [[5]], 5)]:
            self.assertEqual(o.expected(pid, args), answer)

    def test_small_brute_agrees_with_independent_large_reference(self):
        for pid, alphabet in [(2110, [1, 2, 3]), (2221, [0, 1, 9])]:
            for n in range(1, 7):
                for values in product(alphabet, repeat=n):
                    a = list(values)
                    self.assertEqual(o.expected(pid, [a]), o.analytic(pid, [a]))
                    self.assertEqual(a, list(values))

    def test_invalid_domain(self):
        for pid, args in [(2110, [[True]]), (2110, [[0]]), (2110, [[100001]]), (2110, [[1.0]]),
                          (2110, [[]]), (2221, [[10]]), (2221, [[-1]]), (2221, [[False]]),
                          (2221, [[1] * 1001]), (True, [[1]])]:
            with self.subTest(pid=pid, args=str(args)[:80]), self.assertRaises(ValueError):
                o.validate(pid, args)

    def test_full_domain_separate_from_reference_budget(self):
        o.validate(2110, [[1] * 100000])
        o.validate(2221, [[9] * 1000])
        self.assertEqual(o.analytic(2110, [list(range(100000, 0, -1))]), 5000050000)
        self.assertEqual(o.analytic(2221, [[9] * 1000]), (9 * pow(2, 999, 10)) % 10)
        for pid in (2110, 2221):
            with self.assertRaisesRegex(ValueError, 'budget'):
                o.expected(pid, [[1] * (o.SMALL_BUDGET[pid] + 1)])

    def test_definition_pin_fail_closed(self):
        with self.assertRaises(ValueError):
            o.public_examples(2110, b'not the official pinned response')


if __name__ == '__main__':
    unittest.main()
