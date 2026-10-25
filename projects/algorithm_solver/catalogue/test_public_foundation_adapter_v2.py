import copy,hashlib,unittest
from .catalogue import digest,validate
from .public_foundation_adapter_v2 import FOUNDATION,validate_foundation_inputs,replace_canonicals
from .test_catalogue import Catalogue

class PublicFoundationAdoptionV2(unittest.TestCase):
 def artifact(self,pid=120):
  contract={'official_problem_id':pid,'input_validator':{'entrypoint':'validate','numeric_problem_id':pid,'module_sha256':hashlib.sha256((FOUNDATION/'oracle.py').read_bytes()).hexdigest()}}
  return {'status':'qualified','evidence_class':'normative-typed-effects','problem_contract_sha256':digest(contract),'provenance':{'public_foundation':{'problem_contract':contract}}}
 def test_input_predicate_accepts_only_official_domain(self):
  self.assertTrue(validate_foundation_inputs(self.artifact(),[[[1],[2,3]]])['accepted'])
  for args in ([[[1],[2]]],[[]],[[[True]]]):
   with self.assertRaises(ValueError):validate_foundation_inputs(self.artifact(),args)
 def test_other_domain_edges(self):
  for pid,args in [(988,[{'__tree_node__':[0,None,None,1]}]),(1514,[2,[[0,1]],[True],0,1]),(2192,[2,[[0,1],[1,0]]]),(1106,['!(t,f)'])]:
   with self.assertRaises(ValueError):validate_foundation_inputs(self.artifact(pid),args)
 def test_full_validator_not_partial_oracle(self):
  self.assertTrue(validate_foundation_inputs(self.artifact(955),[['ab'*50,'ba'*50]])['accepted'])
 def test_contract_mutation_and_validator_drift_fail(self):
  a=self.artifact();a['provenance']['public_foundation']['problem_contract']['official_problem_id']=931
  with self.assertRaises(ValueError):validate_foundation_inputs(a,[[1,1]])
  a=self.artifact();c=a['provenance']['public_foundation']['problem_contract'];c['input_validator']['module_sha256']='a'*64;a['problem_contract_sha256']=digest(c)
  with self.assertRaises(ValueError):validate_foundation_inputs(a,[[1]])
 def test_admitted_or_probe_not_silently_normative(self):
  for kind in ('frozen-admitted-typed-effects','reference-compatibility'):
   a=self.artifact();a['evidence_class']=kind
   with self.assertRaises(ValueError):validate_foundation_inputs(a,[[1]])
 def replacement_fixture(self):
  u,c,r=Catalogue().fixture();c['schema']='gamma.dual-language-catalogue.v2';c['evidence_policy']={'schema':'gamma.catalogue-evidence-policy.v1','allowed_classes':['normative-typed-effects'],'scope_rule':'exact-bound-contract-only'}
  updated={}
  for row in c['problems']:
   for impl in row['implementations'].values():
    receipt=copy.deepcopy(r[impl['receipt_sha256']]);impl.update(evidence_class='normative-typed-effects',contract_scope='synthetic',caveats=[]);receipt.update(contract_scope='synthetic',caveats=[]);rid=digest(receipt);impl['receipt_sha256']=rid;updated[rid]=receipt
  r=updated;old=c['problems'][0]['implementations']['javascript'];new=copy.deepcopy(old)
  new['provenance']={'previous_canonical':{'implementation_sha256':digest(old),'receipt_sha256':old['receipt_sha256']}}
  receipt=copy.deepcopy(r[old['receipt_sha256']]);receipt['provenance_sha256']=digest(new['provenance']);rid=digest(receipt);new['receipt_sha256']=rid
  return u,c,r,{('a','javascript'):new},{rid:receipt}
 def test_copy_preserves_all_old_receipts_and_population(self):
  u,c,r,new,nr=self.replacement_fixture();old=copy.deepcopy((u,c,r));result,receipts,summary=replace_canonicals(u,c,r,new,nr)
  self.assertEqual((u,c,r),old);self.assertEqual(summary['eligible_problems'],2)
  for key,value in r.items():self.assertEqual(receipts[key],value)
  self.assertEqual(set(result['evidence_policy']['allowed_classes']),{'normative-typed-effects','frozen-admitted-typed-effects'})
 def test_wrong_predecessor_binding_rejected(self):
  args=list(self.replacement_fixture());args[3][('a','javascript')]['provenance']['previous_canonical']['implementation_sha256']='f'*64
  with self.assertRaises(ValueError):replace_canonicals(*args)
 def test_js_source_substitution_rejected(self):
  args=list(self.replacement_fixture());args[3][('a','javascript')]['source_sha256']='f'*64
  with self.assertRaises(ValueError):replace_canonicals(*args)

if __name__=='__main__':unittest.main()
