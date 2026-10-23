from fractions import Fraction
import itertools
import random
import unittest
import ratio as r


def paths(text,vocab):
    if not text:yield [];return
    for code,word in enumerate(vocab):
        if text.startswith(word):
            for rest in paths(text[len(word):],vocab):yield [code]+rest

class RatioTests(unittest.TestCase):
    def test_exhaustive_aggregate_and_ties(self):
        rng=random.Random(21)
        for _ in range(100):
            vocab=['a','b']+rng.sample(['aa','ab','ba','bb','aaa','aba'],4)
            texts={i:''.join(rng.choices('ab',k=5)) for i in range(2)}
            possibilities=[list(paths(t,vocab)) for t in texts.values()]
            def key(seqs):
                C=sum(r.counts(vocab,s)[0] for s in seqs);N=sum(map(len,seqs))
                return Fraction(C,N),N,seqs
            best=min(itertools.product(*possibilities),key=key)
            got,info=r.solve(texts,vocab)
            self.assertEqual(key(tuple(got.values())),key(best))
            proof=r.certificate(texts,vocab,info['p'],info['q'])
            self.assertEqual(sum(x['minimum_transformed_cost'] for x in proof.values()),0)
            self.assertEqual(sum(x['minimum_selections_at_cost'] for x in proof.values()),info['selections'])

    def test_aggregate_not_average_program_fraction(self):
        seq,info=r.solve({1:'abab',2:'x'},['a','b','x','ab','abab'])
        self.assertEqual(seq[1],[3,3]);self.assertEqual(Fraction(info['p'],info['q']),Fraction(1,3))
        # Splitting a learned word lowers the aggregate fraction by increasing N.
        self.assertEqual(info['selections'],3)

    def test_all_character_and_zero_character(self):
        self.assertEqual(r.solve({1:'aaa'},['a'])[1]['p'],1)
        self.assertEqual(r.solve({1:'aaaa'},['a','aa','aaaa'])[0][1],[2])

    def test_certificate_rejects_nonminimum_ratio(self):
        proof=r.certificate({1:'aabb'},['a','b','aa'],1,1)
        self.assertLess(sum(x['minimum_transformed_cost'] for x in proof.values()),0)

    def test_fail_closed_coverage_and_cap(self):
        with self.assertRaises(ValueError):r.solve({1:'x'},['a'])
        with self.assertRaises(ValueError):r.solve({1:''},['a'])
        with self.assertRaises(RuntimeError):r.solve({1:'abab',2:'x'},['a','b','x','ab','abab'],max_iterations=1)

if __name__=='__main__':unittest.main()
