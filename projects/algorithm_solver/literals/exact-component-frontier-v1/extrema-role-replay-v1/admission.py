"""Fail-closed composition of externally pinned independent admission evidence.
No caller-supplied booleans qualify a source; no candidate execution occurs here.
"""
import hashlib,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;R4=HERE.parent
spec=importlib.util.spec_from_file_location('extrema_original_replay_owner',R4/'six-role-replay-v1/qualify.py');original_owner=importlib.util.module_from_spec(spec);sys.modules[spec.name]=original_owner;spec.loader.exec_module(original_owner)
IDS=[123,55,1014,1121,1375,1725,1732,2873]
GUARD='e9fda12b87d325df18b69ddf21e0cf82e8a2c55b3966bc0602e058e7fed5db5e'
RUNTIME_FREEZE='0633d08c20dd9c5025ba3807744425066f2a21ef950930bf91fca0acd0aa8168'
FIXED={'source_review':'29af46715881d0c336a11d7f3fe30372515510e9de8d0687770b0cec866020ea','parser_verified':'ff87b0dfeac768eaf8dc05fb15419f6b92be47b91703376be4ead026302d0f6c','case_audit':'144631d4812c8e21efe907a4d87cb44d5850408ba56f181f31cf0355691054cd','historical123_binding':'9f63aac8116a4aa56c948a4beed61e57f7dda1aebc17f33ba912f28b241ea212'}
def read_pinned(path,digest):
 raw=original_owner.safe_read(path)
 if not isinstance(digest,str)or len(digest)!=64 or hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('trusted independent evidence hash mismatch')
 return json.loads(raw)
def indexed(rows,key,ids):
 if len(rows)!=len(ids)or {r[key]for r in rows}!=set(ids):raise ValueError('exact unique eight evidence rows')
 return {r[key]:r for r in rows}
def review_header(review):
 if review.get('schema')!='gamma.extrema8.composite-transform-review.v1'or review.get('independent_review')is not True or not review.get('reviewer')or review.get('root_parser_transform_authorized')is not True or review.get('source_pool_admission')is not False or review.get('guard_sha256')!=GUARD or review.get('runtime_freeze_sha256')!=RUNTIME_FREEZE:raise ValueError('independent/root parser-transform review required')
 if set(review.get('anchors',{}))!=set(FIXED)|{'runtime_verified','runtime_supervisor'}:raise ValueError('complete proof/runtime evidence closure')
 for name,h in FIXED.items():
  if review['anchors'][name]['sha256']!=h:raise ValueError('immutable reviewed source/proof anchor')
