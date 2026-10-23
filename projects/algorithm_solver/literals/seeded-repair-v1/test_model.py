import itertools
import random
import unittest
import model as m

class SeedTests(unittest.TestCase):
    def test_exact_start_and_optional_coverage(self):
        texts={0:'abab',1:'abba'};fixed=['a'];candidates=['b','ab','ba'];seed=['a','b']
        model=m.build(texts,fixed,candidates,2,seed);self.assertEqual(model['initial'],8)
        for warm in (False,True):
            chosen,r=m.solve(model,candidates,warm,10)
            self.assertTrue(r['optimal']);self.assertEqual(m.slot.exact(texts,fixed+chosen)[0],r['objective'])
            self.assertLessEqual(r['objective'],8)

    def test_unknown_or_unencodable_start_rejected(self):
        with self.assertRaises(AssertionError):m.build({0:'ab'},['a'],['b'],1,['a','b','c'])
        with self.assertRaises(ValueError):m.build({0:'ab'},['a'],['b'],1,['a'])

    def test_cold_warm_and_scipy_match_exhaustive(self):
        rng=random.Random(26)
        for _ in range(32):
            texts={i:''.join(rng.choices('ab',k=6)) for i in range(2)}
            fixed=['a','b'] if rng.randrange(2) else [];candidates=([] if fixed else ['a','b'])+rng.sample(['aa','ab','ba','bb','aaa','aba'],4)
            capacity=rng.randint(2,len(candidates));seed=['a','b'];model=m.build(texts,fixed,candidates,capacity,seed)
            scores=[]
            for k in range(capacity+1):
                for subset in itertools.combinations(candidates,k):
                    try:scores.append(m.slot.exact(texts,fixed+list(subset))[0])
                    except ValueError:pass
            expected=min(scores)
            for warm in (False,True):
                chosen,r=m.solve(model,candidates,warm,10);self.assertTrue(r['optimal']);self.assertEqual(r['objective'],expected)
                self.assertEqual(m.slot.exact(texts,fixed+chosen)[0],expected)
            chosen,r=m.slot.solve(texts,fixed,candidates,capacity,10);self.assertEqual(r['objective'],expected)

    def test_zero_budget_preserves_supplied_feasible_point(self):
        texts={0:'ab'*20};fixed=[];candidates=['a','b','ab','ba'];model=m.build(texts,fixed,candidates,2,['a','b'])
        chosen,r=m.solve(model,candidates,True,0)
        self.assertTrue(r['feasible']);self.assertLessEqual(r['objective'],40)
        self.assertEqual(m.slot.exact(texts,chosen)[0],r['objective'])

if __name__=='__main__':unittest.main()
