"""Bind existing JS baseline/successor qualification to the shared catalogue.

The external trust input is an exact prior independent verifier receipt hash.
No candidate, case, baseline observation or source body is loaded here.
"""
import json
from pathlib import Path
from .catalogue import digest
from .python_receipt_adapter import sha, required_hash

SCHEMAS={'gamma.baseline400.runtime-replay.v1','gamma.adapted-paired-qualification.v1'}

def adapt_files(report_path, verified_path, trusted_verified_sha256, allowed_ids,
                source_population, references, identity_map=None):
 report_path,verified_path=Path(report_path),Path(verified_path)
 raw=report_path.read_bytes();cr=(report_path.parent/'contract.json').read_bytes();vr=verified_path.read_bytes()
 if sha(vr)!=required_hash(trusted_verified_sha256):raise ValueError('external JS verification anchor mismatch')
 r,c,v=json.loads(raw),json.loads(cr),json.loads(vr)
 if c.get('schema')not in SCHEMAS or r.get('schema')!=c['schema'] or r.get('status')!='completed':raise ValueError('unsupported JS qualification contract')
 if r.get('contract_sha256')!=sha(cr) or v.get('report_sha256')!=sha(raw) or v.get('verified')is not True:raise ValueError('JS report/verifier chain mismatch')
 if any(x.get('protected_access')is not False for x in (r,c,v)) or c.get('batch_cases')!=32:raise ValueError('scope/batch drift')
 ids=c['ids'];allowed=set(allowed_ids)
 if len(ids)!=len(set(ids)) or not set(ids)<=allowed or [x['id']for x in r['rows']]!=ids:raise ValueError('execution population mismatch')
 baseline=c['schema']=='gamma.baseline400.runtime-replay.v1'
 if baseline:
  if c.get('entry')!='solve':raise ValueError('baseline executed noncanonical entry')
  eligible=v.get('eligible_ids',[]);sources={}
  if v.get('qualified')!=len(eligible) or r.get('qualified')!=len(eligible):raise ValueError('baseline pass count differs')
 else:
  eligible=[x['id']for x in v.get('alternatives',[])];sources={x['id']:x for x in c['sources']}
  if [x['id']for x in c['sources']]!=ids or any(sources[x['id']]!=x for x in v['alternatives']):raise ValueError('adapted source/verifier mismatch')
 failed=v.get('failed_ids',[])
 if len(eligible)+len(failed)!=len(ids) or len(set(eligible+failed))!=len(ids) or set(eligible+failed)!=set(ids):raise ValueError('failures omitted from JS denominator')
 runtime=c['runtime']
 if runtime.get('schema')!='gamma.pinned-node-runtime.v1' or runtime.get('isolation')!='existing-unshare-all-plus-one-readonly-executable' or runtime.get('sandbox_path')!='/runtime/node':raise ValueError('unrecognized admitted runtime isolation')
 for key in ('node_sha256','adapter_sha256','sandbox_sha256'):required_hash(runtime[key])
 for dependency in runtime['dependencies']:required_hash(dependency['sha256'])
 rows={x['id']:x for x in r['rows']};implementations={};receipts={};bindings={};source_paths={}
 if identity_map is None:identity_map={pid:'development400:'+str(pid)for pid in ids}
 if not set(ids)<=set(identity_map) or len({identity_map[pid]for pid in ids})!=len(ids):raise ValueError('explicit unique JS identity map required')
 for pid in eligible:
  row=rows[pid];inputs=c['input_hashes'][str(pid)]
  if row.get('passed')is not True or row.get('checks_passed')!=row.get('cases') or row.get('failures')!=[]:raise ValueError('verified JS execution metadata disagrees')
  for h in inputs.values():required_hash(h)
  variants=source_population[str(pid)];selected=[x for x in variants if x['label']==references[str(pid)]]
  if len(selected)!=1:raise ValueError('canonical source designation absent/ambiguous')
  selected=selected[0]
  if baseline:
   source_hash=inputs['source'];source_contract={'admitted_source_sha256':source_hash}
   if selected.get('evidence')!='baseline':raise ValueError('baseline receipt cannot qualify successor')
   effects={'historical_observation_sha256':inputs['baseline'],'historical_code_sha256':c['historical_code_sha256'],'host_judge_sha256':c['host_judge_sha256'],'pass_rule':c['pass_rule'],'integer_transport':c['integer_transport']}
   runner=c['runner_sha256']
  else:
   source=sources[pid];source_hash=source['adapted_sha256'];source_contract={k:source[k]for k in ('candidate_sha256','adapter_sha256','semantics_sha256','candidate_bytes','adapter_bytes','complete_bytes')}
   if row.get('adapted_sha256')!=source_hash or selected.get('evidence')!=str(report_path):raise ValueError('successor source/report mismatch')
   effects={'historical_observation_sha256':inputs['baseline'],'harness_sha256':c['harness_sha256'],'oracle_sha256':c['oracle_sha256'],'baseline_loader_sha256':c['baseline_loader_sha256'],'pass_rule':'original host oracle plus exact historical typed result/mutation/alias observation parity, as independently verified'}
   runner=c['code_sha256']
  required_hash(runner);required_hash(source_hash)
  if selected.get('sha256')!=source_hash:raise ValueError('canonical source hash not qualified')
  contract={'schema':'gamma.existing-javascript-admission-binding.v1','numeric_development_id':pid,'qualification_contract_sha256':sha(cr),'frozen_input_manifest_sha256':c['input_manifest_sha256'],'tests_sha256':inputs['cases'],'behavior_effects_sha256':inputs['baseline'],'admitted_reference_sha256':inputs['source'],'source_contract':source_contract,'scope':'existing frozen admitted typed return/mutation/alias behavior specification; finite evidence, no broader all-domain theorem'}
  ch=digest(contract);interface={'schema':'gamma.call-interface.v1','entrypoint':'solve','arguments':'ordered-positional','typed_contract':ch}
  runtime_binding={'manifest':runtime,'qualification_runner_sha256':runner,'resource_policy':'unchanged resource/isolation limits in this pinned qualification runner and sandbox'}
  provenance={'scope':'existing-frozen-source-qualification','numeric_development_id':pid,'report_sha256':sha(raw),'qualification_contract_sha256':sha(cr),'independent_verification_sha256':sha(vr),'case_count':row['cases'],'source_contract':source_contract,'all_domain_proof':False,'recognition_qualified':False,'current_serving_runtime_verified':False}
  scope='Exact existing frozen admitted JavaScript return/type/mutation/alias specification and pinned runtime/isolation/resource contract.'
  caveats=['Finite independently checked cases, not universal-domain or all-input complexity proof.','Historical admitted reference behavior is preserved; broader normative-domain reconciliation remains separate.','Qualification binds the recorded runtime; current serving and recognition qualification remain separate.']
  impl={'status':'qualified','canonical_variant_id':'javascript:'+source_hash,'source_sha256':source_hash,'problem_contract_sha256':ch,'interface':interface,'interface_sha256':digest(interface),'runtime_sha256':digest(runtime_binding),'tests_sha256':inputs['cases'],'effects_sha256':digest(effects),'provenance':provenance,'evidence_class':'frozen-admitted-typed-effects','contract_scope':scope,'caveats':caveats}
  receipt={k:impl[k]for k in ('source_sha256','problem_contract_sha256','interface_sha256','runtime_sha256','tests_sha256','effects_sha256','canonical_variant_id','evidence_class','contract_scope','caveats')}
  receipt.update(problem_id=identity_map[pid],language='javascript',verdict='qualified',independent_verifier=True,provenance_sha256=digest(provenance),original_independent_verification_sha256=sha(vr),verification_mode='metadata chain to externally trusted prior full observation verifier; not new case execution')
  rid=digest(receipt);impl['receipt_sha256']=rid;receipts[rid]=receipt;implementations[identity_map[pid]]=impl
  bindings[identity_map[pid]]={'problem_contract':contract,'runtime':runtime_binding,'effects':effects};source_paths[identity_map[pid]]=selected['path']
 return {'implementations':implementations,'verified_receipts':receipts,'binding_descriptors':bindings,'source_paths':source_paths,'eligible_ids':eligible,'failed_ids':failed,'new_case_reads':0,'new_candidate_executions':0}
