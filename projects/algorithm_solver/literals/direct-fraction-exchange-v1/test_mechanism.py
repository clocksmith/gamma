import itertools
import random
import unittest
import mechanism as m


class ExchangeTests(unittest.TestCase):
    def compare(self,graph,candidate):
        if candidate is None:return
        vocab=sorted(candidate['active']);exact=m.parent.exact(graph.texts,vocab)
        self.assertEqual((candidate['F'],candidate['C'],candidate['N']),(exact['F'],exact['C'],exact['N']))
        for pid,row in exact['per_program'].items():
            self.assertEqual(candidate['rows'][pid]['words'],tuple(vocab[i] for i in row['sequence']))

    def test_exhaustive_tiny_dictionaries_and_all_single_moves(self):
        texts={'x':'abab','y':'baba'};pool=['a','ab','aba','b','ba','bab'];g=m.Graph(texts,pool,4)
        for n in range(1,5):
            for active in itertools.combinations(pool,n):
                try:current=g.initial(active)
                except ValueError:continue
                self.compare(g,current)
                removes=[()]+[(w,) for w in active]
                adds=[()]+[(w,) for w in pool if w not in active]
                for remove,add in itertools.product(removes,adds):
                    if n-len(remove)+len(add)>4:continue
                    candidate,receipt=g.evaluate(current,add,remove)
                    vocab=sorted((set(active)-set(remove))|set(add))
                    try:expected=m.parent.exact(texts,vocab)
                    except ValueError:self.assertIsNone(candidate);self.assertTrue(receipt['coverage_failure']);continue
                    self.assertIsNotNone(candidate);self.compare(g,candidate)

    def test_infeasible_removal_can_have_feasible_improving_swap(self):
        g=m.Graph({'x':'ab'},['a','ab','b'],2);current=g.initial(['a','b'])
        removed,_=g.evaluate(current,remove=['a']);self.assertIsNone(removed)
        swapped,_=g.evaluate(current,add=['ab'],remove=['a']);self.compare(g,swapped)
        self.assertLess(swapped['F'],current['F']);self.assertIs(g.accept(current,swapped),swapped)

    def test_overcapacity_ranking_is_not_retained_or_encoded(self):
        g=m.Graph({'x':'ab'},['a','ab','b'],2);current=g.initial(['a','b'])
        rank,_=g.evaluate(current,add=['ab'],ranking=True)
        self.assertFalse(rank['eligible'])
        with self.assertRaises(AssertionError):g.accept(current,rank)
        with self.assertRaises(AssertionError):g.evaluate(current,add=['ab'])

    def test_unaffected_plans_are_strings_not_renumbered_ids(self):
        g=m.Graph({'x':'ab','y':'cd'},['a','ab','b','c','cd','d'],6)
        current=g.initial(['a','b','c','d'])
        trial,receipt=g.evaluate(current,add=['ab'])
        self.assertEqual(receipt['affected_programs'],1)
        self.assertIs(trial['rows']['y'],current['rows']['y'])
        self.assertEqual(trial['rows']['y']['words'],('c','d'));self.compare(g,trial)
        other,receipt=g.evaluate(trial,remove=['a'])
        self.assertEqual(receipt['affected_programs'],0);self.compare(g,other)

    def test_random_block_moves_equal_full_dp(self):
        rng=random.Random(44)
        for _ in range(30):
            texts={str(p):''.join(rng.choice('abc') for _ in range(7)) for p in range(3)}
            pool=sorted(set('abc')|{t[i:i+2] for t in texts.values() for i in range(6)})
            g=m.Graph(texts,pool,8);current=g.initial('abc')
            for _ in range(10):
                add=rng.sample([w for w in pool if w not in current['active']],2)
                remove=rng.sample(sorted(current['active']),1)
                trial,_=g.evaluate(current,add,remove)
                if trial is not None:self.compare(g,trial)


if __name__=='__main__':unittest.main()
