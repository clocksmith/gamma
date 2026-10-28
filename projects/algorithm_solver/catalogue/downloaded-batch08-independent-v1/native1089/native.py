"""Explicit native 1089 in-place/void evidence, separate from pure solve lane."""
import argparse,json,sys,platform,os,traceback
from pathlib import Path
from dataclasses import asdict
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent))
import qualify as q
import oracles as o
from algsolve.judge import sandbox
ROOT=q.ROOT

def inputs(statements):return q.load_cases(statements)[1089]
def source_rows(repairs):return [r for r in q.source_rows(repairs)if r['problem_id']==1089]
def artifacts(repairs,primary):
 paths=list(HERE.glob('*.py'))+[HERE/'harness.cjs',HERE.parent/'qualify.py',HERE.parent/'oracles.py',HERE.parent/'cases.py',HERE.parent/'contracts.json',primary,ROOT/'projects/algorithm_solver/algsolve/judge/sandbox.py']+[ROOT/r['path']for r in source_rows(repairs)]
 return{str(p.relative_to(ROOT)):q.sha(p.read_bytes())for p in sorted(set(paths))}
def jobs(values):
 for language,entry in [('python','class'),('javascript','class'),('javascript','export')]:
  for b,indices in enumerate(q.batches(1089,values)):yield language,entry,b,indices

def judge(language,values,indices,metadata,stdout):
 if metadata['exit_code']!=0 or metadata['timed_out']or metadata['output_limit_exceeded']:return[{'case':i,'reason':'sandbox_process_failure'}for i in indices]
 try:
  def pairs(values):
   out={}
   for k,v in values:
    if k in out:raise ValueError('duplicate key')
    out[k]=v
   return out
  rows=[json.loads(line,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in()).throw(ValueError(x)))for line in stdout.decode().splitlines()]
  if len(rows)!=len(indices)+1 or set(rows[-1])!={'done'}or type(rows[-1]['done'])is not int or rows[-1]['done']!=len(indices):raise ValueError('incomplete stream')
  for i,row in enumerate(rows[:-1]):
   if type(row)is not dict or type(row.get('i'))is not int or row['i']!=i:raise ValueError('index')
   if set(row)!=({'i','error'}if'error'in row else{'i','result','result_type','args_before','args_after','same_input_object'}):raise ValueError('shape')
 except(ValueError,TypeError,UnicodeError,KeyError):return[{'case':i,'reason':'observation_protocol'}for i in indices]
 failures=[]
 for index,row in zip(indices,rows[:-1]):
  case=values[index];reasons=[]
  if'error'in row:reasons=['candidate_error']
  else:
   if row['result_type']!=('NoneType'if language=='python'else'undefined')or row['result']is not None:reasons.append('native_void_return')
   if not o.exact(row['args_before'],case['args']):reasons.append('input_snapshot')
   if not o.exact(row['args_after'],[case['expected']]):reasons.append('native_in_place_result')
   if row['same_input_object']is not True:reasons.append('native_input_object_identity')
  if reasons:failures.append({'case':index,'reasons':reasons})
 return failures

def freeze(a):
 values=inputs(a.statements);raw=a.primary_freeze.read_bytes();primary=json.loads(raw);assert primary['repair_run']==a.repairs;assert q.artifacts(a.repairs)==primary['artifact_hashes'];profile=q.runtime();assert profile==primary['runtime'];rows=source_rows(a.repairs)
 contract={'schema':'gamma.batch08.native1089.freeze.v1','repair_run':a.repairs,'primary_freeze_path':str(a.primary_freeze.relative_to(ROOT)),'primary_freeze_sha256':q.sha(raw),'artifact_hashes':artifacts(a.repairs,a.primary_freeze),'runtime':profile,'limits':asdict(q.LIMITS),'argv':q.ARGV,'source_rows':rows,'cases_sha256':q.sha(q.encoded(values)),'jobs':list(jobs(values)),'host_memory':q.memory(),'official_contract':{'identity':1089,'argument':'arr:integer[]','mutation':'modify original array to duplicate zeros, truncate to original length','return':'PythonNone / JavaScriptundefined','javascript_entries':['Solution.duplicateZeros','module.duplicateZeros'],'python_entries':['Solution.duplicateZeros']},'expected_results_enter_sandbox':False,'active_promotion':False}
 q.write(a.freeze,contract);print('FROZEN',q.sha(a.freeze.read_bytes()),flush=True)

