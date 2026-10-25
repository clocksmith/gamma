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
 # Code-only: never read source-bearing statement metadata before the gate.
 paths=[HERE/n for n in ('oracle.py','cases.py','qualify.py','verify.py','test_foundation.py','test_transport.cjs')]
 paths += [HERE/'harness.py',HERE/'harness.cjs',Path(sandbox.__file__),Path(pinned_runtime.__file__),SOLVER/'catalogue'/'boundary_policy.py']
 return {str(p.relative_to(SOLVER)):sha(p.read_bytes())for p in paths}
def statement_pins(gate):
 from catalogue.boundary_policy import authorize_before_open
 result={}
 for name in ('PLAN.md','contracts.json','worklist.json'):
  for pid in IDS:authorize_before_open(f'leetcode:{pid}',gate['artifact_paths'],gate['trusted_hashes'],language='python',payload_kind='statement')
  path=HERE/name
  result[str(path.relative_to(SOLVER))]=sha(path.read_bytes())
 for pid in IDS:
  authorize_before_open(f'leetcode:{pid}',gate['artifact_paths'],gate['trusted_hashes'],language='python',payload_kind='statement')
  path=HERE/'semantics'/f'{pid}.json'
  result[str(path.relative_to(SOLVER))]=sha(path.read_bytes())
 return result

