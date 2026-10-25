"""Synthetic representation checks. No program execution or private inputs."""
import unittest
from unittest.mock import patch
import search

class SearchTests(unittest.TestCase):
    def test_pool_requires_distinct_programs_and_bans_solutions(self):
        texts={'a':'abcabcabc','b':'abcdef'}
        pool=search.build_pool(texts,{'abc'})
        self.assertIn('ab',pool);self.assertNotIn('abc',pool);self.assertNotIn('bca',pool)
        self.assertTrue(all(2<=len(p)<=64 and sum(p in t for t in texts.values())>=2 for p in pool))
    def test_solve_bodies_are_banned(self):
        text='function solve(a){return a;}'
        banned=search.forbidden({'a':text})
        self.assertTrue({text,'{return a;}','return a;'}<=banned)
        with self.assertRaises(ValueError):search.forbidden({'a':'class Solution {}'})
    def test_helpers_and_opaque_braces_do_not_hide_solve_body(self):
        text='function F(){return "}";}function solve(a){let r=/[}]/;return a;}class Extra{}'
        banned=search.forbidden({"x":text})
        self.assertIn("{let r=/[}]/;return a;}",banned)
        self.assertIn("let r=/[}]/;return a;",banned)
        with self.assertRaises(ValueError):search.forbidden({"x":"function solve(){return `${x+1}`;}"})

    def test_exact_graph_and_incremental_equal_independent_scorer(self):
        texts={'a':'abacabac','b':'zzabczz','c':'xxxx'}
        graph=search.Graph(texts);initial=search.ALPHABET+['ab','ac','zz']
        rows=graph.score(initial)
        changed=search.ALPHABET+['aba','ac','zz']
        incremental=graph.score(changed,rows,('ab','aba'))
        self.assertEqual(incremental,graph.score(changed))
        self.assertIs(incremental['c'],rows['c'])
        for pid,text in texts.items():
            self.assertEqual(incremental[pid]['used'],[changed[i] for i in search.compare.scorer.shortest_encode(text,changed)])
    def test_character_budget_is_not_selection_objective(self):
        rows={'x':{'selections':100,'characters':20}}
        self.assertEqual(search.objective(rows,'selection'),(100,20))
        self.assertEqual(search.objective(rows,'character-budget'),(100,100,20))
    def test_search_matches_full_rescore_reference(self):
        texts={'a':'abcabcxyz','b':'abcxyzxyz'};initial=search.ALPHABET+['ab','xy']
        pool=search.build_pool(texts,set());original=search.Graph.score
        for arm in ('selection','character-budget'):
            with patch.object(search,'MAX_ROUNDS',2),patch.object(search,'MAX_EVALUATIONS',60):
                expected,trace=search.optimize(texts,initial,pool,98,arm)
                def full(self,vocab,previous=None,changed=()):return original(self,vocab)
                with patch.object(search.Graph,'score',full):actual,other=search.optimize(texts,initial,pool,98,arm)
            self.assertEqual(actual,expected);self.assertEqual(trace['trace'],other['trace']);self.assertEqual(trace['evaluations'],other['evaluations'])
    def test_measurement_roundtrips_and_counts_full_cost(self):
        profile,binary=search.compare.measure({'a':'abcabc'},search.ALPHABET+['abc'],7)
        self.assertEqual(profile['selections'],2)
        self.assertEqual(profile['package_bytes'],len(binary['dictionary'])+len(binary['packets']['a']))
        self.assertGreater(profile['package_plus_decoder_bytes'],profile['package_bytes'])

if __name__=='__main__':unittest.main()
