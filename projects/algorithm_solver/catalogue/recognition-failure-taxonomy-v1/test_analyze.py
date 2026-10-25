import unittest
from analyze import observations
class Tests(unittest.TestCase):
 def obs(self,kind='positive',reason='empirical_confidence_threshold',status='abstain'):
  return observations([('leetcode:2',.7),('leetcode:1',.65)],dict(kind=kind,expected_id='leetcode:1'),dict(reason=reason,status=status),dict(min_cosine=.75,min_margin=.12))
 def test_distractor(self):self.assertEqual(self.obs()['expected_ranks'],{'leetcode:1':2});self.assertIn('distractor_top_identity',self.obs()['mechanical_observations'])
 def test_unknown(self):self.assertEqual(self.obs()['embedding_representation_cause'],'UNKNOWN')
 def test_availability(self):self.assertIn('unavailable_qualified_top_artifact',self.obs(reason='top_identity_not_qualified')['mechanical_observations'])
 def test_control(self):self.assertEqual(self.obs(kind='control',reason=None,status='accepted')['mechanical_observations'],['control_acceptance'])
if __name__=='__main__':unittest.main()
