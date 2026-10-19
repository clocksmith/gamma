import unittest
from pathlib import Path
from unittest.mock import patch
from algsolve.judge import judge
from algsolve.judge.declared_comparison import compare
from algsolve.recognition_release import public_problem


class DeclaredTests(unittest.TestCase):
    @unittest.skipUnless(Path(judge.sandbox.BWRAP).exists(), 'Linux sandbox required')
    def test_declared_public_contract_survives_both_editor_execution_paths(self):
        from algsolve.editor_execution import execute
        problem = {'statement':'Return distinct input integers in any order.',
                   'entry':{'class':'Solution','method':'solve'}, 'params':[['nums','List[int]']],
                   'public_tests':[{'args':[[1,2]],'expected':[1,2], 'compare':'return:unordered_distinct_int'}]}
        for language, code in (
                ('python','class Solution:\n def solve(self, nums): return nums[::-1]'),
                ('javascript','function solve(nums){return nums.slice().reverse();}')):
            with self.subTest(language=language):
                self.assertTrue(execute(language,code,problem)['example_passed'])
                ordered = dict(problem, public_tests=[dict(problem['public_tests'][0],compare='return:exact')])
                self.assertFalse(execute(language,code,ordered)['example_passed'])

    def test_exact_rejects_boolean_and_integer_coercion(self):
        self.assertFalse(compare('return:exact', True, 1))
        self.assertFalse(compare('return:exact', 1.0, 1))
        self.assertTrue(compare('return:exact', [1, {'x':False}], [1, {'x':False}]))

    def test_unordered_contract_preserves_structure_and_multiplicity(self):
        self.assertTrue(compare('return:unordered_distinct_int',[3,1],[1,3]))
        self.assertFalse(compare('return:unordered_distinct_int',[1,1],[1,1]))
        self.assertFalse(compare('return:unordered_distinct_int',[True],[1]))
        mode = 'return:distinct_int_rows'
        self.assertTrue(compare(mode,[[3],[1,2]],[[1,2],[3]]))
        self.assertFalse(compare(mode,[[2,1],[3]],[[1,2],[3]]))
        self.assertFalse(compare(mode,[[1],[1]],[[1],[1]]))

    def test_numeric_tolerance_is_bounded_ordered_and_finite(self):
        mode = 'return:numeric_list_tol_1e-5'
        self.assertTrue(compare(mode,[1.000001,2],[1,2]))
        for actual in ([2,1],[1.01,2],[float('inf'),2],[True,2]):
            self.assertFalse(compare(mode,actual,[1,2]))

    def test_rational_equivalence_without_float_rounding(self):
        mode = 'return:rational_decimal'
        self.assertTrue(compare(mode,'0.1(6)','0.16(6)'))
        self.assertFalse(compare(mode,'0.1666666666666667','0.1(6)'))
        for invalid in ('+1','01','1.0','1e0','-0','0.(9)','0.5(0)','0.'):
            self.assertFalse(compare(mode,invalid,invalid))

    def test_invalid_checker_data_is_not_a_candidate_failure(self):
        with patch.object(judge.sandbox,'run_python') as run:
            verdict = judge.judge_functional('', {}, [judge.FunctionalTest(args=[], expected=[1,1], compare='return:unordered_distinct_int')])
        self.assertEqual(verdict.reason,judge.CHECKER_ERROR)
        run.assert_not_called()

    def test_public_rule_uses_no_oracle_identity(self):
        case = {'query':'Return distinct integers in any order.', 'public_examples':[{'args':[[1]],'expected':[1]}],
                'output_comparison':'unordered list of distinct integers','expected_key':'secret',
                'signature':{'method':'secret'},'private_checks':['secret']}
        public = public_problem(case)
        self.assertEqual(public.entry,{})
        self.assertEqual(public.public_tests[0]['compare'],'return:unordered_distinct_int')
        self.assertNotIn('secret',str(public))
        case['output_comparison']='unknown'
        with self.assertRaises(ValueError):
            public_problem(case)
