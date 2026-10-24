import itertools
import random
import unittest
import prototype as m


def exhaustive(text,pool,active):
    def visit(at):
        if at==len(text):yield ();return
        for entry,word in enumerate(pool):
            if word in active and text.startswith(word,at):
                for tail in visit(at+len(word)):yield (entry,)+tail
    paths=list(visit(0))
    if not paths:return None
    ids=min(paths,key=lambda ids:(len(ids),ids));words=tuple(pool[i] for i in ids)
    return {'N':len(ids),'C':sum(len(w)==1 for w in words),'words':words,'pool_ids':ids,'used':frozenset(words)}


class CanonicalTests(unittest.TestCase):
    def assert_exact(self,g,active,candidate):
        rows={pid:exhaustive(text,g.pool,active) for pid,text in g.texts.items()}
        if any(row is None for row in rows.values()):self.assertIsNone(candidate);return
        self.assertIsNotNone(candidate);self.assertEqual(rows,candidate['rows'])
        N=sum(r['N'] for r in rows.values());C=sum(r['C'] for r in rows.values())
        self.assertEqual((C,N),(candidate['C'],candidate['N']))
        self.assertEqual(candidate['eligible'],len(active)<=g.capacity and all(r['N']<=g.caps[p] for p,r in rows.items()))

    def test_exhaustive_dictionaries_and_all_moves(self):
        texts={'x':'abab','y':'baba'};pool=['a','ab','aba','b','ba','bab'];g=m.Graph(texts,pool,['a','b'],4,banned=texts.values())
        count=0
        for size in range(1,5):
            for words in itertools.combinations(pool,size):
                try:current=g.initial(words)
                except ValueError:continue
                self.assert_exact(g,set(words),current)
                if not current['eligible']:continue
                for remove,add in itertools.product([()]+[(w,) for w in words],[()]+[(w,) for w in pool if w not in words]):
                    active=(set(words)-set(remove))|set(add)
                    if len(active)>4:continue
                    result,_=g.evaluate(current,add,remove);self.assert_exact(g,active,result);count+=1
        self.assertGreater(count,400)

    def test_canonical_tie_is_not_minimum_character_or_F(self):
        g=m.Graph({'p':'abcd'},['a','ab','bcd','cd'],['a','ab','bcd','cd'],4,banned=['abcd'])
        self.assertEqual(g.seed['rows']['p']['words'],('a','bcd'));self.assertEqual(g.seed['C'],1)
        old=m.parent.parent.exact(g.texts,sorted(g.seed['active']))
        self.assertEqual(old['C'],0)

    def test_per_program_cap_rejects_lower_total_N(self):
        g=m.Graph({'x':'abx','y':'ccccx'},['a','ab','b','c','cc','x'],['a','ab','b','c','x'],5,banned=['abx','ccccx'])
        result,receipt=g.evaluate(g.seed,add=['cc'],remove=['ab'])
        self.assertLess(result['N'],g.seed['N']);self.assertEqual(receipt['cap_failures'],['x']);self.assertFalse(result['eligible'])
        with self.assertRaises(AssertionError):g.accept(g.seed,result)

    def test_uncovered_removal_joint_swap_and_optional_character(self):
        g=m.Graph({'p':'abx'},['a','ab','b','x'],['a','b','x'],3,banned=['abx'])
        removed,_=g.evaluate(g.seed,remove=['a']);self.assertIsNone(removed)
        swapped,_=g.evaluate(g.seed,add=['ab'],remove=['a']);self.assertTrue(swapped['eligible']);self.assertLess(swapped['objective'],g.seed['objective'])
        best,receipt=m.sweep(g,g.seed);self.assertTrue(receipt['strict_improvement'])
        self.assertIn(('swap',(g.ids['ab'],),(g.ids['a'],)),receipt['opportunities'])
        rank,_=g.evaluate(g.seed,add=['ab'],ranking=True);self.assertFalse(rank['eligible'])
        with self.assertRaises(AssertionError):g.accept(g.seed,rank)
        with self.assertRaises(AssertionError):m.Graph({'p':'abx'},['a','abx','b','x'],['a','b','x'],3,banned=['abx'])

    def test_exact_ratio_big_integers_and_ties(self):
        n=10**30
        self.assertEqual(float((n-1)/n),float((n-2)/n))
        self.assertLess(m.objective(n-2,n,10),m.objective(n-1,n,10))
        self.assertLess(m.objective(1,2,100),m.objective(2,4,1))
        self.assertLess(m.objective(1,2,99),m.objective(1,2,100))
        # Lower total C alone can worsen aggregate fraction.
        self.assertGreater(m.objective(4,5,10),m.objective(5,10,10))

    def test_cache_unchanged_ids_random_moves(self):
        g=m.Graph({'p':'ab','q':'cd'},['a','ab','b','c','cd','d'],['a','b','c','d'],6)
        result,receipt=g.evaluate(g.seed,add=['ab']);self.assertEqual(receipt['affected_programs'],1)
        self.assertIs(result['rows']['q'],g.seed['rows']['q']);self.assertEqual(result['rows']['q']['pool_ids'],(3,5))
        after,receipt=g.evaluate(result,remove=['a']);self.assertEqual(receipt['affected_programs'],0);self.assert_exact(g,after['active'],after)
        rng=random.Random(47)
        for _ in range(30):
            texts={str(i):''.join(rng.choice('abc') for _ in range(7)) for i in range(3)}
            pool=sorted(set('abc')|{t[k:k+2] for t in texts.values() for k in range(6)})
            g=m.Graph(texts,pool,['a','b','c'],8,banned=texts.values());current=g.seed
            for _ in range(10):
                add=rng.sample([w for w in pool if w not in current['active']],2);remove=rng.sample(sorted(current['active']),1)
                candidate,_=g.evaluate(current,add,remove);self.assert_exact(g,(current['active']-set(remove))|set(add),candidate)
                if candidate is not None and candidate['eligible']:current=candidate


if __name__=='__main__':unittest.main()
