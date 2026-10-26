"""Public aggregate consistency checks; no private source/case or execution."""
import json,pathlib,unittest
class ResultTests(unittest.TestCase):
 def setUp(self):self.r=json.loads(pathlib.Path(__file__).with_name('RESULT-v1.json').read_text())
 def test_full_arms(self):
  rows=self.r['outcomes'];self.assertEqual(len(rows),24);self.assertTrue(all(x['passed']for x in rows));self.assertEqual(sum(x['cases']for x in rows),2406)
 def test_identical_case_denominator(self):
  for arm in('original','format','role'):self.assertEqual(sum(x['cases']for x in self.r['outcomes']if x['arm']==arm),802)
 def test_limits_match(self):
  self.assertEqual(self.r['aggregate_wall_seconds'],87*8+84);self.assertEqual(self.r['unchanged_per_child_limits'],dict(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=4*1024**2))
 def test_no_extra_batch(self):
  self.assertEqual(self.r['launch_history']['actual_batches_executed'],1);self.assertEqual(self.r['calls'],87)
 def test_no_adoption_or_refit(self):
  self.assertFalse(self.r['canonical_adoption']);self.assertFalse(self.r['dictionary_refit']);self.assertEqual(self.r['M1'],'UNMET')
if __name__=='__main__':unittest.main()
