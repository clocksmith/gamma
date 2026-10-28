"""Only independent host reference code is imported; candidate code is never run."""
import copy
from itertools import product
import unittest
import oracles as o

EXAMPLES={3650:[([4,[[0,1,3],[3,1,1],[2,3,4],[0,2,2]]],5),([4,[[0,2,1],[2,1,1],[1,3,1],[2,3,3]]],3)],3651:[([[[1,3,3],[2,5,4],[4,3,5]],2],7),([[[1,2],[2,3],[3,4]],1],9)],3652:[([[4,2,8],[-1,0,1],2],10),([[5,4,3],[1,1,0],2],9)],3653:[([[1,1,1],[[0,2,1,4]]],4),([[2,3,1,5,4],[[1,4,2,3],[0,2,1,2]]],31)],3659:[([[1,2,3,4],2],True),([[3,5,2,2],2],True),([[1,5,2,3],3],False)],3660:[([[2,1,3]],[2,2,3]),([[2,3,1]],[3,3,3])],3661:[([[4],[3],[1,10]],1),([[10,2],[5,1],[5,2,7]],3),([[1,2],[100,1],[10]],0)],3666:[(['110',1],1),(['0101',3],2),(['101',2],-1)],3669:[([100,2],0),([44,3],9)]}
EXAMPLES[3655]=EXAMPLES[3653]

class ReferenceTests(unittest.TestCase):
    def test_official_numeric_examples(self):
        for pid,rows in EXAMPLES.items():
            for args,want in rows:
                with self.subTest(pid=pid,args=args):self.assertEqual(o.expected(pid,args),want)
    def test_generators_are_bounded_valid_and_do_not_mutate(self):
        for pid in o.IDS:
            for row in o.cases(pid):
                before=copy.deepcopy(row['args']);o.validate(pid,row['args']);self.assertEqual(o.expected(pid,row['args']),row['expected']);self.assertEqual(row['args'],before)
    def test_strict_types_and_witness_policy(self):
        self.assertFalse(o.accepts(3659,[[1,2],2],1))
        self.assertFalse(o.accepts(3669,None,[1,1]))
        self.assertFalse(o.accepts(True,[],0))
        self.assertTrue(o.accepts(3669,[44,3],[11,2,2]))
        for row in ([1,4,11],[2,2,True],[2,2,11,1],[2,2,10]):self.assertFalse(o.accepts(3669,[44,3],row))
    def test_group_assignment_against_frequency_theorem(self):
        for n in range(1,8):
            for values in product((1,2),repeat=n):
                for k in range(1,n+1):self.assertEqual(o.expected(3659,[list(values),k]),n%k==0 and max(values.count(1),values.count(2))<=n//k)
    def test_zero_count_symmetry_against_full_masks(self):
        for n in range(1,7):
            for zeros in range(n+1):
                for k in range(1,n+1):
                    target='0'*zeros+'1'*(n-zeros)
                    self.assertEqual(o.expected(3666,[target,k]),o.expected(3666,[target[::-1],k]))
    def test_boundaries_and_rejection(self):
        for pid,args in ((3650,[2,[[0,1,True]]]),(3652,[[1,2],[0,0],True]),(3661,[[1,1],[2,2],[3]]),(3666,['2',1]),(3669,[4,3])):
            with self.assertRaises(ValueError):o.validate(pid,args)
        with self.assertRaises(ValueError):o.expected(3666,['0'*10,2])
        with self.assertRaises(ValueError):o.expected(3660,[[1]*31])
    def test_reversal_switch_and_disconnected(self):
        self.assertEqual(o.expected(3650,[3,[[1,0,2],[2,1,3]]]),10)
        self.assertEqual(o.expected(3650,[3,[[0,1,2]]]),-1)
    def test_robot_endpoints_and_obstacles(self):
        self.assertEqual(o.expected(3661,[[2],[1],[1,2,3]]),2)
        self.assertEqual(o.expected(3661,[[1,2],[100,1],[1,2,3]]),3)
    def test_modular_incidence_can_use_large_exact_integers(self):
        args=[[1000000000],[[0,0,1,100000]]*20]
        self.assertEqual(o.expected(3655,args),1000000000*pow(100000,20,o.MOD)%o.MOD)

if __name__=='__main__':unittest.main()
