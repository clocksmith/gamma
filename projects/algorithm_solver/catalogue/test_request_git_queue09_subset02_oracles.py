"""Focused source-free queue09 subset02 checks."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
from math import comb,gcd
import random
import unittest
from . import imported_qualification as q
from . import request_git_queue09_subset02_oracles as o
class Queue09Subset02Tests(unittest.TestCase):
    def test_examples(self):
        samples=[(3112,[3,[[0,1,2],[1,2,1],[0,2,4]],[1,1,5]],[0,-1,4]),(3112,[3,[[0,1,2],[1,2,1],[0,2,4]],[1,3,5]],[0,2,3]),(3112,[2,[[0,1,1]],[1,1]],[0,-1]),(3116,[[3,6,9],3],9),(3116,[[5,2],7],12),(3122,[[[1,0,2],[1,0,2]]],0),(3122,[[[1,1,1],[0,0,0]]],3),(3122,[[[1],[2],[3]]],2),(3129,[1,1,2],2),(3129,[1,2,1],1),(3129,[3,3,2],14),(3133,[3,4],6),(3133,[2,7],15),(3138,['abba'],2),(3138,['cdef'],4),(3138,['abcbcacabbaccba'],3)]
        for pid,a,v in samples:self.assertTrue(q.exact(o.expected(pid,a),v))
    def test_paths_against_relaxation(self):
        rng=random.Random(3112)
        for _ in range(120):
            n=rng.randint(1,7);e=[[rng.randrange(n),rng.randrange(n),rng.randrange(1,10)] for _ in range(rng.randrange(21))];d=[rng.randrange(1,20) for _ in range(n)]
            dist=[10**9]*n;dist[0]=0
            for _ in range(n-1):
                before=dist[:]
                for u,v,w in e:
                    if before[u]+w<d[v]:dist[v]=min(dist[v],before[u]+w)
                    if before[v]+w<d[u]:dist[u]=min(dist[u],before[v]+w)
            self.assertEqual(o.expected(3112,[n,e,d]),[-1 if x==10**9 else x for x in dist])
    def test_amounts_against_union_multiples(self):
        for mask in range(1,64):
            c=[i+1 for i in range(6) if mask>>i&1]
            for k in (1,10,50):self.assertEqual(o.expected(3116,[c,k]),sorted({v*j for v in c for j in range(1,k+1)})[k-1])
    def test_columns_against_digit_dp(self):
        rng=random.Random(3122)
        for _ in range(50):
            rows=rng.randrange(1,5);cols=rng.randrange(1,5);g=[[rng.randrange(10) for _ in range(cols)] for _ in range(rows)];dp=[0]*10
            for j in range(cols):
                dp=[sum(row[j]!=v for row in g)+min(dp[w] for w in range(10) if w!=v) for v in range(10)]
            self.assertEqual(o.expected(3122,[g]),min(dp))
    def test_stable_compositions_against_literal_and_dp(self):
        for z in range(1,6):
            for a in range(1,6):
                for limit in range(1,7):self.assertEqual(o.stable_run_count(z,a,limit),o.expected(3129,[z,a,limit]))
        for z,a,limit in [(200,200,1),(200,200,2),(200,200,200),(150,199,17),(200,1,199)]:
            # Independent iterative recurrence indexed by last bit and run length.
            states={(0,0,2,0):1}
            for total in range(z+a):
                new={}
                for (zz,aa,last,run),count in states.items():
                    for bit in (0,1):
                        nz,na=zz+(bit==0),aa+(bit==1);nr=run+1 if bit==last else 1
                        if nz<=z and na<=a and nr<=limit:
                            key=(nz,na,bit,nr);new[key]=(new.get(key,0)+count)%1000000007
                states=new
            self.assertEqual(o.stable_run_count(z,a,limit),sum(states.values())%1000000007)
        self.assertEqual(o.stable_run_count(200,200,200),comb(400,200)%1000000007)
    def test_superset_scan_against_bit_placement(self):
        for n in range(1,25):
            for x in range(1,128):
                rank=n-1;v=x;bit=1
                while rank:
                    if not(x&bit):
                        if rank&1:v|=bit
                        rank//=2
                    bit*=2
                self.assertEqual(o.expected(3133,[n,x]),v)
        self.assertLess(10**8*(1<<26)-1,2**53)
    def test_sorted_blocks_against_histograms(self):
        for n in range(1,9):
            for a in product('ab',repeat=n):
                s=''.join(a)
                answer=next(k for k in range(1,n+1) if n%k==0 and len({tuple(s[j:j+k].count(c) for c in 'ab') for j in range(0,n,k)})==1)
                self.assertEqual(o.expected(3138,[s]),answer)
    def test_invalid_domains(self):
        for pid,a in [(3112,[0,[],[]]),(3112,[2,[[0,2,1]],[1,1]]),(3112,[2,[[0,1,0]],[1,1]]),(3112,[1,[],[True]]),(3116,[[1,1],2]),(3116,[[0],2]),(3116,[[1],True]),(3116,[list(range(1,17)),2]),(3122,[[[0],[1,2]]]),(3122,[[[10]]]),(3122,[[[False]]]),(3129,[0,1,1]),(3129,[1,1,201]),(3133,[True,1]),(3133,[1,10**8+1]),(3138,['A']),(3138,[''])]:
            with self.assertRaises(ValueError):o.validate(pid,a)
        # Loops and parallel edges are expressly not rejected.
        o.validate(3112,[1,[[0,0,1],[0,0,1]],[1]])
    def test_full_domains_distinct_from_budgets(self):
        for pid,a in [(3112,[50000,[],[1]*50000]),(3116,[[25],2*10**9]),(3122,[[[0]*1000 for _ in range(1000)]]),(3129,[200,200,200]),(3133,[10**8,10**8]),(3138,['a'*100000])]:
            o.validate(pid,a)
            with self.assertRaisesRegex(ValueError,'budget'):o.expected(pid,a)
    def test_effects_and_statement_identity(self):
        for pid,a in [(3112,[2,[[0,1,1]],[1,2]]),(3116,[[2,3],10]),(3122,[[[1,0],[2,3]]]),(3129,[3,4,2]),(3133,[3,7]),(3138,['abba'])]:
            before=deepcopy(a);o.expected(pid,a);self.assertEqual(a,before)
            with self.assertRaisesRegex(ValueError,'pinned'):o.public_examples(pid,b'bad')
    def test_maximum_grid_packet_gap(self):
        c=dict(args=[[[0]*1000 for _ in range(1000)]],expected=0,compare='return')
        self.assertGreater(len(q.encoded(q.packet([c]))),q.MAX_PACKET)
if __name__=='__main__':unittest.main()
