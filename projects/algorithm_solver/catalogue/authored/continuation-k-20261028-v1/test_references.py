import copy
import unittest
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("gamma_continuation_k_references", Path(__file__).with_name("oracles.py"))
o = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(o)

class ReferenceTests(unittest.TestCase):
    def test_official_examples(self):
        for pid,rows in o.PUBLIC_EXAMPLES.items():
            for args,value in rows:self.assertEqual(o.expected(pid,args),value,(pid,args))
    def test_generated_cases_and_effects(self):
        for pid in o.IDS:
            for row in o.build_cases(pid):
                args=copy.deepcopy(row['args']);before=copy.deepcopy(args);self.assertEqual(o.expected(pid,args),row['expected']);self.assertEqual(args,before);self.assertTrue(o.matches(pid,args,row['expected']))
    def test_prefix_groups_ignore_short_words(self):
        self.assertEqual(o.expected(3839,[['a','a','ab','abc','abz'],2]),1)
    def test_frequency_order_not_minimum(self):
        self.assertEqual(o.expected(3843,[[9,9,1]]),9)
    def test_exact_one_deletion(self):
        self.assertEqual(o.expected(3844,['ab']),2);self.assertEqual(o.expected(3844,['abcd']),2);self.assertEqual(o.expected(3844,['abcba']),5)
    def test_range_and_unsigned_xor(self):
        self.assertEqual(o.expected(3845,[[0,32767,0],0]),32767)
        self.assertEqual(o.expected(3845,[[1,2,3],0]),3)
    def test_complete_digitorial_enumeration(self):
        self.assertEqual(o.all_digitorials(),frozenset((1,2,145,40585)))
        self.assertTrue(o.expected(3848,[154]));self.assertFalse(o.expected(3848,[10]))
    def test_rational_division_and_distinct_actions(self):
        self.assertEqual(o.expected(3850,[[2,4],2]),2)
        self.assertEqual(o.expected(3850,[[1]*19,1]),3**19)
        self.assertEqual(o.expected(3850,[[1,5],7]),0)
    def test_merge_priority_and_signed_parity(self):
        self.assertEqual(o.expected(3853,['aabca',2]),'abca')
        self.assertEqual(o.expected(3854,[[-1,0,-1,0]]),[0,1])
        self.assertEqual(o.expected(3854,[[2,2]]),[1,1])
    def test_domains_and_types(self):
        for pid,args in [(3844,['a']),(3845,[[32768],0]),(3850,[[0],1]),(3849,['0','11']),(3853,['a',2])]:
            with self.assertRaises(ValueError):o.validate(pid,args)
        self.assertFalse(o.matches(3848,[145],1));self.assertFalse(o.matches(3854,[[1]],[False,False]))
    def test_work_budget_not_domain(self):
        o.validate(3850,[[2]*19,1])
        with self.assertRaises(ValueError):o.expected(3850,[[2]*19,1])
        o.validate(3844,['ab'*100])
        with self.assertRaises(ValueError):o.expected(3844,['ab'*100])
if __name__=='__main__':unittest.main()
