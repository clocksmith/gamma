"""Only host reference definitions run; candidate programs are not imported."""
import copy
from itertools import product
import unittest
import oracles as o

class ReferenceTests(unittest.TestCase):
    def test_official_examples(self):
        for pid,rows in o.PUBLIC_EXAMPLES.items():
            for args,want in rows:self.assertEqual(o.expected(pid,args),want)
    def test_every_case_recomputes_and_preserves_arguments(self):
        for pid in o.IDS:
            for row in o.build_cases(pid):
                original=copy.deepcopy(row['args']);self.assertEqual(o.expected(pid,row['args']),row['expected']);self.assertEqual(original,row['args'])
    def test_letter_operation_states_against_single_letter_distances(self):
        for c in 'abcdefghijklmnopqrstuvwxyz':self.assertEqual(o.expected(3675,[c]),(123-ord(c))%26)
        self.assertEqual(o.expected(3675,['ayz']),2)
    def test_window_subset_reference_against_explicit_valid_masks(self):
        self.assertEqual(o.expected(3679,[[1,1,1,1],2,1]),2)
        self.assertEqual(o.expected(3679,[[1,1,2,1],3,1]),1)
    def test_repetition_and_distinctness_are_separate(self):
        self.assertEqual(o.expected(3689,[[1,4],3]),9)
        self.assertEqual(o.expected(3691,[[1,4],3]),3)
    def test_rotation_graph_is_symmetric_and_duplicate_safe(self):
        for a,b in [([1,2,3],[3,2,1]),([1,1,2],[2,1,1]),([-100000,0,100000],[0,100000,-100000])]:self.assertEqual(o.expected(3690,[a,b]),o.expected(3690,[b,a]))
        self.assertEqual(o.expected(3690,[[1,1],[1,1]]),0)
    def test_zigzag_enumeration_against_independent_pair_state_walk(self):
        for n in range(3,8):
            for width in range(2,5):
                state={(a,b):1 for a in range(width) for b in range(width) if a!=b}
                for _ in range(2,n):state={(b,c):sum(v for (a,x),v in state.items() if x==b and ((a<b and c<b) or (a>b and c>b))) for b in range(width) for c in range(width) if c!=b}
                self.assertEqual(o.expected(3699,[n,1,width]),sum(state.values()))
                self.assertEqual(o.expected(3700,[n,1,width]),sum(state.values()))
    def test_domain_and_numeric_types_fail_closed(self):
        for pid,args in [(3675,['A']),(3679,[[1],1,True]),(3689,[[1],0]),(3690,[[1,2],[1,1]]),(3693,[2,[1]]),(3694,['UX',1]),(3698,[[1]]),(3699,[3,1,1]),(3700,[10**9+1,1,2])]:
            with self.assertRaises(ValueError):o.validate(pid,args)
        self.assertFalse(o.matches(3698,[[1,1]],False))
    def test_work_limits_are_not_domain_limits(self):
        for pid,args in [(3675,['abcd']),(3679,[[1]*15,15,1]),(3691,[[1]*41,1]),(3693,[19,[1]*19]),(3694,['U'*201,1]),(3698,[[1]*201]),(3700,[100,1,3])]:
            o.validate(pid,args)
            with self.assertRaises(ValueError):o.expected(pid,args)

if __name__=='__main__':unittest.main()