def prepare(a):
 from catalogue.boundary_policy import authorize_before_open
 gate_raw=a.boundary_config.read_bytes()
 if sha(gate_raw)!=a.boundary_config_sha256:raise ValueError('operator boundary config identity')
 gate=json.loads(gate_raw);public=a.public_contracts.resolve()
 for pid in IDS:
  authorize_before_open(f'leetcode:{pid}',gate['artifact_paths'],gate['trusted_hashes'],language='python',payload_kind='statement')
 manifest_raw=(public/'manifest.json').read_bytes();manifest=json.loads(manifest_raw)
 for pid in IDS:authorize_before_open(f'leetcode:{pid}',gate['artifact_paths'],gate['trusted_hashes'],language='python',payload_kind='statement')
 assignment_raw=(public/'assignment.public-safe.json').read_bytes();assignment=json.loads(assignment_raw)
 if sorted(x['id']for x in assignment['problems'])!=list(IDS):raise ValueError('source assignment identity')
 if manifest.get('input_commit')!='fe357a4b2c226bd9149cb45cb61314c46ad89f0b' or manifest.get('first_wave_ids')!=list(IDS):raise ValueError('owner source commit/wave identity')
 evidence=manifest['official_evidence']
 for pid in IDS:authorize_before_open(f'leetcode:{pid}',gate['artifact_paths'],gate['trusted_hashes'],language='python',payload_kind='statement')
 extracted=Path(evidence['private_path']).read_bytes()
 if sha(extracted)!=evidence['sha256'] or evidence['raw_html_sha256']is not None:raise ValueError('official extraction identity or false raw-HTML claim')
 cases=build();sources={};payloads={'official-pages.web-extract.txt':extracted};auth=[]
 for pid in IDS:
  for language,suffix in [('javascript','js'),('python','py')]:
   auth.append(authorize_before_open(f'leetcode:{pid}',gate['artifact_paths'],gate['trusted_hashes'],language=language))
   selected=[r for r in manifest['source_inventory']if r['id']==pid and r['language']==language]
   if len(selected)!=1:raise ValueError('exact unique source inventory')
   row=selected[0];name=f'{language}/{pid}.{suffix}'
   if row['path']!=name or row['semantics_path']!=f'semantics/{pid}.json':raise ValueError('identity-bound source locator')
   path=public/name
   authorize_before_open(f'leetcode:{pid}',gate['artifact_paths'],gate['trusted_hashes'],language=language)
   data=path.read_bytes()
   authorize_before_open(f'leetcode:{pid}',gate['artifact_paths'],gate['trusted_hashes'],language=language,payload_kind='statement')
   sem=(public/row['semantics_path']).read_bytes()
   if sha(data)!=row['sha256']or sha(sem)!=row['semantics_sha256']:raise ValueError('source/semantics drift')
   sources[f'{language}:{pid}']={'id':pid,'language':language,'path':f'{pid}.{suffix}','sha256':sha(data),'bytes':len(data),'semantics_sha256':sha(sem),'original_path':str(path)};payloads[f'{pid}.{suffix}']=data;payloads[f'semantics/{pid}.json']=sem
   sources[f'{language}:{pid}']['owner_input_commit']=manifest['input_commit'];sources[f'{language}:{pid}']['owner_input_repository_path']=row['repository_path']
 runtime_raw=a.javascript_runtime_contract.read_bytes();python_raw=a.python_runtime_contract.read_bytes()
 if sha(runtime_raw)!=a.runtime_reference_sha256 or sha(python_raw)!=a.runtime_reference_sha256:raise ValueError('operator runtime-reference hash mismatch')
 runtime_ref=json.loads(runtime_raw);python_ref=json.loads(python_raw)
 files=[{'path':'assignment.public-safe.json','sha256':sha(assignment_raw)}]
 c={'schema':'gamma.public-domain.foundation-medium32-wave1-freeze.v1','ids':list(IDS),'languages':['javascript','python'],'sources':sources,'code_sha256':pins(),'statement_sha256':statement_pins(gate),
 'official_extraction_sha256':sha(extracted),'official_extraction_kind':'web-tool text, not raw HTML','public_contract_manifest_sha256':sha(manifest_raw),'public_contract_files':files,'public_contract_directory':str(public),
 'boundary_config_sha256':sha(gate_raw),'boundary_config_path':str(a.boundary_config.resolve()),'source_acquisition_receipts':auth,
 'cases_sha256':sha(encoded(cases)),'case_counts':{str(k):len(v)for k,v in cases.items()},'node_runtime':runtime_ref['node_runtime'],'python_runtime_sha256':python_ref['python_runtime_sha256'],
 'runtime_reference_ancestry':{'metadata_source_sha256':sha(runtime_raw),'inherited_javascript_reference_sha256':runtime_ref['javascript_runtime_reference_sha256'],'inherited_python_reference_sha256':python_ref['python_runtime_reference_sha256']},'javascript_runtime_reference_sha256':sha(a.javascript_runtime_contract.read_bytes()),'python_runtime_reference_sha256':sha(a.python_runtime_contract.read_bytes()),
 'limits':LIMITS,'batch_cases':32,'batch_input_bytes':1800000,'batch_observation_bytes':3900000,'outer_wall_cap_seconds':900,'source_entry':'solve','effect_policy':'read-only args; fresh mutable returns; no result-to-input aliases',
 'result_policy':'typed exact scalars; ID1471 duplicate-sensitive multiset, arbitrary order; local read-only/fresh-return effects','authority':'prospective reviewed pinned public statement snapshots plus explicitly local interface/effects/resource policy',
 'catalogue_population':4081,'permitted_source_population':2872,'historical_m1_population':500,'protected_access':False,'historical_receipts_changed':False,'automatic_promotion':False,'execution_approval':'separate independent root-authorized review required','status':'awaiting_review','supersedes_freeze_sha256':a.supersedes_freeze_sha256}
 a.output.mkdir(parents=True,exist_ok=False)
 for name,data in payloads.items():
  target=a.output/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 write(a.output/'public-cases.json',cases);write(a.output/'contract.json',c)
 return {'status':'awaiting_review','freeze_sha256':sha(encoded(c)),'cases_per_language':sum(len(x)for x in cases.values()),'sources':len(sources)}
