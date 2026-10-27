"""Source-free independent controls for queue 08 subset 03."""
from collections import Counter
from copy import deepcopy
from heapq import heapify, heappop, heappush
import json
import string
import unittest
from unittest.mock import patch
from . import imported_qualification as q
from . import request_git_queue08_subset03_oracles as o

EXAMPLES = {3081: [(['???'], 'abc'), (['a?a?'], 'abac')], 3085: [(['aabcaba', 0], 3), (['dabdcbdcdcd', 2], 2), (['aaabaaa', 2], 1)], 3096: [([[1, 0, 1, 0]], 1), ([[1, 1, 1, 1, 1]], 3), ([[0, 0]], -1)], 3101: [([[0, 1, 1, 1]], 5), ([[1, 0, 1, 0]], 10)], 3106: [(['zbbz', 3], 'aaaz'), (['xaxcd', 4], 'aawcd'), (['lol', 0], 'lol')]}

def fixture(pid):
    body = f'{pid}. {o.TITLES[pid]}\n' + ''.join('Input: '+', '.join(f'{key} = {json.dumps(value)}' for key, value in zip(o.PARAMETERS[pid], args))+'\nOutput: '+json.dumps(want)+'\nExplanation: Synthetic transcription.\n' for args,want in EXAMPLES[pid])
    return q.encoded({'problem_id':pid,'web_result':body})

def balanced(s):
    counts=Counter(s);heap=[(counts[c],c) for c in string.ascii_lowercase];heapify(heap);letters=[]
    for _ in range(counts['?']):
        n,c=heappop(heap);letters.append(c);heappush(heap,(n+1,c))
    assigned=iter(sorted(letters));return ''.join(next(assigned) if c=='?' else c for c in s)

def intervals(word,k):
    counts=list(Counter(word).values())
    return min(sum(c if c<floor else max(0,c-floor-k) for c in counts) for floor in counts)

def running_levels(a):
    total=2*sum(a)-len(a);prefix=0
    for i,x in enumerate(a[:-1],1):
        prefix+=2*x-1
        if 2*prefix>total:return i
    return -1

def run_subarrays(a):
    total=0;length=1
    for x,y in zip(a,a[1:]):
        if x!=y:length+=1
        else:total+=length*(length+1)//2;length=1
    return total+length*(length+1)//2

def lexical_budget(s,k):
    out=[]
    for old in s:
        for new in string.ascii_lowercase:
            d=abs(ord(old)-ord(new));cost=min(d,26-d)
            if cost<=k:out.append(new);k-=cost;break
    return ''.join(out)

class Queue08Subset03(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw={i:fixture(i) for i in o.IDS}
        with patch.dict(o.STATEMENT_SHA256,{i:q.sha(b) for i,b in cls.raw.items()}):
            cls.built={i:o.build_cases(i,cls.raw[i]) for i in o.IDS}
    def test_public_examples_and_unchanged_inputs(self):
        for pid,rows in EXAMPLES.items():
            for args,want in rows:
                before=deepcopy(args);self.assertTrue(q.exact(o.expected(pid,args),want));self.assertEqual(args,before)
    def test_substitution_enumeration_independent_convex_heap_and_lexical_fill(self):
        for c in self.built[3081][0]:self.assertEqual(c['expected'],balanced(c['args'][0]))
    def test_retained_count_enumeration_independent_frequency_intervals(self):
        for c in self.built[3085][0]:self.assertEqual(c['expected'],intervals(*c['args']))
    def test_split_sums_independent_running_prefix(self):
        for c in self.built[3096][0]:self.assertEqual(c['expected'],running_levels(c['args'][0]))
        self.assertEqual(o.expected(3096,[[0,0]]),-1);self.assertEqual(o.expected(3096,[[0,0,0]]),1)
    def test_subarray_enumeration_independent_alternating_runs(self):
        for c in self.built[3101][0]:self.assertEqual(c['expected'],run_subarrays(c['args'][0]))
        self.assertEqual(run_subarrays([0,1]*50000),5000050000)
    def test_lexical_target_enumeration_independent_prefix_affordability(self):
        for c in self.built[3106][0]:self.assertEqual(c['expected'],lexical_budget(*c['args']))
    def test_full_domain_exact_types_shapes_and_boundaries(self):
        invalid={3081:[[''],['? '*2],['é'],['A'],['a'*100001],[True]],
                 3085:[['',0],['A',0],['a',-1],['a',100001],['a',True],['a',0.0],['a'*100001,0]],
                 3096:[[[]],[[0]],[[0,2]],[[True,0]],[[0,1.0]],[[0]*100001]],
                 3101:[[[]],[[2]],[[False]],[[1.0]],[[0]*100001]],
                 3106:[['',0],['é',0],['a'*101,0],['a',-1],['a',2001],['a',True],['a',1.0]]}
        for pid,rows in invalid.items():
            for args in rows:
                with self.subTest(pid=pid,args=str(args)[:60]),self.assertRaises(ValueError):o.validate(pid,args)
        for pid,args in [(True,[]),(3081.0,['?']),(3088,[]),(3081,('?',))]:
            with self.assertRaises(ValueError):o.validate(pid,args)
        o.validate(3081,['?'*100000]);o.validate(3085,['z'*100000,100000]);o.validate(3096,[[1]*100000]);o.validate(3101,[[0]*100000]);o.validate(3106,['z'*100,2000])
    def test_reference_budget_not_domain_restriction(self):
        for pid,args in [(3081,['????']),(3081,['a'*65]),(3085,['a'*100000,0]),(3096,[[0]*129]),(3101,[[1]*65]),(3106,['zzzzz',0]),(3106,['aaaaaa',0])]:
            o.validate(pid,args)
            with self.assertRaises(ValueError):o.expected(pid,args)
    def test_frozen_unique_cases_categories_and_transport(self):
        for pid,(cases,cats) in self.built.items():
            self.assertEqual(len(cases),o.CASE_COUNT[pid]);self.assertEqual(q.sha(q.encoded(cases)),o.CASES_SHA256[pid]);self.assertEqual(len(cats),len(cases));self.assertEqual(len(set(q.encoded(c['args']) for c in cases)),len(cases));self.assertTrue(any('exhaustive' in x for x in cats));self.assertLessEqual(len(q.encoded(cases)),q.MAX_FILE)
            for _,batch in q.batches(cases):
                self.assertLessEqual(len(batch),32);self.assertLessEqual(len(q.encoded(q.packet(batch))),q.MAX_PACKET)
                for lang in ('javascript','python'):self.assertLessEqual(o.expected_observation_bytes(batch,lang),q.LIMITS['max_output_bytes'])
    def test_unpinned_changed_statement_and_case_fail_closed(self):
        for pid in o.IDS:
            with self.assertRaises(ValueError):o.public_examples(pid,self.raw[pid])
            with patch.dict(o.STATEMENT_SHA256,{pid:q.sha(self.raw[pid])}):
                with self.assertRaises(ValueError):o.public_examples(pid,self.raw[pid]+b' ')
                with patch.dict(o.CASE_COUNT,{pid:-1}),patch.object(o,'_generate_cases',return_value=self.built[pid]):
                    with self.assertRaises(ValueError):o.build_cases(pid,self.raw[pid])

if __name__=='__main__':unittest.main()
