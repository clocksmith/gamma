"""Synthetic deterministic development fixtures, not independent confirmation."""
import copy
import hashlib
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np

from algsolve.requirement_filter import RequirementFilter, explicit_facts, answer_with_policy
from algsolve.lookup import LookupIndex, decide
from algsolve.records import Problem
from algsolve.routes import Budget, Context
from algsolve.splits import IndexEntry


def entry(key, statement):
    return IndexEntry(key, key, key, statement, '', {}, [], [], '', [], references=[])


def profile(statement, **facts):
    return {'statement_sha256': hashlib.sha256(statement.encode()).hexdigest(), 'facts': facts}


class RequirementDevelopment(unittest.TestCase):
    def test_opposites_and_paraphrases_are_generic(self):
        cases = [('houses in a line', 'layout', 'line', 'circle'),
                 ('circle of houses', 'layout', 'circle', 'tree'),
                 ('buy once', 'transactions', 'one', 'unlimited'),
                 ('unlimited transactions', 'transactions', 'unlimited', 'two'),
                 ('no transaction fee', 'fee', 'none', 'per_trade'),
                 ('transaction fee of 3', 'fee', 'per_trade', 'none'),
                 ('one-day cooldown', 'cooldown', 'one_day', 'none'),
                 ('no waiting days', 'cooldown', 'none', 'one_day'),
                 ('counting positions from one', 'indexing', 'one', 'zero'),
                 ('zero-based positions', 'indexing', 'zero', 'one'),
                 ('after each insertion', 'updates', 'stream', 'batch'),
                 ('one fixed input', 'updates', 'batch', 'stream'),
                 ('count each distinct value once', 'duplicates', 'distinct', 'occurrences'),
                 ('counting duplicate occurrences separately', 'duplicates', 'occurrences', 'distinct'),
                 ('return any ordering', 'output', 'order', 'possible'),
                 ('true or false', 'output', 'possible', 'order'),
                 ('no cell changes', 'changes', 'none', 'one_flip'),
                 ('flip one zero', 'changes', 'one_flip', 'none')]
        for text, facet, expected, opposite in cases:
            with self.subTest(text=text):
                es = [entry('arbitrary-name-a', 'contract A'), entry('renamed-B', 'contract B')]
                lookup = LookupIndex(es, np.zeros((2, 1)))
                policy = RequirementFilter([profile('contract A', **{facet: opposite}), profile('contract B', **{facet: expected})])
                cs = [{'key': es[0].key, 'score': .9}, {'key': es[1].key, 'score': .8}]
                before = copy.deepcopy(cs)
                kept, trace = policy.apply(text, cs, lookup)
                self.assertEqual(kept, cs[1:]); self.assertEqual(cs, before)
                self.assertTrue(trace['audit'][0]['contradictions'][0]['query_evidence'])
                # Renaming/permuting candidates cannot change semantic decisions.
                kept2, _ = policy.apply(text, list(reversed(cs)), lookup)
                self.assertEqual(kept2, kept)

    def test_unknown_negated_and_hypothetical_wording_does_not_supply_fact(self):
        for text in ['not unsorted', 'not no fees', 'do not flip one zero',
                     'not a straight street', 'maybe houses in a circle',
                     'if there is a one-day cooldown', 'either houses in a line or houses in a circle',
                     '"houses in a circle" is merely an example', 'a winding boulevard']:
            with self.subTest(text=text):
                self.assertEqual({k:v for k,v in explicit_facts(text)['facts'].items() if k != 'family'}, {})

    def test_coordinated_absence_is_conjunction_not_alternative(self):
        for text in ['no fees or waiting days', 'no cooldown or transaction fee',
                     'no transaction fee nor cooldown', 'no waiting day or fees or cooldown']:
            with self.subTest(text=text):
                parsed = explicit_facts(text)
                self.assertEqual(parsed['facts']['fee'], 'none')
                self.assertEqual(parsed['facts']['cooldown'], 'none')
                self.assertNotIn('transactions', parsed['facts'])
                self.assertTrue(parsed['evidence']['cooldown']['none'])
                es = [entry('a', 'A'), entry('b', 'B'), entry('unknown', 'unknown')]
                lookup = LookupIndex(es, np.zeros((3, 1)))
                cs = [{'key': e.key, 'score': .9-i/10} for i, e in enumerate(es)]
                policy = RequirementFilter([profile('A', fee='none', cooldown='one_day'),
                                            profile('B', fee='none', cooldown='none')])
                kept, trace = policy.apply(text, cs, lookup)
                self.assertEqual(kept, cs[1:])
                self.assertEqual(cs[0]['score'], .9)
                self.assertEqual(trace['audit'][0]['contradictions'][0]['facet'], 'cooldown')
                self.assertIsNone(trace['audit'][2]['source_facts'])

    def test_coordinated_absence_does_not_erase_uncertainty_or_invent_defaults(self):
        for text in ['not no fees or waiting days', 'if no fees or waiting days',
                     '"no fees or waiting days" is merely a label',
                     'no fees or waiting days or one-day cooldown',
                     'either no fees or waiting days', 'no fees or waiting days might apply']:
            with self.subTest(text=text):
                parsed = explicit_facts(text)
                self.assertNotIn('fee', parsed['facts'])
                self.assertNotIn('cooldown', parsed['facts'])
        self.assertNotIn('transactions', explicit_facts('No fees or waiting days.')['facts'])
        self.assertNotIn('duplicates', explicit_facts('Return the rank-th largest value.')['facts'])
        # Ordinary alternatives still supply no cardinality assertion.
        self.assertNotIn('transactions', explicit_facts('Buy once or abstain.')['facts'])

    def test_opt_in_zero_action_option_preserves_only_explicit_transaction_bound(self):
        for text, value in [('Buy once and then sell on a later day, or do nothing', 'one'),
                            ('At most two transactions, or do nothing', 'two'),
                            ('Unlimited transactions or do nothing', 'unlimited')]:
            with self.subTest(text=text):
                self.assertNotIn('transactions', explicit_facts(text)['facts'])
                parsed = explicit_facts(text, allow_noop_option=True)
                self.assertEqual(parsed['facts']['transactions'], value)
                self.assertNotIn('fee', parsed['facts'])
                self.assertNotIn('cooldown', parsed['facts'])
        for text in ['Buy once or unlimited transactions', 'Maybe buy once or do nothing',
                     'If buy once or do nothing', '"Buy once or do nothing"',
                     'Buy once or sell twice or do nothing', 'Buy once or do nothing else',
                     'Buy once or abstain', 'Do nothing', 'Not buy once or do nothing']:
            with self.subTest(text=text):
                self.assertNotIn('transactions', explicit_facts(text, allow_noop_option=True)['facts'])
        es = [entry('a', 'A'), entry('b', 'B')]
        lookup = LookupIndex(es, np.zeros((2, 1)))
        cs = [{'key': 'a', 'score': .9}, {'key': 'b', 'score': .8}]
        ps = [profile('A', transactions='unlimited'), profile('B', transactions='one')]
        query = 'Buy once or do nothing.'
        self.assertEqual(RequirementFilter(ps).apply(query, cs, lookup)[0], cs)
        kept, trace = RequirementFilter(ps, allow_noop_option=True).apply(query, cs, lookup)
        self.assertEqual(kept, cs[1:])
        self.assertEqual(trace['pre_filter'], cs)

    def test_conflicts_abstain_without_erasing_candidates(self):
        es=[entry('x','x')];lookup=LookupIndex(es,np.zeros((1,1)))
        cs=[{'key':'x','score':.9}]
        kept,trace=RequirementFilter([profile('x',layout='circle')]).apply('houses in a line. houses in a circle.',cs,lookup)
        self.assertEqual(kept,[]);self.assertEqual(trace['reason'],'conflicting_requirements')
        self.assertEqual(trace['pre_filter'],cs);self.assertFalse(trace['audit'][0]['excluded'])

    def test_unknown_profiles_and_missing_facts_preserve_order_scores(self):
        es=[entry('x','x'),entry('y','y'),entry('z','z')];lookup=LookupIndex(es,np.zeros((3,1)))
        cs=[{'key':e.key,'score':.6-i/100} for i,e in enumerate(es)]
        policy=RequirementFilter([profile('stale x',layout='circle'),profile('y',output='cash')])
        kept,trace=policy.apply('houses in a line',cs,lookup)
        self.assertEqual(kept,cs);self.assertFalse(trace['audit'][0]['profile_bound'])
        self.assertIsNone(trace['audit'][2]['source_facts'])
        # No threshold bypass: retaining one source below the floor still fails.
        self.assertEqual(decide(kept[:1],{'min_score':.7,'min_margin':.02}).decision,'abstain')

    def test_sorted_input_does_not_contradict_arbitrary_input_support(self):
        es=[entry('x','x')];lookup=LookupIndex(es,np.zeros((1,1)));cs=[{'key':'x','score':.8}]
        self.assertEqual(RequirementFilter([profile('x',ordering='arbitrary')]).apply('sorted input',cs,lookup)[0],cs)
        self.assertEqual(RequirementFilter([profile('x',ordering='sorted')]).apply('unsorted input',cs,lookup)[0],[])

    def test_existing_numeric_and_sibling_gates_remain_effective(self):
        from algsolve.approved_library import ApprovedLibrary
        es=[entry('alpha','A'),entry('beta','B')]
        es[0].slug='unrelated-name';es[1].slug='unrelated-name-ii'
        lookup=LookupIndex(es,np.zeros((2,1)))
        cs=[{'key':'alpha','score':.8},{'key':'beta','score':.79}]
        kept,_=RequirementFilter([]).apply('unknown wording',cs,lookup)
        self.assertEqual(kept,cs)
        self.assertFalse(ApprovedLibrary.__new__(ApprovedLibrary).identity_check(es[0],kept,lookup,minimum_margin=.004)['accepted'])
        self.assertEqual(decide(kept,{'min_score':.7,'min_margin':.02}).decision,'abstain')

    def test_duplicate_source_hash_conflicts_rejected(self):
        with self.assertRaises(ValueError):RequirementFilter([profile('x',layout='line'),profile('x',layout='circle')])

    def test_adapter_never_filters_exact_or_missing_example_paths(self):
        es=[entry('x','x')];lookup=LookupIndex(es,np.zeros((1,1)))
        query=Problem('u','user','i','','','x','functional',public_tests=[{'args':[], 'expected':1}])
        context=Context(generator=None,embedder=SimpleNamespace(encode=lambda *a,**k: (_ for _ in ()).throw(AssertionError('encode'))),lookup=lookup,thresholds={'min_margin':.01},classifier=None,entries=es,budget=Budget(1,1,0,30,5,1,1,10))
        class Approved:
            def identity_check(self,*a,**kw):return {'accepted':True}
            def check(self,*a):return {'approved':False,'reason':'not_qualified'}
        policy=SimpleNamespace(apply=lambda *a: (_ for _ in ()).throw(AssertionError('policy')))
        result=answer_with_policy(context,query,Approved(),policy)
        self.assertEqual(result['reason'],'stored_answer_not_approved');self.assertNotIn('requirement_filter',result)
        query.public_tests=[]
        self.assertEqual(answer_with_policy(context,query,Approved(),policy)['reason'],'query_has_no_public_examples')

    def test_unapproved_survivor_and_public_failure_do_not_try_next(self):
        from algsolve.answer import answer
        es=[entry('a','contract a'),entry('b','contract b')]
        lookup=LookupIndex(es,np.zeros((2,1)));lookup.scored_candidates=lambda *a:[{'key':'a','score':.9},{'key':'b','score':.7}]
        context=Context(generator=None,embedder=SimpleNamespace(encode=lambda *a,**k: np.zeros((1,1))),lookup=lookup,thresholds={'min_score':.6,'min_margin':.01},classifier=None,entries=es,budget=Budget(1,1,0,30,5,1,1,10))
        query=Problem('u','user','i','','','houses in a line','functional',public_tests=[{'args':[], 'expected':1}])
        policy=RequirementFilter([])
        class Approved:
            def identity_check(self,*a,**kw):return {'accepted':True}
            def check(self,*a):return {'approved':False,'reason':'not_qualified'}
        result=answer_with_policy(context,query,Approved(),policy)
        self.assertEqual(result['source']['key'],'a');self.assertEqual(result['reason'],'stored_answer_not_approved')
        es[0].references=[{'code':'fixture'}]
        with patch.object(Approved,'check',return_value={'approved':True}),patch('algsolve.answer.check_stored') as check:
            check.return_value=(None,SimpleNamespace(passed=False,reason='wrong_answer',to_dict=lambda:{'passed':False,'reason':'wrong_answer'}))
            result=answer_with_policy(context,query,Approved(),policy)
            self.assertEqual(result['decision'],'abstain');self.assertEqual(check.call_count,1)
        # Default control remains the actual unmodified route.
        self.assertEqual(answer(context,query,approved_library=Approved())['reason'],'stored_answer_not_approved')

if __name__=='__main__':unittest.main()
