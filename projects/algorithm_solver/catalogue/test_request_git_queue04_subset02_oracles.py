"""Semantic wire tests only; never native candidate qualification."""
from itertools import permutations,product
import unittest
from . import request_git_queue04_subset02_oracles as o


class Queue04WireTests(unittest.TestCase):
    def test_examples(self):
        for pid,rows in o.EXAMPLES.items():
            for args,answer in rows:self.assertEqual(o.expected(pid,args),answer)

    def test_perfect_tree_path_mirroring(self):
        for n in (1,3,7,15,31,63,127):
            a=list(range(n));wanted=[]
            for index in range(n):
                address=bin(index+1)[3:]
                mirrored=''.join('1' if c=='0' else '0' for c in address) if len(address)%2 else address
                wanted.append(a[int('1'+mirrored,2)-1])
            self.assertEqual(o.expected(2415,[a]),wanted)

    def test_swap_bfs_against_cycle_decomposition(self):
        for n in range(1,7):
            for values in permutations(range(n)):
                seen=set();answer=0
                for start in range(n):
                    if start in seen:continue
                    length=0;i=start
                    while i not in seen:seen.add(i);length+=1;i=values[i]
                    answer+=length-1
                self.assertEqual(o._swap_distance(values),answer)
        self.assertEqual(o.expected(2471,[[1,None,2,4,3]]),1)

    def test_stateful_transcripts_against_boolean_prefix_mask(self):
        for n in range(1,6):
            for order in permutations(range(1,n+1)):
                mask=0;ops=[];wanted=[]
                for video in order:
                    mask|=1<<(video-1);ops.extend((['upload',video],['longest'],['longest']))
                    k=0
                    while mask>>k&1:k+=1
                    wanted.extend((None,k,k))
                self.assertEqual(o.expected(2424,[n,ops]),wanted)

    def test_invalid_domains(self):
        invalid={2415:[[[]],[[0,1]],[[0]*16384],[[False]],[[100001]],[[0.0]]],
                 2471:[[[]],[[None]],[[1,None]],[[1,None,None,2]],[[1,1]],[[0]],[[True]],[[1.0]],[[100001]]],
                 2424:[[0,[['longest']]],[1,[]],[1,[['upload',1]]],[1,[['upload',1],['upload',1],['longest']]],
                       [1,[['upload',True],['longest']]],[1,[['upload',2],['longest']]],[1,[['longest',0]]],
                       [True,[['longest']]],[1,[['longest']]*200001]]}
        for pid,rows in invalid.items():
            for args in rows:
                with self.assertRaises(ValueError):o.validate(pid,args)
        for pid in o.IDS:
            for args in (None,(),[],[None]*len(o.WIRE_PARAMETERS[pid])):
                with self.assertRaises(ValueError):o.validate(pid,args)

    def test_full_domain_distinct_from_reference_budget(self):
        for pid,args in [(2415,[[100000]*16383]),(2471,[list(range(1,100001))]),
                         (2471,[[1]+[x for v in range(2,100001) for x in (None,v)]]),
                         (2424,[100000,[['longest']]*200000])]:
            o.validate(pid,args)
            with self.assertRaises(ValueError):o.expected(pid,args)
        for pid in o.IDS:
            with self.assertRaises(ValueError):o.build_cases(pid,b'not pinned')


if __name__=='__main__':unittest.main()
