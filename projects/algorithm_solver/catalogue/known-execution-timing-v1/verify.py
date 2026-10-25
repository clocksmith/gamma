"""Independent retained-observation verification; never executes candidate code."""
import argparse,hashlib,importlib.util,json,math,statistics,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;SOLVER=HERE.parents[1]
sys.path.insert(0,str(SOLVER))
from catalogue.public_batch_adapter import bounded_regular_read
from catalogue.boundary_policy import authorize_before_open
from catalogue.known_spec_service import KnownSpecService

def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path,digest=None):
 raw=bounded_regular_read(Path(path).absolute(),maximum_bytes=4*1024**2)
 if digest is not None and sha(raw)!=digest:raise ValueError('artifact hash mismatch')
 def unique(pairs):
  result={}
  for k,v in pairs:
   if k in result:raise ValueError('duplicate JSON key')
   result[k]=v
  return result
 return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in()).throw(ValueError('nonfinite'))),raw

def distribution(xs):return {'count':len(xs),'median_seconds':statistics.median(xs),'p95_seconds':sorted(xs)[math.ceil(.95*len(xs))-1]}
def verify_rows(report,freeze,qualified,root,q):
 expected=[(repeat,p,lang)for repeat in range(5)for p in freeze['probes']for lang in ('javascript','python')]
 if len(expected)!=30 or len(report.get('rows',[]))!=30 or report.get('candidate_calls')!=30 or report.get('all_verified')is not True:raise ValueError('complete30 required')
 if (root/'failure.json').exists():raise ValueError('failed execution retained; cannot claim all verified')
 for row,(repeat,p,language)in zip(report['rows'],expected):
  pid=p['id'];stem=f'{repeat}-{language}-{pid}'
  if row.get('repeat')!=repeat or row.get('language')!=language or row.get('problem_id')!=f'leetcode:{pid}'or row.get('status')!='verified'or row.get('candidate_executions')!=1:raise ValueError('row order/identity')
  source=qualified['sources'][f'{language}:{pid}']['sha256']
  if row.get('source_sha256')!=source:raise ValueError('source binding')
  info,_=read(root/(stem+'.observation.json'))
  if info!=row.get('observation')or info.get('stem')!=stem or info.get('id')!=pid or info.get('language')!=language or info.get('repeat')!=repeat:raise ValueError('observation binding')
  if type(info.get('exit_code'))is not int or type(info.get('timed_out'))is not bool or type(info.get('output_limit_exceeded'))is not bool:raise ValueError('execution status types')
  stdout=bounded_regular_read(root/(stem+'.stdout'),maximum_bytes=4*1024**2);stderr=bounded_regular_read(root/(stem+'.stderr'),maximum_bytes=4*1024**2)
  if sha(stdout)!=info['stdout_sha256']or sha(stderr)!=info['stderr_sha256']:raise ValueError('observation bytes changed')
  q.validate(pid,p['args'])
  if not q.exact(q.expected(pid,p['args']),p['expected']):raise ValueError('probe independent oracle disagreement')
  n,fail=q.check_batch(pid,language,[{'args':p['args'],'expected':p['expected']}],info,stdout,0)
  if n!=1 or fail:raise ValueError('raw typed/effect replay failed')
  result=q.parse(stdout,1)[0]['result'];response=q.encoded({'status':'verified','result':result})
  if row.get('response_sha256')!=sha(response)or row.get('response_bytes')!=len(response):raise ValueError('response binding')
  t=row.get('timing_seconds',{});keys={'retrieval_and_hash','input_admission','isolated_execution','verification','response_serialization','end_to_end'}
  if set(t)!=keys or any(type(v)not in(int,float)or not math.isfinite(v)or v<0 for v in t.values()):raise ValueError('invalid timings')
  if not math.isclose(sum(t[k]for k in keys-{'end_to_end'}),t['end_to_end'],abs_tol=1e-8,rel_tol=1e-8):raise ValueError('timing partition mismatch')
 per={lang:distribution([r['timing_seconds']['end_to_end']for r in report['rows']if r['language']==lang])for lang in ('javascript','python')}
 if per!=report.get('per_language'):raise ValueError('aggregate timing mismatch')
 return per

