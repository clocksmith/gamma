import json
from pathlib import Path
import unittest
class Tests(unittest.TestCase):
 def setUp(self):self.r=json.loads(Path(__file__).with_name('RESULT-v3.json').read_text())
 def test_scope(self):
  self.assertEqual(self.r['scope'],dict(variants=44,owners=22,source_bytes=9111))
  self.assertEqual(self.r['syntactically_eligible'],dict(variants=28,owners=16,source_bytes=5684))
 def test_all_controls(self):
  t=self.r['controls'];self.assertEqual(len(t),46);self.assertEqual(len({r['name']for r in t}),46)
  self.assertTrue(all(r['expected']==r['observed']for r in t));self.assertTrue(all(r['alpha_structure_verified']for r in t if r['expected']))
  self.assertTrue({'escaped_strict_not_promoted','genuine_strict_preserved','lexical_selfread','parameter_default_crossref','object_pattern_method_escape'}<={r['name']for r in t})
 def test_rejections_retained(self):
  yes=self.r['eligible_source_identities'];no=self.r['source_level_rejections'];self.assertEqual((len(yes),len(no)),(28,16));self.assertEqual(len({r['key']for r in yes+no}),44)
  self.assertEqual(sum(r['source_bytes']for r in yes+no),9111);self.assertTrue(all(r['reasons']for r in no))
 def test_no_behavior_admission(self):
  self.assertEqual(self.r['additional_sources_admitted'],0);self.assertEqual(self.r['private_transforms'],0);self.assertFalse(self.r['candidate_execution']);self.assertTrue(self.r['cleanup_passed'])
if __name__=='__main__':unittest.main()
