import unittest
from evaluate import extraction_score,veto
class Tests(unittest.TestCase):
 def test_zero(self):self.assertIsNone(extraction_score([dict(facts={})],[dict(facts={'x':'y'})])['reviewed_precision'])
 def test_unknown(self):self.assertEqual(extraction_score([dict(facts={'x':'y'})],[dict(facts={},unknown_facets=['x'],annotation_complete_for_supported_facets=True)])['unreviewed'],1)
 def test_precision(self):
  s=extraction_score([dict(facts={'x':'y','z':'bad'})],[dict(facts={'x':'y','z':'good'},annotation_complete_for_supported_facets=True)]);self.assertEqual(s['reviewed_precision'],.5);self.assertEqual(s['gold_recall'],.5)
 def test_veto_only(self):
  b=dict(query_id='q',status='abstain',reason='threshold',problem_id=None);self.assertEqual(veto(b,dict(conflicts=[]),dict(contradictions=['x'])),b)
 def test_accept_veto(self):self.assertEqual(veto(dict(query_id='q',status='accepted',reason=None,problem_id='id'),dict(conflicts=[]),dict(contradictions=['x']))['status'],'abstain')
if __name__=='__main__':unittest.main()
