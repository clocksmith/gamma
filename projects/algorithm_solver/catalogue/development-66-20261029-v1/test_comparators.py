"""Comparator controls: alternate valid answers are accepted, invalid ones rejected."""
from pathlib import Path
import importlib.util
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('development_comparators', HERE / 'comparators.py')
comparators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparators)


def ok(kind, got, expected, args, language='python', **extra):
    return comparators.compare(got, expected, dict(kind=kind, **extra), args, language, lambda a, b: a == b)


class Comparators(unittest.TestCase):
    def test_no_declaration_keeps_exact(self):
        self.assertTrue(comparators.compare([1, 2], [1, 2], None, [], 'python', lambda a, b: a == b))
        self.assertFalse(comparators.compare([2, 1], [1, 2], None, [], 'python', lambda a, b: a == b))
        with self.assertRaises(ValueError):
            comparators.compare(1, 1, {'kind': 'invented'}, [], 'python', lambda a, b: a == b)

    def test_float_tolerance_and_python_float_type(self):
        self.assertTrue(ok('float_abs_tolerance', [3.0, 3.0, 0.0], [3.0, 3.0, 0.0], [], abs_tol=1e-5, python_result_type='float'))
        self.assertFalse(ok('float_abs_tolerance', [3, 3, 0.0], [3.0, 3.0, 0.0], [], abs_tol=1e-5, python_result_type='float'))
        self.assertTrue(ok('float_abs_tolerance', [3, 3, 0.0], [3.0, 3.0, 0.0], [], 'javascript', abs_tol=1e-5, python_result_type='float'))
        self.assertTrue(ok('float_abs_tolerance', 0.500004, 0.5, [], abs_tol=1e-5))
        self.assertFalse(ok('float_abs_tolerance', 0.50002, 0.5, [], abs_tol=1e-5))
        self.assertFalse(ok('float_abs_tolerance', True, 1.0, [], abs_tol=1e-5))

    def test_unordered_kinds(self):
        self.assertTrue(ok('unordered_multiset', ['96', '11', '88', '69'], ['11', '69', '88', '96'], [2]))
        self.assertFalse(ok('unordered_multiset', ['96', '11', '88'], ['11', '69', '88', '96'], [2]))
        self.assertFalse(ok('unordered_multiset', ['11', '11', '88', '96'], ['11', '69', '88', '96'], [2]))
        self.assertTrue(ok('unordered_nested', [[3, 4], [6, 2], [3, 2, 2]], [[2, 6], [3, 4], [2, 2, 3]], [12]))
        self.assertFalse(ok('unordered_nested', [[2, 6], [3, 4]], [[2, 6], [3, 4], [2, 2, 3]], [12]))
        self.assertTrue(ok('ordered_groups_unordered_members', [[3, 5, 4], [2], [1]], [[4, 5, 3], [2], [1]], [[1, 2, 3, 4, 5]]))
        self.assertFalse(ok('ordered_groups_unordered_members', [[2], [4, 5, 3], [1]], [[4, 5, 3], [2], [1]], [[1, 2, 3, 4, 5]]))

    def test_wiggle(self):
        args = [[3, 5, 2, 1, 6, 4]]
        self.assertTrue(ok('valid_wiggle', [3, 5, 1, 6, 2, 4], [3, 5, 1, 6, 2, 4], args))
        self.assertTrue(ok('valid_wiggle', [2, 6, 1, 5, 3, 4], [3, 5, 1, 6, 2, 4], args))
        self.assertFalse(ok('valid_wiggle', [1, 2, 3, 4, 5, 6], [3, 5, 1, 6, 2, 4], args))
        self.assertFalse(ok('valid_wiggle', [3, 5, 2, 6, 1, 6], [3, 5, 1, 6, 2, 4], args))

    def test_nearest_leaf(self):
        self.assertTrue(ok('valid_nearest_leaf', 3, 2, [[1, 3, 2], 1]))
        self.assertTrue(ok('valid_nearest_leaf', 2, 2, [[1, 3, 2], 1]))
        self.assertFalse(ok('valid_nearest_leaf', 1, 2, [[1, 3, 2], 1]))
        tree = [1, 2, 3, 4, None, None, None, 5, None, 6]
        self.assertTrue(ok('valid_nearest_leaf', 3, 3, [tree, 2]))
        self.assertFalse(ok('valid_nearest_leaf', 6, 3, [tree, 2]))
        self.assertTrue(ok('valid_nearest_leaf', 1, 1, [[1], 1]))

    def test_alien_order(self):
        self.assertTrue(ok('valid_alien_order', 'wertf', 'wertf', [['wrt', 'wrf', 'er', 'ett', 'rftt']]))
        for good in ('abc', 'bac', 'bca'):
            self.assertTrue(ok('valid_alien_order', good, 'abc', [['ab', 'ac']]))
        self.assertFalse(ok('valid_alien_order', 'acb', 'abc', [['ab', 'ac']]))
        self.assertFalse(ok('valid_alien_order', 'ab', 'abc', [['ab', 'ac']]))
        self.assertTrue(ok('valid_alien_order', '', '', [['abc', 'ab']]))
        self.assertFalse(ok('valid_alien_order', 'abc', '', [['abc', 'ab']]))
        self.assertTrue(ok('valid_alien_order', '', '', [['z', 'x', 'z']]))
        self.assertFalse(ok('valid_alien_order', 'zx', '', [['z', 'x', 'z']]))
        self.assertTrue(ok('valid_alien_order', '\U0001F600ab', 'ab\U0001F600', [['\U0001F600a', '\U0001F600b']]))
        self.assertFalse(ok('valid_alien_order', 'b\U0001F600a', 'ab\U0001F600', [['\U0001F600a', '\U0001F600b']]))

    def test_k_distance_rearrangement(self):
        self.assertTrue(ok('valid_k_distance_rearrangement', 'acbacb', 'abcabc', ['aabbcc', 3]))
        self.assertFalse(ok('valid_k_distance_rearrangement', 'abcbac', 'abcabc', ['aabbcc', 3]))
        self.assertFalse(ok('valid_k_distance_rearrangement', 'abcab', 'abcabc', ['aabbcc', 3]))
        self.assertTrue(ok('valid_k_distance_rearrangement', '', '', ['aaabc', 3]))
        self.assertFalse(ok('valid_k_distance_rearrangement', 'abaca', '', ['aaabc', 3]))
        self.assertTrue(ok('valid_k_distance_rearrangement', 'ba', 'a', ['a', 0]) is False)
        self.assertTrue(ok('valid_k_distance_rearrangement', 'a', 'a', ['a', 0]))


if __name__ == '__main__':
    unittest.main()
