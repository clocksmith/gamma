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


class Hard2AndMemoryPolicyTests(unittest.TestCase):
 def test_numeric_policy_exact_lane_ids_and_tolerance(self):
  f={'ids':[1515,1521,1542,1585,1713,2111,2127],
     'effect_policy':'read-only args; fresh mutable returns; no result-to-input aliases',
     'result_policy':'1515 finite numerical absolute tolerance 1e-5 with exact binary-float conversion and analytic oracle uncertainty guard; other results exact typed scalar; local read-only effects'}
  a.check_observation_policy('hard32-wave2-numeric-v2',f)
  for lane in('hard32-wave2-v1','hard32-wave1-v1','hard10-v1','medium32-wave2-v1','medium32-wave2-memory-v1'):
   with self.assertRaises(ValueError):a.check_observation_policy(lane,f)
  for key,value in(('ids',f['ids']+[1788]),('ids',f['ids'][1:]),('result_policy',f['result_policy'].replace('1e-5','1e-3')),('effect_policy','mutation allowed')):
   changed=copy.deepcopy(f);changed[key]=value
   with self.assertRaises(ValueError):a.check_observation_policy('hard32-wave2-numeric-v2',changed)
 def test_numeric_caveat_is_preserved_and_narrow(self):
  base=a.qualification_caveats('hard32-wave1-v1',1515)
  self.assertEqual(a.qualification_caveats('hard32-wave2-numeric-v2',1521),base)
  added=a.qualification_caveats('hard32-wave2-numeric-v2',1515)
  self.assertEqual(added[:len(base)],base)
  self.assertTrue(any('20 analytic' in x for x in added))
  self.assertTrue(any('absolute 1e-5' in x and '1e-35' in x for x in added))
  self.assertTrue(any('arbitrary-input correctness verification is not established' in x for x in added))
 def test_memory_successor_has_fixed_lane_and_unchanged_comparator(self):
  self.assertEqual(a.lane_path('medium32-wave2-memory-v1').name,'public-domain-qualification-medium32-wave2-memory-v1')
  f={'ids':[1567,1573,1630,1653,1743,1817,1877,1887],
     'effect_policy':'read-only args; fresh mutable returns; no result-to-input aliases',
     'result_policy':'typed exact scalars and ordered lists; ID1743 relational unique-vertex adjacent path, either orientation; local read-only/fresh-return effects'}
  a.check_observation_policy('medium32-wave2-memory-v1',f)
  a.check_observation_policy('medium32-wave2-v1',f)
  f['ids']=[1743]
  with self.assertRaises(ValueError):a.check_observation_policy('medium32-wave2-memory-v1',f)

class Medium34PolicyTests(unittest.TestCase):
 def test_exact_populations_and_cross_lane_rejection(self):
  rows=[('medium32-wave3-v1',[1894,1911,1921,1953,1976,2079,2131,2135]),('medium32-wave4-v1',[2170,2186,2256,2433,2587,2597,2602,2860])]
  for lane,ids in rows:
   f={'ids':ids,'effect_policy':'read-only args; fresh mutable returns; no result-to-input aliases','result_policy':('exact typed integer scalar; local read-only effects' if lane=='medium32-wave3-v1' else 'exact typed integer scalar/list; local read-only effects')}
   a.check_observation_policy(lane,f)
   for other,_ in rows:
    if other!=lane:
     with self.assertRaises(ValueError):a.check_observation_policy(other,f)
   for key,value in [('ids',ids[:-1]),('ids',list(reversed(ids))),('result_policy','approximate numeric'),('effect_policy','mutation allowed')]:
    changed=copy.deepcopy(f);changed[key]=value
    with self.assertRaises(ValueError):a.check_observation_policy(lane,changed)
   with self.assertRaises(ValueError):a.check_observation_policy('hard32-wave2-numeric-v2',f)

class Hard3TransportPolicyTests(unittest.TestCase):
 def test_fixed_eight_ids_and_transport_policy(self):
  f={'ids':[2132,2267,2290,2426,2565,2569,2573,2663],'effect_policy':'read-only args; fresh mutable returns; no result-to-input aliases','result_policy':'exact typed scalar/list; ID2569 canonical integer transport tags decoded in both languages; local read-only effects'}
  a.check_observation_policy('hard32-wave3-transport-v2',f)
  for key,value in [('ids',f['ids'][:-1]),('ids',list(reversed(f['ids']))),('result_policy','approximate numeric'),('effect_policy','mutation allowed')]:
   changed=copy.deepcopy(f);changed[key]=value
   with self.assertRaises(ValueError):a.check_observation_policy('hard32-wave3-transport-v2',changed)
  for lane in('hard32-wave3-v1','hard32-wave2-numeric-v2','medium32-wave4-v1'):
   with self.assertRaises(ValueError):a.check_observation_policy(lane,f)
 def test_finite_coverage_caveats(self):
  base=a.qualification_caveats('hard10-v1',2573)
  self.assertEqual(a.qualification_caveats('hard32-wave3-transport-v2',2132),base)
  self.assertTrue(any('reach100' in x and 'up to1000' in x for x in a.qualification_caveats('hard32-wave3-transport-v2',2573)))
  self.assertTrue(any('at most8' in x for x in a.qualification_caveats('hard32-wave3-transport-v2',2663)))
  self.assertTrue(any('both language' in x and 'malformed' in x for x in a.qualification_caveats('hard32-wave3-transport-v2',2569)))

