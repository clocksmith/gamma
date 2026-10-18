import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np

from algsolve.description_journey import DescriptionJourney
from algsolve.judge import judge, sandbox
from algsolve.lookup import LookupIndex
from algsolve.lookup import adapt_solution
from algsolve.records import Problem
from algsolve.routes import Budget, Context
from algsolve.splits import IndexEntry


def fixture(expected=5, public=True):
    statement = 'Straight line of houses. Return maximum cash.'
    entry = IndexEntry('lc:fixture','fixture','Fixture',statement,'',{'class':'Solution','method':'f'},
                       [['nums','List[int]']],[],'Easy',['fixture'],
                       [{'code':'class Solution:\n def f(self,nums): return max(nums)','validated':True}],
                       license=['fixture'],attribution=['test'])
    class Embedding:
        def encode(self,*args,**kwargs): return np.array([[1.,0.]])
    context = Context(generator=None,embedder=Embedding(),lookup=LookupIndex([entry],np.array([[1.,0.]])),
                      thresholds={},classifier=None,entries=[entry],budget=Budget(0,0,0,10,5,0,0,1))
    query = Problem('user','user','u','User','','Pick from a straight line of houses for maximum cash.',
                     'functional',starter_code='class Solution:\n def solve(self,nums: List[int]): ...',
                     entry={'class':'Solution','method':'solve'},public_tests=[{'args':[[2,3]],'expected':expected}] if public else [],
                     hidden_tests_path='never_read',reference_solutions=['secret'])
    catalog = {'facets':{'family':{'question':'Family?','values':{'houses':'houses'}},
                         'layout':{'question':'Layout?','values':{'line':'line'}},
                         'output':{'question':'Output?','values':{'cash':'cash'}}},
               'profiles':[{'key':entry.key,'title':'Fixture','contract':statement,
                            'facts':{'family':'houses','layout':'line','output':'cash'},
                            'statement_sha256':hashlib.sha256(statement.encode()).hexdigest()}]}
    thresholds={r:{'min_score':.9,'min_margin':0} for r in ('embedding_only','requirement_selection')}
    return context,query,catalog,thresholds


class DescriptionJourneyTests(unittest.TestCase):
    def test_selection_without_examples_never_returns_code(self):
        journey=DescriptionJourney(*fixture(public=False),route='requirement_selection')
        result=journey.start()
        self.assertEqual(result['reason'],'query_has_no_public_examples')
        self.assertIsNone(result['code'])
        self.assertFalse(journey.query.hidden_tests_path)
        self.assertFalse(journey.query.reference_solutions)

    def test_assisted_route_requires_bound_confirmation_even_with_complete_facts(self):
        journey=DescriptionJourney(*fixture(),route='selection_clarification')
        prompt=journey.start()
        self.assertEqual(prompt['decision'],'confirm')
        self.assertIn('statement',prompt)
        with self.assertRaisesRegex(ValueError,'Confirmation'):
            journey.reply(prompt['question_id'],'yes',reviewed_statement_sha256='wrong')
        self.assertEqual(journey.cancel()['reason'],'cancelled')
        with self.assertRaises(ValueError):journey.reply(prompt['question_id'],'yes')

    def test_candidate_statement_changes_fail_closed(self):
        c,q,profiles,t=fixture()
        c.entries[0].statement='Changed.'
        journey=DescriptionJourney(c,q,profiles,t,route='selection_clarification')
        self.assertEqual(journey.start()['reason'],'profile_statement_changed')

    def test_conflict_does_not_execute_code(self):
        c,q,p,t=fixture();q.statement+=' Use zero-based positions and one-based positions.'
        with patch('algsolve.description_journey.check_stored',side_effect=AssertionError('must not execute')):
            result=DescriptionJourney(c,q,p,t,route='requirement_selection').start()
        self.assertEqual(result['reason'],'conflicting_requirements')

    def test_method_rename_preserves_recursion_and_rejects_helper_collision(self):
        entry=fixture()[0].entries[0]
        code='class Solution:\n def f(self,n): return 1 if n==0 else n*self.f(n-1)'
        namespace={}
        exec(adapt_solution(code,entry,'solve'),namespace)
        self.assertEqual(namespace['Solution']().solve(5),120)
        with self.assertRaisesRegex(ValueError,'collides'):
            adapt_solution(code+'\n def solve(self,n): return 0',entry,'solve')

    @unittest.skipUnless(Path(sandbox.BWRAP).exists(),'Linux sandbox required')
    def test_all_routes_check_original_query_instead_of_selected_problem(self):
        for route in ('embedding_only','requirement_selection','selection_clarification'):
            for expected,accepted in ((5,False),(3,True)):
                journey=DescriptionJourney(*fixture(expected),route=route)
                result=journey.start()
                if result['decision']=='confirm':
                    result=journey.reply(result['question_id'],'yes',
                        reviewed_statement_sha256=result['candidate']['statement_sha256'])
                self.assertEqual(result['decision']=='answered',accepted,(route,result))
                self.assertEqual(result['example_passed'],accepted)
                self.assertGreaterEqual(result['seconds'],0)


if __name__ == '__main__': unittest.main()
