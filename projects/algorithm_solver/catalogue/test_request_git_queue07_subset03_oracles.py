"""Independent source-free controls for queue 07 subset 03."""
from bisect import bisect_left,bisect_right
from copy import deepcopy
from functools import lru_cache
import json
import unittest
from unittest.mock import patch
from . import imported_qualification as q
from . import request_git_queue07_subset03_oracles as o
EXAMPLES={2920:[([[[0,1],[1,2],[2,3]],[10,10,3,3],5],11),([[[0,1],[0,2]],[8,4,4],0],16)],2925:[([[[0,1],[0,2],[0,3],[2,4],[4,5]],[5,2,5,2,1,1]],11),([[[0,1],[0,2],[1,3],[1,4],[2,5],[2,6]],[20,10,9,7,4,3,5]],40)],2967:[([[1,2,3,4,5]],6),([[10,12,13,14,15]],11),([[22,33,22,33,22]],22)],2972:[([[1,2,3,4]],10),([[6,5,7,8]],7),([[8,7,6,6]],3)]}

def fixture(pid):return (f'{pid}. {o.TITLES[pid]}\n'+''.join('Input: '+', '.join(f'{key} = {json.dumps(v)}' for key,v in zip(o.PARAMETERS[pid],args))+'\nOutput: '+json.dumps(want)+'\n' for args,want in EXAMPLES[pid])).encode()

def children(edges,n):
    adj=[[] for _ in range(n)]
    for a,b in edges:adj[a].append(b);adj[b].append(a)
    parent=[-1]*n;order=[0];out=[[] for _ in range(n)]
    for v in order:
        for w in adj[v]:
            if w!=parent[v]:parent[w]=v;out[v].append(w);order.append(w)
    return out,order

def half_dp(edges,coins,k):
    child,order=children(edges,len(coins));dp=[[0]*15 for _ in coins]
    for v in reversed(order):
        for h in range(13,-1,-1):
            value=coins[v]>>h
            dp[v][h]=max(value-k+sum(dp[w][h] for w in child[v]),(value>>1)+sum(dp[w][h+1] for w in child[v]))
    return dp[0][0]

def keep_dp(edges,values):
    child,order=children(edges,len(values));cost=[0]*len(values)
    for v in reversed(order):cost[v]=values[v] if not child[v] else min(values[v],sum(cost[w] for w in child[v]))
    return sum(values)-cost[0]

@lru_cache(None)
def palindromes():
    result=set()
    for first in range(1,100000):
        s=str(first)
        for value in (int(s+s[-2::-1]),int(s+s[::-1])):
            if value<=1000000001:result.add(value)
    return sorted(result)

