"""Public aggregate invariants; no private source opens or candidate execution."""
import json
from pathlib import Path
import unittest

class ResultTests(unittest.TestCase):
    def setUp(self):
        self.e=json.loads(Path(__file__).with_name('RESULT-v1.json').read_text())
        self.r=self.e['report']
    def test_full_scope_and_no_search(self):
        self.assertEqual((self.r['fit_denominator'],self.r['original_variants_retained']), (300,875))
        self.assertFalse(self.r['dictionary_search'])
        self.assertFalse(self.r['candidate_execution'])
        self.assertFalse(self.r['m1_qualified'])
    def test_exact_negative_all_four_arms(self):
        arms=self.r['comparisons']; self.assertEqual(set(arms),{'original_pool','plus_format','plus_role','plus_both'})
        for a in arms.values():
            self.assertEqual(a['metrics'],arms['original_pool']['metrics'])
            self.assertEqual(a['source_choices_sha256'],self.r['original_source_choices_sha256'])
            self.assertEqual(a['changed_owners'],[])
            self.assertEqual((a['metrics']['coverage'],a['metrics']['selections'],a['metrics']['characters'],a['metrics']['package_bytes']),(300,35086,14892,57502))
    def test_storage_accounting(self):
        for arm,a in self.r['comparisons'].items():
            s=self.r['source_storage'][arm]
            self.assertEqual(a['variant_count'],s['registry_source_entries'])
            self.assertEqual(a['source_pool_utf8_bytes'],s['registry_utf8_bytes'])
            self.assertLessEqual(s['unique_content_utf8_bytes'],s['registry_utf8_bytes'])
        self.assertEqual(self.r['introduced_arm_entries'],16)
        self.assertEqual(self.r['comparisons']['plus_both']['variant_count'],891)
    def test_clean_bounded_exit(self):
        c=self.e['cleanup'];self.assertEqual(c['exit_code'],0)
        self.assertTrue(c['no_executing_owned_processes_observed'])
        self.assertFalse(c['remaining_live_owned']);self.assertFalse(c['inspection_unreadable_pids'])
        self.assertFalse(c['wall_timeout']);self.assertEqual(c['wall_budget_seconds'],60)

if __name__=='__main__':unittest.main()
