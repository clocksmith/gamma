"""Verify exact guarded native parser outputs as data; never execute candidates."""
import argparse,hashlib,json
from pathlib import Path
import admission
q=admission.original_owner

def verify(run,digest):
 raw=q.safe_read(run/'native-freeze.json');freeze=json.loads(raw)
 if q.b.sha(raw)!=digest:raise ValueError('operator native transform pin')
 for filename,h in freeze['pins'].items():
  if filename.endswith('inputs.private.json'):continue
  actual=q.b.pinned_runtime.freeze_runtime(Path(filename))['node_sha256']if filename=='/workspace/shared/gamma-dot-diagnostics/node'else q.b.sha(q.safe_read(filename))
  if actual!=h:raise ValueError('actual transform code/receipt identity')
 review_path=next(Path(k)for k,v in freeze['pins'].items()if v==freeze['composite_review_sha256']);accepted=admission.load(review_path,freeze['composite_review_sha256'])
 if q.b.sha(q.b.encoded(accepted))!=freeze['admission_sha256']:raise ValueError('guarded transform admission drift')
 supraw=q.safe_read(run/'native/supervisor.json');sup=json.loads(supraw);resources=json.loads(q.safe_read(run/'resources.json'));native=json.loads(q.safe_read(run/'native/worker.log'))
 if sup['exit_code']!=0 or sup['wall_timeout']or not sup['no_executing_owned_processes_observed']or sup['remaining_live_owned']or sup['inspection_unreadable_pids']or resources['exit_code']!=0:raise ValueError('parser execution/cleanup incomplete')
 expected_tail=['--jitless','--single-threaded','--max-old-space-size=128','projects/algorithm_solver/literals/exact-component-frontier-v1/extrema-role-replay-v1/transform.mjs',str(run/'generated'),str(run/'admission.json'),freeze['admission_sha256']]
 if sup['command'][-len(expected_tail):]!=expected_tail or native!={'sources':8,'arms':2,'transformed_variants':16,'candidate_execution':False,'qualified':0}:raise ValueError('exact native transform command/protocol')
 _,_,read=q.context();outcomes=[];manifests={};audits={r['problem_id']:r for r in accepted['audits']}
 for arm in('format','role'):
  raw=q.safe_read(run/'generated'/arm/'transformations.json');m=json.loads(raw);manifests[arm]=q.b.sha(raw)
  if m['schema']!='gamma.extrema8.transformed.v1'or m['ids']!=list(map(str,admission.IDS))or m['candidate_executions']!=0 or m['qualified']!=0 or m['original_variants_retained']!=875 or m['fit_owners']!=300 or m['admission_sha256']!=freeze['admission_sha256']or [r['problem_id']for r in m['rows']]!=m['ids']:raise ValueError('full matched transform manifest')
  for row in m['rows']:
   pid=int(row['problem_id']);source=read(pid,run/'generated'/arm/f'{pid}.js',row[arm+'_sha256'])
   if row['original_sha256']!=audits[pid]['source_sha256']or row['mode']!=arm or row['admission_sha256']!=freeze['admission_sha256']or row['qualification']is not False or row['ast_verified']is not True or row['occurrence_resolution_verified']is not True or len(source)!=row[arm+'_bytes']or (arm=='format'and row['changed_bindings']!=0):raise ValueError('exact transformed source/AST witness')
   source.decode('utf8');outcomes.append({'problem_id':pid,'arm':arm,'original_sha256':row['original_sha256'],'source_sha256':row[arm+'_sha256'],'source_bytes':len(source),'original_bytes':row['original_bytes'],'changed_bindings':row['changed_bindings']})
 if sum(r['original_bytes']for r in outcomes)!=2106:raise ValueError('original source mass')
 return {'schema':'gamma.extrema8.guarded-transform-verification.v1','verified':True,'native_freeze_sha256':digest,'admission_sha256':freeze['admission_sha256'],'independent_composite_review_sha256':freeze['composite_review_sha256'],'supervisor_sha256':q.b.sha(supraw),'manifest_sha256':manifests,'sources':8,'variants':16,'outcomes':outcomes,'resources':resources,'candidate_executions':0,'qualified':0,'cleanup_passed':True,'original_fallbacks':875,'fit_owners':300}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--freeze-sha256',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();result=verify(a.run,a.freeze_sha256);a.output.write_bytes(q.b.encoded(result));print(json.dumps({'verified':True,'sources':8,'variants':16,'qualification':False,'report_sha256':q.b.sha(a.output.read_bytes()),'source_bytes_by_arm':{arm:sum(r['source_bytes']for r in result['outcomes']if r['arm']==arm)for arm in('format','role')}}))
