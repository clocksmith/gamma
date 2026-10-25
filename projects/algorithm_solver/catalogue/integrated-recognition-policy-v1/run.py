"""Operator-authorized one-shot runner; sealed data is never read during setup."""
import argparse,collections,fcntl,hashlib,json,os,resource,signal,sys,time
from pathlib import Path
from runtime import pinned,sha,build
HERE=Path(__file__).resolve().parent

def save(path,value):
 tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n');os.replace(tmp,path)
def available_memory():
 available=int(next(l.split()[1]for l in Path('/proc/meminfo').read_text().splitlines()if l.startswith('MemAvailable:')))*1024
 maximum=Path('/sys/fs/cgroup/memory.max');current=Path('/sys/fs/cgroup/memory.current')
 if maximum.exists()and current.exists()and maximum.read_text().strip()!='max':available=min(available,int(maximum.read_text())-int(current.read_text()))
 return available

def authorize(f,freeze_sha,authorization,mode):
 a=pinned(authorization);scope=f['runs'][mode]
 if a.get('schema')!='gamma.integrated-run-authorization.v1'or a.get('approved')is not True:raise PermissionError('explicit root run authorization required')
 if a.get('freeze_sha256')!=freeze_sha or a.get('mode')!=mode or a.get('cohort_sha256')!=scope['cohort']['sha256']or a.get('query_count')!=scope['queries']:raise PermissionError('authorization identity/scope mismatch')
 if a.get('resources')!=f['resources']or a.get('exclusive_heavy_work_confirmed')is not True or a.get('one_shot')is not True:raise PermissionError('resource/exclusive/one-shot authorization required')
 if a.get('ledger_path')!=scope['ledger_path']:raise PermissionError('one-shot ledger binding')
 return a

def claim(path,freeze_sha,mode):
 path=Path(path)
 if not path.is_absolute():raise ValueError('absolute trusted ledger required')
 path.parent.mkdir(parents=True,exist_ok=True)
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'w')as stream:json.dump(dict(status='claimed',freeze_sha256=freeze_sha,mode=mode,cohort_open_started=False),stream);stream.flush();os.fsync(stream.fileno())
 return path

def declared_scope_matches(query,selected_pid,selections):
 # Evaluation-only, invoked AFTER prediction/artifact delivery. Never a model
 # feature, accepted-ID whitelist, or runtime identity lookup.
 if query['kind']!='positive':return None
 expected=[query['expected_id']]if query.get('expected_id')else query.get('expected_ids',[])
 if selected_pid not in expected or not selections:return False
 declared=query.get('declared_contract_scope',{})
 for language in ('javascript','python'):
  impl=selections[language]['implementation'];contract=impl.get('provenance',{}).get('public_foundation',{}).get('problem_contract',{})
  if impl.get('evidence_class')!='normative-typed-effects'or contract.get('official_problem_id')!=declared.get('official_problem_id')or contract.get('official_contract_sha256')!=declared.get('official_contract_sha256')or contract.get('official_preconditions')!=declared.get('official_constraints'):return False
 return True

def classify(query,response,summary,selections):
 positive=query['kind']=='positive';expected=[query['expected_id']]if query.get('expected_id')else query.get('expected_ids',[])
 decision_accept=summary.get('decision_status')=='accepted';artifact=response['status']=='artifact_returned';pid=summary.get('decision_problem_id');scope=declared_scope_matches(query,response.get('problem_id'),selections)if artifact and positive else None
 return dict(positive=positive,correct_artifact=bool(positive and artifact and response.get('problem_id')in expected and scope is True),wrong_positive_decision=bool(positive and decision_accept and pid not in expected),control_decision_accept=bool(not positive and decision_accept),wrong_artifact_accept=bool(artifact and (not positive or response.get('problem_id')not in expected)),scope_mismatch=bool(positive and artifact and scope is not True),control_abstention=bool(not positive and response['status']=='abstain'and not decision_accept),error=response['status']=='error')

