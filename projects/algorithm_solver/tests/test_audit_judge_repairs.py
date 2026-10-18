import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from algsolve import validate
from algsolve.judge import judge, sandbox
from algsolve.judge.functional_semantics import alphabet_board_path, nonaverage_neighbors, unordered_outer


class OutputSemanticsTests(unittest.TestCase):
    def test_invalid_test_domain_is_not_a_wrong_solution(self):
        from algsolve.library_audit import independent_status
        self.assertEqual(independent_status([{'passed':False,'reason':'checker_error','tests_total':100}]),
                         'unusable_independent_tests')
        self.assertEqual(independent_status([{'passed':False,'reason':'wrong_answer','tests_total':100}]), 'failed')
        self.assertEqual(independent_status([{'passed':True,'reason':None,'tests_total':0}]), 'missing_tests')

    def test_outer_order_does_not_allow_inner_permutation_or_duplicates(self):
        expected = [[0,1,3],[0,2,3]]
        self.assertTrue(unordered_outer(expected,expected[::-1]))
        for wrong in ([[0,3,1],[0,2,3]], [[0,1,3],[0,1,3]], [[0,1,3]], None):
            self.assertFalse(unordered_outer(expected,wrong))
        self.assertFalse(unordered_outer([1],[True]))

    def test_board_checks_moves_target_and_optimal_length_including_z(self):
        for target,path in [('leet','RDD!UURRR!!DDD!'),('z','DDDDD!'),('za','DDDDD!UUUUU!')]:
            self.assertTrue(alphabet_board_path([target],path))
        for target,path in [('a','RL!'),('z','RDDDDDL!'),('z','DDDD!'),('a','?'),('za','DDDDD!')]:
            self.assertFalse(alphabet_board_path([target],path))

    def test_nonaverage_checks_permutation_types_and_every_internal_position(self):
        args = [[1,2,3,4,5]]
        self.assertTrue(nonaverage_neighbors(args,[1,4,2,5,3]))
        for wrong in ([1,2,3,4,5],[1,4,2,5,5],[True,4,2,5,3],[1,4,2],None):
            self.assertFalse(nonaverage_neighbors(args,wrong))

    def test_semantics_require_both_identity_and_method(self):
        p = SimpleNamespace(io_mode='functional',slug='accounts-merge',entry={'method':'accountsMerge'},
                            cpu_seconds=1,memory_bytes=10000)
        with patch.object(judge,'judge_functional') as invoke:
            validate.judge_problem(p,'code',[{'args':[], 'expected':[]}])
            self.assertEqual(invoke.call_args.args[2][0].compare,'return:unordered_outer')
            p.slug = 'other'
            validate.judge_problem(p,'code',[{'args':[], 'expected':[]}])
            self.assertEqual(invoke.call_args.args[2][0].compare,'return')

    @unittest.skipUnless(Path(sandbox.BWRAP).exists(), 'Linux sandbox required')
    def test_modular_pow_and_explicit_candidate_imports(self):
        for source,expected in [
            ('class Solution:\n def solve(self): return pow(2,10,1000)',24),
            ('from math import pow\nclass Solution:\n def solve(self): return pow(2,3)',8.0),
        ]:
            result = judge.judge_functional(source,{'class':'Solution','method':'solve'},
                                           [judge.FunctionalTest(args=[],expected=expected)])
            self.assertTrue(result.passed,result)

    @unittest.skipUnless(Path(sandbox.BWRAP).exists(), 'Linux sandbox required')
    def test_wrong_board_output_stays_rejected_in_sandbox(self):
        for path,accepted in [('RDD!UURRR!!DDD!',True),('DDR!UURRR!!DD!',False)]:
            result = judge.judge_functional('class Solution:\n def solve(self,x): return '+repr(path),
                {'class':'Solution','method':'solve'},[judge.FunctionalTest(args=['leet'],expected='unused',
                                                                         validator='alphabet_board_path')])
            self.assertEqual(result.passed,accepted,result)


if __name__ == '__main__': unittest.main()
