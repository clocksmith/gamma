import importlib.util,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('incremental_supply_tests_module',HERE/'prepare.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class DedupTests(unittest.TestCase):
 def test_hash_dedup_is_per_problem(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a.js';p.write_text('function solve(a){return a;}');rows={};owners={};proof={'report':'synthetic','report_sha256':'0'*64}
   self.assertTrue(m.add_variant(rows,owners,1,p,'role',proof))
   self.assertFalse(m.add_variant(rows,owners,1,p,'format',proof))
   self.assertTrue(m.add_variant(rows,owners,2,p,'role',proof))
   self.assertEqual(len(rows),2);self.assertEqual(set(owners.values()),{'1','2'})
if __name__=='__main__':unittest.main()
