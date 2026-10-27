"""Pure stdlib reference/validator tests; no candidate or statement file reads."""
from itertools import product
import unittest

from . import request_git_queue03_oracles as o


class Queue03Tests(unittest.TestCase):
    def test_public_examples(self):
        for pid, examples in o.EXAMPLES.items():
            for args, answer in examples:
                self.assertEqual(o.expected(pid,args),answer)

    def test_zero_runs_and_splices_independent(self):
        for n in range(1,6):
            for values in product((-1,0,1),repeat=n):
                run=0
                total=0
                for value in values:
                    run=run+1 if value == 0 else 0
                    total+=run
                self.assertEqual(o.expected(2348,[list(values)]),total)
            for values in product((1,4),repeat=2*n):
                a,b=list(values[:n]),list(values[n:])
                results=[]
                for first,second in ((a,b),(b,a)):
                    current=best=0
                    for x,y in zip(first,second):
                        current=max(0,current+y-x)
                        best=max(best,current)
                    results.append(sum(first)+best)
                self.assertEqual(o.expected(2321,[a,b]),max(results))

    def test_actual_array_operations_independent_of_gap_reduction(self):
        for n in (1,2):
            for values in product(range(3),repeat=2*n):
                for k1,k2 in ((0,0),(1,0),(0,1),(1,1),(2,0),(0,2)):
                    states={(values,0,0)}
                    frontier=list(states)
                    best=sum((values[i]-values[n+i])**2 for i in range(n))
                    while frontier:
                        state,u,v=frontier.pop()
                        best=min(best,sum((state[i]-state[n+i])**2 for i in range(n)))
                        for offset,budget,used in ((0,k1,u),(n,k2,v)):
                            if used == budget:
                                continue
                            for i in range(n):
                                for sign in (-1,1):
                                    altered=list(state)
                                    altered[offset+i]+=sign
                                    item=(tuple(altered),u+(offset==0),v+(offset==n))
                                    if item not in states:
                                        states.add(item)
                                        frontier.append(item)
                    self.assertEqual(o.expected(2333,[list(values[:n]),list(values[n:]),k1,k2]),best)

    def test_tile_event_witnesses_and_directional_matching(self):
        for mask in range(1,128):
            tiles=[[i+1,i+1] for i in range(7) if mask>>i&1]
            for length in range(1,10):
                starts={x for l,r in tiles for x in (l,r-length+1)}
                answer=max(sum(max(0,min(r,s+length-1)-max(l,s)+1) for l,r in tiles) for s in starts)
                self.assertEqual(o.expected(2271,[tiles,length]),answer)
        for s in ('a','b','ab','ba','aaaa','baba','0Ab'):
            for sub in ('a','b','ab','aa','a0'):
                if len(sub)>len(s):
                    continue
                for maps in ([],[['a','b']],[['b','a']],[['a','b'],['b','0']]):
                    answer=any(all(x==y or [x,y] in maps for x,y in zip(sub,s[i:i+len(sub)])) for i in range(len(s)-len(sub)+1))
                    self.assertEqual(o.expected(2301,[s,sub,maps]),answer)

    def test_corner_paths_prime_factors(self):
        for values in product((1,2,5,10),repeat=4):
            grid=[list(values[:2]),list(values[2:])]
            def factors(value,p):
                count=0
                while value%p == 0:
                    value//=p
                    count+=1
                return count
            paths=[(i,) for i in range(4)]+[(0,1),(0,2),(1,3),(2,3)]+[(0,1,2),(0,1,3),(0,2,3),(1,2,3)]
            answer=max(min(sum(factors(values[i],2) for i in path),sum(factors(values[i],5) for i in path)) for path in paths)
            self.assertEqual(o.expected(2245,[grid]),answer)

    def test_simultaneous_removal_not_sequential(self):
        for args,answer in [([[5,4,3,2,1]],1),([[5,1,2,3,4]],4),([[2,1,1,1]],3),([[1,1,1]],0),([[3,2,2,4,1,2,3]],3)]:
            self.assertEqual(o.expected(2289,args),answer)

    def test_invalid_domains_and_type_controls(self):
        invalid={2245:[[],[[0]],[[1001]],[[1],[1,2]],[[True]]],
                 2289:[[],[0],[10**9+1],[True],[1.0]],2348:[[],[-10**9-1],[10**9+1],[False],[0.0]]}
        for pid,values in invalid.items():
            for value in values:
                with self.assertRaises(ValueError):
                    o.validate(pid,[value])
        for pid,args in [(2271,[[[1,2],[2,3]],1]),(2271,[[[2,1]],1]),(2271,[[[1,1]],0]),
                         (2301,['é','é',[]]),(2301,['a','aa',[]]),(2301,['a','a',[['a','a']]]),
                         (2321,[[0],[1]]),(2321,[[1],[1,2]]),(2321,[[True],[1]]),
                         (2333,[[0],[0],-1,0]),(2333,[[0],[0],True,0]),(2333,[[100001],[0],0,0])]:
            with self.assertRaises(ValueError):
                o.validate(pid,args)
        for pid in o.IDS:
            for args in (None,{},(),[],[None]*len(o.PARAMETERS[pid])):
                with self.assertRaises(ValueError):
                    o.validate(pid,args)

    def test_full_domain_not_reference_budget(self):
        for pid,args in [(2245,[[[1]*100000]]),(2271,[[[1,10**9]],10**9]),(2289,[[1]*100000]),
                         (2301,['a'*5000,'a'*5000,[]]),(2321,[[10000]*100000,[10000]*100000]),
                         (2333,[[100000]*100000,[100000]*100000,10**9,10**9]),(2348,[[-10**9]*100000])]:
            o.validate(pid,args)
            with self.assertRaises(ValueError):
                o.expected(pid,args)
        with self.assertRaises(ValueError):
            o.build_cases(2348,b'not pinned')


if __name__ == '__main__':
    unittest.main()
