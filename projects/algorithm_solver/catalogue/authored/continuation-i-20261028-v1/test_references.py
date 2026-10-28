import copy
from itertools import product
import unittest
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location('continuation_i_test_oracles', Path(__file__).with_name('oracles.py'))
o = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(o)

class ReferenceTests(unittest.TestCase):
    def test_official_examples(self):
        for pid,rows in o.PUBLIC_EXAMPLES.items():
            for args,wanted in rows:self.assertEqual(o.expected(pid,args),wanted,(pid,args))
    def test_generators_exact_nonmutating(self):
        for pid in o.IDS:
            for row in o.build_cases(pid):
                args=copy.deepcopy(row['args']);before=copy.deepcopy(args)
                self.assertEqual(o.expected(pid,args),row['expected']);self.assertEqual(args,before);self.assertTrue(o.matches(pid,args,row['expected']))
    def test_caesar_uniform_shift_not_anagram(self):
        self.assertEqual(o.expected(3805,[['ab','za','bc']]),3)
        self.assertEqual(o.expected(3805,[['ab','ba']]),0)
        self.assertEqual(o.expected(3805,[['a']*1000]),499500)
    def test_increment_uniform_certificates(self):
        for n in range(1,5):
            for value in range(1,6):
                for k in range(1,6):
                    for m in range(1,n+1):
                        # Independent allocation enumeration verifies closed-form uniform certificate.
                        best=0
                        def allocate(i,left,current):
                            nonlocal best
                            if i==m:best=max(best,current);return
                            for d in range(left+1):allocate(i+1,left-d,value+d if i==0 else current&(value+d))
                        allocate(0,k,0)
                        self.assertEqual(o.expected(3806,[[value]*n,k,m]),best)
    def test_global_updates_and_strict_budget(self):
        self.assertEqual(o.expected(3810,[[1,2,1],[2,1,3]]),2)
        self.assertEqual(o.expected(3814,[[2,3],[8,9],5]),9)
        self.assertEqual(o.expected(3814,[[2,3],[8,9],6]),17)
    def test_xor_partition_against_cut_enumeration(self):
        for n in range(1,7):
            for values in product(range(2),repeat=n):
                for t1,t2 in [(0,1),(1,0)]:
                    count=0
                    for mask in range(1<<(n-1)):
                        blocks=[];value=0
                        for i,x in enumerate(values):
                            value^=x
                            if i==n-1 or mask>>i&1:blocks.append(value);value=0
                        count+=all(x==(t1 if i%2==0 else t2) for i,x in enumerate(blocks))
                    self.assertEqual(o.expected(3811,[list(values),t1,t2]),count)
    def test_tree_identity_parity_and_edge_order(self):
        self.assertEqual(o.expected(3812,[3,[[2,1],[0,1]],'000','101']),[0,1])
        self.assertEqual(o.expected(3812,[2,[[0,1]],'01','01']),[])
        self.assertEqual(o.expected(3812,[2,[[0,1]],'00','10']),[-1])
    def test_duplicates_may_remain_and_prefix_can_empty(self):
        self.assertEqual(o.expected(3816,['aaccb']),'aacb')
        self.assertEqual(o.expected(3816,['aaba']),'aab')
        self.assertEqual(o.expected(3816,['aaaa']),'a')
        self.assertEqual(o.expected(3818,[[1,2,3]]),0)
    def test_domains_and_exact_output_types(self):
        for pid,args in [(3806,[[1],0,1]),(3805,[['a','bb']]),(3811,[[0],1,1]),(3812,[3,[[0,1],[1,0]],'000','000']),(3814,[[1],[1],0])]:
            with self.assertRaises(ValueError):o.validate(pid,args)
        self.assertFalse(o.matches(3804,[[1]],True));self.assertFalse(o.matches(3809,[[[0,0,1]],[0,0],0],[False,False]))
    def test_reference_budget_not_domain(self):
        o.validate(3816,['ab'*20])
        with self.assertRaises(ValueError):o.expected(3816,['ab'*20])
        o.validate(3806,[[1,2],10**9,2])
        with self.assertRaises(ValueError):o.expected(3806,[[1,2],10**9,2])
if __name__=='__main__':unittest.main()
