import unittest

from algsolve.lookup import decide


class GateTests(unittest.TestCase):
    def test_tied_or_missing_competitor_never_matches(self):
        policy={'min_score':0.,'min_margin':0.}
        self.assertEqual(decide([{'key':'a','score':10.}],policy).decision,'abstain')
        self.assertEqual(decide([{'key':'a','score':10.},{'key':'b','score':10.}],policy).decision,'abstain')

    def test_absolute_and_gap_thresholds_both_apply_to_actual_top_scores(self):
        candidates=[{'key':'b','score':3.9},{'key':'a','score':4.2}]
        self.assertEqual(decide(candidates,{'min_score':4.,'min_margin':.2}).key,'a')
        self.assertEqual(decide(candidates,{'min_score':4.,'min_margin':.5}).decision,'abstain')
        self.assertEqual(decide(candidates,{'min_score':5.,'min_margin':.2}).decision,'abstain')

    def test_nonfinite_or_duplicate_evidence_is_rejected(self):
        for rows in ([],[{'key':'a','score':float('inf')}],
                     [{'key':'a','score':2.},{'key':'a','score':1.}]):
            with self.subTest(rows=rows),self.assertRaises(ValueError):
                decide(rows,{'min_score':0.,'min_margin':0.})
        with self.assertRaises(ValueError):
            decide([{'key':'a','score':1.}],{'min_score':0.,'min_margin':-1.})


if __name__=='__main__':unittest.main()
