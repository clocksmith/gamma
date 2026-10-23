import itertools
import random
import unittest
import search as s


def paths(text,vocab):
    if not text:return [()]
    return [(i,)+seq for i,w in enumerate(vocab) if text.startswith(w) for seq in paths(text[len(w):],vocab)]

def key(seq,vocab,w):
    n=len(seq);c=sum(len(vocab[i])==1 for i in seq);return (4*n+w*c,n,c,seq)

class CharacterSearchTests(unittest.TestCase):
    def test_weighted_dp_against_exhaustive_paths(self):
        rng=random.Random(18)
        for _ in range(100):
            text=''.join(rng.choice('ab') for _ in range(rng.randint(0,7)))
            vocab=['a','b']+rng.sample(['aa','ab','ba','bb','aaa','aab','aba','abb'],rng.randint(0,5))
            for w in (0,1,4,16):self.assertEqual(tuple(s.encode(text,vocab,w)),min(paths(text,vocab),key=lambda x:key(x,vocab,w)))
    def test_weight_changes_tradeoff_and_zero_prefers_fewer_characters(self):
        vocab=list('abcdefg')+['abcdef','ab','cd','efg'];text='abcdefg'
        self.assertEqual(len(s.encode(text,vocab,0)),2)
        self.assertEqual(len(s.encode(text,vocab,16)),3)
        self.assertEqual(s.encode('abcd',list('abcd')+['abc','ab','cd'],0),[5,6])
    def test_cached_evaluation_matches_full(self):
        texts={1:'ababaa',2:'bbaabb'};vocab=list(s.v3.base.ALPHABET)+['ab','bb','aa'];budget=s.Budget({'trials':1000,'seconds':60})
        for w in (0,1,4,16):
            base=s.evaluate(texts,vocab,7,w,None,budget)
            for removed,added in [('ab','aba'),('bb','bbb'),('aa','aab')]:
                cand=set(vocab)-{removed}|{added}
                self.assertEqual(s.evaluate(texts,cand,7,w,base,budget),s.evaluate(texts,cand,7,w,None,budget))
    def test_pruning_retains_objective_and_fallback(self):
        texts={1:'abab',2:'abab'};vocab=list(s.v3.base.ALPHABET)+['ab','zz'];budget=s.Budget({'trials':100,'seconds':60})
        state=s.evaluate(texts,vocab,7,4,None,budget);after,removed=s.prune(texts,state,7,4,budget)
        self.assertEqual(removed,['zz']);self.assertEqual(s.cost(state)[:3],s.cost(after)[:3]);self.assertTrue(s.FALLBACK<=set(after['vocab']))
    def test_proposals_require_two_owners_and_exclude_bodies(self):
        texts={1:'abab',2:'abab',3:'xy'};budget=s.Budget({'trials':100,'seconds':60})
        state=s.evaluate(texts,list(s.v3.base.ALPHABET),7,4,None,budget)
        got=s.propose(texts,state,100,{'abab'})
        self.assertIn('ab',got);self.assertNotIn('xy',got);self.assertNotIn('abab',got)
    def test_refill_and_local_search_preserve_legal_incumbent(self):
        texts={1:'ababac',2:'ababac'};budget=s.Budget({'trials':40,'seconds':60});banned=set(texts.values())
        state=s.evaluate(texts,list(s.v3.base.ALPHABET),7,16,None,budget);initial=s.cost(state)
        nb={'additions':10,'swaps':10,'pair_additions':4,'pair_removals':2,'pairs':4}
        state,_=s.refill(texts,state,7,16,banned,nb,4,budget)
        state,stop=s.local_search(texts,state,7,16,banned,nb,budget,[])
        self.assertLess(s.cost(state),initial);self.assertFalse(set(state['vocab'])&banned)
        self.assertTrue(s.FALLBACK<=set(state['vocab']));self.assertLessEqual(len(state['vocab']),128)
        for pid,text in texts.items():self.assertEqual(''.join(state['parsed'][pid]),text)

if __name__=='__main__':unittest.main()
