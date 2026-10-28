"""Reference cross-checks and validator negative controls, not candidate tests."""
from collections import Counter
from itertools import combinations, permutations, product
import math
import unittest

import cases
import oracles as o


class References(unittest.TestCase):
    def test_digit_cover_against_forward_definition(self):
        for count in range(1,5):
            for digits in combinations(range(10),count):
                text = ''.join(o.DIGITS[i] for i in digits)
                self.assertEqual(o.word_digits(text),''.join(map(str,digits)))

    def test_magical_fixed_point_known_prefix_and_runs(self):
        self.assertEqual(o.magical_prefix(19),'1221121221221121122')
        text = o.magical_prefix(10000)
        lengths = ''.join(str(len(list(g))) for _,g in __import__('itertools').groupby(text))
        # Last run may be cut by the requested prefix boundary.
        self.assertEqual(lengths[:-1],text[:len(lengths)-1])

    def test_interval_hitting_set_against_greedy_crosscheck(self):
        options = [(a,b) for a in range(-2,3) for b in range(a+1,4)]
        for intervals in combinations(options,3):
            arrows=[]
            for a,b in sorted(intervals,key=lambda p:p[1]):
                if not arrows or arrows[-1] < a: arrows.append(b)
            self.assertEqual(o.expected(452,[[list(p) for p in intervals]]),len(arrows))

    def test_project_search_against_all_execution_orders(self):
        for profits in product((0,1,2),repeat=3):
            for capital in product((0,1,3),repeat=3):
                best=0
                for order in permutations(range(3)):
                    money=0
                    for i in order[:2]:
                        if capital[i] > money: break
                        money += profits[i]; best=max(best,money)
                self.assertEqual(o.expected(502,[2,0,list(profits),list(capital)]),best)

    def test_special_output_predicates_reject_wrong_answers(self):
        args=[[[5,0],[5,1]]];want=o.expected(406,args)
        self.assertTrue(o.matches(406,args,[[5,0],[5,1]],want))
        self.assertFalse(o.matches(406,args,[[5,1],[5,0]],want))
        self.assertFalse(o.matches(406,args,[[5,False],[5,True]],want))
        self.assertTrue(o.matches(451,['tree'],'eetr','eert'))
        self.assertFalse(o.matches(451,['tree'],'etre','eert'))
        self.assertTrue(o.matches(491,[[1,1]],[[1,1]],[(1,1)]))
        self.assertFalse(o.matches(491,[[1,1]],[[1,1],[1,1]],[(1,1)]))

    def test_alias_type_mutation_negative_controls(self):
        args=[[[5,0]]];want=[(5,0)]
        record={'result':[[5,0]],'result_type':'list','args_before':args,'args_after':args,'alias_edges':[]}
        self.assertEqual(o.compare(406,args,want,record,'python'),(True,None))
        self.assertEqual(o.compare(406,args,want,dict(record,alias_edges=[['result.0','args.0.0']]),'python'),(False,'mutable_return_alias'))
        self.assertEqual(o.compare(406,args,want,dict(record,args_after=[[[6,0]]]),'python'),(False,'input_effects'))
        self.assertEqual(o.compare(406,args,want,dict(record,result_type='tuple'),'python'),(False,'result_type'))

    def test_generated_domain_rejections(self):
        for pid,args in [(402,['01',1]),(403,[[0]]),(410,[[1,2],3]),(442,[[1,1,1]]),
                         (458,[2,3,1]),(474,[['0'],0,1]),(481,[0]),(494,[[1000,1000],0])]:
            with self.subTest(pid=pid),self.assertRaises(AssertionError): cases.validate_generated(pid,args)


if __name__=='__main__': unittest.main()
