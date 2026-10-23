import itertools
import random
import unittest
import repair as r

class CoverageTests(unittest.TestCase):
    def test_missing_character_is_not_free(self):
        chosen,info=r.solve({1:'ab'},['a'],['bb'],1,10)
        self.assertFalse(info['feasible'])
        chosen,info=r.solve({1:'ab'},['a'],['b'],1,10)
        self.assertTrue(info['feasible']);self.assertEqual(chosen,['b']);self.assertEqual(info['objective'],2)

    def test_multiple_character_entry_can_cover_removed_character(self):
        chosen,info=r.solve({1:'ab',2:'abab'},[],['a','b','ab'],1,10)
        self.assertEqual(chosen,['ab']);self.assertEqual(info['objective'],3)
        self.assertEqual(r.exact({1:'ab',2:'abab'},chosen)[0],3)

    def test_exact_mixed_character_and_string_bruteforce(self):
        rng=random.Random(24)
        for _ in range(40):
            texts={i:''.join(rng.choices('ab',k=5)) for i in range(2)}
            candidates=['a','b']+rng.sample(['aa','ab','ba','bb','aaa','aba'],3);capacity=rng.randint(1,4)
            scores=[]
            for k in range(capacity+1):
                for vocab in itertools.combinations(candidates,k):
                    try:scores.append(r.exact(texts,list(vocab))[0])
                    except ValueError:pass
            chosen,info=r.solve(texts,[],candidates,capacity,10)
            self.assertEqual(info['feasible'],bool(scores))
            if scores:
                self.assertEqual(info['status'],0);self.assertEqual(r.exact(texts,chosen)[0],min(scores));self.assertEqual(info['objective'],min(scores))

    def test_reserved_unseen_and_matched_free_budget(self):
        vocab=r.ALPHABET+[chr(65+i//10)+str(i) for i in range(100)];observed=set('ab12');reserved=set(r.ALPHABET)-observed
        cfg={'free_characters':8,'priority_characters':4,'free_total':48,'top':3,'random':2}
        for mode in ('fixed96','optional'):
            fixed,candidates,cap,stats=r.proposal(vocab,observed,reserved,['ab','ba'],['ab','ba'],random.Random(24),mode,cfg,{'a':1,'b':0,'1':0,'2':3})
            self.assertEqual(stats['freed_characters']+stats['freed_learned'],48)
            self.assertEqual(cap,256-len(fixed));self.assertTrue(reserved<=set(fixed));self.assertFalse(set(fixed)&set(candidates))
            self.assertEqual(stats['freed_characters'],4 if mode=='optional' else 0)

if __name__=='__main__':unittest.main()
