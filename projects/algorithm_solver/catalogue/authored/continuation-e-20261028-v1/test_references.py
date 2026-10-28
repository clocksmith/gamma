"""Host reference tests, no candidate modules exist at initial freeze."""
import copy
from itertools import product,combinations
import unittest
import oracles as o

class ReferenceTests(unittest.TestCase):
    def test_official_examples(self):
        for pid,rows in o.PUBLIC_EXAMPLES.items():
            for args,want in rows:self.assertEqual(o.expected(pid,args),want)
    def test_generator_recomputation_and_no_mutation(self):
        for pid in o.IDS:
            for row in o.build_cases(pid):
                before=copy.deepcopy(row['args']);self.assertEqual(o.expected(pid,row['args']),row['expected']);self.assertEqual(before,row['args'])
    def test_decimal_lexicographic_score_tie_and_impossible(self):
        self.assertEqual(o.expected(3723,[2,9]),'90');self.assertEqual(o.expected(3723,[3,1]),'100');self.assertEqual(o.expected(3723,[1,11]),'')
    def test_stable_subarray_negative_and_length(self):
        self.assertEqual(o.expected(3728,[[1,1,1]]),1);self.assertEqual(o.expected(3728,[[0,0,0,0]]),3)
    def test_sorted_distinct_sequence_definition(self):
        self.assertEqual(o.expected(3729,[[1,1,1],1]),3)
        self.assertEqual(o.expected(3729,[[1,1,2,2],1]),8)
    def test_exact_replacement_and_palindrome_strictness(self):
        self.assertEqual(o.expected(3732,[[0,0,0]]),0)
        self.assertEqual(o.expected(3734,['abba','abba']),'baab')
        self.assertEqual(o.expected(3734,['a','a']),'')
        self.assertEqual(o.expected(3734,['b','a']),'b')
    def test_majority_reference_matches_sign_walk(self):
        for n in range(1,8):
            for a in product((1,2),repeat=n):
                prefix=[0]
                for v in a:prefix.append(prefix[-1]+(1 if v==1 else -1))
                want=sum(prefix[j]>prefix[i] for i,j in combinations(range(n+1),2))
                for pid in (3737,3739):self.assertEqual(o.expected(pid,[list(a),1]),want)
    def test_input_and_output_types(self):
        for pid,args in [(3723,[True,1]),(3724,[[1],[1]]),(3727,[[40001]]),(3728,[[1,1]]),(3729,[[2,1],1]),(3732,[[1,2]]),(3734,['A','a']),(3737,[[1],False]),(3738,[[1.0]])]:
            with self.assertRaises(ValueError):o.validate(pid,args)
        self.assertFalse(o.matches(3738,[[1]],True))
    def test_reference_budgets_remain_distinct(self):
        for pid,args in [(3723,[6,1]),(3724,[[1]*4,[1]*5]),(3727,[[1]*9]),(3728,[[1]*81]),(3729,[[1]*61,1]),(3732,[[1]*11]),(3734,['aabbccdde','a'*9]),(3739,[[1,2]*31,1]),(3738,[list(range(15))])]:
            o.validate(pid,args)
            with self.assertRaises(ValueError):o.expected(pid,args)

if __name__=='__main__':unittest.main()
