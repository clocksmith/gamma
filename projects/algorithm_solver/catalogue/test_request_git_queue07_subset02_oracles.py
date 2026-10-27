"""Independent source-free checks for queue 07 subset 02."""
from collections import Counter
from copy import deepcopy
from functools import lru_cache
import json
import unittest
from unittest.mock import patch
from . import imported_qualification as q
from . import request_git_queue07_subset02_oracles as o

EXAMPLES={2896:[(['1100011000','0101001010',2],4),(['10110','00011',4],-1)],2939:[([12,5,4],98),([6,7,5],930),([1,6,3],12)],2949:[(['baeyh',2],2),(['abba',1],3),(['bcdf',1],0)],2962:[([[1,3,2,3,3],2],6),([[1,4,2,1],3],0)]}

def fixture(pid):
    return (f'{pid}. {o.TITLES[pid]}\n'+''.join('Input: '+', '.join(f'{key} = {json.dumps(v)}' for key,v in zip(o.PARAMETERS[pid],args))+'\nOutput: '+json.dumps(want)+'\n' for args,want in EXAMPLES[pid])).encode()

def matching(a,b,x):
    indices=tuple(i for i,(u,v) in enumerate(zip(a,b)) if u!=v)
    if len(indices)%2:return -1
    if len(indices)>12:
        # Full cases have explicit pairing certificates, checked separately.
        if not indices:return 0
        if len(indices)==500:return 250
        if indices==tuple(range(0,500,2)):return 125*min(x,2)
        if indices==(0,499):return min(x,499)
        raise ValueError('independent matching budget')
    @lru_cache(None)
    def f(left):
        if not left:return 0
        return min(min(x,abs(left[0]-left[j]))+f(left[1:j]+left[j+1:]) for j in range(1,len(left)))
    return f(indices)

def balanced(a,b,n):
    mask=(1<<n)-1;left=a&~mask;right=b&~mask
    for bit in range(n-1,-1,-1):
        unit=1<<bit
        if bool(a&unit)==bool(b&unit):left|=unit;right|=unit
        elif left<right:left|=unit
        else:right|=unit
    return left*right%o.MOD

