import unittest
from long_spans import longest_cross_owner

class IndexedControls(unittest.TestCase):
    def test_maximal_prefix_lengths_match_independent_distinct_owner_brute(self):
        for texts in ({'a':'ababa','b':'babab','c':'abac'}, {'a':'abcabc','b':'abcabc','c':'zzabc'}, {'a':'ééab','b':'aééb','c':'bb'}):
            actual=longest_cross_owner(texts)
            for pid,text in texts.items():
                expected=[]
                for at in range(len(text)):
                    expected.append(max([0]+[length for length in range(1,len(text)-at+1)
                        if any(text[at:at+length] in other for op,other in texts.items() if op!=pid)]))
                self.assertEqual(actual[pid],expected)

    def test_same_owner_repeats_are_not_cross_owner_support(self):
        self.assertEqual(longest_cross_owner({'a':'aaaa','b':'bbbb'})['a'],[0,0,0,0])

if __name__=='__main__':unittest.main()

class ComplementaryRepairControls(unittest.TestCase):
    def test_full_cross_product_and_charged_capacity(self):
        from long_spans import pair_frontier_repairs
        bundles,overflow=pair_frontier_repairs(('a','b'),[('a','b','ab'),('a','b','ba')],[('X',),('Y',)],4)
        self.assertEqual(set(bundles),{('ab','X'),('ab','Y'),('ba','X'),('ba','Y')})
        self.assertEqual(overflow,0)
        self.assertEqual(pair_frontier_repairs(('a','b'),[('a','b','ab')],[('X',)],3),([('ab','X')],1))

    def test_existing_literal_not_charged_twice_but_no_implicit_basis(self):
        from long_spans import pair_frontier_repairs
        bundles,overflow=pair_frontier_repairs(('a','b'),[('a','b','ab')],[('ab','X')],4)
        self.assertEqual(bundles,[('ab','X')])
        self.assertEqual(overflow,0)


class ExplicitUnionRetirementControls(unittest.TestCase):
    def test_unused_retirement_preserves_best_source_and_retires_characters(self):
        import time
        from long_spans import clean_union
        result=clean_union(('a','b','ab','x'),{'p:1':'abab','p:2':'xxxx','q:1':'ababab'},
                           {'p:1':'p','p:2':'p','q:1':'q'},{'p':'p:1','q':'q:1'},time.monotonic()+2)
        self.assertEqual(result,('ab',))

    def test_unreachable_owner_cannot_be_dropped_in_retirement(self):
        import time
        from long_spans import clean_union
        result=clean_union(('a',),{'p:1':'aa','q:1':'bb'},{'p:1':'p','q:1':'q'},
                           {'p':'p:1','q':'q:1'},time.monotonic()+2)
        self.assertIsNone(result)
