import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from algsolve import validate
from algsolve.judge import judge, sandbox
from algsolve.judge.functional_semantics import edge_index_groups


class EdgeIndexGroups(unittest.TestCase):
    def test_permutation_preserves_membership_and_group_roles(self):
        args = [4, [[0,1,1],[1,2,1],[2,3,2],[0,3,2]]]
        expected = [[0,1],[2,3]]
        self.assertTrue(edge_index_groups(args,expected,[[1,0],[3,2]]))
        for wrong in ([[2,3],[0,1]], [[0],[2,3]], [[0,0,1],[2,3]],
                      [[0,1],[1,2,3]], [[False,1],[2,3]], [[0,1],[2,4]], None, [[],[]]):
            self.assertFalse(edge_index_groups(args,expected,wrong))
        with self.assertRaises(ValueError): edge_index_groups(args,[[0,0],[]],None)

    def test_host_matcher_keeps_normal_lists_ordered(self):
        args = [3,[[0,1,1],[1,2,1],[0,2,1]]]
        test = judge.FunctionalTest(args=args,expected=[[],[0,1,2]],compare='return:edge_index_groups')
        self.assertTrue(judge._matches(test,{'result':[[],[2,0,1]]}))
        self.assertFalse(judge._matches(test,{}))
        test.compare = 'return'
        self.assertFalse(judge._matches(test,{'result':[[],[2,0,1]]}))

    def test_only_matching_problem_and_method_select_comparison(self):
        p = SimpleNamespace(io_mode='functional',
            slug='find-critical-and-pseudo-critical-edges-in-minimum-spanning-tree',
            entry={'method':'findCriticalAndPseudoCriticalEdges'},cpu_seconds=1,memory_bytes=10000)
        raw = [{'args':[2,[[0,1,1]]], 'expected':[[0],[]]}]
        with patch.object(judge,'judge_functional') as invoke:
            validate.judge_problem(p,'source',raw)
            self.assertEqual(invoke.call_args.args[2][0].compare,'return:edge_index_groups')
            p.entry['method'] = 'other'
            validate.judge_problem(p,'source',raw)
            self.assertEqual(invoke.call_args.args[2][0].compare,'return')

    def test_invalid_expected_groups_fail_before_execution(self):
        test = judge.FunctionalTest(args=[2,[[0,1,1]]],expected=[[0,0],[]],compare='return:edge_index_groups')
        with patch.object(sandbox,'run_python',side_effect=AssertionError('must not execute')):
            verdict = judge.judge_functional('source',{'method':'solve'},[test])
        self.assertEqual(verdict.reason,judge.CHECKER_ERROR)

    @unittest.skipUnless(Path(sandbox.BWRAP).exists() and Path(sandbox.PRLIMIT).exists(), 'Linux sandbox required')
    def test_sandbox_accepts_reordered_groups_but_rejects_wrong_membership(self):
        test = judge.FunctionalTest(args=[3,[[0,1,1],[1,2,1],[0,2,1]]],
                                    expected=[[],[0,1,2]],compare='return:edge_index_groups')
        for answer, accepted in (('[[],[2,0,1]]',True), ('[[0],[2,1]]',False), ('[[],[2,0,0,1]]',False)):
            source = 'class Solution:\n    def solve(self,n,edges):\n        return ' + answer
            verdict = judge.judge_functional(source,{'class':'Solution','method':'solve'},[test])
            self.assertEqual(verdict.passed,accepted)


if __name__ == '__main__': unittest.main()
