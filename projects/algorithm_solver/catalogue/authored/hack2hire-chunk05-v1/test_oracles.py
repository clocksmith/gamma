import unittest
from oracles import reference
from cases import build_cases


class ReferenceChecks(unittest.TestCase):
    def test_literal_edges(self):
        self.assertEqual(reference('passwords', ['abba']), 5)
        self.assertEqual(reference('squares', [[[2, 3], [0, 3]]]), [8, 0])
        self.assertTrue(reference('date', [2000, 2, 29]))
        self.assertFalse(reference('date', [1900, 2, 29]))
        self.assertEqual(reference('goodness', [[2, 1]]), [0, 1, 2])
        self.assertEqual(reference('products', [[2, 2, 3]]), [2, 3, 4, 6, 12])
        self.assertEqual(reference('earliest', [0, 0, 1, 1, 'NE']), 2)
        self.assertEqual(reference('adjacent', ['aaaaa']), 2)
        self.assertEqual(reference('timeline', [[['a', 0, 2], ['a', 1, 3]]]), [[0, 3, ['a']]])

    def test_reference_generators_are_deterministic(self):
        for key in ['ratings', 'access', 'orders', 'crypto', 'ip', 'meeting', 'pagination', 'path', 'radix', 'rate', 'lru', 'trading']:
            self.assertEqual(build_cases(key), build_cases(key))


if __name__ == '__main__':
    unittest.main()
