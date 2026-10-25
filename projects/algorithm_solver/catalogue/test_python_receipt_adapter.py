import copy
import unittest
from .catalogue import digest
from .python_receipt_adapter import adapt_verified_metadata,encoded,sha

class FrozenPythonReceipt(unittest.TestCase):
 def fixture(self):
  source={'ids':[6,7],'protected_access':False,'sources':{str(i):{'method':'solve','sha256':'a'*64,'semantics_sha256':'b'*64}for i in (6,7)}}
  pins={k:'c'*64 for k in ('algsolve/judge/sandbox.py','algsolve/judge/judge.py','algsolve/judge/functional_semantics.py','algsolve/judge/declared_comparison.py','literals/admission500-v1/qualify_rules.py','literals/python-compact-v1/harness.py')}
  run={'schema':'gamma.python.compact-runtime-replay.v1','protected_access':False,'ids':[6,7],'source_freeze_sha256':sha(encoded(source)),'code_sha256':pins,'python_runtime_sha256':'d'*64,'limits':{'cpu_seconds':3,'wall_seconds':8,'memory_bytes':1024**3,'max_output_bytes':4*1024**2},'batch_cases':32,'input_manifest_sha256':'e'*64,'input_hashes':{str(i):{'cases':'f'*64,'baseline':'1'*64,'source':'2'*64}for i in (6,7)}}
  report={'schema':run['schema'],'contract_sha256':'3'*64,'status':'completed','protected_access':False,'qualified':1,'rows':[{'id':6,'passed':True,'cases':8,'checks_passed':8,'failures':[]},{'id':7,'passed':False,'cases':8,'checks_passed':7,'failures':['synthetic']} ]}
  verified={'schema':'gamma.python.compact-independent-verification.v1','report_sha256':'4'*64,'verified':True,'protected_access':False,'eligible_ids':[6],'failed_ids':[7],'blocked_ids':[],'qualified':1}
  run_raw=encoded(run);report['contract_sha256']=sha(run_raw);report_raw=encoded(report);verified['report_sha256']=sha(report_raw);verified_raw=encoded(verified)
  kw={'report_sha256':sha(report_raw),'run_sha256':sha(run_raw),'verified_sha256':sha(verified_raw),'trusted_verified_sha256':sha(verified_raw),'allowed_ids':[6,7],'verified_raw':verified_raw,'report_raw':report_raw,'run_raw':run_raw}
  return [report,run,source,verified],kw
 def test_existing_bindings_preserved_without_promotion_policy(self):
  args,kw=self.fixture();r=adapt_verified_metadata(*args,**kw);self.assertEqual(r['eligible_ids'],[6]);self.assertEqual(r['failed_ids'],[7]);self.assertEqual(r['new_case_reads'],0)
  impl=r['implementations']['development400:6'];receipt=r['verified_receipts'][impl['receipt_sha256']]
  self.assertEqual(receipt['evidence_class'],'frozen-admitted-typed-effects');self.assertEqual(impl['tests_sha256'],'f'*64)
  desc=r['binding_descriptors']['development400:6'];self.assertEqual(impl['effects_sha256'],digest(desc['effects']))
 def test_external_anchor_required(self):
  args,kw=self.fixture();kw['trusted_verified_sha256']='6'*64
  with self.assertRaises(ValueError):adapt_verified_metadata(*args,**kw)
 def test_compatibility_receipts_excluded(self):
  args,kw=self.fixture();args[3]['schema']='gamma.python.reference-compatibility.verification.v1'
  with self.assertRaises(ValueError):adapt_verified_metadata(*args,**kw)
 def test_source_freeze_drift(self):
  args,kw=self.fixture();args[2]['sources']['6']['sha256']='7'*64
  with self.assertRaises(ValueError):adapt_verified_metadata(*args,**kw)
 def test_unauthorized_problem(self):
  args,kw=self.fixture();kw['allowed_ids']=[6]
  with self.assertRaises(ValueError):adapt_verified_metadata(*args,**kw)
 def test_failed_verifier_row_cannot_be_reused(self):
  args,kw=self.fixture();args[0]['rows'][0]['passed']=False
  with self.assertRaises(ValueError):adapt_verified_metadata(*args,**kw)
 def test_outcome_denominator_duplicate(self):
  args,kw=self.fixture();args[3]['failed_ids']=[6,7]
  with self.assertRaises(ValueError):adapt_verified_metadata(*args,**kw)
 def test_modified_isolation_limit_rejected(self):
  args,kw=self.fixture();args[1]['limits']['cpu_seconds']=5
  with self.assertRaises(ValueError):adapt_verified_metadata(*args,**kw)

if __name__=='__main__':unittest.main()
