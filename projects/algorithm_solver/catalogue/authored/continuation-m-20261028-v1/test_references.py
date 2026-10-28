import copy
import importlib.util
from pathlib import Path
import unittest
S=importlib.util.spec_from_file_location('gamma_continuation_m_oracles',Path(__file__).with_name('oracles.py'));o=importlib.util.module_from_spec(S);S.loader.exec_module(o)

class ReferenceTests(unittest.TestCase):
    def test_public_examples(self):
        for pid,rows in o.PUBLIC_EXAMPLES.items():
            for args,value in rows:self.assertTrue(o.exact(o.expected(pid,args),value),(pid,args))
    def test_generated_cases_nonmutating(self):
        for pid in o.IDS:
            for row in o.build_cases(pid):
                args=copy.deepcopy(row['args']);before=copy.deepcopy(args);self.assertTrue(o.exact(o.expected(pid,args),row['expected']));self.assertEqual(args,before);self.assertTrue(o.matches(pid,args,row['expected']))
    def test_comma_boundaries(self):
        for n in (999,1000,1001,9999):self.assertEqual(o.expected(3871,[n]),sum((len(str(x))-1)//3 for x in range(1,n+1)))
    def test_arithmetic_integer_not_fractional(self):
        self.assertEqual(o.expected(3872,[[1,2,8,4]]),4)
        self.assertEqual(o.expected(3872,[[1,3,8,7,9]]),5)
    def test_activation_newpoint_and_distinctness(self):
        self.assertEqual(o.expected(3873,[[[0,0]]]),2);self.assertEqual(o.expected(3873,[[[0,0],[1,1]]]),3)
    def test_empty_xor_and_or_membership(self):
        self.assertEqual(o.expected(3877,[[1],0]),1);self.assertEqual(o.expected(3878,[[1,2]]),2)
    def test_direction_own_orientation_free(self):
        for pos in range(4):self.assertEqual(o.expected(3881,[4,pos,2]),6)
    def test_native_priority_ties_stale_and_empty(self):
        args=[['EventManager','updatePriority','updatePriority','pollHighest','pollHighest','pollHighest'],[[[[2,10],[1,10]]],[1,1],[1,10],[],[],[]]]
        self.assertEqual(o.expected(3885,args),[None,None,None,1,2,-1])
        with self.assertRaises(ValueError):o.validate(3885,[['EventManager','pollHighest','updatePriority'],[[[[1,1]]],[],[1,2]]])
    def test_cubes_unordered_positive_pairs(self):
        self.assertEqual(o.expected(3890,[1728]),[]);self.assertEqual(o.expected(3890,[1729]),[1729])
    def test_domain_and_types(self):
        for pid,args in [(3873,[[[1,1],[1,1]]]),(3876,[[1,1]]),(3881,[2,0,2]),(3872,[[1,2,3]])]:
            with self.assertRaises(ValueError):o.validate(pid,args)
        self.assertFalse(o.matches(3876,[[1]],1));self.assertFalse(o.matches(3890,[1],[False]));self.assertFalse(o.matches(3885,o.PUBLIC_EXAMPLES[3885][0][0],[None,True,None,5,9]))
    def test_work_budget_distinct(self):
        o.validate(3877,[[1,2]*20,0])
        with self.assertRaises(ValueError):o.expected(3877,[[1,2]*20,0])
if __name__=='__main__':unittest.main()
