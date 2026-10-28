"""Definition-bound source-free controls. No candidate module is imported."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location('continuation_d_case_tests', ROOT / 'cases.py')
cases = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cases)
o = cases.oracle


class ReferenceTests(unittest.TestCase):
    def test_all_official_examples(self):
        for pid, examples in cases.EXAMPLES.items():
            for args, wanted in examples:
                with self.subTest(pid=pid, args=args): self.assertTrue(o.exact(o.reference(pid, args), wanted))

    def test_exact_types_identities_and_full_domain_boundaries(self):
        for pid in (True, '3702', 3702.0, 3723):
            with self.assertRaises(ValueError): o.validate(pid, [[1]])
        invalid = {3702: [[[]], [[True]], [[-1]], [[10**9+1]]],
                   3703: [['(', 1], ['()', True], ['(x', 1], ['()', 2]],
                   3704: [[True], [1], [10**15+1], [2.0]],
                   3708: [[[1, 2]], [[0, 1, 1]], [[1, True, 2]]],
                   3713: [[''], ['A'], ['é']], 3714: [['d'], ['a'*100001]],
                   3719: [[[0]], [[True]], [[1]*1501]],
                   3720: [['a', 'aa'], ['a', 'A']],
                   3721: [[[100001]], [[1]*100001]], 3722: [['a'*1001], ['A']]}
        for pid, inputs in invalid.items():
            for args in inputs:
                with self.subTest(pid=pid), self.assertRaises(ValueError): o.validate(pid, args)
        for pid in o.IDS:
            for case in cases.maximum_cases(pid): o.validate(pid, case['args'])

    def test_reference_budget_does_not_shrink_domain(self):
        inputs = {3702: [[1]*17], 3703: ['('*200+')'*200, 2], 3704: [20001],
                  3708: [[1]*36], 3713: ['a'*25], 3714: ['a'*25],
                  3719: [[1]*31], 3720: ['a'*9, 'b'*9], 3721: [[1]*31], 3722: ['a'*41]}
        for pid, args in inputs.items():
            o.validate(pid, args)
            with self.assertRaises(ValueError): o.reference(pid, args)

    def test_no_zero_pairs_are_ordered_positive_and_closed_form_is_checked(self):
        for digits in range(1, 5):
            self.assertEqual(o.reference(3704, [10**digits]), o.power_ten_no_zero_pairs(digits))
        for n in range(2, 120):
            result = o.reference(3704, [n])
            fixed = n % 2 == 0 and '0' not in str(n//2)
            self.assertEqual(result % 2, int(fixed))
            self.assertLessEqual(result, n-1)
        self.assertLess(cases.maximum_cases(3704)[-1]['expected'], 2**53)

    def test_removal_pattern_has_no_self_overlap_and_cascades(self):
        for k in range(1, 20):
            pattern = '('*k + ')'*k
            self.assertTrue(all(pattern[:i] != pattern[-i:] for i in range(1, len(pattern))))
        self.assertEqual(o.reference(3703, ['(((())))', 2]), '')
        self.assertEqual(o.reference(3703, ['(()())', 2]), '(()())')

    def test_distinct_parity_is_not_occurrence_parity(self):
        for pid in (3719, 3721):
            self.assertEqual(o.reference(pid, [[1, 2, 1]]), 3)
            self.assertEqual(o.reference(pid, [[2, 2, 2]]), 0)
            self.assertEqual(o.reference(pid, [[1, 2, 3, 2]]), 3)

    def test_character_membership_is_optional_in_balance(self):
        for pid in (3713, 3714):
            self.assertEqual(o.reference(pid, ['aaaaa']), 5)
            self.assertEqual(o.reference(pid, ['ababab']), 6)
            self.assertEqual(o.reference(pid, ['abcabc']), 6)
            self.assertEqual(o.reference(pid, ['aabcc']), 3)

    def test_permutation_is_strict_and_preserves_multiset(self):
        for args in (['abbc', 'abcb'], ['a', 'a'], ['abc', 'aaa'], ['aab', 'aba']):
            result = o.reference(3720, args)
            if result:
                self.assertGreater(result, args[1]); self.assertEqual(sorted(result), sorted(args[0]))
            else: self.assertLessEqual(''.join(sorted(args[0], reverse=True)), args[1])

    def test_exactly_one_reverse_may_be_identity(self):
        for s in ('a', 'aaaaa', 'abc', 'cba', 'abba'):
            result = o.reference(3722, [s])
            self.assertLessEqual(result, s); self.assertEqual(sorted(result), sorted(s))

    def test_generation_unique_repeatable_and_input_preserving(self):
        for pid in o.IDS:
            rows = cases.build_cases(pid)
            keys = [repr(row['args']) for row in rows]
            self.assertEqual(len(keys), len(set(keys)))
            for row in rows[:20]:
                before = repr(row['args'])
                self.assertTrue(o.exact(o.reference(pid, row['args']), row['expected']))
                self.assertEqual(before, repr(row['args']))
            self.assertTrue(all(type(row['expected']) in (int, str) for row in rows))


if __name__ == '__main__': unittest.main()