def load_freeze(path):
 raw=(path/'contract.json').read_bytes();c=json.loads(raw)
 if c['schema']!='gamma.public-domain.foundation-medium32-wave1-freeze.v1' or c['ids']!=list(IDS)or c['code_sha256']!=pins() or c['limits']!=LIMITS or c['batch_cases']!=32 or c['batch_input_bytes']!=1800000 or c.get('batch_observation_bytes')!=3900000 or c.get('outer_wall_cap_seconds')!=900 or c['protected_access']is not False:raise ValueError('foundation freeze drift')
 from catalogue.boundary_policy import authorize_before_open
 gate_raw=Path(c['boundary_config_path']).read_bytes()
 if sha(gate_raw)!=c['boundary_config_sha256']:raise ValueError('boundary config drift')
 gate=json.loads(gate_raw)
 if c.get('statement_sha256')!=statement_pins(gate):raise ValueError('gated statement metadata drift')
 if c.get('languages')!=['javascript','python']or set(c.get('sources',{}))!={f'{lang}:{pid}'for lang in c['languages']for pid in IDS}:raise ValueError('exact source-language denominator required')
 for pid in IDS:
  for language in c['languages']:authorize_before_open(f'leetcode:{pid}',gate['artifact_paths'],gate['trusted_hashes'],language=language)
 public=Path(c['public_contract_directory'])
 for pid in IDS:authorize_before_open(f'leetcode:{pid}',gate['artifact_paths'],gate['trusted_hashes'],language='python',payload_kind='statement')
 if sha((public/'manifest.json').read_bytes())!=c['public_contract_manifest_sha256']:raise ValueError('official contract manifest drift')
 for row in c['public_contract_files']:
  if row['path']!='assignment.public-safe.json':raise ValueError('unexpected combined public contract locator')
  for pid in IDS:authorize_before_open(f'leetcode:{pid}',gate['artifact_paths'],gate['trusted_hashes'],language='python',payload_kind='statement')
  if sha((public/row['path']).read_bytes())!=row['sha256']:raise ValueError('official clause or authored case drift')
 for pid in IDS:authorize_before_open(f'leetcode:{pid}',gate['artifact_paths'],gate['trusted_hashes'],language='python',payload_kind='statement')
 if sha((path/'official-pages.web-extract.txt').read_bytes())!=c['official_extraction_sha256']:raise ValueError('official extraction drift')
 for pid in IDS:authorize_before_open(f'leetcode:{pid}',gate['artifact_paths'],gate['trusted_hashes'],language='python',payload_kind='statement')
 cases_raw=(path/'public-cases.json').read_bytes()
 if sha(cases_raw)!=c['cases_sha256']:raise ValueError('public case hash changed')
 cases=json.loads(cases_raw);regenerated=build(Path(c['public_contract_directory']))
 if not exact(cases,{str(k):v for k,v in regenerated.items()}):raise ValueError('public oracle/case regeneration mismatch')
 values={}
 for key,row in c['sources'].items():
  pid,language=row['id'],row['language']
  if pid not in IDS or language not in ('javascript','python')or key!=f'{language}:{pid}'or row['path']!=f"{pid}.{'js'if language=='javascript'else'py'}":raise ValueError('frozen source identity-bound locator')
  authorize_before_open(f'leetcode:{pid}',gate['artifact_paths'],gate['trusted_hashes'],language=language)
  data=(path/row['path']).read_bytes()
  if sha(data)!=row['sha256']or len(data)!=row['bytes']:raise ValueError('candidate frozen bytes changed')
  authorize_before_open(f'leetcode:{pid}',gate['artifact_paths'],gate['trusted_hashes'],language=language,payload_kind='statement')
  semraw=(path/f'semantics/{pid}.json').read_bytes()
  if sha(semraw)!=row['semantics_sha256']:raise ValueError('frozen rich semantics sidecar drift')
  values[key]=data
 return c,cases,values

def review_check(craw,review):
 required={'official_problem_contracts','independent_oracle','local_effects','sixteen_exact_sources','source_complexity','boundary_policy','bounded_batching'}
 if review.get('schema')!='gamma.public-domain.foundation-medium32-wave1-review.v1' or review.get('freeze_sha256')!=sha(craw)or review.get('independent_review')is not True or review.get('root_execution_authorized')is not True or not required<=set(review.get('reviewed',[]))or not review.get('reviewer'):raise ValueError('independent reviewed freeze and root authority required')
