import importlib.util,json,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('direct_supply_tests_module',HERE/'supply.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
class SupplyTests(unittest.TestCase):
 def test_output_scope_and_accounting(self):
  sources={'1':'class Solution{}','2':'unsupported'}
  rows={'1':{'ok':True,'ast_verified':True,'helpers_verbatim':True,'strict_directive_added':True,'candidate_executions':0,'source':'function solve(){}','source_bytes':16,'lowered_bytes':18},'2':{'ok':False,'error':'unsupported'}}
  rows['1']['source_bytes']=len(sources['1']);rows['1']['lowered_bytes']=len(rows['1']['source'])
  def invoke(*args,**kwargs):return SimpleNamespace(stdout=json.dumps(rows).encode())
  with patch.object(s.subprocess,'run',invoke):
   self.assertEqual(s.generate(sources,Path('/synthetic-node')),rows)
   rows['1']['candidate_executions']=1
   with self.assertRaises(ValueError):s.generate(sources,Path('/synthetic-node'))
   rows['1']['candidate_executions']=0;del rows['2']
   with self.assertRaises(ValueError):s.generate(sources,Path('/synthetic-node'))
 def test_identity_pins_cover_generator_and_judge(self):
  names=s.pins()
  for name in ['direct-entry-v1/lower.mjs','direct-entry-v1/qualify.py','direct-entry-v1/verify.py','role-canonical-v1/parser.mjs']:
   self.assertIn(name,names);self.assertEqual(len(names[name]),64)
if __name__=='__main__':unittest.main()
