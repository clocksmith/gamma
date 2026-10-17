import json
import unittest
from algsolve.rerank import scores_from_output

class RerankTests(unittest.TestCase):
    def output(self, rows):
        return '[progress]\n' + json.dumps({'ok':True,'result':{'output':{'query':'q','ranking':rows}}},indent=2)
    def test_rank_order_is_restored_to_candidate_order(self):
        rows=[{'index':1,'document':'b','score':4.0},{'index':0,'document':'a','score':-2.0}]
        self.assertEqual(scores_from_output(self.output(rows),'q',['a','b']),[-2.,4.])
    def test_duplicate_mismatched_nonfinite_and_failed_output_are_rejected(self):
        valid={'index':0,'document':'a','score':1}
        for rows in [[valid,valid], [dict(valid,document='wrong')], [dict(valid,score=float('nan'))]]:
            with self.assertRaises(ValueError): scores_from_output(self.output(rows),'q',['a'])
        with self.assertRaises(ValueError): scores_from_output('{"ok":false,"result":{}}','q',['a'])
        with self.assertRaises(ValueError): scores_from_output(self.output([valid]),'different',['a'])

if __name__ == '__main__': unittest.main()
