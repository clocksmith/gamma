"""Invented strings and exact exhaustive tiny checks only."""
import itertools,random,statistics,unittest
import mechanism as m

class MechanismTests(unittest.TestCase):
    def test_capped_paths_penalty_bound_and_unrestricted_embedding(self):
        rng=random.Random(42)
        for case in range(50):
            n=rng.randrange(2,9);texts={'p':'abcdefgh'[:n]};q={'p':[[rng.randrange(10) for _ in m.parent.BINS] for i in range(n)]}
            ends={'p':[set() for _ in range(n)]};ends['p'][0].add(n)
            for i in range(n):
                for j in range(i+2,n+1):
                    if rng.randrange(5)==0:ends['p'][i].add(j)
            def paths(start):
                if start==n:return [(0,0)]
                out=[]
                for end in range(start+1,n+1):
                    if end in ends['p'][start]:continue
                    b=m.parent.bin_index(end-start);edge=(9 if b==0 else -1)*10+q['p'][start][b]
                    out.extend((cost+edge,count+1) for cost,count in paths(end))
                return out
            allpaths=paths(0);exact=m.exact_caps(texts,q,10,ends,n)['p']
            lower,free=m.penalty_caps(texts,q,10,ends,[0,1,5,10,20],range(1,n+1))
            self.assertEqual(free['p'],min(cost for cost,count in allpaths))
            for k in range(1,n+1):
                values=[cost for cost,count in allpaths if count<=k]
                self.assertEqual(exact[k],min(values) if values else None)
                self.assertGreaterEqual(lower['p'][k],free['p'])
                if values:self.assertLessEqual(lower['p'][k],exact[k])
    def test_integer_assignments_match_exhaustive_and_each_other(self):
        rng=random.Random(43)
        for n,counts in [(6,[3,2,1]),(5,[2,1,1,1])]:
            for _ in range(30):
                rows=[[rng.randrange(-30,31) if rng.randrange(6) else None for j in counts] for i in range(n)]
                values=[sum(rows[p][label] for p,label in enumerate(labels)) for labels in itertools.product(range(len(counts)),repeat=n)
                        if [labels.count(j) for j in range(len(counts))]==counts and all(rows[p][label] is not None for p,label in enumerate(labels))]
                expected=min(values) if values else None
                self.assertEqual(m.assignment_flow(rows,counts),expected)
                if len(counts)==3:self.assertEqual(m.three_class_assignment(rows,*counts),expected)
    def test_even_median_union_is_exact_but_150_at32_is_only_necessary(self):
        examples=[[31]*150+[33]*135+[150]*15,[32]*150+[33]*135+[150]*15,[32]*151+[96]*134+[150]*15]
        rng=random.Random(44);examples += [[rng.randrange(1,150) for _ in range(300)] for _ in range(60)]
        for values in examples:
            actual=statistics.median(values)<=32 and sorted(values)[284]<=96
            union=any(sum(v<=a for v in values)>=150 and sum(v<=64-a for v in values)>=151 and sum(v<=96 for v in values)>=285 for a in range(1,33))
            self.assertEqual(actual,union)
            if actual:self.assertGreaterEqual(sum(v<=32 for v in values),150)
        self.assertTrue(statistics.median(examples[0])<=32);self.assertEqual(sum(v<=32 for v in examples[0]),150)
        self.assertGreater(statistics.median(examples[1]),32);self.assertEqual(sum(v<=32 for v in examples[1]),150)
    def test_penalty_grid_rejects_invalid_multiplier(self):
        for grid in ([1],[-1,0],[0,0]):
            with self.assertRaises(AssertionError):m.penalty_caps({'p':'ab'},{'p':[[0]*11]*2},1,{'p':[set(),set()]},grid)

if __name__=='__main__':unittest.main()
