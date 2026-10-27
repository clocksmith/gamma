"""Node-value oracle checks, not native candidate/identity qualification."""
from itertools import product
import unittest
from . import request_git_queue03_subset02_oracles as o


class Queue03NodeTests(unittest.TestCase):
    def test_examples(self):
        for pid,examples in o.EXAMPLES.items():
            for args,answer in examples:
                self.assertEqual(o.expected(pid,args),answer)

    def test_spirals_independent_direction_walker(self):
        for m in range(1,9):
            for n in range(1,9):
                r=c=d=0
                steps=((0,1),(1,0),(0,-1),(-1,0))
                seen=set()
                path=[]
                for _ in range(m*n):
                    path.append((r,c))
                    seen.add((r,c))
                    dr,dc=steps[d]
                    nr,nc=r+dr,c+dc
                    if not(0<=nr<m and 0<=nc<n) or (nr,nc) in seen:
                        d=(d+1)%4
                        dr,dc=steps[d]
                    r,c=r+dr,c+dc
                self.assertEqual(o.spiral_coordinates(m,n),path)
                for length in (1,m*n//2+1,m*n):
                    expected=[[-1]*n for _ in range(m)]
                    for i,(r,c) in enumerate(path[:length]):
                        expected[r][c]=i
                    self.assertEqual(o.expected(2326,[m,n,list(range(length))]),expected)

    def test_trees_independent_bottom_up(self):
        for width in range(1,7):
            for values in product((0,1,3),repeat=width):
                totals=list(values)
                sizes=[1]*width
                answer=0
                for i in range(width-1,-1,-1):
                    for child in (2*i+1,2*i+2):
                        if child<width:
                            totals[i]+=totals[child]
                            sizes[i]+=sizes[child]
                    answer+=totals[i]//sizes[i]==values[i]
                self.assertEqual(o.expected(2265,[list(values)]),answer)
        self.assertEqual(o.expected(2265,[[0,None,1,None,0]]),2)
        self.assertEqual(o.expected(2265,[[1000,None,0,None,1000]]),1)

    def test_invalid_wires_and_domains(self):
        for root in (None,[],[None],[0,None],[0,None,None,1],[True],[1.0],[1001],[-1],[0]*1001):
            with self.assertRaises(ValueError):
                o.validate(2265,[root])
        for args in ([0,1,[0]],[1,0,[0]],[100000,2,[0]],[1,1,[]],[1,1,[0,0]],[1,1,[True]],[1,1,[-1]],[1,1,[1001]],[True,1,[0]]):
            with self.assertRaises(ValueError):
                o.validate(2326,args)

    def test_maximum_domains_and_reference_bound(self):
        for args in ([[0]*1000],[[0]+[x for _ in range(999) for x in (None,0)]]):
            o.validate(2265,args)
            with self.assertRaises(ValueError):
                o.expected(2265,args)
        for args in ([1,100000,[1000]*100000],[100000,1,[0]],[400,250,[0]]):
            o.validate(2326,args)
            with self.assertRaises(ValueError):
                o.expected(2326,args)
        with self.assertRaises(ValueError):
            o.build_cases(2265,b'not pinned')


if __name__=='__main__':
    unittest.main()
