"""Inert synthetic exact-string tests; never execute candidate programs."""
from pathlib import Path
import importlib.util
import unittest
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('joint_test_search',HERE/'search.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
class JointTests(unittest.TestCase):
    def test_distinct_problem_not_variant_support(self):
        texts={'1:a':'unique_fragment','1:b':'unique_fragment'};owners={key:'1' for key in texts}
        pool,_=s.build_pool(texts,owners,set(),20);self.assertEqual(pool,[])
        texts['2:c']='unique_fragment';owners['2:c']='2';pool,_=s.build_pool(texts,owners,set(),20)
        self.assertIn('unique_fragment',pool)
    def test_balanced_pool_and_whole_solution_bans(self):
        texts={'1:a':'abcdef0123456789'*5,'2:a':'abcdef0123456789'*5};owners={key:key[0] for key in texts}
        pool,stats=s.build_pool(texts,owners,{'abcdef'},3)
        self.assertNotIn('abcdef',pool);self.assertTrue(all(x['retained']<=3 for x in stats));self.assertEqual(len(stats),5)
        self.assertTrue(all(s.bucket(p)is not None for p in pool))
    def test_solution_method_and_solve_body_are_not_entries(self):
        text='class Solution { sample(x) { return x+1; } }\nfunction solve(...a){return new Solution().sample(...a);}'
        banned=s.banned_strings({'1:x':text})
        self.assertIn('return x+1;',banned);self.assertIn('return new Solution().sample(...a);',banned);self.assertIn(text,banned)
    def test_selection_uses_exact_counts_then_characters_then_reference(self):
        rows={'1:a':{'selections':5,'characters':3},'1:b':{'selections':5,'characters':2},'2:a':{'selections':4,'characters':1},'2:b':{'selections':4,'characters':1}}
        chosen,_=s.select_sources(rows,{'1':['1:a','1:b'],'2':['2:a','2:b']},{'1':'1:a','2':'2:b'})
        self.assertEqual(chosen,{'1':'1:b','2':'2:b'})
    def test_cached_graph_matches_full_score_across_joint_choices(self):
        texts={'1:a':'abcdabcd','1:b':'abcd ef','2:a':'abcd ef'};g=s.compact.Graph(texts)
        vocab=s.ALPHABET+['abcd'];rows=g.score(vocab)
        changed=s.ALPHABET+[' ef','abcd'];cached=g.score(changed,rows,(' ef',));self.assertEqual(cached,g.score(changed))
    def test_complementary_pair_join_is_real_adjacency(self):
        g=s.compact.Graph({'1:a':'abcd abcd','2:a':'ab cd'})
        self.assertEqual(s.pair_joins(g,'ab','cd'),2)
        self.assertEqual(s.pair_joins(g,'cd','ab'),0)
    def test_optimizer_independent_exact_encoding(self):
        texts={'1:a':'abab xyxy','1:b':'abab abab','2:a':'abab xyxy'};groups={'1':['1:a','1:b'],'2':['2:a']};refs={'1':'1:a','2':'2:a'}
        cfg={**s.CONFIG,'rounds':2,'evaluations':40,'cpu_seconds':10,'additions_per_bucket':2,'pair_proposals':4}
        vocab,choices,receipt=s.optimize(texts,groups,refs,s.ALPHABET,['ab','xy','abab','xyxy',' abab'],128,'selection',cfg)
        self.assertLessEqual(len(vocab),128);self.assertLessEqual(receipt['evaluations'],40)
        for pid,key in choices.items():
            sequence=s.compare.scorer.shortest_encode(texts[key],vocab)
            self.assertEqual(''.join(vocab[i] for i in sequence),texts[key])
    def test_four_arms_fit_only_policy_is_pinned(self):
        self.assertEqual(s.BUCKETS,((2,4),(5,8),(9,16),(17,32),(33,64)))
        self.assertEqual(s.objective({'x':{'selections':10,'characters':2}},'character-budget'),(10,10,2))
if __name__=='__main__':unittest.main()
