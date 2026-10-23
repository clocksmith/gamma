"""Synthetic checks only; never opens Gamma source/case populations."""
import itertools
import random
import tempfile
from pathlib import Path
import unittest
import engine as e

class EngineTests(unittest.TestCase):
    def test_full_capacity_after_sparse_incumbent(self):
        cfg={'free':2,'top':5,'random':3}
        fixed,cand,capacity=e.proposal(e.sel.ALPHABET+['aa','bb'],['aa','ab','bb'],['ab','aa','bb'],random.Random(1),cfg)
        self.assertEqual(capacity,160);self.assertEqual(set(fixed),set(e.sel.ALPHABET));self.assertEqual(set(cand),{'aa','ab','bb'})

    def test_selected_source_reselection(self):
        variants={1:{'a':'aaaaX','b':'bbbbX'}}
        old=e.choose(variants,e.sel.ALPHABET+['aa']);new=e.choose(variants,e.sel.ALPHABET+['bbbb'])
        self.assertEqual(old['chosen'][1],'a');self.assertEqual(new['chosen'][1],'b')
        self.assertEqual(new['selections'],2)

    def test_solver_matches_exhaustive(self):
        rng=random.Random(4)
        for _ in range(12):
            texts={i:''.join(rng.choices('abc',k=8)) for i in range(2)}
            cand=sorted({t[i:i+2] for t in texts.values() for i in range(7)})[:6]
            chosen,solver=e.lns.repair(texts,e.sel.ALPHABET,cand,2,10)
            self.assertTrue(solver['feasible']);self.assertEqual(solver['status'],0)
            got=e.check_solver(texts,e.sel.ALPHABET+chosen,solver)
            want=min(e.sel.exact_fit(texts,e.sel.ALPHABET+list(s)) for n in range(3) for s in itertools.combinations(cand,n))
            self.assertEqual(got,want)

    def test_solver_objective_rejected(self):
        with self.assertRaises(AssertionError):e.check_solver({1:'aaaa'},e.sel.ALPHABET,{'feasible':True,'objective':3,'status':1})
        with self.assertRaises(AssertionError):e.check_solver({1:'aaaa'},e.sel.ALPHABET,{'feasible':True,'objective':5,'status':0})
        self.assertEqual(e.check_solver({1:'aaaa'},e.sel.ALPHABET,{'feasible':True,'objective':5,'status':1}),4)

    def test_prune_at_cap_retains_incumbent(self):
        budget=e.v3.Budget({'trials':1,'seconds':100});budget.trials=1;state={'vocab':['a']}
        self.assertEqual(e.capped_prune({},state,8,budget),(state,[]));self.assertEqual(budget.trials,1)

    def test_pool_support_and_bans(self):
        pool,ranked=e.ranked_pool({1:'aabb',2:'aacc'},{'aa'},3)
        self.assertNotIn('aa',pool);self.assertNotIn('bb',pool);self.assertEqual(set(pool),set(ranked))

    def test_repair_receipts_and_no_equal_acceptance(self):
        variants={1:{'seed':'aaaaab'},2:{'seed':'aaaaac'}};state=e.choose(variants,e.sel.ALPHABET)
        cfg={'max_length':3,'seed':3,'moves':2,'free':40,'top':30,'random':5,'seconds':20,'solver_seconds':10}
        with tempfile.TemporaryDirectory() as d:
            final,info=e.repairs(variants,state,set(),cfg,Path(d),0)
            self.assertLess(final['selections'],state['selections']);self.assertTrue(info['moves'][0]['accepted'])
            self.assertFalse(info['moves'][1]['accepted']);self.assertTrue((Path(d)/'incumbent-00.json').exists())
            self.assertFalse(info['moves'][0]['validation_loaded'])

    def test_naming_preserves_graph_and_decreases_cost(self):
        text='function solve(a){let longer=a+1;return longer*longer}'
        vocab=e.sel.ALPHABET+['return x*x','let x='];out,stats=e.naming({1:text},vocab,{'sweeps':2,'trials':6000})
        self.assertLessEqual(e.sel.exact_fit(out,vocab),e.sel.exact_fit({1:text},vocab))
        self.assertNotEqual(out[1],text);self.assertGreater(stats['1']['moves'],0)

if __name__=='__main__':unittest.main()