class Hard4PolicyTests(unittest.TestCase):
 def test_actual_2709_oracle_rejects_integer_true(self):
  import importlib.util
  path=a.lane_path('hard32-wave4-v1')/'oracle.py'
  spec=importlib.util.spec_from_file_location('_hard4_boolean_control',path)
  oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
  args=[[2,3,6]]
  for language,kind in(('python','bool'),('javascript','boolean')):
   record={'result':1,'result_type':kind,'args_before':args,'args_after':args,'alias_edges':[]}
   self.assertFalse(oracle.compare(2709,args,True,record,language)[0])
   record['result']=True;self.assertTrue(oracle.compare(2709,args,True,record,language)[0])
  self.assertTrue(any('exact boolean' in x and 'integer1' in x for x in a.qualification_caveats('hard32-wave4-v1',2709)))
 def test_seven_ids_and_no_premium_promotion(self):
  f={'ids':[2709,2781,2953,3003,3041,3093,3130],'effect_policy':'read-only args; fresh mutable returns; no result-to-input aliases','result_policy':'exact typed integer scalar/list; local read-only effects'}
  a.check_observation_policy('hard32-wave4-v1',f)
  for ids in(f['ids']+[2792],f['ids'][:-1],list(reversed(f['ids']))):
   x=copy.deepcopy(f);x['ids']=ids
   with self.assertRaises(ValueError):a.check_observation_policy('hard32-wave4-v1',x)
  with self.assertRaises(ValueError):a.check_observation_policy('hard32-wave3-transport-v2',f)

class ObserverSuccessorPolicyTests(unittest.TestCase):
 def test_only_original_medium2_semantics(self):
  f={'ids':[1567,1573,1630,1653,1743,1817,1877,1887],
     'effect_policy':'read-only args; fresh mutable returns; no result-to-input aliases',
     'result_policy':'typed exact scalars and ordered lists; ID1743 relational unique-vertex adjacent path, either orientation; local read-only/fresh-return effects'}
  a.check_observation_policy('medium32-wave2-observer-v1',f)
  for key,value in [('ids',f['ids'][:-1]),('effect_policy','ignore aliases'),('result_policy','return equality only')]:
   changed=copy.deepcopy(f);changed[key]=value
   with self.assertRaises(ValueError):a.check_observation_policy('medium32-wave2-observer-v1',changed)
  self.assertEqual(a.qualification_caveats('medium32-wave2-observer-v1',1743),a.qualification_caveats('medium32-wave2-v1',1743))


