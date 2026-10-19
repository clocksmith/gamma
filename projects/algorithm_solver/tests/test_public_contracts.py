"""Public contract selection and real-sandbox adversarial comparator checks."""
from dataclasses import replace
import unittest
from algsolve.public_contracts import bind, unordered_outer_declared
from algsolve.records import Problem
from algsolve import validate


def problem(statement='Return the answer in any order.', expected=None):
    return Problem('fixture:order','fixture','order','','',statement,'functional',
                   entry={'class':'Solution','method':'solve'},
                   public_tests=[{'args':[], 'expected':[[1,2],[3,4]] if expected is None else expected}])


class PublicContractsTests(unittest.TestCase):
    def test_complete_positive_clause_only(self):
        self.assertTrue(unordered_outer_declared('Compute all paths. You may return the answer in any order.'))
        self.assertTrue(unordered_outer_declared('The input array is sorted. Return the answer in any order.'))
        for text in ['Do not return the answer in any order.', 'You may return the answer in any order that satisfies the constraints.',
                     'Example 1:\nReturn the answer in any order.', '"Return the answer in any order."',
                     'If the input is empty, return the answer in any order.',
                     'Return the answer in any order. The answer must be sorted.',
                     'Return the answer in any order. Return the answer sorted.',
                     'Return the answer in any order. You must return the answer in ascending order.',
                     'Return the answer in any order. You should return the output in its original order.',
                     'The input can appear in any order.']:
            with self.subTest(text=text):self.assertFalse(unordered_outer_declared(text))

    def test_binding_preserves_explicit_contracts_data_and_original(self):
        p=problem();bound=bind(p)
        self.assertNotIn('compare',p.public_tests[0])
        self.assertEqual(bound.public_tests[0]['compare'],'return:unordered_outer')
        self.assertEqual(bound.public_tests[0]['expected'],p.public_tests[0]['expected'])
        for mode in ['return:exact','return:distinct_int_rows','arg:0']:
            q=replace(p,public_tests=[dict(p.public_tests[0],compare=mode)])
            self.assertIs(bind(q),q)
        q=problem(expected=7);self.assertIs(bind(q),q)

    def test_answer_contract_is_opt_in_and_still_executes_public_checks(self):
        import numpy as np
        from algsolve.answer import answer
        from algsolve.lookup import LookupIndex
        from algsolve.routes import Budget, Context
        from algsolve.splits import IndexEntry
        q=problem(expected=[2,1])
        source='class Solution:\n def solve(self):\n  return [1,2]\n'
        entry=IndexEntry('fixture:order','order','Order',q.statement,'',q.entry,[],[],
                         'Easy',['fixture:source'],[{'code':source,'validated':True}])
        ctx=Context(generator=None,embedder=None,lookup=LookupIndex([entry],np.array([[1.]])),
                    thresholds={'min_score':0,'min_margin':0},classifier=None,entries=[entry],
                    budget=Budget(100,100,1,20,5,2,2,1))
        self.assertEqual(answer(ctx,q)['decision'],'abstain')
        result=answer(ctx,q,public_output_contracts=True)
        self.assertEqual(result['decision'],'answered')
        self.assertTrue(result['attempts'][0]['public']['passed'])
        self.assertEqual(q.public_tests[0]['expected'],[2,1])

    def test_real_judge_retains_inner_order_multiplicity_and_types(self):
        p=bind(problem())
        for value,passed in [('[[3,4],[1,2]]',True),('[[2,1],[3,4]]',False),
                             ('[[1,2],[1,2]]',False),('[[True,2],[3,4]]',False),
                             ('[[1.0,2],[3,4]]',False),('[[1,2]]',False)]:
            with self.subTest(value=value):
                code='class Solution:\n def solve(self):\n  return '+value+'\n'
                verdict=validate.judge_problem(p,code,p.public_tests,wall_seconds=3)
                self.assertEqual(verdict.passed,passed,verdict)
