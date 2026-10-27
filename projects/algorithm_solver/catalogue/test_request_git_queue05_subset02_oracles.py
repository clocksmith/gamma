"""Source-free unit and cross-reference checks; no statement/candidate reads."""
from functools import lru_cache
from itertools import product
from math import gcd
import random
import unittest
from . import request_git_queue05_subset02_oracles as o
from . import imported_qualification as q

class Queue05Subset02Tests(unittest.TestCase):
    def test_official_examples(self):
        examples=[(2585,[6,[[6,1],[3,2],[2,3]]],7),(2585,[5,[[50,1],[50,2],[50,5]]],4),(2585,[18,[[6,1],[3,2],[2,3]]],1),
            (2654,[[2,6,3,4]],4),(2654,[[2,10,6,14]],-1),
            (2662,[[1,1],[4,5],[[1,2,3,3,2],[3,4,4,5,1]]],5),
            (2662,[[3,2],[5,7],[[5,7,3,2,1],[3,2,3,4,4],[3,3,5,5,5],[3,4,5,6,6]]],7),
            (2662,[[1,1],[10,4],[[4,2,1,1,3],[1,2,7,4,4],[10,3,6,1,2],[6,1,1,2,3]]],8),
            (2698,[10],182),(2698,[37],1478),(2712,['0011'],2),(2712,['010101'],9)]
        for pid,args,want in examples:
            with self.subTest(pid=pid):self.assertTrue(q.exact(o.expected(pid,args),want))

    def test_quantities_against_polynomial_coefficients(self):
        rng=random.Random(25052)
        for _ in range(120):
            target=rng.randint(1,25);types=[[rng.randint(1,4),rng.randint(1,5)] for _ in range(rng.randint(1,5))]
            dp=[1]+[0]*target
            for count,marks in types:
                dp=[sum(dp[score-used*marks] for used in range(count+1) if score>=used*marks)%o.MOD for score in range(target+1)]
            self.assertEqual(o.expected(2585,[target,types]),dp[target])
        self.assertEqual(o.expected(2585,[1,[[1,1],[1,1]]]),2)

    def test_large_composition_identity_against_convolution(self):
        for target,count in [(1000,50),(20,50),(25,1),(1000,1),(1,50)]:
            dp=[1]+[0]*target
            for _ in range(50):
                dp=[sum(dp[t-c] for c in range(min(count,t)+1))%o.MOD for t in range(target+1)]
            self.assertEqual(o.bounded_compositions(target,50,count),dp[target])

    def test_gcd_state_graph_against_first_one_bound(self):
        for n in range(2,6):
            for nums in product((1,2,3,6),repeat=n):
                if 1 in nums:want=n-nums.count(1)
                else:
                    lengths=[]
                    for i in range(n):
                        g=0
                        for j in range(i,n):
                            g=gcd(g,nums[j])
                            if g==1:lengths.append(j-i+1)
                    want=min(lengths)+n-2 if lengths else -1
                self.assertEqual(o.expected(2654,[list(nums)]),want)

    def test_explicit_grid_against_endpoint_floyd_warshall(self):
        rng=random.Random(266205)
        for _ in range(100):
            start=[1,1];target=[rng.randint(2,5),rng.randint(2,5)]
            roads=[[rng.randint(1,target[0]),rng.randint(1,target[1]),rng.randint(1,target[0]),rng.randint(1,target[1]),rng.randint(1,10)] for _ in range(rng.randint(1,6))]
            points=list(dict.fromkeys([tuple(start),tuple(target)]+[tuple(r[k:k+2]) for r in roads for k in (0,2)]))
            index={p:i for i,p in enumerate(points)}
            d=[[abs(x-u)+abs(y-v) for u,v in points] for x,y in points]
            for x,y,u,v,c in roads:d[index[x,y]][index[u,v]]=min(d[index[x,y]][index[u,v]],c)
            for k in range(len(points)):
                for i in range(len(points)):
                    for j in range(len(points)):d[i][j]=min(d[i][j],d[i][k]+d[k][j])
            self.assertEqual(o.expected(2662,[start,target,roads]),d[index[tuple(start)]][index[tuple(target)]])
        self.assertEqual(o.expected(2662,[[1,1],[3,3],[[3,3,1,1,1]]]),4)
        self.assertEqual(o.expected(2662,[[5,5],[5,5],[[5,5,5,5,50]]]),0)

    def test_all_square_cut_masks_against_recursive_numeric_suffixes(self):
        def possible(value,remaining):
            if value==0:return remaining==0
            divisor=10
            while True:
                piece=value%divisor
                if piece<=remaining and possible(value//divisor,remaining-piece):return True
                if divisor>value:break
                divisor*=10
            return False
        total=0
        for n in range(1,1001):
            if possible(n*n,n):total+=n*n
            self.assertEqual(o.expected(2698,[n]),total)
        self.assertEqual(o.punishment_prefixes()[1000]-o.punishment_prefixes()[999],1000000)

    def test_weighted_state_distances_against_boundary_lower_bound(self):
        for n in range(1,11):
            for bits in product('01',repeat=n):
                s=''.join(bits);want=sum(min(i,n-i) for i in range(1,n) if s[i]!=s[i-1])
                self.assertEqual(o.expected(2712,[s]),want)

    def test_invalid_full_domains(self):
        bad=[(2585,[0,[[1,1]]]),(2585,[1001,[[1,1]]]),(2585,[1,[]]),(2585,[1,[[0,1]]]),(2585,[1,[[1,True]]]),(2585,[1,[[1,1]]*51]),
             (2654,[[1]]),(2654,[[1,0]]),(2654,[[True,1]]),(2654,[[1,1000001]]),(2654,[[1]*51]),
             (2662,[[0,1],[2,2],[[1,1,2,2,1]]]),(2662,[[2,2],[1,2],[[2,2,1,2,1]]]),(2662,[[1,1],[2,2],[]]),
             (2662,[[1,1],[2,2],[[1,1,3,2,1]]]),(2662,[[1,1],[2,2],[[1,1,2,2,0]]]),(2662,[[1,1],[2,2],[[1,1,2,2,True]]]),
             (2698,[0]),(2698,[1001]),(2698,[True]),(2712,['']),(2712,['2']),(2712,['０']),(2712,['0'*100001])]
        for pid,args in bad:
            with self.subTest(pid=pid),self.assertRaises(ValueError):o.validate(pid,args)

    def test_domain_and_reference_budget_are_separate(self):
        for pid,args in [(2585,[1000,[[50,1]]*50]),(2654,[[1000000]*50]),(2662,[[1,1],[100000,100000],[[1,1,1,1,1]]*200]),(2712,['0'*100000])]:
            o.validate(pid,args)
            with self.assertRaisesRegex(ValueError,'budget'):o.expected(pid,args)
        o.validate(2698,[1000])

    def test_expected_values_are_host_only_and_statement_is_pinned(self):
        case=dict(args=[10],expected=182,compare='return')
        self.assertEqual(q.packet([case])['calls'],[dict(args=[10])])
        for pid in o.IDS:
            with self.assertRaisesRegex(ValueError,'pinned'):o.public_examples(pid,b'not a permitted definition')
        with self.assertRaises(ValueError):o.expected_observation_bytes([case],'other')

if __name__=='__main__':unittest.main()
