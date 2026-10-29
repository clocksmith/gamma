import importlib.util
from pathlib import Path
import unittest

_spec = importlib.util.spec_from_file_location('gamma_ds39_reference_test_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_o)
reference, validate_domain, IDS = _o.reference, _o.validate_domain, _o.IDS

_cspec = importlib.util.spec_from_file_location('gamma_ds39_reference_test_cases', Path(__file__).with_name('cases.py'))
_c = importlib.util.module_from_spec(_cspec)
_cspec.loader.exec_module(_c)
build_cases = _c.build_cases


class References(unittest.TestCase):
    def test_median_finder(self):
        self.assertEqual(
            reference(295, [['MedianFinder', 'addNum', 'addNum', 'findMedian', 'addNum', 'findMedian'], [[], [1], [2], [], [3], []]]),
            [None, None, None, 1.5, None, 2.0],
        )

    def test_serialize_bintree(self):
        self.assertEqual(reference(297, [[1, 2, 3, None, None, 4, 5]]), [1, 2, 3, None, None, 4, 5])

    def test_range_sum_immutable(self):
        self.assertEqual(
            reference(303, [['NumArray', 'sumRange', 'sumRange', 'sumRange'], [[[-2, 0, 3, -5, 2, -1]], [0, 2], [2, 5], [0, 5]]]),
            [None, 1, -1, -3],
        )

    def test_range_sum_2d(self):
        mat = [[3, 0, 1, 4, 2], [5, 6, 3, 2, 1], [1, 2, 0, 1, 5], [4, 1, 0, 1, 7], [1, 0, 3, 0, 5]]
        self.assertEqual(
            reference(304, [['NumMatrix', 'sumRegion', 'sumRegion', 'sumRegion'], [[mat], [2, 1, 4, 3], [1, 1, 2, 2], [1, 2, 2, 4]]]),
            [None, 8, 11, 12],
        )

    def test_range_sum_mutable(self):
        self.assertEqual(
            reference(307, [['NumArray', 'sumRange', 'update', 'sumRange'], [[[1, 3, 5]], [0, 2], [1, 2], [0, 2]]]),
            [None, 9, None, 8],
        )

    def test_create_max_number(self):
        self.assertEqual(reference(321, [[3, 4, 6, 5], [9, 1, 2, 5, 8, 3], 5]), [9, 8, 6, 5, 3])

    def test_odd_even_list(self):
        self.assertEqual(reference(328, [[1, 2, 3, 4, 5]]), [1, 3, 5, 2, 4])

    def test_nested_iterator(self):
        self.assertEqual(
            reference(341, [['NestedIterator', 'hasNext', 'next', 'hasNext', 'next', 'hasNext', 'next', 'hasNext'], [[[[1, 1], 2, [1, 1]]], [], [], [], [], [], [], []]]),
            [None, True, 1, True, 1, True, 2, True],
        )

    def test_summary_ranges(self):
        self.assertEqual(
            reference(352, [['SummaryRanges', 'addNum', 'getIntervals', 'addNum', 'getIntervals', 'addNum', 'getIntervals'], [[], [1], [], [3], [], [2], []]]),
            [None, None, [[1, 1]], None, [[1, 1], [3, 3]], None, [[1, 3]]],
        )

    def test_twitter(self):
        self.assertEqual(
            reference(355, [['Twitter', 'postTweet', 'getNewsFeed', 'follow', 'postTweet', 'getNewsFeed', 'unfollow', 'getNewsFeed'], [[], [1, 5], [1], [1, 2], [2, 6], [1], [1, 2], [1]]]),
            [None, None, [5], None, None, [6, 5], None, [5]],
        )

    def test_guess_number(self):
        self.assertEqual(reference(374, [10, 6]), 6)

    def test_randomized_set_and_collection(self):
        self.assertEqual(reference(380, [['RandomizedSet', 'insert', 'getRandom'], [[], [7], []]]), [None, True, 7])
        self.assertEqual(reference(381, [['RandomizedCollection', 'insert', 'insert', 'getRandom'], [[], [7], [7], []]]), [None, True, False, 7])
        self.assertEqual(reference(382, [['Solution', 'getRandom'], [[[42]], []]]), [None, 42])
        self.assertEqual(reference(384, [['Solution', 'reset'], [[[1, 2, 3]], []]]), [None, [1, 2, 3]])
        self.assertEqual(reference(398, [['Solution', 'pick'], [[[5]], [5]]]), [None, 0])

    def test_mini_parser(self):
        self.assertEqual(reference(385, ['[123,[456,[789]]]']), [123, [456, [789]]])

    def test_strong_password(self):
        self.assertEqual(reference(420, ['a']), 5)
        self.assertEqual(reference(420, ['aA1']), 3)
        self.assertEqual(reference(420, ['1337C0d3']), 0)

    def test_quad_and_nary_and_multilevel(self):
        self.assertEqual(reference(427, [[[0, 1], [1, 0]]]), [[0, 1], [1, 0], [1, 1], [1, 1], [1, 0]])
        self.assertEqual(reference(429, [[1, None, 3, 2, 4, None, 5, 6]]), [[1], [3, 2, 4], [5, 6]])
        self.assertEqual(reference(430, [[1, 2, 3, 4, 5, 6, None, None, None, 7, 8, 9, 10, None, None, 11, 12]]), [1, 2, 3, 7, 8, 11, 12, 9, 10, 4, 5, 6])

    def test_all_one_and_lfu(self):
        self.assertEqual(
            reference(432, [['AllOne', 'inc', 'inc', 'getMaxKey', 'getMinKey', 'inc', 'getMaxKey', 'getMinKey'], [[], ['hello'], ['hello'], [], [], ['leet'], [], []]]),
            [None, None, None, 'hello', 'hello', None, 'hello', 'leet'],
        )
        self.assertEqual(
            reference(460, [['LFUCache', 'put', 'put', 'get', 'put', 'get', 'get'], [[2], [1, 1], [2, 2], [1], [3, 3], [2], [3]]]),
            [None, None, None, 1, None, -1, 3],
        )

    def test_bst_repetitions_rand10_palindrome_median_base_zuma(self):
        self.assertEqual(reference(449, [[2, 1, 3]]), [2, 1, 3])
        self.assertEqual(reference(466, ['acb', 4, 'ab', 2]), 2)
        self.assertEqual(reference(470, [[1, 1]]), 1)
        self.assertEqual(reference(479, [2]), 987)
        self.assertEqual(reference(480, [[1, 3, -1, -3, 5, 3, 6, 7], 3]), [1.0, -1.0, -1.0, 3.0, 5.0, 6.0])
        self.assertEqual(reference(483, ['13']), '3')
        self.assertEqual(reference(483, ['4681']), '8')
        self.assertEqual(reference(488, ['WRRBBW', 'RB']), -1)
        self.assertEqual(reference(488, ['WWRRBBWW', 'WRBRW']), 2)

    def test_remaining_problems(self):
        self.assertEqual(reference(497, [['Solution', 'pick'], [[[[5, 5, 5, 5]]], []]]), [None, [5, 5]])
        self.assertEqual(reference(519, [['Solution', 'flip'], [[1, 1], []]]), [None, [0, 0]])
        self.assertEqual(reference(528, [['Solution', 'pickIndex'], [[[10]], []]]), [None, 0])
        self.assertEqual(reference(535, ['https://leetcode.com/problems/design-tinyurl']), 'https://leetcode.com/problems/design-tinyurl')
        self.assertEqual(reference(558, [[[1, 0]], [[1, 1]]]), [[1, 1]])
        self.assertEqual(reference(559, [[1, None, 3, 2, 4, None, 5, 6]]), 3)
        self.assertEqual(reference(572, [[3, 4, 5, 1, 2], [4, 1, 2]]), True)
        self.assertEqual(reference(587, [[[1, 1], [2, 2], [2, 0], [2, 4], [3, 3], [4, 2]]]), [[1, 1], [2, 0], [2, 4], [3, 3], [4, 2]])

    def test_all_cases_and_domain_errors(self):
        for pid in IDS:
            rows = build_cases(pid, include_maximum=True)
            self.assertGreaterEqual(len(rows), 2)
            self.assertTrue(any(r['category'] == 'analytic-maximum' for r in rows))
        with self.assertRaises(ValueError):
            validate_domain(295, [['MedianFinder', 'findMedian'], [[], []]])
        with self.assertRaises(ValueError):
            validate_domain(374, [10, 11])
        with self.assertRaises(ValueError):
            validate_domain(449, [[2, 3, 1]])


if __name__ == '__main__':
    unittest.main()
