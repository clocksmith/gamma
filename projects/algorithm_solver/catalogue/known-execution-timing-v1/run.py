"""Native-only, operator-frozen exact-ID full-path diagnostic. No informal claims."""
import argparse,hashlib,importlib.util,json,math,resource,signal,statistics,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;SOLVER=HERE.parents[1]
sys.path.insert(0,str(SOLVER));sys.path.insert(0,str(HERE))
from pipeline import request
from catalogue.known_spec_service import KnownSpecService
from catalogue.public_batch_adapter import bounded_regular_read,validate_batch_inputs
from catalogue.boundary_policy import authorize_before_open
from algsolve.judge import sandbox,pinned_runtime

def sha(raw):return hashlib.sha256(raw).hexdigest()
def pinned(path,digest):
 raw=bounded_regular_read(Path(path).absolute())
 if sha(raw)!=digest:raise ValueError('frozen artifact mismatch')
 return json.loads(raw)
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def run(args):
 freeze=pinned(args.freeze,args.freeze_sha256)
 if freeze['schema']!='gamma.known-execution-timing-freeze.v1' or freeze['candidate_calls']!=30 or freeze['repeats']!=5:raise ValueError('scope/budget')
 for name,h in freeze['code_sha256'].items():
  if sha(bounded_regular_read(HERE/name))!=h:raise ValueError('runner code drift')
 for name,h in freeze['dependency_code_sha256'].items():
  if sha(bounded_regular_read(SOLVER/name))!=h:raise ValueError('service dependency drift')
 if sha(Path('/usr/bin/python3').read_bytes())!=freeze['python_runtime_sha256']:raise ValueError('native Python identity')
 if Path(sys.executable).resolve()!=Path('/usr/bin/python3').resolve():raise ValueError('native interpreter required')
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3));resource.setrlimit(resource.RLIMIT_CPU,(120,125))
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('180s outer wall')));signal.alarm(180)
 gate=pinned(**freeze['gate'])
 for pid in freeze['qualification_ids']:authorize_before_open(f'leetcode:{pid}',gate['artifact_paths'],gate['trusted_hashes'],language='python',payload_kind='statement')
 qualified=pinned(**freeze['qualification'])
 if qualified['ids']!=freeze['qualification_ids']:raise ValueError('qualification population drift')
 for name,h in qualified['code_sha256'].items():
  if sha(bounded_regular_read(SOLVER/name))!=h:raise ValueError('qualified code drift')
 qdir=SOLVER/'catalogue/public-domain-qualification-v3'
 # This dedicated CLI process has no caller modules; import only pinned trusted oracles.
 sys.modules['oracle']=module('oracle',qdir/'oracle.py');sys.modules['cases']=module('cases',qdir/'cases.py');q=module('known_execution_qualifier',qdir/'qualify.py')
 runtime=pinned_runtime.freeze_runtime(Path(freeze['node_path']))
 if runtime!=qualified['node_runtime'] or q.LIMITS!=qualified['limits']:raise ValueError('runtime/limits drift')
 start=time.perf_counter();service=KnownSpecService.from_config(freeze['service']['path'],freeze['service']['digest']);initialized=time.perf_counter()
 output=Path(args.output);output.mkdir(exist_ok=False);rows=[]
 for repeat in range(5):
  for probe in freeze['probes']:
   pid=probe['id'];call_args=probe['args']
   if pid not in (802,875,2406):raise ValueError('probe scope')
   for language in ('javascript','python'):
    source_pin=qualified['sources'][f'{language}:{pid}']['sha256']
    def admit(values,answer):validate_batch_inputs(answer['implementations'][language],values)
    observation_box=[]
    def execute(source,values):
     packet=q.encoded(q.make_packet([{'args':values}]))
     if len(packet)>1500000:raise ValueError('packet limit')
     if language=='python':result=sandbox.run(['/usr/bin/python3','-I','-S','harness.py'],files={'program.py':source,'harness.py':(qdir/'harness.py').read_bytes(),'inputs.json':packet},limits=sandbox.Limits(**q.LIMITS))
     else:result=pinned_runtime.run_node(Path(freeze['node_path']),manifest=runtime,files={'program.js':source,'harness.cjs':(qdir/'harness.cjs').read_bytes(),'inputs.json':packet},limits=sandbox.Limits(**q.LIMITS),node_args=['--jitless','--single-threaded','--max-old-space-size=64','harness.cjs'])
     observation_box.append(result);return result
    def verify(values,result):
     call={'exit_code':result.exit_code,'timed_out':result.timed_out,'output_limit_exceeded':result.output_limit_exceeded}
     count,failures=q.check_batch(pid,language,[{'args':values,'expected':probe['expected']}],call,result.stdout,0)
     if count!=1 or failures:raise ValueError('independent typed/effect verification failed')
     return q.parse(result.stdout,1)[0]['result']
    stem=f'{repeat}-{language}-{pid}'
    try:
     row=request(service,f'leetcode:{pid}',language,call_args,source_sha256=source_pin,admit=admit,execute=execute,verify=verify)
     if row['status']!='verified':raise ValueError('known probe unavailable')
    except BaseException as error:
     (output/'failure.json').write_text(json.dumps({'status':'failed','stem':stem,'completed_verified_calls':len(rows),'error':type(error).__name__+': '+str(error),'all_verified':False})+'\n')
     raise
    finally:
     if observation_box:
      observation=observation_box[0]
      (output/(stem+'.stdout')).write_bytes(observation.stdout);(output/(stem+'.stderr')).write_bytes(observation.stderr)
      evidence={'stem':stem,'id':pid,'language':language,'repeat':repeat,'exit_code':observation.exit_code,'timed_out':observation.timed_out,'output_limit_exceeded':observation.output_limit_exceeded,'stdout_sha256':sha(observation.stdout),'stderr_sha256':sha(observation.stderr)}
      (output/(stem+'.observation.json')).write_text(json.dumps(evidence,sort_keys=True)+'\n')
    rows.append(dict(row,observation=evidence,problem_id=f'leetcode:{pid}',language=language,repeat=repeat))
    (output/'progress.json').write_text(json.dumps({'completed_calls':len(rows),'total_calls':30})+'\n')
 elapsed=time.perf_counter()-start
 def distribution(xs):return {'count':len(xs),'median_seconds':statistics.median(xs),'p95_seconds':sorted(xs)[math.ceil(.95*len(xs))-1]}
 report={'schema':'gamma.known-execution-timing-result.v1','freeze_sha256':args.freeze_sha256,'population':4081,'diagnostic_problem_count':3,'candidate_calls':len(rows),'all_verified':True,'initialization_seconds':initialized-start,'total_seconds':elapsed,'per_language':{lang:distribution([r['timing_seconds']['end_to_end']for r in rows if r['language']==lang])for lang in ('javascript','python')},'rows':rows,'parent_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'max_child_peak_rss_kib':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,'memory_scope':'Separate parent and maximum individual child peaks, not simultaneous process-tree RSS.','scope':'Known-ID retrieval, live source authorization/hash, input admission, fresh isolated runtime, independent typed/effect oracle, response serialization. Three explicit public probes only.','cache_state':'OS cache uncontrolled; service initialization reported separately; every candidate uses fresh sandbox process.','excluded_stages':['informal description encoding and recognition','network delivery','whole catalogue execution'],'reporting_io_in_total_not_request_intervals':True,'goal_1c_qualified':False,'recognition_qualified':False,'protected_access':False}
 (output/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');signal.alarm(0);print(json.dumps({k:report[k]for k in ('candidate_calls','all_verified','initialization_seconds','total_seconds','per_language')}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--freeze',required=True);p.add_argument('--freeze-sha256',required=True);p.add_argument('--output',required=True);run(p.parse_args())