def run(args):
 started=time.perf_counter();cpu=time.process_time();f=pinned(dict(path=str(Path(args.freeze).resolve()),sha256=args.freeze_sha256));mode=args.mode
 if mode not in f['runs']:raise PermissionError('unapproved run mode')
 authorization=dict(path=str(Path(args.authorization).resolve()),sha256=args.authorization_sha256);authorize(f,args.freeze_sha256,authorization,mode)
 for name,h in f['code_sha256'].items():assert sha(HERE/name)==h
 limits=f['resources'];resource.setrlimit(resource.RLIMIT_AS,(limits['address_space_bytes'],)*2);resource.setrlimit(resource.RLIMIT_CPU,(limits['cpu_seconds'],limits['cpu_seconds']+5))
 def terminate(*_):raise TimeoutError('resource or termination signal')
 for sig in (signal.SIGALRM,signal.SIGXCPU,signal.SIGTERM):signal.signal(sig,terminate)
 signal.alarm(limits['wall_seconds']);os.environ.update(OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
 if available_memory()<limits['required_headroom_bytes']:raise RuntimeError('insufficient effective memory headroom')
 lock=Path(f['heavy_work_lock']);lock.parent.mkdir(parents=True,exist_ok=True);lockstream=lock.open('a');fcntl.flock(lockstream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
 output=Path(args.output);output.mkdir(exist_ok=False);scope=f['runs'][mode];ledger=claim(scope['ledger_path'],args.freeze_sha256,mode);phase='initialization';rows=[];totals=collections.Counter()
 try:
  save(output/'progress.json',dict(phase=phase,completed_requests=0,total_requests=scope['queries'],confirmation_opened=False))
  manifest=pinned(f['authoring_manifest']);assert manifest['files'][scope['manifest_key']]['sha256']==scope['cohort']['sha256']and manifest['files'][scope['manifest_key']]['queries']==scope['queries']
  t=time.perf_counter();engine=build(f);initialization=time.perf_counter()-t
  phase='authorized_cohort_open';save(ledger,dict(status='claimed',phase=phase,freeze_sha256=args.freeze_sha256,mode=mode,cohort_open_started=True));cohort=pinned(scope['cohort']);queries=cohort['queries']
  assert len(queries)==scope['queries']and len({q['query_id']for q in queries})==scope['queries']and collections.Counter(q['kind']for q in queries)==scope['kind_counts']
  # Gold fields stay in this evaluator. Only text crosses the predictor boundary.
  phase='fresh_query_requests'
  for position,query in enumerate(queries):
   response,summary,selections=engine.request(query['text']);evaluation=classify(query,response,summary,selections);totals.update({k:int(v)for k,v in evaluation.items()});row=dict(position=position,query_id=query['query_id'],summary=summary,evaluation=evaluation);rows.append(row)
   with (output/'requests.jsonl').open('a')as stream:stream.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n');stream.flush();os.fsync(stream.fileno())
   save(output/'progress.json',dict(phase=phase,completed_requests=len(rows),total_requests=scope['queries'],confirmation_opened=mode=='confirmation'))
  gates=dict(correct_artifacts=totals['correct_artifact']>=scope['gates']['minimum_correct_positives'],zero_wrong_decisions=totals['wrong_positive_decision']==0,zero_control_decisions=totals['control_decision_accept']==0,zero_wrong_artifacts=totals['wrong_artifact_accept']==0,all_controls_abstain=totals['control_abstention']==scope['gates']['controls_must_abstain'],zero_scope_mismatches=totals['scope_mismatch']==0,zero_errors=totals['error']==0)
  equivalence=None
  if mode=='development-equivalence':
   original=pinned(f['development_baseline']);prior=next(x['arms']['both']['decisions']for x in original['results']if x['policy']==engine.policy);assert [x['query_id']for x in prior]==[q['query_id']for q in queries]
   equivalence=all(old['status']==row['summary'].get('decision_status')and old.get('reason')==row['summary'].get('decision_reason')and old.get('problem_id')==row['summary'].get('decision_problem_id')for old,row in zip(prior,rows));gates['exact_development_decision_equivalence']=equivalence
  for name,h in f['code_sha256'].items():assert sha(HERE/name)==h
  report=dict(schema='gamma.integrated-one-shot-result.v1',status='completed',mode=mode,freeze_sha256=args.freeze_sha256,authorization_sha256=args.authorization_sha256,policy=engine.policy,matched_service_sha256=f['matched_service_sha256'],population=4081,query_count=len(rows),query_encodings=sum(row['summary']['encoder_invocations']for row in rows),requests=rows,totals=dict(totals),gates=gates,finite_cohort_gates_pass=all(gates.values()),development_equivalence=equivalence,initialization_seconds=initialization,wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,confirmation_opened=mode=='confirmation',candidate_executions=0,recognition_qualified=False,goal_1c_qualified=False,sampling='Shared-author non-IID authored cohort; not universal proof or population-risk estimate',input_sha256={k:v['sha256']for k,v in f.items()if isinstance(v,dict)and 'path'in v and 'sha256'in v})
  save(output/'report.json',report);save(ledger,dict(status='completed',mode=mode,freeze_sha256=args.freeze_sha256,cohort_open_started=True,completed_requests=len(rows),report_sha256=sha(output/'report.json')))
 except BaseException as error:
  failure=dict(status='failed',phase=phase,error_type=type(error).__name__,mode=mode,freeze_sha256=args.freeze_sha256,completed_requests=len(rows),recognition_qualified=False,no_automatic_retry=True);save(output/'failure.json',failure);save(ledger,dict(failure,claim_consumed=True));raise
 finally:signal.alarm(0);lockstream.close()

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for name in ('freeze','freeze-sha256','authorization','authorization-sha256','mode','output'):p.add_argument('--'+name,required=True)
 run(p.parse_args())
