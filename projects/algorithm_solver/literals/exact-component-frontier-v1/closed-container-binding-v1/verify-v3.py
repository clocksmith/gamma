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
 if len(tests)!=46 or len({t['name']for t in tests})!=46 or any(t['expected']!=t['observed'] or t['expected'] and t['alpha_structure_verified'] is not True for t in tests):raise ValueError('46 controls required')
 if lines[-1]!={'done':44,'owners':22,'source_bytes':9111,'candidate_execution':False,'admitted':0,'private_transforms':0}:raise ValueError('terminal protocol')
 prior=read('/workspace/shared/gamma-receiver209-classification-20261026-0042/native/worker.log')
 if sha(prior)!=prep['metadata_sha256']:raise ValueError('prior metadata identity')
 sys.path.insert(0,str(HERE.parent/'receiver-classification-v1'));from closure import container_shape_upper_bound
 expected={r['key']:r for r in map(json.loads,prior.splitlines())if 'key'in r and container_shape_upper_bound(r)}
 if len(rows)!=44 or len({r['key']for r in rows})!=44 or {r['key']for r in rows}!=set(expected)or len({r['problem_id']for r in rows})!=22 or sum(r['source_bytes']for r in rows)!=9111:raise ValueError('scope/mass')
 for r in rows:
  if r['source_sha256']!=expected[r['key']]['source_sha256']or r['problem_id']!=expected[r['key']]['problem_id']or r['admitted']is not False or r['qualification']is not False:raise ValueError('identity or unsafe admission')
 def agg(rs):return dict(variants=len(rs),owners=len({r['problem_id']for r in rs}),source_bytes=sum(r['source_bytes']for r in rs))
 candidates=[r for r in rows if r['syntactic_candidate']]
 reasons=sorted({reason for r in rows for reason in r['reasons']});groups=[dict(reason=k,**agg([r for r in rows if k in r['reasons']]))for k in reasons]
 out=dict(schema='gamma.container44.proof-inventory.v3',freeze_sha256=a.freeze_sha256,metadata_sha256=sha(raw),preparation_sha256=sha(read(d/'preparation.json')),supervisor_sha256=sha(read(d/'native/supervisor.json')),resources=res,cleanup_passed=True,controls=tests,scope=agg(rows),syntactically_eligible=agg(candidates),rejection_families_overlapping=sorted(groups,key=lambda r:(-r['source_bytes'],r['reason'])),eligible_source_identities=[{k:r[k]for k in ('key','problem_id','source_sha256','source_bytes','container_calls','math_calls','proven_immutable_container_bindings')}for r in candidates],candidate_execution=False,private_transforms=0,additional_sources_admitted=0,M1='UNMET',scope_limitation='Structural alpha eligibility only. Independent exact finite-domain/runtime/effects review and matched original/format/role replay still required. No candidate execution, refit, canonical adoption or blanket calls.')
 a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({k:out[k]for k in ('scope','syntactically_eligible','rejection_families_overlapping')}))
if __name__=='__main__':main()
