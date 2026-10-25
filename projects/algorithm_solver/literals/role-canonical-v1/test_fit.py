import importlib.util,unittest
from unittest import mock
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('role_pilot_fit',HERE/'fit.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
class FreshTests(unittest.TestCase):
 def test_distinct_owner_support(self):
  dictionary,metrics=f.fresh_seed({'only':'abababab'},128,set())
  self.assertEqual(dictionary,f.joint.ALPHABET);self.assertEqual(metrics['accepted_merges'],0)
 def test_full_literal_charge_and_reconstruction(self):
  texts={'1':'abcabcabcX','2':'abcabcabcY'}
  dictionary,metrics=f.fresh_seed(texts,128,set(texts.values()))
  self.assertLessEqual(len(dictionary),128);self.assertEqual(len(dictionary),len(set(dictionary)))
  self.assertTrue(metrics['accepted_merges']);self.assertTrue(all(len(t['owners'])>=2 for t in metrics['trace']))
  for source in texts.values():
   sequence=f.compare.scorer.shortest_encode(source,dictionary)
   self.assertEqual(''.join(dictionary[i] for i in sequence),source)
  summary,artifacts=f.compare.measure(texts,dictionary,7)
  self.assertEqual(summary['dictionary_utf8_bytes'],sum(len(s.encode()) for s in dictionary))
  self.assertEqual(summary['whole_solution_entries'],0)
  for pid,packet in artifacts['packets'].items():self.assertEqual(f.compare.independent_decode(artifacts['dictionary'],packet),texts[pid].encode())
 def test_deterministic_whole_body_exclusion(self):
  texts={'1':'abcabcabc','2':'abcabcabd'};banned={'abc','abcabc','abcabcabc'}
  first,_=f.fresh_seed(texts,256,banned);second,_=f.fresh_seed(dict(reversed(list(texts.items()))),256,banned)
  self.assertEqual(first,second);self.assertFalse(set(first)&banned);self.assertTrue(all(len(s)<=64 for s in first))
 def test_seed_budget_failure_is_not_partial_dictionary(self):
  with unittest.mock.patch.object(f,'SEED_CPU_SECONDS',-1):
   with self.assertRaises(TimeoutError):f.fresh_seed({'1':'abcdef','2':'abcdef'},128,set())
if __name__=='__main__':unittest.main()
