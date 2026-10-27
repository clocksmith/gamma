"""Independent source-free controls for queue 08 subset 02."""
from collections import Counter
from copy import deepcopy
import json
import unittest
from unittest.mock import patch
from . import imported_qualification as q
from . import request_git_queue08_subset02_oracles as o

EXAMPLES = {3020: [([[5, 4, 1, 2, 2]], 3), ([[1, 3, 2, 4]], 1)], 3039: [(['aabcbbca'], 'ba'), (['abcd'], 'abcd')], 3048: [([[2, 2, 0], [2, 2, 2, 2, 3, 2, 2, 1]], 8), ([[1, 3], [1, 1, 1, 2, 1, 1, 1]], 6), ([[0, 1], [2, 2, 2]], -1)], 3070: [([[[7, 6, 3], [6, 6, 1]], 18], 4), ([[[7, 2, 9], [1, 5, 0], [2, 6, 6]], 20], 6)], 3080: [([[1, 2, 2, 1, 2, 3, 1], [[1, 2], [3, 3], [4, 2]]], [8, 3, 0]), ([[1, 4, 2, 3], [[0, 1]]], [7])]}

def fixture(pid):
    body = f'{pid}. {o.TITLES[pid]}\n' + ''.join('Input: '+', '.join(f'{key} = {json.dumps(value)}' for key, value in zip(o.PARAMETERS[pid], args))+'\nOutput: '+json.dumps(want)+'\nExplanation: Synthetic transcription.\n' for args,want in EXAMPLES[pid])
    return q.encoded({'problem_id':pid,'web_result':body})

def chains(a):
    counts=Counter(a);best=max(1,counts[1]-(counts[1]%2==0))
    for root in counts:
        if root==1:continue
        v=root;level=0
        while counts[v]>=2:
            level+=1;v*=v
        best=max(best,2*level+(1 if counts[v] else -1))
    return best

def last_round(s):
    counts=Counter(s);maximum=max(counts.values());last={c:i for i,c in enumerate(s)}
    return ''.join(c for i,c in enumerate(s) if counts[c]==maximum and last[c]==i)

def schedules(nums,changes):
    n=len(nums)
    for length in range(n+sum(nums),len(changes)+1):
        last={x:i for i,x in enumerate(changes[:length])}
        if len(last)!=n:continue
        free=0
        for i,x in enumerate(changes[:length]):
            if last[x]==i:
                if free<nums[x-1]:break
                free-=nums[x-1]
            else:free+=1
        else:return length
    return -1

def prefixes(grid,k):
    above=[0]*(len(grid[0])+1);count=0
    for row in grid:
        current=[0]
        for j,x in enumerate(row):
            current.append(x+current[-1]+above[j+1]-above[j]);count+=current[-1]<=k
        above=current
    return count

def sorted_queries(a,queries):
    order=sorted(range(len(a)),key=lambda i:(a[i],i));marked=set();total=sum(a);cursor=0;out=[]
    for index,k in queries:
        if index not in marked:marked.add(index);total-=a[index]
        while cursor<len(a) and k:
            j=order[cursor];cursor+=1
            if j not in marked:marked.add(j);total-=a[j];k-=1
        out.append(total)
    return out

