import copy
from collections import deque
import math
from itertools import permutations
import unittest
import oracles as o

class ReferenceChecks(unittest.TestCase):
    def test_square_theorem_against_exhaustive_dp(self):
        dp=[0]+[1000]*128
        for n in range(1,129):
            dp[n]=1+min(dp[n-k*k] for k in range(1,math.isqrt(n)+1))
            self.assertEqual(o.expected(279,[n]),dp[n])
    def test_smooth_heap_against_integer_factorization(self):
        smooth=[]
        for n in range(1,10000):
            v=n
            for p in (2,3,5):
                while v%p==0:v//=p
            if v==1:smooth.append(n)
        for index,n in enumerate(smooth):self.assertEqual(o.expected(264,[index+1]),n)
    def test_replacement_against_breadth_first_search(self):
        for n in range(1,100):
            queue=deque([(n,0)]);seen={n}
            while queue:
                v,d=queue.popleft()
                if v==1:break
                for nxt in ((v//2,) if v%2==0 else (v-1,v+1)):
                    if nxt not in seen:seen.add(nxt);queue.append((nxt,d+1))
            self.assertEqual(o.expected(397,[n]),d)
    def test_roman_domain_roundtrip_and_uniqueness(self):
        self.assertEqual(len(o.ROMANS),3999)
        self.assertEqual(o.expected(13,['MCMXCIV']),1994)
    def test_result_freedom_and_negative_controls(self):
        self.assertTrue(o.matches(162,[[3,1,2]],2,[0,2]))
        self.assertFalse(o.matches(162,[[3,1,2]],True,[0,2]))
        self.assertTrue(o.matches(368,[[1,2,3]],[3,1],2))
        self.assertFalse(o.matches(368,[[1,2,3]],[2,3],2))
        self.assertTrue(o.matches(324,[[1,1,2,2]],[1,2,1,2],[1,1,2,2]))
        self.assertFalse(o.matches(324,[[1,1,2,2]],[1,1,2,2],[1,1,2,2]))
        args=[[1,2],1];record={'result':[2,1],'result_type':'list','args_before':args,'args_after':args,'alias_edges':[]}
        self.assertEqual(o.compare(189,args,[2,1],record,'python'),(True,None))
        altered=copy.deepcopy(record);altered['args_after']=[[2,1],1]
        self.assertEqual(o.compare(189,args,[2,1],altered,'python'),(False,'input_effects'))
    def test_rpn_truncation(self):
        for a,b,v in ((-7,3,-2),(7,-3,-2),(-7,-3,2)):
            self.assertEqual(o.expected(150,[[str(a),str(b),'/']]),v)
if __name__=='__main__':unittest.main()