def verify(freeze_path,freeze_sha256,report_path):
 f,_=read(freeze_path,freeze_sha256)
 if f['schema']!='gamma.known-execution-timing-freeze.v1'or f['candidate_calls']!=30 or f['repeats']!=5 or [p['id']for p in f['probes']]!=[802,875,2406]:raise ValueError('exact diagnostic scope')
 for name,h in f['code_sha256'].items():
  if sha(bounded_regular_read(HERE/name))!=h:raise ValueError('runner code drift')
 if f['code_sha256'].get('verify.py')!=sha(Path(__file__).read_bytes()):raise ValueError('verifier not frozen')
 for name,h in f['dependency_code_sha256'].items():
  if sha(bounded_regular_read(SOLVER/name))!=h:raise ValueError('dependency drift')
 if sha(bounded_regular_read(Path('/usr/bin/python3').resolve(strict=True)))!=f['python_runtime_sha256']:raise ValueError('Python runtime drift')
 g,_=read(f['gate']['path'],f['gate']['digest'])
 for pid in f['qualification_ids']:authorize_before_open(f'leetcode:{pid}',g['artifact_paths'],g['trusted_hashes'],language='python',payload_kind='statement')
 qualified,_=read(f['qualification']['path'],f['qualification']['digest'])
 if qualified['ids']!=f['qualification_ids']or qualified['limits']!={'cpu_seconds':3,'wall_seconds':8,'memory_bytes':1024**3,'max_output_bytes':4*1024**2}:raise ValueError('qualification runtime scope')
 for name,h in qualified['code_sha256'].items():
  if sha(bounded_regular_read(SOLVER/name))!=h:raise ValueError('qualified code drift')
 from algsolve.judge import pinned_runtime
 if pinned_runtime.freeze_runtime(Path(f['node_path']))!=qualified['node_runtime']:raise ValueError('Node runtime drift')
 service=KnownSpecService.from_config(f['service']['path'],f['service']['digest'])
 for p in f['probes']:
  for lang in ('javascript','python'):
   answer=service.request(f"leetcode:{p['id']}",language=lang,include_source=False)
   if answer['status']!='matched'or answer['implementations'][lang]['source_sha256']!=qualified['sources'][f"{lang}:{p['id']}"]['sha256']:raise ValueError('service qualification source binding')
 report,raw=read(report_path)
 if report.get('population')!=4081 or report.get('diagnostic_problem_count')!=3 or report.get('reporting_io_in_total_not_request_intervals')is not True:raise ValueError('report denominator/accounting')
 if report.get('freeze_sha256')!=freeze_sha256 or report.get('schema')!='gamma.known-execution-timing-result.v1'or any(report.get(k)is not False for k in ('goal_1c_qualified','recognition_qualified','protected_access')):raise ValueError('report scope')
 qdir=SOLVER/'catalogue/public-domain-qualification-v3';saved={k:sys.modules.get(k)for k in ('oracle','cases')}
 def load(name,path):
  s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 try:
  for name in saved:sys.modules[name]=load(name,qdir/(name+'.py'))
  q=load('_timing_verification_qualifier',qdir/'qualify.py');q.validate=sys.modules['oracle'].validate;q.expected=sys.modules['oracle'].expected;q.exact=sys.modules['oracle'].exact
  per=verify_rows(report,f,qualified,Path(report_path).absolute().parent,q)
 finally:
  for k,v in saved.items():
   if v is None:sys.modules.pop(k,None)
   else:sys.modules[k]=v
 return {'schema':'gamma.known-execution-timing-independent-verification.v1','verified':True,'freeze_sha256':freeze_sha256,'report_sha256':sha(raw),'calls':30,'per_language':per,'timing_scope':'Reported monotonic timing arithmetic checked, not independent wall-clock attestation.','raw_output_type_effect_response_replay':True,'candidate_executions':0,'goal_1c_qualified':False,'recognition_qualified':False}
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for k in ('freeze','freeze-sha256','report'):p.add_argument('--'+k,required=True)
 a=p.parse_args();print(json.dumps(verify(a.freeze,a.freeze_sha256,a.report),sort_keys=True))
