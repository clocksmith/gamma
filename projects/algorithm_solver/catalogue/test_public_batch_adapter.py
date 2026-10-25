import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from . import public_batch_adapter as a
from .catalogue import digest
from . import test_public_foundation_adapter_v2 as prior_tests

class PublicBatchTests(unittest.TestCase):
 def authority(self):
  witness={'identity':'https://leetcode.com/problems/example/','sha256':'a'*64,'role':'official-statement'}
  contract={'problem_id':'leetcode:3894','numeric_problem_id':3894,'statement_sha256':'a'*64,
   'source_identity':{'url':witness['identity']},'domain':{'timer':[0,1000]},
   'interface':{'entrypoint':'solve','arguments':'ordered-positional','parameters':['timer']},
   'result':'string','complexity':'O(1)','local_effects':{'mutation':'none'},'authority_evidence_sha256':['a'*64]}
  return {'schema':'gamma.public-batch-authority-review.v1','lane':'easy16-v1','freeze_sha256':'b'*64,
   'review_sha256':'c'*64,'reviewer':'independent test reviewer','review_scope':'independent-statement-identity-domain-interface-effects-complexity',
   'contracts':{'leetcode:3894':contract},'evidence_artifacts':[witness],'source_publication_authorized':False}
 def check(self,x):return a.check_authority(x,lane='easy16-v1',freeze_sha256='b'*64,review_sha256='c'*64,ids=[3894])
 def test_authority_is_exact_review_binding(self):
  self.assertEqual(set(self.check(self.authority())),{'leetcode:3894'})
  for field,value in [('freeze_sha256','d'*64),('reviewer',''),('source_publication_authorized',True)]:
   x=self.authority();x[field]=value
   with self.assertRaises(ValueError):self.check(x)
 def test_claim_boolean_not_authority(self):
  with self.assertRaises(ValueError):self.check({'official':True})
 def test_no_missing_or_extra_ids(self):
  x=self.authority();x['contracts']['leetcode:1']=x['contracts']['leetcode:3894']
  with self.assertRaises(ValueError):self.check(x)
 def test_no_unanchored_clause_evidence(self):
  x=self.authority();x['contracts']['leetcode:3894']['authority_evidence_sha256']=['f'*64]
  with self.assertRaises(ValueError):self.check(x)
 def test_no_caller_import_path(self):
  for lane in ('../../evil', '/tmp/evil', [], None):
   with self.assertRaises(ValueError):a.lane_path(lane)
 def test_replay_checks_code_before_import(self):
  with patch.object(a,'_module',side_effect=AssertionError('must not import')):
   with self.assertRaises(ValueError):a.replay('easy16-v1',{'code_sha256':{}},Path('/tmp/no-report'))
 def test_pins_strict_and_bounded(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)/'x.json';p.write_text('{"a":1,"a":2}')
   with self.assertRaises(ValueError):a.pinned({'path':str(p),'sha256':a.sha(p.read_bytes())})
   with self.assertRaises(ValueError):a.pinned({'path':str(p),'sha256':'0'*64})
 def test_replacement_preserves_and_allows_new_js_bytes(self):
  u,c,r,new,nr=prior_tests.PublicFoundationAdoptionV2().replacement_fixture()
  old=copy.deepcopy((u,c,r)); impl=new[('a','javascript')];impl['source_sha256']='f'*64
  receipt=next(iter(nr.values()));receipt['source_sha256']='f'*64;rid=digest(receipt);impl['receipt_sha256']=rid;nr={rid:receipt}
  out,retained,summary=a.replace_canonicals(u,c,r,new,nr)
  self.assertEqual((u,c,r),old);self.assertEqual(summary['eligible_problems'],2)
  self.assertEqual(out['problems'][0]['implementations']['javascript']['source_sha256'],'f'*64)
  for key,value in r.items():self.assertEqual(retained[key],value)
 def test_bad_predecessor_and_receipt_denied(self):
  args=list(prior_tests.PublicFoundationAdoptionV2().replacement_fixture());args[3][('a','javascript')]['provenance']['previous_canonical']['implementation_sha256']='f'*64
  with self.assertRaises(ValueError):a.replace_canonicals(*args)
  args=list(prior_tests.PublicFoundationAdoptionV2().replacement_fixture());args[4]={'0'*64:next(iter(args[4].values()))}
  with self.assertRaises(ValueError):a.replace_canonicals(*args)
 def test_input_validator_no_promotion(self):
  directory=a.lane_path('easy16-v1');contract={'reviewed_statement_contract':{'numeric_problem_id':3894,'problem_id':'leetcode:3894'},
   'input_validator':{'lane':'easy16-v1','module_sha256':a.sha((directory/'oracle.py').read_bytes()),'numeric_problem_id':3894,'entrypoint':'validate','required_before_candidate_execution':True}}
  impl={'status':'qualified','evidence_class':'normative-typed-effects','problem_contract_sha256':digest(contract),'provenance':{'public_batch':{'problem_contract':contract}}}
  self.assertTrue(a.validate_batch_inputs(impl,[0])['accepted'])
  for args in ([True],[-1],[1001]):
   with self.assertRaises(ValueError):a.validate_batch_inputs(impl,args)
  impl['evidence_class']='frozen-admitted-typed-effects'
  with self.assertRaises(ValueError):a.validate_batch_inputs(impl,[0])

 def test_bounded_reader_rejects_links_fifo_and_oversize(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);regular=root/'regular';regular.write_bytes(b'abc')
   self.assertEqual(a.bounded_regular_read(regular,maximum_bytes=3),b'abc')
   link=root/'link';link.symlink_to(regular)
   with self.assertRaises(OSError):a.bounded_regular_read(link)
   directory=root/'sub';directory.mkdir();(directory/'x').write_bytes(b'abc')
   alias=root/'alias';alias.symlink_to(directory,target_is_directory=True)
   with self.assertRaises(OSError):a.bounded_regular_read(alias/'x')
   fifo=root/'fifo';os.mkfifo(fifo)
   with self.assertRaises(ValueError):a.bounded_regular_read(fifo)
   with self.assertRaises(ValueError):a.bounded_regular_read(regular,maximum_bytes=2)
   with self.assertRaises(ValueError):a.bounded_regular_read(directory)
 def test_actual_reopen_after_precheck_is_guarded(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);source=root/'1.py';source.write_bytes(b'pass')
   self.assertEqual(a.bounded_regular_read(source),b'pass')
   guarded=a.guarded_path_class([source]);target=root/'other';target.write_bytes(b'pass')
   source.unlink();source.symlink_to(target)
   with self.assertRaises(OSError):guarded(source).read_bytes()
 def test_replay_path_source_and_output_caps(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);source=root/'1.py';source.write_bytes(b'x'*(1_048_576+1))
   guarded=a.guarded_path_class([source])
   with self.assertRaises(ValueError):guarded(source).read_bytes()
   output=root/'x.stdout';output.write_bytes(b'x'*(4*1024**2+1))
   with self.assertRaises(ValueError):guarded(output).read_bytes()
 def test_authority_pin_rejects_nonregular(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);fifo=root/'authority.json';os.mkfifo(fifo)
   with self.assertRaises(ValueError):a.pinned({'path':str(fifo),'sha256':'a'*64})


