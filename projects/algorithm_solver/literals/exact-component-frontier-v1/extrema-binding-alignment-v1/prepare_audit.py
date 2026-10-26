"""Explicitly authorized eight extrema finite case files ONLY; no execution."""
import collections,hashlib,importlib.util,json,math,sys
from pathlib import Path
R4=Path('/workspace/shared/deco/gamma/projects/algorithm_solver/literals/exact-component-frontier-v1');sys.path.insert(0,str(R4));import run_js_global as owner
IDS=(123,55,1014,1121,1375,1725,1732,2873)
def main():
 transfer=owner.f.load('role_alignment_transfer',owner.f.LIT/'readable-joint-blocks-v1/transfer.py');spec,manifest=transfer.load_manifest();base=owner.pinned(owner.BASE,owner.BASE_SHA)
 cfg=owner.pinned(owner.CONFIG,owner.CONFIG_SHA);gs=cfg['source_access']['boundary_gate'];gate=owner.pinned(gs['path'],gs['sha256']);service=owner.KnownSpecService.from_config(owner.CONFIG,owner.CONFIG_SHA)
 if not set(IDS)<=set(spec['partition']['dev_fit']):raise ValueError('eight must remain fit only')
 rows=[];variants=[];blocked=[]
 for pid in IDS:
  impl=service.request('leetcode:'+str(pid),language='javascript',include_source=False)['implementations']['javascript'];source=base['source_rows'][str(pid)+':original'];root=Path(source['path']).parents[2]
  files={row['kind']:row for row in spec['files']if row.get('id')==pid}
  if root/files['source']['path']!=Path(source['path']) or files['source']['sha256']!=source['sha256']:raise ValueError('exact historical source binding mismatch')
  if impl['source_sha256']!=source['sha256'] or impl['tests_sha256']!=files['cases']['sha256']:
   blocked.append({'problem_id':pid,'status':'blocked_current_service_binding_differs','historical_source_sha256':source['sha256'],'current_service_source_sha256':impl['source_sha256'],'historical_cases_sha256':files['cases']['sha256'],'current_service_cases_sha256':impl['tests_sha256'],'payloads_opened':0});continue
  # Source gate is a current availability check only. Case access authority is
  # parent's explicit six-ID finite-case audit instruction, never inferred here.
  owner.boundary_policy.authorize_before_open('leetcode:'+str(pid),gate['artifact_paths'],gate['trusted_hashes'],language='javascript',payload_kind='source')
  raw=transfer.read_relative(root,files['cases']['path'])
  if hashlib.sha256(raw).hexdigest()!=files['cases']['sha256']:raise ValueError('bound case bytes changed')
  cases=json.loads(raw)
  if type(cases)is dict and 'cases'in cases:cases=cases['cases']
  if type(cases)is not list:raise ValueError('unexpected exact casefile container')
  leaf=collections.Counter();arg_shapes=collections.Counter();bad=0;maxdepth=0
  def walk(v,depth=0):
   nonlocal bad,maxdepth
   maxdepth=max(maxdepth,depth)
   if type(v)is list:
    for x in v:walk(x,depth+1)
   elif v is None:leaf['null']+=1;bad+=1
   elif type(v)is bool:leaf['boolean']+=1;bad+=1
   elif type(v)is int:leaf['safe_integer'if abs(v)<=2**53-1 else'unsafe_integer']+=1;bad+=int(abs(v)>2**53-1)
   elif type(v)is float and math.isfinite(v):leaf['finite_float']+=1
   else:leaf[type(v).__name__]+=1;bad+=1
  def shape(v):
   if type(v)is list:return 'array('+','.join(sorted({shape(x)for x in v})) +')'
   return type(v).__name__
  for case in cases:
   if type(case)is not dict or type(case.get('args'))is not list:raise ValueError('original positional args missing')
   arg_shapes[','.join(shape(x)for x in case['args'])]+=1;walk(case['args'])
  if len(cases)!=impl['provenance']['original_provenance']['case_count']:raise ValueError('all original cases required')
  owner.boundary_policy.authorize_before_open('leetcode:'+str(pid),gate['artifact_paths'],gate['trusted_hashes'],language='javascript',payload_kind='source')
  source_raw=transfer.read_relative(root,files['source']['path'])
  if hashlib.sha256(source_raw).hexdigest()!=source['sha256']:raise ValueError('exact source byte binding')
  variants.append({'key':str(pid)+':original','problem_id':str(pid),'source_sha256':source['sha256'],'source':source_raw.decode()})
  rows.append({'problem_id':pid,'source_sha256':source['sha256'],'cases_path':str(root/files['cases']['path']),'cases_sha256':files['cases']['sha256'],'original_baseline_path':str(root/files['baseline']['path']),'original_baseline_sha256':files['baseline']['sha256'],'baseline_payload_opened':False,'typed_contract_sha256':impl['problem_contract_sha256'],'effects_sha256':impl['effects_sha256'],'original_receipt_sha256':impl['receipt_sha256'],'cases':len(cases),'arg_shapes':dict(arg_shapes),'leaf_counts':dict(leaf),'max_array_depth':maxdepth,'unsupported_leaf_count':bad,'all_args_numeric_JSON_arrays_scalars':bad==0,'reflection_input_scope':'Every exact frozen args tree has only safe primitive JSON numbers and arrays, no objects/strings/callables/proxies/accessors. No general normative-domain assertion.'})
 output={'schema':'gamma.extrema-binding-alignment.finite-case-audit.v1','source_population':875,'fit_population':300,'input_manifest_sha256':manifest,'source_pool_freeze_sha256':owner.BASE_SHA,'gate_config_sha256':gs['sha256'],'ids':list(IDS),'rows':rows,'case_files_opened':len(rows),'source_files_opened':len(variants),'blocked':blocked,'baseline_files_opened':0,'candidate_executions':0,'protected_payloads_opened':0,'scope':'ONLY exact eight existing admitted finite cases; independent review and full unchanged effects replay still required.'}
 dest=Path(sys.argv[1]);dest.mkdir(mode=0o700,parents=True,exist_ok=False)
 (dest/'inputs.private.json').write_text(json.dumps({'variants':variants},sort_keys=True,separators=(',',':'))+'\n')
 p=dest/'finite-case-audit.json'
 if p.exists():raise ValueError('preserve audit')
 p.write_text(json.dumps(output,sort_keys=True,indent=2)+'\n');print(json.dumps({'cases':sum(r['cases']for r in rows),'all_opened_numeric':all(r['all_args_numeric_JSON_arrays_scalars']for r in rows),'opened_ids':[r['problem_id']for r in rows],'blocked':blocked,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))
if __name__=='__main__':main()
