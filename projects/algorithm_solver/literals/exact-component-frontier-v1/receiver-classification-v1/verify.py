"""Source-free metadata/cleanup verifier; neither source packets nor cases opened."""
import argparse,hashlib,json,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]))
from catalogue.public_batch_adapter import bounded_regular_read

def read(p):return bounded_regular_read(str(pathlib.Path(p).absolute()),maximum_bytes=4*1024**2)
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=pathlib.Path,required=True);p.add_argument('--freeze-sha256',required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();d=a.run
 raw=read(d/'freeze.json')
 if sha(raw)!=a.freeze_sha256:raise ValueError('freeze drift')
 c=json.loads(raw);prep=json.loads(read(d/'preparation.json'));sup=json.loads(read(d/'native/supervisor.json'));res=json.loads(read(d/'resources.json'))
 for path,digest in c['code_and_inputs_sha256'].items():
  if path.endswith('inputs.private.json'):continue
  # Node executable exceeds metadata bound; stream hash rather than materialize.
  h=hashlib.sha256()
  with open(path,'rb')as f:
   for chunk in iter(lambda:f.read(1024**2),b''):h.update(chunk)
  if h.hexdigest()!=digest:raise ValueError('code/runtime drift')
 if sup['exit_code']!=0 or res['exit_code']!=0 or not sup['no_executing_owned_processes_observed']or sup['remaining_live_owned']or sup['wall_timeout']or sup['inspection_unreadable_pids']:raise ValueError('execution/cleanup failure')
 raw=read(d/'native/worker.log');lines=[json.loads(s)for s in raw.splitlines()];tests=lines[0]['controls'];rows=lines[1:-1]
 if len(tests)!=18 or len({t['name']for t in tests})!=18 or any(t['expected']!=t['observed']for t in tests):raise ValueError('18 controls required')
 if lines[-1]!={'done':209,'owners':116,'source_bytes':50555,'candidate_execution':False,'admitted':0}:raise ValueError('terminal protocol')
 prior=read('/workspace/shared/gamma-current875-ast-inventory-20261025-2222/native-v3/worker.log')
 if sha(prior)!=prep['metadata_sha256']:raise ValueError('prior metadata identity')
 allowed={'unsupported_CallExpression','non_length_named_property','unresolved_global_reference','unsupported_NewExpression','string_or_regex_value'}
 expected={r['key']:r for r in map(json.loads,prior.splitlines())if 'key'in r and set(r.get('rejection_reasons',[]))<=allowed and r['index_proof']['all_computed_indices_inductively_numeric']}
 if len(rows)!=209 or len({r['key']for r in rows})!=209 or {r['key']for r in rows}!=set(expected)or len({r['problem_id']for r in rows})!=116 or sum(r['source_bytes']for r in rows)!=50555:raise ValueError('scope/mass')
 for r in rows:
  if r['source_sha256']!=expected[r['key']]['source_sha256']or r['problem_id']!=expected[r['key']]['problem_id']or r['admitted']is not False or r['origin_is_shape_not_type_or_dominance_proof']is not True:raise ValueError('identity or unsafe admission')
 def agg(rs):return dict(variants=len(rs),owners=len({r['problem_id']for r in rs}),source_bytes=sum(r['source_bytes']for r in rs))
 cats=sorted({k for r in rows for k in r['counts']});groups=[dict(category=k,occurrences=sum(r['counts'].get(k,0)for r in rows),**agg([r for r in rows if r['counts'].get(k,0)]))for k in cats]
 families={}
 for name,prefixes in [('fresh_Map',('member/new_Map/',)),('fresh_Set',('member/new_Set/',)),('literal_array',('member/array_literal/',)),('parameter_methods',('member/parameter_unknown/',)),('literal_string',('member/string_literal/',))]:
  supported=[r for r in rows if any(any(k.startswith(pre)for pre in prefixes)for k in r['counts'])]
  families[name]={'callsite_support':agg(supported),'sources_without_reported_risk_flags':agg([r for r in supported if not any(k.startswith('risk/')for k in r['counts'])]),'source_identities':[dict(key=r['key'],problem_id=r['problem_id'],source_sha256=r['source_sha256'],source_bytes=r['source_bytes'])for r in supported]}
 out=dict(schema='gamma.receiver209.classification-result.v1',freeze_sha256=a.freeze_sha256,metadata_sha256=sha(raw),preparation_sha256=sha(read(d/'preparation.json')),supervisor_sha256=sha(read(d/'native/supervisor.json')),resources=res,cleanup_passed=True,controls=tests,scope=agg(rows),categories_overlapping=sorted(groups,key=lambda r:(-r['source_bytes'],r['category'])),families=families,candidate_execution=False,additional_sources_admitted=0,M1='UNMET',scope_limitation='209-row syntax upper bound only. Receiver initializer shape is not definite initialization, runtime type or safety; method replacements, prototype mutation, alias/effects, function escape, coercion and exact finite contracts need separate source-specific review. No blanket call/constructor/global admission.')
 a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'scope':out['scope'],'families':{k:{x:y for x,y in v.items()if x!='source_identities'}for k,v in families.items()}}))
if __name__=='__main__':main()
