"""Frozen, reviewed public-domain qualification; candidate execution native only."""
import argparse,hashlib,json,math,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOLVER=HERE.parents[1];LIT=SOLVER/'literals'
sys.path.insert(0,str(SOLVER))
from algsolve.judge import sandbox,pinned_runtime
from oracle import IDS,compare,expected,exact
from cases import build
LIMITS={'cpu_seconds':3,'wall_seconds':8,'memory_bytes':1024**3,'max_output_bytes':4*1024**2}
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def encoded(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def write(path,value):path.write_bytes(encoded(value))
def pins():
 paths=[HERE/n for n in ('oracle.py','cases.py','qualify.py','verify.py','test_foundation.py','PLAN.md','test_transport.cjs')]
 paths += [HERE/'harness.py',HERE/'harness.cjs',Path(sandbox.__file__),Path(pinned_runtime.__file__)]
 return {str(p.relative_to(SOLVER)):sha(p.read_bytes())for p in paths}
def prepare(a):
 public=a.public_contracts.resolve();manifest_raw=(public/'manifest.json').read_bytes();manifest=json.loads(manifest_raw)
 for row in manifest['files']:
  if sha((public/row['path']).read_bytes())!=row['sha256']:raise ValueError('public contract manifest drift')
 joint_raw=(a.joint_freeze/'contract.json').read_bytes();joint=json.loads(joint_raw)
 py_raw=(a.python_freeze/'contract.json').read_bytes();py=json.loads(py_raw)
 if not set(IDS)<=set(joint['partition']['dev_fit']+joint['partition']['dev_val']) or py['protected_access']is not False:raise ValueError('fourteen permitted development source scope')
 cases=build(public);sources={};payloads={}
 for pid in IDS:
  pf=a.python_devval_freeze if pid in (120,931,988) else a.python_freeze
  pr=(pf/'contract.json').read_bytes();pd=json.loads(pr);p=pd['sources'][str(pid)];path=pf/p['path'];data=path.read_bytes()
  if p['method']!='solve' or sha(data)!=p['sha256']:raise ValueError('Python frozen source identity')
  sources[f'python:{pid}']={'id':pid,'language':'python','path':f'{pid}.py','sha256':sha(data),'bytes':len(data),'source_freeze_sha256':sha(pr),'semantics_sha256':p['semantics_sha256'],'original_path':str(path)};payloads[f'{pid}.py']=data
  selected=[r for r in joint['population'][str(pid)]if r['label']==joint['references'][str(pid)]]
  if len(selected)!=1 or selected[0]['evidence']!='baseline':raise ValueError('expected reviewed original JS reference')
  p=selected[0];data=Path(p['path']).read_bytes()
  if sha(data)!=p['sha256']:raise ValueError('JS source changed')
  sources[f'javascript:{pid}']={'id':pid,'language':'javascript','path':f'{pid}.js','sha256':sha(data),'bytes':len(data),'joint_freeze_sha256':sha(joint_raw),'original_path':p['path']};payloads[f'{pid}.js']=data
 runtime_ref=json.loads(a.javascript_runtime_contract.read_bytes());python_ref=json.loads(a.python_runtime_contract.read_bytes())
 c={'schema':'gamma.public-domain.foundation-freeze.v2','ids':list(IDS),'languages':['javascript','python'],'sources':sources,'code_sha256':pins(),
 'public_contract_manifest_sha256':sha(manifest_raw),'public_contract_files':manifest['files'],'public_contract_directory':str(public),
 'cases_sha256':sha(encoded(cases)),'case_counts':{str(k):len(v)for k,v in cases.items()},'node_runtime':runtime_ref['runtime'],'python_runtime_sha256':python_ref['python_runtime_sha256'],
 'javascript_runtime_reference_sha256':sha(a.javascript_runtime_contract.read_bytes()),'python_runtime_reference_sha256':sha(a.python_runtime_contract.read_bytes()),
 'limits':LIMITS,'batch_cases':32,'source_entry':'solve','effect_policy':'read-only args; fresh mutable returns; no result-to-input aliases',
 'result_policy':'exact typed ordered structure; 1514 finite numeric absolute error <=1e-5 excluding bool; 988 canonical trimmed BFS tree','authority':'prospective reviewed official public clauses plus explicitly local interface/effects/resource policy',
 'source_population':400,'historical_m1_population':500,'protected_access':False,'historical_receipts_changed':False,'automatic_promotion':False,'execution_approval':'separate independent root-authorized review required','status':'awaiting_review'}
 a.output.mkdir(parents=True,exist_ok=False)
 for name,data in payloads.items():(a.output/name).write_bytes(data)
 write(a.output/'public-cases.json',cases);write(a.output/'contract.json',c)
 return {'status':'awaiting_review','freeze_sha256':sha(encoded(c)),'cases_per_language':sum(len(x)for x in cases.values()),'sources':len(sources)}
def load_freeze(path):
 raw=(path/'contract.json').read_bytes();c=json.loads(raw)
 if c['schema']!='gamma.public-domain.foundation-freeze.v2' or c['ids']!=list(IDS)or c['code_sha256']!=pins() or c['limits']!=LIMITS or c['protected_access']is not False:raise ValueError('foundation freeze drift')
 public=Path(c['public_contract_directory'])
 if sha((public/'manifest.json').read_bytes())!=c['public_contract_manifest_sha256']:raise ValueError('official contract manifest drift')
 for row in c['public_contract_files']:
  if sha((public/row['path']).read_bytes())!=row['sha256']:raise ValueError('official clause or authored case drift')
 cases_raw=(path/'public-cases.json').read_bytes()
 if sha(cases_raw)!=c['cases_sha256']:raise ValueError('public case hash changed')
 cases=json.loads(cases_raw);regenerated=build(Path(c['public_contract_directory']))
 if not exact(cases,{str(k):v for k,v in regenerated.items()}):raise ValueError('public oracle/case regeneration mismatch')
 values={}
 for key,row in c['sources'].items():
  data=(path/row['path']).read_bytes()
  if sha(data)!=row['sha256']or len(data)!=row['bytes']:raise ValueError('candidate frozen bytes changed')
  values[key]=data
 return c,cases,values

def review_check(craw,review):
 required={'official_clauses','independent_oracle','local_effects','twenty_eight_exact_sources','iterative_transport_equivalence','1514_absolute_tolerance'}
 if review.get('schema')!='gamma.public-domain.foundation-review.v2' or review.get('freeze_sha256')!=sha(craw)or review.get('independent_review')is not True or review.get('root_execution_authorized')is not True or not required<=set(review.get('reviewed',[]))or not review.get('reviewer'):raise ValueError('independent reviewed freeze and root authority required')
def parse(raw,n):
 def pairs(items):
  result={}
  for key,value in items:
   if key in result:raise ValueError('duplicate output key')
   result[key]=value
  return result
 records=[json.loads(line,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite output')))for line in raw.splitlines()]
 if len(records)!=n+1 or records[-1]!={'done':n}or any(type(r)is not dict or type(r.get('i'))is not int or r['i']!=i for i,r in enumerate(records[:-1])):raise ValueError('complete indexed output protocol required')
 return records[:-1]
def check_batch(pid,language,cases,call,stdout,offset):
 try:
  if call['exit_code']!=0 or call['timed_out']or call['output_limit_exceeded']:raise ValueError('isolated candidate process failure')
  records=parse(stdout,len(cases));count=0;failures=[]
  for i,(case,record)in enumerate(zip(cases,records)):
   want=expected(pid,case['args'])
   if not exact(want,case['expected']):raise ValueError('frozen host expectation drift')
   passed,reason=compare(pid,case['args'],want,record,language);count+=passed
   if not passed:failures.append({'case_index':offset+i,'reason':reason})
  return count,failures
 except Exception as error:return 0,[{'offset':offset,'error':type(error).__name__+': '+str(error)}]
def make_packet(batch):return {'entry':'solve','method':'solve','calls':[{'args':x['args']}for x in batch]}
def run(a):
 c,cases,sources=load_freeze(a.freeze);craw=(a.freeze/'contract.json').read_bytes();reviewraw=a.review.read_bytes();review_check(craw,json.loads(reviewraw))
 if sha(Path('/usr/bin/python3').read_bytes())!=c['python_runtime_sha256']:raise ValueError('Python runtime drift')
 actual=pinned_runtime.freeze_runtime(a.node_path)
 if actual!=c['node_runtime']:raise ValueError('approved Node runtime drift')
 a.output.mkdir(parents=True,exist_ok=False)
 rc={'schema':'gamma.public-domain.foundation-run.v2','freeze':str(a.freeze),'freeze_sha256':sha(craw),'review_sha256':sha(reviewraw),'runtime':actual,'python_runtime_sha256':c['python_runtime_sha256'],'limits':LIMITS,'max_wall_seconds':a.max_wall,'protected_access':False}
 write(a.output/'contract.json',rc);(a.output/'review.json').write_bytes(reviewraw)
 report={'schema':rc['schema'],'contract_sha256':sha(encoded(rc)),'status':'running','rows':[],'candidate_executions':0,'passed_source_language_pairs':0,'checks_passed':0,'protected_access':False,'automatic_promotion':False,'historical_m1_qualified':False};start=time.monotonic()
 try:
  for language in c['languages']:
   for pid in IDS:
    row={'id':pid,'language':language,'cases':len(cases[str(pid)]),'source_sha256':c['sources'][f'{language}:{pid}']['sha256'],'calls':[],'failures':[],'checks_passed':0,'passed':False};report['rows'].append(row)
    for offset in range(0,len(cases[str(pid)]),32):
     if time.monotonic()-start>a.max_wall:raise TimeoutError('foundation outer wall budget')
     batch=cases[str(pid)][offset:offset+32];packet=make_packet(batch)
     if language=='python':result=sandbox.run(['/usr/bin/python3','-I','-S','harness.py'],files={'program.py':sources[f'{language}:{pid}'],'harness.py':(HERE/'harness.py').read_bytes(),'inputs.json':encoded(packet)},limits=sandbox.Limits(**LIMITS))
     else:result=pinned_runtime.run_node(a.node_path,manifest=actual,files={'program.js':sources[f'{language}:{pid}'],'harness.cjs':(HERE/'harness.cjs').read_bytes(),'inputs.json':encoded(packet)},limits=sandbox.Limits(**LIMITS),node_args=['--jitless','--single-threaded','--max-old-space-size=64','harness.cjs'])
     stem=f'{language}-{pid}-{offset}';(a.output/(stem+'.stdout')).write_bytes(result.stdout);(a.output/(stem+'.stderr')).write_bytes(result.stderr)
     call={'stem':stem,'exit_code':result.exit_code,'timed_out':result.timed_out,'output_limit_exceeded':result.output_limit_exceeded,'stdout_sha256':sha(result.stdout),'stderr_sha256':sha(result.stderr)};row['calls'].append(call);report['candidate_executions']+=1
     count,failures=check_batch(pid,language,batch,call,result.stdout,offset);row['checks_passed']+=count;row['failures']+=failures
    row['passed']=row['checks_passed']==row['cases']and not row['failures'];report['passed_source_language_pairs']+=int(row['passed']);report['checks_passed']+=row['checks_passed'];write(a.output/'report.json',report);print(json.dumps({k:row[k]for k in ('id','language','passed','cases','checks_passed')}),flush=True)
  report['status']='completed'
 except Exception as error:report['status']='blocked'if isinstance(error,sandbox.SandboxUnavailable)else'failed';report['error']=type(error).__name__+': '+str(error)
 finally:report['elapsed_seconds']=time.monotonic()-start;write(a.output/'report.json',report)
 return {k:report[k]for k in ('status','passed_source_language_pairs','checks_passed','candidate_executions')}
if __name__=='__main__':
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
 x=sub.add_parser('prepare')
 for name in ('public-contracts','joint-freeze','python-freeze','python-devval-freeze','javascript-runtime-contract','python-runtime-contract','output'):x.add_argument('--'+name,type=Path,required=True)
 x=sub.add_parser('run')
 for name in ('freeze','review','output','node-path'):x.add_argument('--'+name,type=Path,required=True)
 x.add_argument('--max-wall',type=int,default=600);a=p.parse_args();print(json.dumps(prepare(a)if a.command=='prepare'else run(a)))
