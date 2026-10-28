import copy
from itertools import product
import unittest
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location('continuation_g_test_oracles', Path(__file__).with_name('oracles.py'))
o = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(o)

class ReferenceTests(unittest.TestCase):
    def test_official_examples(self):
        for pid,rows in o.PUBLIC_EXAMPLES.items():
            for args,wanted in rows:self.assertEqual(o.expected(pid,args),wanted,(pid,args))
    def test_generators_are_bounded_and_nonmutating(self):
        for pid in o.IDS:
            for row in o.build_cases(pid):
                args=copy.deepcopy(row['args']);before=copy.deepcopy(args)
                self.assertEqual(o.expected(pid,args),row['expected']);self.assertEqual(args,before)
                self.assertTrue(o.matches(pid,args,row['expected']))
    def test_mirror_direction_and_trailing_zero(self):
        self.assertEqual(o.expected(3761,[[120,21]]),1)
        self.assertEqual(o.expected(3761,[[21,120]]),-1)
        self.assertEqual(o.expected(3761,[[1]]),-1)
    def test_prime_prefix_suffix_and_binary_distance(self):
        for num,wanted in [(2,True),(23,True),(313,True),(29,False),(101,False),(1,False)]:self.assertEqual(o.expected(3765,[num]),wanted)
        self.assertEqual(o.expected(3766,[[1,2,3,4,5,6,7,8]]),[0,1,0,1,0,1,0,1])
        self.assertEqual(o.expected(3770,[41]),41);self.assertEqual(o.expected(3770,[40]),17)
    def test_at_least_k_not_exactly_k(self):
        self.assertEqual(o.expected(3767,[[9,8],[1,2],0]),17)
        self.assertEqual(o.expected(3767,[[1,2],[9,8],2]),3)
    def test_transport_conservation_and_opposite_distance(self):
        self.assertEqual(o.expected(3776,[[0,-2,0,2]]),4)
        self.assertEqual(o.expected(3776,[[-2,1]]),-1)
        self.assertEqual(o.expected(3776,[[0]]),0)
    def test_alternating_reference_against_subsequence_enumeration(self):
        for n in range(1,8):
            for chars in product('AB',repeat=n):
                s=''.join(chars);best=0
                for mask in range(1<<n):
                    t=''.join(s[i] for i in range(n) if mask>>i&1)
                    if all(x!=y for x,y in zip(t,t[1:])):best=max(best,len(t))
                self.assertEqual(o.expected(3777,[s,[[2,0,n-1]]]),[n-best])
        self.assertEqual(o.expected(3777,['AA',[[1,0],[1,0],[2,0,1]]]),[1])
    def test_uniform_triple_certificate(self):
        self.assertEqual(o.expected(3780,[[2]*81]),6)
        self.assertEqual(o.expected(3780,[[1]*81]),3)
        self.assertEqual(o.expected(3780,[[100000]*100000]),300000)
    def test_types_and_official_domain(self):
        self.assertFalse(o.matches(3765,[2],1));self.assertFalse(o.matches(3766,[[1]],[False]));self.assertFalse(o.matches(3777,['A',[[2,0,0]]],[False]))
        for pid,args in [(3760,['']),(3765,[True]),(3766,[[5001]]),(3776,[[-1,-1]]),(3777,['A',[[2,0,1]]]),(3780,[[1,2]])]:
            with self.assertRaises(ValueError):o.validate(pid,args)
    def test_reference_budget_is_not_domain(self):
        o.validate(3760,['ab'*20])
        with self.assertRaises(ValueError):o.expected(3760,['ab'*20])
        o.validate(3767,[[1]*17,list(range(1,18)),2])
        with self.assertRaises(ValueError):o.expected(3767,[[1]*17,list(range(1,18)),2])

if __name__=='__main__':unittest.main()
