import itertools
import random
import unittest
import numpy as np
import dual as d

class DualTests(unittest.TestCase):
    def test_negative_edges_and_tie(self):
        cost,seq=d.encode_objective('abab',['a','b','ab','abab'])
        self.assertEqual(cost,-2);self.assertEqual(seq,[2,2])
        self.assertEqual(d.encode_objective('ab',['a','b'])[0],18)
        with self.assertRaises(ValueError):d.encode_objective('ab',['a'])

    def test_bound_and_forward_replay_exhaustive(self):
        rng=random.Random(25)
        for _ in range(60):
            texts={i:''.join(rng.choices('ab',k=5)) for i in range(2)}
            mandatory=['a','b'] if rng.randrange(2) else []
            pool=([] if mandatory else ['a','b'])+rng.sample(['aa','ab','ba','bb','aaa','aba'],4)
            capacity=rng.randint(2,len(pool));scores=[]
            for k in range(capacity+1):
                for subset in itertools.combinations(pool,k):
                    try:scores.append(d.objective(texts,mandatory+list(subset)))
                    except ValueError:pass
            g=d.Graph(texts,pool,mandatory);lam=np.asarray([rng.random()*20 for _ in g.occ_entry])
            sp,y=g.shortest(lam);sums=np.bincount(g.occ_entry,weights=lam,minlength=len(pool));bound=sp-sum(sorted(sums,reverse=True)[:capacity])
            cert,q=g.certificate(lam,capacity,1000)
            self.assertEqual(cert['numerator'],d.independent_certificate(texts,pool,mandatory,q,capacity,1000))
            if scores:
                self.assertLessEqual(bound,min(scores)+1e-8);self.assertLessEqual(cert['integer_lower_bound'],min(scores))

    def test_encoder_against_exhaustive_paths(self):
        rng=random.Random(251)
        for _ in range(60):
            text=''.join(rng.choices('ab',k=6));vocab=['a','b']+rng.sample(['aa','ab','ba','bb','aaa','aba'],4)
            def paths(i):
                if i==len(text):yield []
                for k,word in enumerate(vocab):
                    if text.startswith(word,i):
                        for rest in paths(i+len(word)):yield [k]+rest
            def key(seq):return (10*sum(len(vocab[k])==1 for k in seq)-len(seq),len(seq),seq)
            expected=min(paths(0),key=key);cost,actual=d.encode_objective(text,vocab)
            self.assertEqual((cost,len(actual),actual),key(expected))

    def test_positive_certificate_and_nonpositive_witness(self):
        g=d.Graph({0:'ab'},[],['a','b']);c,q=g.certificate(np.array([]),0,1000)
        self.assertEqual(c['integer_lower_bound'],18)
        self.assertEqual(d.independent_certificate({0:'ab'},[],['a','b'],q,0,1000),18000)
        self.assertLessEqual(d.objective({0:'abab'},['ab']),0)

    def test_optimizer_with_optional_characters(self):
        rows=[];texts={0:'abab',1:'baba'};pool=['a','b','ab','ba','aba','bab']
        g,r,q,v,gen=d.optimize(texts,pool,[],3,['a','b'],{'iterations':25,'seconds':10,'halve_after':5,'primal_every':5,'denominator':1000},rows.append)
        self.assertLessEqual(r['certificate']['integer_lower_bound'],d.objective(texts,v))
        self.assertEqual(r['certificate']['numerator'],d.independent_certificate(texts,pool,[],q,3,1000))
        self.assertTrue(rows);self.assertLessEqual(len(v),3)

if __name__=='__main__':unittest.main()