def validate(review,evidence):
 review_header(review)
 static=evidence['source_review'];parser=evidence['parser_verified'];audit=evidence['case_audit'];hist=evidence['historical123_binding'];runtime=evidence['runtime_verified'];sup=evidence['runtime_supervisor']
 if static['alignment_sha256']!=GUARD or static['guard_review']['controls_executed_by_reviewer']is not False:raise ValueError('source review identity')
 if parser.get('verified')is not True or parser['sources']!=8 or parser['syntactic_candidates']!=8 or parser['qualified']!=0 or parser['candidate_execution']is not False or not parser['cleanup_passed']or len(parser['controls'])!=38 or any(t['expected']!=t['observed']for t in parser['controls']):raise ValueError('native parser proof incomplete')
 if audit['ids']!=IDS or audit['blocked']or audit['case_files_opened']!=8 or sum(r['cases']for r in audit['rows'])!=802:raise ValueError('all eight original finite contracts required')
 if runtime.get('schema')!='gamma.extrema-public-runtime-control.verified.v2'or runtime.get('verified')is not True or runtime.get('freeze_sha256')!=RUNTIME_FREEZE or runtime.get('checks')!=6 or runtime.get('public_isolated_executions')!=2 or runtime.get('corpus_executions')!=0 or runtime.get('algorithm_admission')is not False:raise ValueError('fresh independently verified public runtime controls required')
 if sup.get('exit_code')!=0 or sup.get('no_executing_owned_processes_observed')is not True or sup.get('remaining_live_owned')!=[]or sup.get('inspection_unreadable_pids')!=[]or sup.get('wall_timeout')is not False:raise ValueError('public runtime process cleanup required')
 if runtime['runtime']!=hist['bindings']['runtime']['manifest']:raise ValueError('control and historical pinned runtime differ')
 src=indexed(static['rows'],'problem_id',IDS);cases=indexed(audit['rows'],'problem_id',IDS);parsed=indexed(parser['source_results'],'key',[str(pid)+':original'for pid in IDS]);out=[]
 for pid in IDS:
  s=src[pid];c=cases[pid];p=parsed[str(pid)+':original']
  if any(s[k]!=c[k]for k in('source_sha256','cases_sha256','effects_sha256','runtime_sha256'))or p['source_sha256']!=s['source_sha256']or not p['syntactic_candidate']or p['admitted']is not False or s['case_count']!=c['cases']:raise ValueError('exact source/case/effect/runtime proof binding')
  if not all(s.get(k)is True for k in('finite_primitive_number_arguments_reasoned','numeric_bounds_reasoned','no_reflection_or_callable_escape_in_source'))or s.get('source_contains_intrinsic_or_input_mutation')is not False or c['all_args_numeric_JSON_arrays_scalars']is not True:raise ValueError('independently reasoned primitive argument/nonmutation proof required')
  if s['runtime_sha256']!=hist['implementation']['runtime_sha256']:raise ValueError('same historical runtime binding required')
  out.append({'problem_id':pid,'source_sha256':s['source_sha256'],'cases_sha256':s['cases_sha256'],'effects_sha256':s['effects_sha256'],'runtime_sha256':s['runtime_sha256'],'independent_review':True,'finite_contract_numeric_arguments':True,'numeric_index_and_array_access_review':True,'no_reflection_or_coercion':True,'fresh_unmodified_intrinsics':True,'cases':c['cases'],'scope':'Exact original finite inputs; reviewed nonmutation plus public controls under exact unchanged fresh runtime/harness, not universal admission.'})
 if hist['implementation']['source_sha256']!=src[123]['source_sha256']or hist['implementation']['tests_sha256']!=src[123]['cases_sha256']:raise ValueError('historical123 owner mismatch')
 return out
def check_caller_pins(review):
 critical={str(HERE/n)for n in ('admission.py','prepare_transform.py','transform.mjs')}
 critical.update(str(R4/'extrema-binding-alignment-v1'/n)for n in ('alignment-v3.mjs',))
 critical.update(str(R4/'ast-binding-alignment-v1'/n)for n in ('parser.mjs','alignment.mjs','numeric-index-proof-v2.mjs','canonicalize.mjs','bindings.mjs'))
 pins=review.get('caller_code_sha256',{})
 if not critical<=set(pins):raise ValueError('reviewed trusted caller/semantic closure missing')
 repo=R4.parents[3]
 for filename,digest in pins.items():
  path=Path(filename)
  if not path.is_absolute()or not path.is_relative_to(repo)or path.suffix not in('.py','.mjs','.js','.cjs'):raise ValueError('caller code path outside repository closure')
  if hashlib.sha256(original_owner.safe_read(path)).hexdigest()!=digest:raise ValueError('actual reviewed caller code drift')
def load(review_path,review_sha):
 review=read_pinned(review_path,review_sha);review_header(review);check_caller_pins(review)
 if hashlib.sha256((R4/'extrema-binding-alignment-v1/alignment-v3.mjs').read_bytes()).hexdigest()!=GUARD:raise ValueError('actual guard identity drift')
 evidence={name:read_pinned(item['path'],item['sha256'])for name,item in review.get('anchors',{}).items()};audits=validate(review,evidence)
 return {'schema':'gamma.extrema8.transform-admission.v1','independent_review_sha256':review_sha,'root_parser_transform_authorized':True,'source_pool_admission':False,'guard_sha256':GUARD,'runtime_freeze_sha256':RUNTIME_FREEZE,'anchors':review['anchors'],'audits':audits,'runtime':evidence['runtime_verified']['runtime'],'case_audit':evidence['case_audit'],'runtime_verified_sha256':review['anchors']['runtime_verified']['sha256']}