def modular_prefix(s,k):
    needed=1;prime=2;remaining=k
    while prime*prime<=remaining:
        exponent=0
        while remaining%prime==0:remaining//=prime;exponent+=1
        needed*=prime**((exponent+1)//2);prime+=1
    if remaining>1:needed*=remaining
    counts=Counter({(0,0):1});balance=answer=0
    for i,c in enumerate(s,1):
        balance+=1 if c in 'aeiou' else -1;key=(balance,i%(2*needed));answer+=counts[key];counts[key]+=1
    return answer

def maxima_positions(a,k):
    maximum=max(a);seen=[];answer=0
    for i,x in enumerate(a):
        if x==maximum:seen.append(i)
        if len(seen)>=k:answer+=seen[-k]+1
    return answer

class Queue07Subset02(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw={pid:fixture(pid) for pid in o.IDS}
        with patch.dict(o.STATEMENT_SHA256,{pid:q.sha(raw) for pid,raw in cls.raw.items()}):
            cls.built={pid:o.build_cases(pid,raw) for pid,raw in cls.raw.items()}
    def test_official_examples_and_unchanged_inputs(self):
        for pid,rows in EXAMPLES.items():
            for args,want in rows:
                before=deepcopy(args);self.assertTrue(q.exact(o.expected(pid,args),want));self.assertEqual(args,before)
    def test_mismatch_dijkstra_independent_perfect_matching(self):
        for c in self.built[2896][0]:self.assertEqual(c['expected'],matching(*c['args']))
    def test_xor_exhaustion_independent_high_to_low_balance(self):
        for c in self.built[2939][0]:self.assertEqual(c['expected'],balanced(*c['args']))
        self.assertEqual(o.expected(2939,[(1<<50)-1,(1<<50)-2,0]),(((1<<50)-1)*((1<<50)-2))%o.MOD)
    def test_literal_substrings_independent_modular_prefix_classes(self):
        for c in self.built[2949][0]:self.assertEqual(c['expected'],modular_prefix(*c['args']))
        self.assertEqual(o.expected(2949,['ay',1]),1)
    def test_global_maximum_intervals_independent_occurrence_positions(self):
        for c in self.built[2962][0]:self.assertEqual(c['expected'],maxima_positions(*c['args']))
        self.assertEqual(o.expected(2962,[[1,1,2],1]),3)
    def test_full_domains_exact_types_and_shapes(self):
        invalid={2896:[['','',1],['0','00',1],['a','0',1],['0','0',True],['0','0',0],['0'*501,'1'*501,1]],2939:[[True,0,1],[1.0,0,1],[-1,0,1],[1<<50,0,1],[0,0,51],[0,0,False]],2949:[['',1],['A',1],['é',1],['a',0],['a',1001],['a',True]],2962:[[[],1],[[0],1],[[1000001],1],[[True],1],[[1.0],1],[[1],0],[[1],100001],[[1],True]]}
        for pid,rows in invalid.items():
            for args in rows:
                with self.subTest(pid=pid,args=str(args)[:50]),self.assertRaises(ValueError):o.validate(pid,args)
        for pid,args in [(True,[]),(2939.0,[0,0,1]),(2900,[]),(2949,('a',1))]:
            with self.assertRaises(ValueError):o.validate(pid,args)
        o.validate(2896,['0'*500,'1'*500,500]);o.validate(2939,[(1<<50)-1,(1<<50)-1,50]);o.validate(2949,['z'*50000,1000]);o.validate(2962,[[1000000]*100000,100000]);o.validate(2962,[[1],100000])
    def test_reference_budgets_not_domain_restrictions(self):
        for pid,args in [(2896,['0'*13,'1'*13,1]),(2939,[0,0,11]),(2949,['a'*81,1]),(2962,[[1]*61,1])]:
            o.validate(pid,args)
            with self.assertRaises(ValueError):o.expected(pid,args)
    def test_frozen_unique_cases_categories_and_limits(self):
        for pid,(cases,cats) in self.built.items():
            self.assertEqual(len(cases),o.CASE_COUNT[pid]);self.assertEqual(q.sha(q.encoded(cases)),o.CASES_SHA256[pid]);self.assertEqual(len(cats),len(cases));self.assertEqual(len({q.encoded(c['args']) for c in cases}),len(cases));self.assertLessEqual(len(q.encoded(cases)),q.MAX_FILE)
            for _,batch in q.batches(cases):
                self.assertLessEqual(len(batch),32);self.assertLessEqual(len(q.encoded(q.packet(batch))),q.MAX_PACKET)
                for lang in ('javascript','python'):self.assertLessEqual(o.expected_observation_bytes(batch,lang),q.LIMITS['max_output_bytes'])
    def test_definition_case_identity_tampering_rejected(self):
        for pid in o.IDS:
            with self.assertRaises(ValueError):o.public_examples(pid,self.raw[pid])
            with patch.dict(o.STATEMENT_SHA256,{pid:q.sha(self.raw[pid])}):
                with self.assertRaises(ValueError):o.public_examples(pid,self.raw[pid]+b' ')
                with patch.dict(o.CASE_COUNT,{pid:-1}),patch.object(o,'_generate_cases',return_value=self.built[pid]):
                    with self.assertRaises(ValueError):o.build_cases(pid,self.raw[pid])
    def test_comparison_stays_exact_and_effect_checked(self):
        c={'args':[[1]],'expected':5000050000,'compare':'return'};r={'result':5000050000,'result_type':'int','args_before':[[1]],'args_after':[[1]],'alias_edges':[]}
        self.assertIsNone(q.compare(c,r,'python'))
        for delta,reason in [({'result':5000050000.0},'result_value'),({'args_after':[[2]]},'input_effects'),({'alias_edges':[[0,0]]},'return_aliases')]:self.assertEqual(q.compare(c,dict(r,**delta),'python'),reason)

if __name__=='__main__':unittest.main()