class ObservationPolicyTests(unittest.TestCase):
 def test_property_comparator_is_exact_lane_scoped(self):
  f={'ids':[1317,1351,1470,1556,1598,1716,1800,1854],'effect_policy':'read-only args; fresh mutable returns; no result-to-input aliases','result_policy':'exact typed ordered structures except1317 any valid positive no-zero pair'}
  a.check_observation_policy('easy32-wave1-v1',f)
  for lane in ('easy16-v1','hard32-wave1-v1','easy32-wave2-v1'):
   with self.assertRaises(ValueError):a.check_observation_policy(lane,f)
  f['ids']=[1317]
  with self.assertRaises(ValueError):a.check_observation_policy('easy32-wave1-v1',f)
 def test_historical_equality_and_effects_unchanged(self):
  f={'effect_policy':'read-only args; fresh mutable returns; no result-to-input aliases','result_policy':'exact typed ordered structures'}
  a.check_observation_policy('hard10-v1',f)
  f['effect_policy']='mutation permitted'
  with self.assertRaises(ValueError):a.check_observation_policy('hard10-v1',f)


class MediumPolicyTests(unittest.TestCase):
 def test_multiset_and_path_are_not_general_order_relaxations(self):
  cases=[('medium32-wave1-v1',[1248,1319,1338,1400,1466,1471,1482,1540],'typed exact scalars; ID1471 duplicate-sensitive multiset, arbitrary order; local read-only/fresh-return effects'),('medium32-wave2-v1',[1567,1573,1630,1653,1743,1817,1877,1887],'typed exact scalars and ordered lists; ID1743 relational unique-vertex adjacent path, either orientation; local read-only/fresh-return effects')]
  for lane,ids,policy in cases:
   f={'ids':ids,'effect_policy':'read-only args; fresh mutable returns; no result-to-input aliases','result_policy':policy}
   a.check_observation_policy(lane,f)
   for other in ('easy32-wave1-v1','hard32-wave1-v1'):
    with self.assertRaises(ValueError):a.check_observation_policy(other,f)
   f['ids']=ids[:-1]
   with self.assertRaises(ValueError):a.check_observation_policy(lane,f)

if __name__=='__main__':unittest.main()