def run(a):
 raw=a.freeze.read_bytes();assert q.sha(raw)==a.freeze_sha256;f=json.loads(raw);primary=ROOT/f['primary_freeze_path'];assert q.sha(primary.read_bytes())==f['primary_freeze_sha256'];assert artifacts(f['repair_run'],primary)==f['artifact_hashes'];assert q.runtime()==f['runtime'];values=inputs(a.statements);assert q.sha(q.encoded(values))==f['cases_sha256'];assert list(jobs(values))==[tuple(v)for v in f['jobs']];a.output.mkdir(exist_ok=False)
 q.write(a.output/'run-identity.json',{'freeze_sha256':q.sha(raw),'host':platform.node(),'host_memory':q.memory(),'artifact_hashes':f['artifact_hashes'],'max_concurrent_candidate_interpreters':1});sources={r['language']:r for r in f['source_rows']};outcomes={}
 for language,entry,b,indices in jobs(values):
  source=sources[language];extension,harness=('py','harness.py')if language=='python'else('js','harness.cjs');packet={'entry':entry,'calls':[{'args':values[i]['args']}for i in indices]};stem=f'{language}-{entry}-{b:03d}';q.write(a.output/(stem+'.start.json'),{'language':language,'entry':entry,'indices':indices,'inputs_sha256':q.sha(q.encoded(packet)),'source_sha256':source['sha256']})
  try:result=sandbox.run(q.ARGV[language],files={'program.'+extension:(ROOT/source['path']).read_bytes(),harness:(HERE/harness).read_bytes(),'inputs.json':q.encoded(packet)},limits=q.LIMITS)
  except BaseException as e:q.write(a.output/(stem+'.setup-failure.json'),{'type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()});raise
  metadata=asdict(result)
  for stream in('stdout','stderr'):
   payload=metadata.pop(stream)
   with(a.output/(stem+'.'+stream)).open('xb')as file:file.write(payload);file.flush();os.fsync(file.fileno())
   metadata[stream+'_sha256']=q.sha(payload)
  q.write(a.output/(stem+'.result.json'),metadata);key=language+'-'+entry;row=outcomes.setdefault(key,{'language':language,'entry':entry,'source_sha256':source['sha256'],'attempted_calls':0,'failures':[]});row['attempted_calls']+=len(indices);row['failures']+=judge(language,values,indices,metadata,result.stdout)
 for row in outcomes.values():row['passed']=not row['failures']
 report={'schema':'gamma.batch08.native1089.report.v1','freeze_sha256':q.sha(raw),'outcomes':list(outcomes.values()),'all_entries_passed':all(r['passed']for r in outcomes.values()),'active_promotion':False};q.write(a.output/'report.json',report);print(json.dumps({k:v for k,v in report.items()if k!='outcomes'}),flush=True)

def verify(a):
 raw=a.freeze.read_bytes();f=json.loads(raw);primary=ROOT/f['primary_freeze_path'];assert artifacts(f['repair_run'],primary)==f['artifact_hashes'];assert q.sha(primary.read_bytes())==f['primary_freeze_sha256'];values=inputs(a.statements);assert q.sha(q.encoded(values))==f['cases_sha256'];assert list(jobs(values))==[tuple(v)for v in f['jobs']];sources={r['language']:r for r in f['source_rows']};outcomes={}
 identity=json.loads((a.output/'run-identity.json').read_bytes());assert identity['freeze_sha256']==q.sha(raw)and identity['artifact_hashes']==f['artifact_hashes']
 for language,entry,b,indices in jobs(values):
  stem=f'{language}-{entry}-{b:03d}';source=sources[language];packet={'entry':entry,'calls':[{'args':values[i]['args']}for i in indices]};assert json.loads((a.output/(stem+'.start.json')).read_bytes())=={'language':language,'entry':entry,'indices':indices,'inputs_sha256':q.sha(q.encoded(packet)),'source_sha256':source['sha256']};metadata=json.loads((a.output/(stem+'.result.json')).read_bytes())
  for stream in('stdout','stderr'):assert q.sha((a.output/(stem+'.'+stream)).read_bytes())==metadata[stream+'_sha256']
  row=outcomes.setdefault(language+'-'+entry,{'language':language,'entry':entry,'source_sha256':source['sha256'],'attempted_calls':0,'failures':[]});row['attempted_calls']+=len(indices);row['failures']+=judge(language,values,indices,metadata,(a.output/(stem+'.stdout')).read_bytes())
 for row in outcomes.values():row['passed']=not row['failures']
 report={'schema':'gamma.batch08.native1089.report.v1','freeze_sha256':q.sha(raw),'outcomes':list(outcomes.values()),'all_entries_passed':all(r['passed']for r in outcomes.values()),'active_promotion':False};assert report==json.loads((a.output/'report.json').read_bytes());hashes={p.name:q.sha(p.read_bytes())for p in sorted(a.output.iterdir())if p.is_file()and p.name!='replay.json'}
 return{'schema':'gamma.batch08.native1089.replay.v1','freeze_sha256':q.sha(raw),'all_observations_match':True,'raw_artifact_hashes':hashes,'entries_passed':sum(r['passed']for r in outcomes.values()),'entries_failed':sum(not r['passed']for r in outcomes.values()),'calls_replayed':sum(r['attempted_calls']for r in outcomes.values())}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('op',choices=['freeze','run','verify']);p.add_argument('--statements',type=Path,required=True);p.add_argument('--freeze',type=Path,required=True);p.add_argument('--primary-freeze',type=Path);p.add_argument('--freeze-sha256');p.add_argument('--output',type=Path);p.add_argument('--repairs',action='store_true');a=p.parse_args()
 if a.op=='freeze':freeze(a)
 elif a.op=='run':run(a)
 else:r=verify(a);q.write(a.output/'replay.json',r);print(json.dumps({k:v for k,v in r.items()if k!='raw_artifact_hashes'}))
