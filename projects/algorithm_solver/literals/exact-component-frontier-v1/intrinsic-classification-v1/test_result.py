import json,pathlib,unittest
class Controls(unittest.TestCase):
 def setUp(self):self.r=json.loads(pathlib.Path(__file__).with_name('RESULT-v1.json').read_text())
 def test_scope(self):self.assertEqual(self.r['scope'],dict(variants=52,owners=48,source_bytes=8942))
 def test_native_controls(self):self.assertEqual(len(self.r['controls']),14);self.assertTrue(all(x['expected']==x['observed']for x in self.r['controls']))
 def test_math_only(self):
  rows=self.r['numeric_Math_only_source_identities'];self.assertEqual(len(rows),13);self.assertEqual(sum(r['source_bytes']for r in rows),1738);self.assertTrue(all(r['member_write_occurrences']==0 for r in rows))
 def test_extrema_scope(self):
  rows=[r for r in self.r['numeric_Math_only_source_identities']if set(r['numeric_intrinsics'])<={'direct_numeric_Math.max','direct_numeric_Math.min'}]
  self.assertEqual(len(rows),8);self.assertEqual(sum(r['source_bytes']for r in rows),1053)
 def test_no_admission(self):self.assertEqual(self.r['additional_sources_admitted'],0);self.assertFalse(self.r['candidate_execution']);self.assertTrue(self.r['cleanup_passed'])
if __name__=='__main__':unittest.main()