class Queue08Subset02(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw={i:fixture(i) for i in o.IDS}
        with patch.dict(o.STATEMENT_SHA256,{i:q.sha(b) for i,b in cls.raw.items()}):
            cls.built={i:o.build_cases(i,cls.raw[i]) for i in o.IDS}
    def test_examples_and_unchanged_inputs(self):
        for pid,rows in EXAMPLES.items():
            for args,want in rows:
                before=deepcopy(args);self.assertTrue(q.exact(o.expected(pid,args),want));self.assertEqual(args,before)
    def test_square_subset_reference_independent_frequency_paths(self):
        for c in self.built[3020][0]:self.assertEqual(c['expected'],chains(c['args'][0]))
    def test_round_simulation_independent_maximum_frequency_last_positions(self):
        for c in self.built[3039][0]:self.assertEqual(c['expected'],last_round(c['args'][0]))
    def test_marking_state_graph_independent_deadline_schedules(self):
        for c in self.built[3048][0]:self.assertEqual(c['expected'],schedules(*c['args']))
    def test_explicit_rectangle_sums_independent_prefix_recurrence(self):
        for c in self.built[3070][0]:self.assertEqual(c['expected'],prefixes(*c['args']))
        self.assertEqual(o.expected(3070,[[[1]],1]),1)
    def test_scan_marking_independent_sorted_pointer(self):
        for c in self.built[3080][0]:self.assertEqual(c['expected'],sorted_queries(*c['args']))
        self.assertEqual(o.expected(3080,[[1,1,1],[[0,0],[0,1]]]),[2,1])
    def test_full_domain_strict_shapes_types(self):
        invalid={3020:[[[]],[[1]],[[0,1]],[[True,1]],[[1,1.0]],[[1,10**9+1]]],
                 3039:[[''],['a'*500001],['A'],['é'],[False]],
                 3048:[[[],[1]],[[0],[]],[[0],[0]],[[0],[2]],[[True],[1]],[[0],[True]],[[10**9+1],[1]],[[0]*2001,[1]]],
                 3070:[[[],1],[[[]],1],[[[1],[1,2]],1],[[[True]],1],[[[1001]],1],[[[0]],0],[[[0]],True],[[[0]*1001],1]],
                 3080:[[[],[[0,0]]],[[1],[]],[[1],[[0,1]]],[[1],[[1,0]]],[[1],[[0,0],[0,0]]],[[0],[[0,0]]],[[True],[[0,0]]],[[1],[[False,0]]]]}
        for pid,rows in invalid.items():
            for args in rows:
                with self.subTest(pid=pid,args=str(args)[:60]),self.assertRaises(ValueError):o.validate(pid,args)
        for pid,args in [(True,[]),(3020.0,[[1,1]]),(3032,[]),(3020,([1,1],))]:
            with self.assertRaises(ValueError):o.validate(pid,args)
        o.validate(3020,[[10**9]*100000]);o.validate(3039,['a'*500000]);o.validate(3048,[[10**9]*2000,[2000]*2000]);o.validate(3070,[[[1000]*1000 for _ in range(1000)],10**9]);o.validate(3080,[[100000]*100000,[[99999,99999]]*100000])
    def test_reference_budget_distinct_from_domain(self):
        for pid,args in [(3020,[[1]*13]),(3039,['a'*81]),(3048,[[5],[1]]),(3070,[[[0]*11 for _ in range(10)],1]),(3080,[[1]*33,[[0,0]]])]:
            o.validate(pid,args)
            with self.assertRaises(ValueError):o.expected(pid,args)
    def test_frozen_unique_cases_categories_packets_and_output(self):
        for pid,(cases,cats) in self.built.items():
            self.assertEqual(len(cases),o.CASE_COUNT[pid]);self.assertEqual(q.sha(q.encoded(cases)),o.CASES_SHA256[pid]);self.assertEqual(len(cats),len(cases));self.assertEqual(len(set(q.encoded(c['args']) for c in cases)),len(cases));self.assertTrue(any('exhaustive' in x for x in cats));self.assertLessEqual(len(q.encoded(cases)),q.MAX_FILE)
            for _,batch in q.batches(cases):
                self.assertLessEqual(len(batch),32);self.assertLessEqual(len(q.encoded(q.packet(batch))),q.MAX_PACKET)
                for lang in ('javascript','python'):self.assertLessEqual(o.expected_observation_bytes(batch,lang),q.LIMITS['max_output_bytes'])
        with self.assertRaises(ValueError):list(q.batches([{'args':[[[0]*1000 for _ in range(1000)],1],'expected':1000000}]))
    def test_unpinned_or_changed_statement_and_case_fail_closed(self):
        for pid in o.IDS:
            with self.assertRaises(ValueError):o.public_examples(pid,self.raw[pid])
            with patch.dict(o.STATEMENT_SHA256,{pid:q.sha(self.raw[pid])}):
                with self.assertRaises(ValueError):o.public_examples(pid,self.raw[pid]+b' ')
                with patch.dict(o.CASE_COUNT,{pid:-1}),patch.object(o,'_generate_cases',return_value=self.built[pid]):
                    with self.assertRaises(ValueError):o.build_cases(pid,self.raw[pid])

if __name__=='__main__':unittest.main()