def parse(raw,n):
 def pairs(items):
  result={}
  for key,value in items:
   if key in result:raise ValueError('duplicate output key')
   result[key]=value
  return result
 records=[json.loads(line,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite output')))for line in raw.splitlines()]
 if len(records)!=n+1 or (type(records[-1])is not dict or records[-1]!={'done':n}or type(records[-1].get('done'))is not int)or any(type(r)is not dict or type(r.get('i'))is not int or r['i']!=i for i,r in enumerate(records[:-1])):raise ValueError('complete indexed output protocol required')
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
def observation_bound(case):
 # All current domains use ASCII strings and safe integer scalars. Candidate
 # records contain args twice, expected-size result, type/alias protocol. This
 # is a conservative packing bound, NOT an expected output sent to candidates.
 return 2*len(encoded(case['args']))+len(encoded(case['expected']))+1024

def batches(cases):
 offset=0;batch=[];bound=1024
 for case in cases:
  single=len(encoded(make_packet([case])))
  cost=observation_bound(case)
  if single>1800000 or cost+1024>3900000:raise ValueError('single official-domain case exceeds explicit transport cap')
  trial=batch+[case]
  if batch and (len(trial)>32 or len(encoded(make_packet(trial)))>1800000 or bound+cost>3900000):
   yield offset,batch;offset+=len(batch);batch=[];bound=1024
  batch.append(case);bound+=cost
 if batch:yield offset,batch

def run(a):
 if type(a.max_wall)is not int or not 1<=a.max_wall<=900:raise ValueError('outer wall budget must remain <=900 seconds')
 c,cases,sources=load_freeze(a.freeze);craw=(a.freeze/'contract.json').read_bytes();reviewraw=a.review.read_bytes();review_check(craw,json.loads(reviewraw))
 if sha(Path('/usr/bin/python3').read_bytes())!=c['python_runtime_sha256']:raise ValueError('Python runtime drift')
 actual=pinned_runtime.freeze_runtime(a.node_path)
 if actual!=c['node_runtime']:raise ValueError('approved Node runtime drift')
 a.output.mkdir(parents=True,exist_ok=False)
 rc={'schema':'gamma.public-domain.foundation-medium32-wave1-run.v1','freeze':str(a.freeze),'freeze_sha256':sha(craw),'review_sha256':sha(reviewraw),'runtime':actual,'python_runtime_sha256':c['python_runtime_sha256'],'limits':LIMITS,'max_wall_seconds':a.max_wall,'protected_access':False}
 write(a.output/'contract.json',rc);(a.output/'review.json').write_bytes(reviewraw)
 report={'schema':rc['schema'],'contract_sha256':sha(encoded(rc)),'status':'running','rows':[],'candidate_executions':0,'passed_source_language_pairs':0,'checks_passed':0,'protected_access':False,'automatic_promotion':False,'historical_m1_qualified':False};start=time.monotonic()
 try:
  for language in c['languages']:
   for pid in IDS:
    row={'id':pid,'language':language,'cases':len(cases[str(pid)]),'source_sha256':c['sources'][f'{language}:{pid}']['sha256'],'calls':[],'failures':[],'checks_passed':0,'passed':False};report['rows'].append(row)
    for offset,batch in batches(cases[str(pid)]):
     if time.monotonic()-start>a.max_wall:raise TimeoutError('foundation outer wall budget')
     packet=make_packet(batch)
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
 for name in ('public-contracts','boundary-config','javascript-runtime-contract','python-runtime-contract','output'):x.add_argument('--'+name,type=Path,required=True)
 x.add_argument('--boundary-config-sha256',required=True)
 x.add_argument('--runtime-reference-sha256',required=True)
 x.add_argument('--supersedes-freeze-sha256')
 x=sub.add_parser('run')
 for name in ('freeze','review','output','node-path'):x.add_argument('--'+name,type=Path,required=True)
 x.add_argument('--max-wall',type=int,default=900);a=p.parse_args();print(json.dumps(prepare(a)if a.command=='prepare'else run(a)))
