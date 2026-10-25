import json,tempfile,unittest
from pathlib import Path
from .javascript_receipt_adapter import adapt_files
from .python_receipt_adapter import sha
class JavascriptBindings(unittest.TestCase):
 def fixture(self,root,adapted=False):
  source={'id':6,'adapted_sha256':'a'*64,'candidate_sha256':'b'*64,'adapter_sha256':'c'*64,'semantics_sha256':'d'*64,'candidate_bytes':20,'adapter_bytes':30,'complete_bytes':50,'path':'6.js'}
  runtime={'schema':'gamma.pinned-node-runtime.v1','isolation':'existing-unshare-all-plus-one-readonly-executable','sandbox_path':'/runtime/node','node_sha256':'e'*64,'adapter_sha256':'f'*64,'sandbox_sha256':'1'*64,'dependencies':[]}
  c={'schema':'gamma.adapted-paired-qualification.v1'if adapted else'gamma.baseline400.runtime-replay.v1','protected_access':False,'batch_cases':32,'ids':[6],'runtime':runtime,'input_manifest_sha256':'2'*64,'input_hashes':{'6':{'source':'a'*64,'cases':'3'*64,'baseline':'4'*64}}}
  if adapted:c.update(sources=[source],code_sha256='5'*64,harness_sha256='6'*64,oracle_sha256='7'*64,baseline_loader_sha256='8'*64)
  else:c.update(entry='solve',runner_sha256='5'*64,historical_code_sha256={},host_judge_sha256='6'*64,pass_rule='synthetic exact typed effects',integer_transport='synthetic')
  cr=json.dumps(c).encode();(root/'contract.json').write_bytes(cr)
  row={'id':6,'passed':True,'checks_passed':2,'cases':2,'failures':[]}
  if adapted:row['adapted_sha256']=source['adapted_sha256']
  r={'schema':c['schema'],'contract_sha256':sha(cr),'status':'completed','protected_access':False,'qualified':1,'rows':[row]};rr=json.dumps(r).encode();(root/'report.json').write_bytes(rr)
  v={'verified':True,'protected_access':False,'report_sha256':sha(rr),'failed_ids':[]}
  if adapted:v['alternatives']=[source]
  else:v.update(eligible_ids=[6],qualified=1)
  vr=json.dumps(v).encode();(root/'verified.json').write_bytes(vr)
  population={'6':[{'label':'selected','sha256':'a'*64,'evidence':str(root/'report.json')if adapted else'baseline','path':str(root/'6.js')}]}
  return (root/'report.json',root/'verified.json',sha(vr),[6],population,{'6':'selected'})
 def test_baseline_metadata_binding(self):
  with tempfile.TemporaryDirectory()as d:
   r=adapt_files(*self.fixture(Path(d)));self.assertEqual(r['eligible_ids'],[6]);self.assertEqual(r['new_case_reads'],0)
   impl=r['implementations']['development400:6'];self.assertEqual(impl['evidence_class'],'frozen-admitted-typed-effects')
 def test_adapted_complete_bytes_binding(self):
  with tempfile.TemporaryDirectory()as d:
   r=adapt_files(*self.fixture(Path(d),True));self.assertEqual(r['implementations']['development400:6']['source_sha256'],'a'*64)
 def test_anchor_tamper_rejected(self):
  with tempfile.TemporaryDirectory()as d:
   args=list(self.fixture(Path(d)));args[2]='9'*64
   with self.assertRaises(ValueError):adapt_files(*args)
 def test_source_selection_tamper_rejected(self):
  with tempfile.TemporaryDirectory()as d:
   args=list(self.fixture(Path(d)));args[4]['6'][0]['sha256']='9'*64
   with self.assertRaises(ValueError):adapt_files(*args)
 def test_unauthorized_id_rejected(self):
  with tempfile.TemporaryDirectory()as d:
   args=list(self.fixture(Path(d)));args[3]=[]
   with self.assertRaises(ValueError):adapt_files(*args)
 def test_report_mutation_rejected(self):
  with tempfile.TemporaryDirectory()as d:
   args=self.fixture(Path(d));args[0].write_text(args[0].read_text()+' ')
   with self.assertRaises(ValueError):adapt_files(*args)
if __name__=='__main__':unittest.main()
