import json,tempfile,pathlib,hashlib,unittest
from run import authorize,claim,classify,declared_scope_matches
class Tests(unittest.TestCase):
 def test_unapproved_and_wrong_mode(self):
  with tempfile.TemporaryDirectory()as td:
   p=pathlib.Path(td)/'permit.json';f=dict(resources={'cpu_seconds':300},runs={'confirmation':dict(cohort={'sha256':'a'*64},queries=28,ledger_path=td+'/ledger')})
   for approved,mode in [(False,'confirmation'),(True,'development-equivalence')]:
    p.write_text(json.dumps(dict(schema='gamma.integrated-run-authorization.v1',approved=approved,freeze_sha256='f'*64,mode=mode,cohort_sha256='a'*64,query_count=28,resources=f['resources'],exclusive_heavy_work_confirmed=True,one_shot=True,ledger_path=td+'/ledger')))
    with self.assertRaises(PermissionError):authorize(f,'f'*64,dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()),'confirmation')
 def test_claim_once(self):
  with tempfile.TemporaryDirectory()as td:
   path=pathlib.Path(td)/'attempt.json';claim(path,'a'*64,'confirmation')
   with self.assertRaises(FileExistsError):claim(path,'a'*64,'confirmation')
 def test_error_is_failure_not_abstention(self):
  q=dict(kind='ambiguous');x=classify(q,dict(status='error'),dict(decision_status='abstain'),None);self.assertTrue(x['error']);self.assertFalse(x['control_abstention'])
 def test_delivery_failure_does_not_hide_control_decision(self):
  q=dict(kind='absent');x=classify(q,dict(status='error'),dict(decision_status='accepted',decision_problem_id='other'),None);self.assertTrue(x['control_decision_accept']);self.assertTrue(x['error'])
 def test_scope_evaluation_only(self):
  q=dict(kind='positive',expected_id='id',declared_contract_scope=dict(official_problem_id=1,official_contract_sha256='a'*64,official_constraints={'n':[1,2]}));c=dict(official_problem_id=1,official_contract_sha256='a'*64,official_preconditions={'n':[1,2]});s={l:dict(implementation=dict(evidence_class='normative-typed-effects',provenance={'public_foundation':{'problem_contract':c}}))for l in ('javascript','python')}
  self.assertTrue(declared_scope_matches(q,'id',s));self.assertFalse(declared_scope_matches(q,'other',s))
if __name__=='__main__':unittest.main()
