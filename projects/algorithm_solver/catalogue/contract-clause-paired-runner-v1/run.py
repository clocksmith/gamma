"""Explicitly permitted bounded phase runner. No default model run."""
import argparse,fcntl,json,os,resource,time,sys
from pathlib import Path
from owner import verified,pinned,build,sha,module,HERE,BASE

def save(path,value):
 tmp=path.with_suffix('.tmp')
 with tmp.open('x')as stream:json.dump(value,stream,sort_keys=True,allow_nan=False);stream.flush();os.fsync(stream.fileno())
 os.replace(tmp,path)
def available_memory():
 available=int(next(l.split()[1]for l in Path('/proc/meminfo').read_text().splitlines()if l.startswith('MemAvailable:')))*1024
 maximum=Path('/sys/fs/cgroup/memory.max');current=Path('/sys/fs/cgroup/memory.current')
 if maximum.exists()and current.exists()and maximum.read_text().strip()!='max':available=min(available,int(maximum.read_text())-int(current.read_text()))
 return available

def normalize_labels(rows):
 labels=[]
 for r in rows:
  relation=r['relationship_to_selected_contract']
  if relation not in ('positive','selected-contract-contrast'):raise ValueError('new development relation schema')
  labels.append(dict(kind='positive'if relation=='positive'else'selected_contract_contrast',target_id=r['problem_id'],artifact_eligible=r['artifact_applicability']['dual_artifact_acceptance_eligible']))
 if sum(x['kind']=='positive'for x in labels)!=48 or len(labels)!=72:raise ValueError('48positive24contrast population')
 return labels

def main(a):
 start=time.perf_counter();cpu=time.process_time();f=verified(dict(path=a.freeze,sha256=a.freeze_sha256));permit=pinned(dict(path=a.authorization,sha256=a.authorization_sha256));limits=f['resources']
 if permit.get('approved')is not True or permit.get('freeze_sha256')!=a.freeze_sha256 or permit.get('phase')!=a.phase or permit.get('resources')!=limits or permit.get('exclusive_heavy_work_confirmed')is not True:raise PermissionError('explicit exact phase/resource permit required')
 if a.phase=='replay'and permit.get('development_sha256')!=f['development']['sha256']:raise PermissionError('development population permit')
 if Path(sys.executable)!=Path(f['python'])or sha(Path(sys.executable).resolve().read_bytes())!=f['native_python_sha256']:raise ValueError('pinned native interpreter required')
 if available_memory()<limits['minimum_available_memory_bytes']:raise RuntimeError('insufficient effective memory headroom')
 resource.setrlimit(resource.RLIMIT_AS,(limits['address_space_bytes'],)*2);resource.setrlimit(resource.RLIMIT_CPU,(limits['cpu_seconds'],limits['cpu_hard_seconds']))
 lock=Path(f['heavy_lock']).open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 expected_claim=f['initial_claim_paths'][a.phase]
 if permit.get('resume_exact_cache')is True:
  if a.phase!='cache'or not isinstance(permit.get('reviewed_failure_sha256'),str)or len(permit['reviewed_failure_sha256'])!=64:raise PermissionError('reviewed exact-cache resume only')
  expected_claim=f['reviewed_cache_resume_claim_path']
  pinned(dict(path=str(Path(f['clause_cache_path'])/'progress.json'),sha256=permit['cache_progress_sha256']))
 if permit.get('claim_path')!=expected_claim:raise PermissionError('attempt claim identity')
 claim=Path(expected_claim);claim.parent.mkdir(exist_ok=True,parents=True)
 with claim.open('x')as stream:json.dump(dict(freeze_sha256=a.freeze_sha256,phase=a.phase,authorization_sha256=a.authorization_sha256),stream)
 out=Path(a.output);out.mkdir(exist_ok=False);predictions=[]
 try:
  save(out/'progress.json',dict(phase='initialization',confirmation_read=False));owner=build(f);cache=owner['cache'];cache_path=Path(f['clause_cache_path'])
  if a.phase=='replay':
   progress=pinned(dict(path=str(cache_path/'progress.json'),sha256=permit['cache_progress_sha256']))
   if len(progress['completed'])!=26 or progress['job']['count']!=104:raise ValueError('complete104 clause cache required before replay')
  class ReadOnlyCacheEncoder:
   def encode_records(self,*args,**kwargs):raise RuntimeError('replay cannot fill incomplete clause cache')
  cache_encoder=ReadOnlyCacheEncoder()if a.phase=='replay'else owner['encoder']
  vectors,cache_job_sha=cache.cached_clauses(owner['inputs'],cache_encoder,cache_path,owner['cache_identity'],owner['chunk_gate'],resume=(a.phase=='replay'or permit.get('resume_exact_cache')is True))
  if len(vectors)!=104:raise ValueError('exact104 clause vector population')
  if a.phase=='cache':result=dict(status='completed',phase='cache',clause_vectors=104,cache_job_sha256=cache_job_sha,cache_progress_sha256=sha((cache_path/'progress.json').read_bytes()),encoder_calls=owner['encoder'].calls)
  else:
   cohort=pinned(f['development']);rows=cohort['descriptions']
   if cohort.get('split')!='development'or len(rows)!=72 or len({r['description_id']for r in rows})!=72:raise ValueError('exact72 development population')
   predictor=owner['predictor'](vectors)
   with (out/'requests.jsonl').open('x')as log:
    for i,row in enumerate(rows):
     prediction=predictor.request(row['description']);predictions.append(prediction);log.write(json.dumps(dict(position=i,prediction=prediction),sort_keys=True)+'\n');log.flush();os.fsync(log.fileno());save(out/'progress.json',dict(phase='requests',completed=i+1,scheduled=72,confirmation_read=False))
   # Evaluator labels are normalized ONLY after all predictions complete.
   evaluation=module('evaluation',HERE/'evaluation.py').evaluate(predictions,normalize_labels(rows),owner['policy_family']);result=dict(status='completed',phase='replay',query_count=72,actual_encoder_calls=owner['encoder'].calls,actual_fresh_encoder_rows=sum(p.get('fresh_encoder_rows',0)for p in predictions),operational_errors=sum(p['status']!='completed'for p in predictions),evaluation=evaluation)
  result.update(freeze_sha256=a.freeze_sha256,authorization_sha256=a.authorization_sha256,wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,confirmation_read=False,recognition_qualified=False,artifact_bytes_materialized=False);save(out/'report.json',result)
 except BaseException as exc:save(out/'failure.json',dict(error_type=type(exc).__name__,freeze_sha256=a.freeze_sha256,completed_requests=len(predictions),confirmation_read=False,claim_consumed=True));raise
 finally:fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=('cache','replay'),required=True)
 for n in ('freeze','freeze-sha256','authorization','authorization-sha256','output'):p.add_argument('--'+n,required=True)
 main(p.parse_args())
