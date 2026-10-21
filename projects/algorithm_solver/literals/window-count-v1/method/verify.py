import hashlib,importlib.util,json,sys,time
from pathlib import Path
D=Path(__file__).resolve().parent;R=Path('/home/x/deco/gamma/output/literal-joint-v1');L=R/'projects/algorithm_solver/literals'
sys.path.insert(0,str(L.parent))
from algsolve.judge import sandbox
sha=lambda b:hashlib.sha256(b).hexdigest()
def exact(a,b):
 if isinstance(a,str) and isinstance(b,str):return a.encode('utf-16-le','surrogatepass')==b.encode('utf-16-le','surrogatepass')
 if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
 return type(a) is type(b) and a==b
c=json.loads((D/'contract.json').read_text());tests=json.loads((D/'cases.json').read_text());assert sha((D/'cases.json').read_bytes())==c['cases_sha256']
for p,h in c['code_hashes'].items():assert sha(Path(p).read_bytes())==h
for p,h in c['inputs'].items():assert sha(Path(p).read_bytes())==h
out=D/'qualification';out.mkdir();(out/'observations').mkdir()
harness=(L/'row-v1/harness.cjs').read_text();began=time.monotonic();rows=[];original=[]
for spec in c['sources']:
 source=Path(spec['file']).read_text();assert sha(source.encode())==spec['sha256'];passed=0;failures=[];calls=[];observations=[]
 for offset in range(0,len(tests),c['limits']['batch_cases']):
  assert time.monotonic()-began<c['limits']['qualification_seconds']
  batch=tests[offset:offset+c['limits']['batch_cases']]
  result=sandbox.run(['/usr/bin/node','--jitless','--single-threaded','--max-old-space-size=64','harness.cjs'],files={'program.js':source,'inputs.json':json.dumps({'entry':'solve','calls':[{'args':t['args']} for t in batch]}),'harness.cjs':harness},limits=sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=4*1024**2))
  stem=spec['variant']+'-'+str(offset)
  for ext,data in [('stdout',result.stdout),('stderr',result.stderr)]:(out/'observations'/(stem+'.'+ext)).write_bytes(data)
  calls.append({'stem':stem,'exit_code':result.exit_code,'timed_out':result.timed_out,'wall_seconds':result.wall_seconds,'stdout_sha256':sha(result.stdout),'stderr_sha256':sha(result.stderr)})
  assert result.ok,'sandbox failure; retain receipts'
  records=[json.loads(x) for x in result.stdout.splitlines()];assert len(records)==len(batch)+1 and records[-1]=={'done':len(batch)}
  for k,rec in enumerate(records[:-1]):
   assert type(rec.get('i')) is int and rec['i']==k
   valid=(not rec.get('error') and rec.get('result_type')=='string' and exact(rec.get('result'),batch[k]['expected']) and exact(rec.get('args_before'),batch[k]['args']) and exact(rec.get('args_after'),batch[k]['args']) and rec.get('alias_edges')==[])
   if spec['variant']!='original':valid=valid and exact(rec.get('result'),original[offset+k])
   observations.append(rec.get('result'));passed+=bool(valid)
   if not valid:failures.append(offset+k)
 row={**spec,'checks_passed':passed,'checks_total':len(tests),'failures':failures,'calls':calls};rows.append(row)
 if spec['variant']=='original':original=observations
 (out/'checkpoint.json').write_text(json.dumps(rows,indent=2)+'\n')
 print(json.dumps({'variant':spec['variant'],'checks_passed':passed,'checks_total':len(tests),'failures':failures[:10]}),flush=True)
 assert passed==len(tests) and not failures,'qualification failed; no candidate promotion'
report={'schema':'gamma.window-count.qualification.v1','passed':True,'rows':rows,'distinct_cases':len(tests),'checks_passed':sum(x['checks_passed'] for x in rows),'elapsed_seconds':time.monotonic()-began,'contract_sha256':sha((D/'contract.json').read_bytes()),'verification_code_sha256':sha(Path(__file__).read_bytes()),'harness_sha256':sha(harness.encode()),'oracle':'Independent host Python brute-force UTF-16 oracle; expected outputs excluded from native sandbox; two stress expectations analytic.'}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='rows'}),flush=True)
