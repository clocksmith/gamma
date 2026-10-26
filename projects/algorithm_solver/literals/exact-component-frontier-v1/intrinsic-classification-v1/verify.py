"""Host verifier/aggregate producer; source payloads are not opened."""
import argparse,hashlib,json,pathlib
HERE=pathlib.Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=pathlib.Path,required=True);p.add_argument('--freeze-sha256',required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();d=a.run
 if sha(d/'freeze.json')!=a.freeze_sha256:raise ValueError('freeze drift')
 c=json.loads((d/'freeze.json').read_bytes());prep=json.loads((d/'preparation.json').read_bytes());sup=json.loads((d/'native/supervisor.json').read_bytes());res=json.loads((d/'resources.json').read_bytes())
 # Do not reopen private source packet; it was pinned immediately before native read.
 for path,digest in c['code_and_inputs_sha256'].items():
  if path.endswith('inputs.private.json'):continue
  if sha(pathlib.Path(path))!=digest:raise ValueError('code/runtime identity drift')
 if sup['exit_code']!=0 or res['exit_code']!=0 or not sup['no_executing_owned_processes_observed']or sup['remaining_live_owned']or sup['wall_timeout']or sup['inspection_unreadable_pids']:raise ValueError('execution/cleanup failure')
 log=d/'native/worker.log';data=log.read_bytes()
 if len(data)>4*1024**2:raise ValueError('bounded metadata output')
 lines=[json.loads(s)for s in data.splitlines()];tests=lines[0]['controls'];rows=lines[1:-1]
 if len(tests)!=14 or any(t['expected']!=t['observed']for t in tests)or len({t['name']for t in tests})!=14:raise ValueError('controls incomplete')
 if lines[-1]!={'done':52,'owners':48,'source_bytes':8942,'candidate_execution':False,'admitted':0}:raise ValueError('terminal protocol')
 prior=pathlib.Path('/workspace/shared/gamma-current875-ast-inventory-20261025-2222/native-v3/worker.log')
 if sha(prior)!=prep['metadata_sha256']:raise ValueError('prior inventory identity')
 allowed={'unsupported_CallExpression','non_length_named_property','unresolved_global_reference'}
 expected={r['key']:r for r in map(json.loads,prior.read_bytes().splitlines())if 'key'in r and r.get('rejection_reasons')and set(r['rejection_reasons'])<=allowed and r['index_proof']['all_computed_indices_inductively_numeric']}
 if len(rows)!=52 or {r['key']for r in rows}!=set(expected)or len({r['problem_id']for r in rows})!=48 or sum(r['source_bytes']for r in rows)!=8942:raise ValueError('scope/source mass')
 for r in rows:
  if r['source_sha256']!=expected[r['key']]['source_sha256']or r['problem_id']!=expected[r['key']]['problem_id']or r['admitted']is not False:raise ValueError('exact hash/owner/admission')
 def agg(rs):return {'variants':len(rs),'owners':len({r['problem_id']for r in rs}),'source_bytes':sum(r['source_bytes']for r in rs)}
 cats=sorted({k for r in rows for k in r['counts']if k!='sources'});groups=[dict(category=k,occurrences=sum(r['counts'].get(k,0)for r in rows),**agg([r for r in rows if r['counts'].get(k,0)]))for k in cats]
 candidates=[r for r in rows if r['direct_numeric_Math_only_investigation_candidate']]
 out={'schema':'gamma.intrinsic52.classification-result.v1','freeze_sha256':a.freeze_sha256,'metadata_sha256':sha(log),'preparation_sha256':sha(d/'preparation.json'),'supervisor_sha256':sha(d/'native/supervisor.json'),'resources':res,'cleanup_passed':True,'controls':tests,'scope':agg(rows),'categories_overlapping':sorted(groups,key=lambda r:(-r['source_bytes'],r['category'])),'numeric_Math_only_investigation':agg(candidates),'numeric_Math_only_per_intrinsic':[dict(category=k,occurrences=sum(r['counts'].get(k,0)for r in candidates),**agg([r for r in candidates if r['counts'].get(k,0)]))for k in cats if k.startswith('direct_numeric_Math.') and any(r['counts'].get(k,0)for r in candidates)],'numeric_Math_only_source_identities':[{'key':r['key'],'problem_id':r['problem_id'],'source_sha256':r['source_sha256'],'source_bytes':r['source_bytes'],'member_write_occurrences':r['counts'].get('member_write',0),'numeric_intrinsics':{k:v for k,v in r['counts'].items()if k.startswith('direct_numeric_Math.')}}for r in candidates],'candidate_execution':False,'additional_sources_admitted':0,'M1':'UNMET','scope_limitation':'Callee/reflection/mutation syntax classification only. Numeric arguments, coercion, exceptional values, finite contract domain and full return/mutation/alias/effects require independent exact-source review and matched replay. No blanket member/global/call admission.'}
 a.output.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k in('scope','numeric_Math_only_investigation','categories_overlapping','cleanup_passed')}))
if __name__=='__main__':main()
