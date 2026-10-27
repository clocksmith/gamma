"""Focused source-free tests. No candidate or definition file access."""
from copy import deepcopy
from itertools import product
import unittest
from . import imported_qualification as q
from . import request_git_queue09_subset01_oracles as o

class Queue09Subset01Tests(unittest.TestCase):
    def test_official_examples(self):
        for pid,args,result in [(3107,[[2,5,6,8,5],4],2),(3107,[[2,5,6,8,5],7],3),(3107,[[1,2,3,4,5,6],4],0),(3111,[[[2,1],[1,0],[1,4],[1,8],[3,5],[4,6]],1],2),(3111,[[[i,i] for i in range(7)],2],3),(3111,[[[2,3],[1,2]],0],2),(3115,[[4,2,9,5,3]],3),(3115,[[4,8,2,8]],0),(3121,['aaAbcBC'],3),(3121,['abc'],0),(3121,['AbBCab'],0)]:
            self.assertEqual(o.expected(pid,args),result)
    def test_median_literal_assignments(self):
        for n in range(1,5):
            assignments=list(product((1,2,3),repeat=n))
            for a in assignments:
                for k in (1,2,3):
                    answer=min(sum(abs(x-y) for x,y in zip(a,b)) for b in assignments if sorted(b)[n//2]==k)
                    self.assertEqual(o.expected(3107,[list(a),k]),answer)
    def test_rectangle_leftmost_exchange(self):
        universe=list(product(range(3),range(2)))
        for bits in range(1,64):
            pts=[list(p) for i,p in enumerate(universe) if bits>>i&1]
            for w in range(3):
                end=-1;answer=0
                for x in sorted(p[0] for p in pts):
                    if x>end:answer+=1;end=x+w
                self.assertEqual(o.expected(3111,[pts,w]),answer)
    def test_prime_sieve_all_values(self):
        prime=[True]*101;prime[0]=prime[1]=False
        for d in range(2,101):
            if prime[d]:
                for j in range(d*d,101,d):prime[j]=False
        for x in range(1,101):self.assertEqual(o._prime(x),prime[x])
        for a in product((1,2,4,97),repeat=4):
            inds=[i for i,x in enumerate(a) if prime[x]]
            if inds:self.assertEqual(o.expected(3115,[list(a)]),inds[-1]-inds[0])
    def test_case_order_state_machine(self):
        for n in range(1,6):
            for chars in product('aAbB',repeat=n):
                states={}
                for c in chars:
                    key=c.lower();old=states.get(key,0)
                    if c.islower():states[key]=1 if old in (0,1) else 3
                    else:states[key]=2 if old in (1,2) else 3
                self.assertEqual(o.expected(3121,[''.join(chars)]),sum(x==2 for x in states.values()))
    def test_strict_domain_rejections(self):
        bad=[(3107,[[],1]),(3107,[[1],0]),(3107,[[True],1]),(3107,[[1],True]),(3107,[[1.0],1]),(3107,[[1]*200001,1]),(3111,[[[0,0],[0,0]],1]),(3111,[[[0,False]],1]),(3111,[[[0,0]],-1]),(3111,[[[0,0,1]],1]),(3111,[[[10**9+1,0]],1]),(3115,[[1,4,100]]),(3115,[[2,101]]),(3115,[[True,2]]),(3115,[[2]*300001]),(3121,['']),(3121,['a0']),(3121,['a\u0130']),(3121,['a'*200001]),(True,[[1],1]),(3107,([1],1))]
        for pid,args in bad:
            with self.assertRaises(ValueError):o.validate(pid,args)
    def test_full_domain_not_reference_budget(self):
        for pid,args in [(3107,[[10**9]*200000,10**9]),(3111,[[[i,10**9] for i in range(100000)],10**9]),(3115,[[100]*299999+[97]]),(3121,['a'*200000])]:
            o.validate(pid,args)
            with self.assertRaisesRegex(ValueError,'budget'):o.expected(pid,args)
    def test_effects_and_numeric_boundaries(self):
        for pid,args in [(3107,[[10**9]*10,1]),(3111,[[[0,10**9],[10**9,0]],10**9]),(3115,[[100,97,1,2]]),(3121,['aAbBCc'])]:
            copy=deepcopy(args);o.expected(pid,args);self.assertEqual(args,copy)
        self.assertEqual(o.expected(3107,[[10**9]*10,1]),6*(10**9-1))
    def test_maximum_packet_omissions(self):
        for args in [[[10**9]*200000,1],[[[10**9-i,10**9] for i in range(100000)],0],[[100]*299999+[97]]]:
            self.assertGreater(len(q.encoded(q.packet([dict(args=args,expected=0,compare='return')]))),q.MAX_PACKET)
    def test_packet_and_pinned_statement_fail_closed(self):
        case=dict(args=[[2,1]],expected=0,compare='return')
        self.assertEqual(q.packet([case])['calls'],[dict(args=[[2,1]])]);self.assertNotIn('expected',q.packet([case])['calls'][0])
        for pid in o.IDS:
            with self.assertRaisesRegex(ValueError,'pinned'):o.public_examples(pid,b'no statement')
        self.assertLess(o.expected_observation_bytes([case],'python'),q.LIMITS['max_output_bytes'])

if __name__=='__main__':unittest.main()