class Request3215AdoptionTests(unittest.TestCase):
 def test_mapping_is_explicit_and_cannot_escape(self):
  self.assertEqual(a.relocated_artifact('/native/bundle/run/a', '/native/bundle', '/local/bundle'), Path('/local/bundle/run/a'))
  for path in ('/native/bundle2/run/a', '/native/bundle/../a', '/native/bundle//a', 'run/a', '/native/bundle'):
   with self.subTest(path=path), self.assertRaises(ValueError):
    a.relocated_artifact(path, '/native/bundle', '/local/bundle')
  for root in ('/local//bundle', '/local/../bundle', 'local'):
   with self.subTest(root=root), self.assertRaises(ValueError):
    a.relocated_artifact('/native/bundle/a', '/native/bundle', root)

 def observation_fixture(self, directory):
  from . import imported_qualification as q
  case={'args':[[1],[2],[3]], 'expected':1, 'compare':'return'}
  record={'i':0,'result':1,'result_type':'int','args_before':case['args'],
          'args_after':case['args'],'alias_edges':[]}
  job={'id':3215,'language':'python','source_sha256':'a'*64,'tests_raw_sha256':'b'*64}
  call={'stem':'3215-python-0','offset':0,'count':1,'exit_code':0,'timed_out':False,'output_limit_exceeded':False}
  row={'id':3215,'language':'python','source_sha256':job['source_sha256'],'cases':1,
       'calls':[call],'failures':[],'passed':True}
  def write(records):
   stdout=b''.join(q.encoded(x) for x in records)
   (directory/'3215-python-0.stdout').write_bytes(stdout)
   (directory/'3215-python-0.stderr').write_bytes(b'')
   call['stdout_sha256']=a.sha(stdout);call['stderr_sha256']=a.sha(b'')
  write([record,{'done':1}])
  return job,case,record,row,write

 def test_comparator_replays_values_types_effects_and_aliases_not_pass_flag(self):
  # Synthetic unit records exercise the comparator only; they are not an
  # adoption plan or evidence for the real source qualification.
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);job,case,record,row,write=self.observation_fixture(root)
   self.assertTrue(a.request3215_observations({'rows':[row]},[job],[case],root)[0]['passed'])
   for key,value in [('result',0),('result',True),('result_type','number'),
                     ('args_after',[[1],[2],[4]]),('alias_edges',[['result','args[0]']])]:
    with self.subTest(key=key,value=value):
     forged=copy.deepcopy(record);forged[key]=value;write([forged,{'done':1}])
     with self.assertRaisesRegex(ValueError,'replay disagrees'):
      a.request3215_observations({'rows':[row]},[job],[case],root)

 def test_observation_incompleteness_order_and_resource_failures_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);job,case,record,row,write=self.observation_fixture(root)
   for records in ([record], [record,record,{'done':1}], [{**record,'i':1},{'done':1}]):
    write(records)
    with self.assertRaises(ValueError):a.request3215_observations({'rows':[row]},[job],[case],root)
   write([record,{'done':1}])
   for key,value in [('offset',1),('count',2),('stem','../elsewhere'),('timed_out',True),('exit_code',1),('output_limit_exceeded',True)]:
    changed=copy.deepcopy(row);changed['calls'][0][key]=value
    with self.subTest(key=key),self.assertRaises(ValueError):
     a.request3215_observations({'rows':[changed]},[job],[case],root)
   for rows in ([],[row,row]):
    with self.assertRaises(ValueError):a.request3215_observations({'rows':rows},[job],[case],root)

 def pre_payload_fixture(self):
  from . import imported_qualification as q
  from . import request_qualification as request
  from . import verify_imported_qualification as verifier
  native='/native/bundle';local='/local/bundle';fr=native+'/run-3215/freeze';repo=a.HERE.parents[2]
  current=q.code_pins()
  code={native+'/code/'+str(Path(p).relative_to(repo)):h for p,h in current.items()}
  generator=native+'/code/'+str(Path(request.__file__).relative_to(repo))
  jobs=[]
  for language,suffix in [('javascript','js'),('python','py')]:
   jobs.append({'id':3215,'language':language,'source':f'sources/3215.{suffix}',
    'source_sha256':request.SOURCE_SHA256[language],'original_source':native+f'/inputs/sources/{language}/3215.{suffix}',
    'tests':'tests/3215.json','tests_raw_sha256':request.CASES_SHA256,'tests_canonical_sha256':'a'*64,
    'case_count':request.CASE_COUNT,'statement':{'path':fr+'/statement.md','sha256':request.STATEMENT_SHA256},
    'domain_validator':a.REQUEST3215_LANE,'comparison_policy':'exact',
    'source_interface':'commonjs-object-solve-v1' if language=='javascript' else 'global-solve-v1'})
  runtime={p:{'resolved':p,'sha256':'a'*64} for p in ('/usr/bin/node','/usr/bin/python3','/usr/bin/bwrap','/usr/bin/prlimit')}
  raws={k:k.encode() for k in ('freeze','report','verification','review','universe','catalogue','receipts','qualification_service','qualification_boundary_gate')}
  freeze={'schema':'gamma.imported-independent-execution.v1','selected_problem_ids':[3215],
   'jobs':jobs,'pending':[],'automatic_promotion':False,'protected_access':False,'limits':q.LIMITS,
   'max_packet_bytes':q.MAX_PACKET,'code':code,'additional_code':{generator:code[generator]},
   'runtime':runtime,'service_config_sha256':a.sha(raws['qualification_service'])}
  report={'schema':'gamma.imported-independent-report.v1','freeze':fr,'freeze_sha256':a.sha(raws['freeze']),
   'status':'completed','new_qualifications':0}
  review={'independent_review':True,'reviewed':list(a.REQUEST3215_REVIEW),
   **{k+'_sha256':a.sha(raws[k]) for k in ('freeze','report','verification')},
   'source_sha256':request.SOURCE_SHA256,'native_runtime_sha256':digest(runtime)}
  gate={'schema':'gamma.boundary-gate-config.v1','artifact_paths':{},'trusted_hashes':{'universe':a.sha(raws['universe'])}}
  service={'schema':'gamma.known-spec-service.v2','source_access':{'boundary_gate':{'sha256':a.sha(raws['qualification_boundary_gate'])}},
   **{name:{'sha256':a.sha(raws[key])} for name,key in [('universe','universe'),('catalogue','catalogue'),('verified_receipts','receipts')]}}
  values={'freeze':freeze,'report':report,'verification':{},'review':review,'boundary_gate':gate,
   'qualification_boundary_gate':copy.deepcopy(gate),'qualification_service':service,'authority_review':{}}
  plan={'native_bundle_root':native,'artifact_root':local,
   'freeze':{'path':local+'/run-3215/freeze/contract.json'},'report':{'path':local+'/run-3215/observations/report.json'},
   'verification':{'path':local+'/run-3215/independent-verification.json'}}
  code_payloads={str(Path(local)/'code'/Path(p).relative_to(repo)):Path(p).read_bytes() for p in [*current,verifier.__file__]}
  return plan,values,raws,code_payloads

 def test_denied_gate_never_reads_candidate_statement_or_cases(self):
  plan,values,raws,code=self.pre_payload_fixture()
  with patch.object(a,'bounded_regular_read',side_effect=lambda p,**kw:code[str(p)]) as reads, \
       patch.object(a.boundary_policy,'authorize_before_open',side_effect=PermissionError('denied')):
   with self.assertRaises(PermissionError):a.replay_request3215(plan,values,raws)
  self.assertTrue(reads.call_args_list)
  self.assertTrue(all('/code/' in str(call.args[0]) for call in reads.call_args_list))

 def test_missing_authority_never_reads_candidate_statement_or_cases(self):
  plan,values,raws,code=self.pre_payload_fixture()
  with patch.object(a,'bounded_regular_read',side_effect=lambda p,**kw:code[str(p)]) as reads, \
       patch.object(a.boundary_policy,'authorize_before_open'):
   with self.assertRaisesRegex(ValueError,'adoption fields'):a.replay_request3215(plan,values,raws)
  self.assertTrue(all('/code/' in str(call.args[0]) for call in reads.call_args_list))

 def test_interface_and_population_fail_before_payload_reads(self):
  plan,values,raws,_=self.pre_payload_fixture()
  for key,value in [('source_interface','global-solve-v1'),('id',3216),('source','../3215.js')]:
   changed=copy.deepcopy(values);changed['freeze']['jobs'][0][key]=value
   with self.subTest(key=key),patch.object(a,'bounded_regular_read',side_effect=AssertionError('must not read')):
    with self.assertRaises(ValueError):a.replay_request3215(plan,changed,raws)

 def test_review_and_runtime_changes_fail_before_payload_reads(self):
  plan,values,raws,code=self.pre_payload_fixture()
  for key,value in [('independent_review',False),('source_sha256',{}),('reviewed',['boundary_policy']),('native_runtime_sha256','f'*64)]:
   changed=copy.deepcopy(values);changed['review'][key]=value
   with self.subTest(key=key),patch.object(a,'bounded_regular_read',side_effect=lambda p,**kw:code[str(p)]) as reads:
    with self.assertRaisesRegex(ValueError,'review required'):a.replay_request3215(plan,changed,raws)
   self.assertTrue(all('/code/' in str(call.args[0]) for call in reads.call_args_list))

 def test_fixed_input_gate_uses_existing_request_owner_without_execution(self):
  from . import request_qualification as request
  contract={'reviewed_statement_contract':{'problem_id':'leetcode:3215','numeric_problem_id':3215},
   'input_validator':{'lane':a.REQUEST3215_LANE,'module_sha256':a.sha(Path(request.__file__).read_bytes()),
    'numeric_problem_id':3215,'entrypoint':'validate','required_before_candidate_execution':True}}
  impl={'status':'qualified','evidence_class':'normative-typed-effects','problem_contract_sha256':digest(contract),
   'provenance':{'public_batch':{'problem_contract':contract}}}
  self.assertEqual(a.validate_batch_inputs(impl,[[0],[1],[2]])['candidate_executed'],False)
  for args in ([[True],[0],[0]],[[],[0],[0]],[[10**9+1],[0],[0]]):
   with self.assertRaises(ValueError):a.validate_batch_inputs(impl,args)
  contract['input_validator']['numeric_problem_id']=3216
  impl['problem_contract_sha256']=digest(contract)
  with self.assertRaises(ValueError):a.validate_batch_inputs(impl,[[0],[1],[2]])

if __name__=='__main__':unittest.main()