def median_palindrome(a):
    ordered=sorted(a);median=ordered[len(a)//2];values=palindromes();i=bisect_left(values,median)
    candidates=values[max(0,i-1):i+1]
    return min(sum(abs(x-v) for x in a) for v in candidates)

def prefix_suffix(a):
    n=len(a);p=0
    while p+1<n and a[p]<a[p+1]:p+=1
    if p==n-1:return n*(n+1)//2
    s=n-1
    while s>0 and a[s-1]<a[s]:s-=1
    total=0
    for kept in range(p+2):
        start=max(s,kept+1)
        if kept:start=max(start,bisect_right(a,a[kept-1],s,n))
        total+=n-start+1
    return total

class Queue07Subset03(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw={pid:fixture(pid) for pid in o.IDS}
        with patch.dict(o.STATEMENT_SHA256,{pid:q.sha(raw) for pid,raw in cls.raw.items()}):cls.built={pid:o.build_cases(pid,raw) for pid,raw in cls.raw.items()}
    def test_official_examples_and_no_input_changes(self):
        for pid,rows in EXAMPLES.items():
            for args,want in rows:
                before=deepcopy(args);self.assertTrue(q.exact(o.expected(pid,args),want));self.assertEqual(args,before)
    def test_mode_subsets_independent_iterative_half_count_dp(self):
        for c in self.built[2920][0]:self.assertEqual(c['expected'],half_dp(*c['args']))
    def test_retention_subsets_independent_path_cover_cost(self):
        for c in self.built[2925][0]:self.assertEqual(c['expected'],keep_dp(*c['args']))
    def test_literal_palindrome_targets_independent_median_neighbors(self):
        for c in self.built[2967][0]:self.assertEqual(c['expected'],median_palindrome(c['args'][0]))
        self.assertIn(1000000001,palindromes());self.assertEqual(median_palindrome([1000000000]),1)
    def test_literal_removals_independent_prefix_suffix_boundaries(self):
        for c in self.built[2972][0]:self.assertEqual(c['expected'],prefix_suffix(c['args'][0]))
    def test_full_domain_types_shapes_and_tree_invariants(self):
        invalid={2920:[[[],[0],0],[[[0,0]],[0,0],0],[[[0,1],[1,0]],[1,1,1],0],[[[0,1],[1,2],[2,0]],[1]*4,0],[[[0,2]],[0,0],0],[[[0,1]],[0,10001],0],[[[0,1]],[0,0],True]],2925:[[[],[1]],[[[0,1]],[0,1]],[[[0,1]],[True,1]],[[[0,1],[0,1]],[1,2,3]],[[[0,1]],[1,10**9+1]]],2967:[[[]],[[0]],[[True]],[[1.0]],[[10**9+1]]],2972:[[[]],[[0]],[[False]],[[1.0]],[[10**9+1]]]}
        for pid,rows in invalid.items():
            for args in rows:
                with self.subTest(pid=pid,args=str(args)[:50]),self.assertRaises(ValueError):o.validate(pid,args)
        for pid,args in [(True,[]),(2967.0,[[1]]),(2900,[]),(2967,([1],))]:
            with self.assertRaises(ValueError):o.validate(pid,args)
        for pid in (2967,2972):o.validate(pid,[[10**9]*100000])
        o.validate(2920,[[[0,i] for i in range(1,100000)],[0]*100000,10000]);o.validate(2925,[[[0,i] for i in range(1,20000)],[10**9]*20000])
    def test_reference_budgets_do_not_shrink_domains(self):
        for pid,args in [(2920,[[[0,i] for i in range(1,11)],[1]*11,0]),(2925,[[[0,i] for i in range(1,13)],[1]*13]),(2967,[[1001]]),(2967,[[1]*9]),(2972,[[1]*61])]:
            o.validate(pid,args)
            with self.assertRaises(ValueError):o.expected(pid,args)
    def test_frozen_cases_categories_and_transport(self):
        for pid,(cases,cats) in self.built.items():
            self.assertEqual(len(cases),o.CASE_COUNT[pid]);self.assertEqual(q.sha(q.encoded(cases)),o.CASES_SHA256[pid]);self.assertEqual(len(cats),len(cases));self.assertEqual(len({q.encoded(c['args']) for c in cases}),len(cases));self.assertLessEqual(len(q.encoded(cases)),q.MAX_FILE)
            for _,batch in q.batches(cases):
                self.assertLessEqual(len(batch),32);self.assertLessEqual(len(q.encoded(q.packet(batch))),q.MAX_PACKET)
                for lang in ('javascript','python'):self.assertLessEqual(o.expected_observation_bytes(batch,lang),q.LIMITS['max_output_bytes'])
    def test_omitted_maximum_shapes_really_exceed_unchanged_packet(self):
        for args in ([[10**9]*100000],[[[0,i] for i in range(1,100000)],[0]*100000,0]):
            with self.assertRaises(ValueError):list(q.batches([{'args':args,'expected':0,'compare':'return'}]))
    def test_statement_and_case_identity_tampering_rejected(self):
        for pid in o.IDS:
            with self.assertRaises(ValueError):o.public_examples(pid,self.raw[pid])
            with patch.dict(o.STATEMENT_SHA256,{pid:q.sha(self.raw[pid])}):
                with self.assertRaises(ValueError):o.public_examples(pid,self.raw[pid]+b' ')
                with patch.dict(o.CASE_COUNT,{pid:-1}),patch.object(o,'_generate_cases',return_value=self.built[pid]):
                    with self.assertRaises(ValueError):o.build_cases(pid,self.raw[pid])

if __name__=='__main__':unittest.main()
