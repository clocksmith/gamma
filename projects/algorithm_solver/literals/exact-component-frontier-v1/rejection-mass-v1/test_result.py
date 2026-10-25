"""Public aggregate consistency controls; no source or case access."""
import json,pathlib,unittest
class ResultTests(unittest.TestCase):
 def setUp(self):self.r=json.loads(pathlib.Path(__file__).with_name('RESULT-v1.json').read_text())
 def test_disjoint_partition(self):
  self.assertEqual(sum(x['variants']for x in self.r['disjoint_reason_combinations']),875)
  self.assertEqual(sum(x['source_bytes']for x in self.r['disjoint_reason_combinations']),379939)
 def test_nested_bounds(self):
  a=self.r['call_member_global_only_rejected_upper_bound'];b=self.r['call_member_global_only_and_current_index_proof_upper_bound']
  for k in ('variants','owners','source_bytes'):self.assertLessEqual(b[k],a[k])
 def test_sizes_and_scope(self):
  p=self.r['source_size_provenance'];self.assertEqual(p['freeze_bound_lengths']+p['metadata_stat_only_lengths'],875);self.assertEqual(p['source_payload_opens'],0)
  self.assertEqual(self.r['existing_research_candidates'],dict(variants=6,owners=6,source_bytes=582))
 def test_not_a_partition_of_families(self):
  self.assertGreater(sum(r['source_bytes']for r in self.r['overlapping_rejection_families']),379939)
if __name__=='__main__':unittest.main()
