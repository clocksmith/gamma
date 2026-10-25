"""Preserve existing frozen Python source qualification as catalogue bindings.

No new oracle or semantic requirement is invented. A caller supplies the SHA256
of an already independently recomputed verification result as an external trust
anchor. This adapter checks its metadata chain, not cases/observations again.
It never claims universal-domain proof, recognition or current serving readiness.
"""
import hashlib
import json
from pathlib import Path
from .catalogue import digest, hash_value

SCHEMAS = {
 'gamma.python.compact-runtime-replay.v1':'gamma.python.compact-independent-verification.v1',
 'gamma.python.devval-runtime-replay.v1':'gamma.python.devval-independent-verification.v1',
}
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def encoded(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def required_hash(value):
 if not hash_value(value):raise ValueError('invalid frozen evidence hash')
 return value

def adapt_verified_metadata(report, run, source_freeze, verified, *, report_sha256,
                            run_sha256, verified_sha256, trusted_verified_sha256,
                            allowed_ids, verified_raw, report_raw, run_raw, identity_map=None):
 """Pure metadata bridge. Trust anchor comes from a prior independent verifier."""
 if not hash_value(trusted_verified_sha256) or verified_sha256!=trusted_verified_sha256:
  raise ValueError('external independent-verification trust anchor mismatch')
 for raw,value,expected in ((verified_raw,verified,verified_sha256),(report_raw,report,report_sha256),(run_raw,run,run_sha256)):
  if sha(raw)!=expected or json.loads(raw)!=value:raise ValueError('parsed metadata not bound to exact original bytes')
 schema=run.get('schema')
 if schema not in SCHEMAS or report.get('schema')!=schema or verified.get('schema')!=SCHEMAS[schema]:
  raise ValueError('unsupported or compatibility-only receipt schema')
 if report.get('contract_sha256')!=run_sha256 or verified.get('report_sha256')!=report_sha256:
  raise ValueError('report/contract/verifier chain mismatch')
 if verified.get('verified')is not True or report.get('status')!='completed':raise ValueError('incomplete independent verification')
 if any(x.get('protected_access')is not False for x in (report,run,source_freeze,verified)):
  raise ValueError('protected qualification scope mismatch')
 if run.get('source_freeze_sha256')!=sha(encoded(source_freeze)) or run.get('ids')!=source_freeze.get('ids'):
  raise ValueError('source freeze chain mismatch')
 ids=run['ids'];allowed=set(allowed_ids)
 if len(ids)!=len(set(ids)) or not set(ids)<=allowed:raise ValueError('unauthorized qualification IDs')
 if set(source_freeze.get('sources',{}))!={str(pid)for pid in ids}:raise ValueError('source inventory denominator mismatch')
 if run.get('limits')!={'cpu_seconds':3,'wall_seconds':8,'memory_bytes':1024**3,'max_output_bytes':4*1024**2} or run.get('batch_cases')!=32:raise ValueError('original admitted isolation limits differ')
 if [r['id']for r in report['rows']]!=ids:raise ValueError('execution denominator changed')
 eligible=verified.get('eligible_ids',[])
 if len(eligible)!=len(set(eligible)) or not set(eligible)<=set(ids):raise ValueError('invalid verified source subset')
 partitions=[eligible,verified.get('failed_ids',[]),verified.get('blocked_ids',[])]
 if sum(map(len,partitions))!=len(ids) or any(len(x)!=len(set(x))for x in partitions):raise ValueError('duplicate verification outcome')
 if set(eligible)|set(verified.get('failed_ids',[]))|set(verified.get('blocked_ids',[]))!=set(ids):raise ValueError('verification omits failures')
 if verified.get('qualified')!=len(eligible) or report.get('qualified')!=len(eligible):raise ValueError('qualification aggregate mismatch')
 if identity_map is None:identity_map={pid:'development400:'+str(pid)for pid in ids}
 if not set(ids)<=set(identity_map) or len({identity_map[pid]for pid in ids})!=len(ids):raise ValueError('explicit unique identity map required')
 pins=run['code_sha256'];runtime=required_hash(run['python_runtime_sha256'])
 for path,h in pins.items():required_hash(h)
 required=('algsolve/judge/sandbox.py','algsolve/judge/judge.py','algsolve/judge/functional_semantics.py','algsolve/judge/declared_comparison.py','literals/admission500-v1/qualify_rules.py')
 if any(k not in pins for k in required):raise ValueError('original judge binding missing')
 harness=[(k,v)for k,v in pins.items()if k.endswith('/harness.py')]
 if len(harness)!=1:raise ValueError('unique typed transport identity required')
 implementations={};receipts={};bindings={};rows={r['id']:r for r in report['rows']}
 for pid in eligible:
  row=rows[pid]
  if row.get('passed')is not True or row.get('checks_passed')!=row.get('cases') or row.get('failures')!=[]:raise ValueError('verified row metadata disagrees')
  source=source_freeze['sources'][str(pid)];inputs=run['input_hashes'][str(pid)]
  if source.get('method')!='solve':raise ValueError('noncanonical executed entry')
  for h in (source['sha256'],source['semantics_sha256'],inputs['cases'],inputs['baseline'],inputs['source']):required_hash(h)
  # This descriptor is a lossless identity bundle for the EXISTING admitted
  # behavior specification, not a freshly authored normative problem statement.
  contract_binding={'schema':'gamma.existing-python-admission-binding.v1','numeric_development_id':pid,
   'source_semantics_sha256':source['semantics_sha256'],'frozen_input_manifest_sha256':run['input_manifest_sha256'],
   'frozen_tests_sha256':inputs['cases'],'frozen_behavior_effects_sha256':inputs['baseline'],
   'admitted_reference_sha256':inputs['source'],'qualification_contract_sha256':run_sha256,
   'scope':'existing admitted frozen return/type/mutation/alias specification; finite tests, not universal domain or complexity proof'}
  contract_hash=digest(contract_binding)
  interface={'schema':'gamma.call-interface.v1','entrypoint':'solve','arguments':'ordered-positional','typed_contract':contract_hash}
  runtime_binding={'python_executable_sha256':runtime,'sandbox_sha256':pins['algsolve/judge/sandbox.py'],'limits':run['limits']}
  effects_binding={'historical_behavior_effects_sha256':inputs['baseline'],'typed_transport_sha256':harness[0][1],
   'host_judge_sha256':pins['algsolve/judge/judge.py'],'functional_semantics_sha256':pins['algsolve/judge/functional_semantics.py'],
   'declared_comparison_sha256':pins['algsolve/judge/declared_comparison.py'],'admitted_comparison_rules_sha256':pins['literals/admission500-v1/qualify_rules.py']}
  provenance={'scope':'existing-frozen-source-qualification','numeric_development_id':pid,
   'report_sha256':report_sha256,'qualification_contract_sha256':run_sha256,
   'independent_verification_sha256':verified_sha256,'source_freeze_sha256':run['source_freeze_sha256'],
   'source_semantics_sha256':source['semantics_sha256'],'evidence_class':'frozen-admitted-typed-effects',
   'case_count':row['cases'],'all_domain_proof':False,'recognition_qualified':False,'current_serving_runtime_verified':False}
  impl={'status':'qualified','canonical_variant_id':'python:'+source['sha256'],'source_sha256':source['sha256'],
   'problem_contract_sha256':contract_hash,'interface':interface,'interface_sha256':digest(interface),
   'runtime_sha256':digest(runtime_binding),'tests_sha256':inputs['cases'],'effects_sha256':digest(effects_binding),'provenance':provenance}
  scope='Exact existing frozen admitted Python return/type/mutation/alias specification and unchanged isolation/resource contract.'
  caveats=['Finite independently checked cases, not universal-domain or all-input complexity proof.','Qualification binds the recorded Python runtime; current serving-runtime validation remains separate.','Not recognition qualification; protected cases remain unopened.']
  impl.update(evidence_class='frozen-admitted-typed-effects',contract_scope=scope,caveats=caveats)
  receipt={k:impl[k]for k in ('source_sha256','problem_contract_sha256','interface_sha256','runtime_sha256','tests_sha256','effects_sha256')}
  receipt.update(problem_id=identity_map[pid],language='python',verdict='qualified',evidence_class='frozen-admitted-typed-effects',independent_verifier=True,
   canonical_variant_id=impl['canonical_variant_id'],provenance_sha256=digest(provenance),original_independent_verification_sha256=verified_sha256,
   verification_mode='metadata chain to externally trusted prior full observation verifier; not new case execution')
  receipt.update(contract_scope=scope,caveats=caveats)
  rid=digest(receipt);impl['receipt_sha256']=rid;receipts[rid]=receipt;implementations[identity_map[pid]]=impl
  bindings[identity_map[pid]]={'problem_contract':contract_binding,'runtime':runtime_binding,'effects':effects_binding}
 return {'implementations':implementations,'verified_receipts':receipts,'binding_descriptors':bindings,
         'eligible_ids':eligible,'failed_ids':verified.get('failed_ids',[]),'blocked_ids':verified.get('blocked_ids',[]),
         'new_case_reads':0,'new_candidate_executions':0,'recognition_qualified':False}


def adapt_files(report_path, verified_path, trusted_verified_sha256, allowed_ids, identity_map=None):
 report_path,verified_path=Path(report_path),Path(verified_path)
 report_raw=report_path.read_bytes();run_raw=(report_path.parent/'contract.json').read_bytes();verify_raw=verified_path.read_bytes()
 run=json.loads(run_raw);source=json.loads((Path(run['source_freeze'])/'contract.json').read_bytes())
 return adapt_verified_metadata(json.loads(report_raw),run,source,json.loads(verify_raw),
  report_sha256=sha(report_raw),run_sha256=sha(run_raw),verified_sha256=sha(verify_raw),
  trusted_verified_sha256=trusted_verified_sha256,allowed_ids=allowed_ids,verified_raw=verify_raw,report_raw=report_raw,run_raw=run_raw,identity_map=identity_map)
