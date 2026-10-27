"""Focused public-reference tests; no candidate access."""
from collections import Counter
from copy import deepcopy
from itertools import product
import random
import unittest
from . import imported_qualification as q
from . import request_git_queue09_subset03_oracles as o
class Queue09Subset03Tests(unittest.TestCase):
    def test_examples(self):
        cases=[(3143,[[[2,2],[-1,-2],[-4,4],[-3,1],[3,-3]],'abdca'],2),(3143,[[[1,1],[-2,-2],[-2,2]],'abb'],1),(3143,[[[1,1],[-1,-1],[2,-2]],'ccd'],0),(3148,[[[9,5,7,3],[8,9,6,1],[6,7,14,3],[2,5,3,1]]],9),(3148,[[[4,3,2],[3,2,1]]],-1),(3152,[[3,4,1,2,6],[[0,4]]],[False]),(3152,[[4,3,1,6],[[0,2],[2,3]]],[False,True]),(3153,[[13,23,12]],4),(3153,[[10]*4],0),(3160,[4,[[1,4],[2,5],[1,3],[3,4]]],[1,2,2,3]),(3160,[4,[[0,1],[1,2],[2,2],[3,4],[4,5]]],[1,2,2,3,4]),(3163,['abcde'],'1a1b1c1d1e'),(3163,['aaaaaaaaaaaaaabb'],'9a5a2b')]
        for pid,a,v in cases:self.assertTrue(q.exact(o.expected(pid,a),v))
    def test_square_threshold_second_occurrence(self):
        rng=random.Random(3143)
        for _ in range(150):
            p=[list(x) for x in rng.sample(list(product(range(-4,5),repeat=2)),rng.randint(1,40))];s=''.join(rng.choice('abc') for _ in p);dist={}
            for (x,y),tag in zip(p,s):dist.setdefault(tag,[]).append(max(abs(x),abs(y)))
            threshold=min([sorted(v)[1] for v in dist.values() if len(v)>1]+[10**10])
            want=sum(max(abs(x),abs(y))<threshold for x,y in p)
            self.assertEqual(o.expected(3143,[p,s]),want)
    def test_grid_dynamic_path_scores(self):
        rng=random.Random(3148)
        for _ in range(100):
            m,n=rng.randint(2,5),rng.randint(2,5);g=[[rng.randint(1,9) for _ in range(n)] for _ in range(m)];dp=[[-10**9]*n for _ in range(m)];best=-10**9
            for i in range(m):
                for j in range(n):
                    values=[max(0,dp[u][j])+g[i][j]-g[u][j] for u in range(i)]+[max(0,dp[i][v])+g[i][j]-g[i][v] for v in range(j)]
                    if values:dp[i][j]=max(values);best=max(best,dp[i][j])
            self.assertEqual(o.expected(3148,[g]),best)
    def test_queries_bad_edge_prefix(self):
        for n in range(1,8):
            for a in product((1,2),repeat=n):
                prefix=[0]
                for i in range(n-1):prefix.append(prefix[-1]+(a[i]%2==a[i+1]%2))
                queries=[[i,j] for i in range(n) for j in range(i,n)]
                self.assertEqual(o.expected(3152,[list(a),queries]),[prefix[i]==prefix[j] for i,j in queries])
    def test_digits_frequency_counts(self):
        for a in product((10,11,20),repeat=5):
            total=0
            for col in zip(*(str(v) for v in a)):
                counts=Counter(col);total+=(len(a)**2-sum(c*c for c in counts.values()))//2
            self.assertEqual(o.expected(3153,[list(a)]),total)
        self.assertEqual(o.expected(3153,[[111111111]*30+[999999999]*30]),8100)
    def test_color_counts_incremental(self):
        rng=random.Random(3160)
        for _ in range(100):
            seq=[[rng.randrange(6),rng.randrange(1,8)] for _ in range(100)];balls={};counts={};answer=[]
            for x,c in seq:
                if x in balls:
                    old=balls[x];counts[old]-=1
                    if counts[old]==0:del counts[old]
                balls[x]=c;counts[c]=counts.get(c,0)+1;answer.append(len(counts))
            self.assertEqual(o.expected(3160,[10**9,seq]),answer)
    def test_compression_group_lengths(self):
        rng=random.Random(3163)
        for _ in range(100):
            text=''.join(rng.choice('ab')*rng.randint(1,40) for _ in range(5));groups=[]
            for c in text:
                if groups and groups[-1][0]==c:groups[-1][1]+=1
                else:groups.append([c,1])
            answer=''.join(('9'+c)*(n//9)+(str(n%9)+c if n%9 else '') for c,n in groups)
            self.assertEqual(o.expected(3163,[text]),answer)
    def test_invalid_domains(self):
        cases=[(3143,[[[0,0],[0,0]],'ab']),(3143,[[[0,0]],'A']),(3143,[[[True,0]],'a']),(3148,[[[1,2]]]),(3148,[[[1],[2]]]),(3148,[[[1,2],[3,True]]]),(3148,[[[1,2],[3]]]),(3152,[[1,2],[[1,0]]]),(3152,[[1,2],[[0,2]]]),(3152,[[1],[]]),(3152,[[True],[[0,0]]]),(3153,[[1,10]]),(3153,[[10**9,10**9]]),(3153,[[1]]),(3153,[[True,1]]),(3160,[0,[[0,1]]]),(3160,[1,[[2,1]]]),(3160,[1,[[0,0]]]),(3160,[1,[[False,1]]]),(3163,['aA']),(3163,[''])]
        for pid,a in cases:
            with self.assertRaises(ValueError):o.validate(pid,a)
    def test_full_domains_not_budgets(self):
        for pid,a in [(3143,[[[i,0] for i in range(100000)],'a'*100000]),(3148,[[[100000]*1000 for _ in range(100)]]),(3152,[[100000]*100000,[[0,99999]]]),(3153,[[999999999]*100000]),(3160,[10**9,[[10**9,10**9]]*100000]),(3163,['a'*200000])]:
            o.validate(pid,a)
            with self.assertRaisesRegex(ValueError,'budget'):o.expected(pid,a)
    def test_effects_and_strict_types(self):
        for pid,a in [(3143,[[[0,0],[1,1]],'ab']),(3148,[[[4,3],[2,1]]]),(3152,[[1,2],[[0,1]]]),(3153,[[11,12]]),(3160,[2,[[0,1],[1,2]]]),(3163,['aaaaab'])]:
            before=deepcopy(a);v=o.expected(pid,a);self.assertEqual(a,before)
            if pid==3152:self.assertTrue(all(type(x) is bool for x in v))
            with self.assertRaisesRegex(ValueError,'pinned'):o.public_examples(pid,b'bad')
    def test_packet_omissions(self):
        for pid,a in o.maximum_omitted_inputs().items():
            o.validate(pid,a);self.assertGreater(len(q.encoded(q.packet([dict(args=a,expected=0,compare='return')]))),q.MAX_PACKET)
if __name__=='__main__':unittest.main()
