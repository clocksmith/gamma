import hashlib,json,sys,time
from pathlib import Path
D=Path(__file__).resolve().parent;L=Path('/home/x/deco/gamma/output/literal-joint-v1/projects/algorithm_solver/literals');sys.path.insert(0,str(L.parent))
from algsolve.judge import sandbox
sha=lambda b:hashlib.sha256(b).hexdigest()
def exact(a,b):
 if isinstance(a,bool) or isinstance(b,bool):return type(a) is type(b) and a==b
 if isinstance(a,(int,float)) and isinstance(b,(int,float)):return a==b
 if type(a) is not type(b):return False
 if isinstance(a,list):return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
 if isinstance(a,dict):return a.keys()==b.keys() and all(exact(a[k],b[k]) for k in a)
 return a==b
c=json.loads((D/'contract.json').read_text())
for group in ['code_hashes','inputs']:
 for p,h in c[group].items():assert sha(Path(p).read_bytes())==h
out=D/'qualification';out.mkdir();(out/'observations').mkdir();rows=[];began=time.monotonic();harness=(L/'row-v1/harness.cjs').read_text()
for row in c['rows']:
 raw=Path(row['test_file']).read_bytes();assert sha(raw)==row['test_sha256'];cases=json.loads(raw);original=[]
 for spec in row['sources']:
  source=Path(spec['file']).read_text();assert sha(source.encode())==spec['sha256'];passed=0;failures=[];calls=[];observations=[]
  for offset in range(0,len(cases),c['limits']['batch_cases']):
   assert time.monotonic()-began<c['limits']['qualification_seconds']
   batch=cases[offset:offset+c['limits']['batch_cases']]
   result=sandbox.run(['/usr/bin/node','--jitless','--single-threaded','--max-old-space-size=64','harness.cjs'],files={'program.js':source,'inputs.json':json.dumps({'entry':'solve','calls':[{'args':t['args']} for t in batch]}),'harness.cjs':harness},limits=sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=4*1024**2))
   stem=f"{row['id']}-{spec['variant']}-{offset}"
   for ext,data in [('stdout',result.stdout),('stderr',result.stderr)]:(out/'observations'/(stem+'.'+ext)).write_bytes(data)
   calls.append({'stem':stem,'exit_code':result.exit_code,'timed_out':result.timed_out,'wall_seconds':result.wall_seconds,'stdout_sha256':sha(result.stdout),'stderr_sha256':sha(result.stderr)})
   assert result.ok,'sandbox failure; receipts retained'
   records=[json.loads(x) for x in result.stdout.splitlines()];assert len(records)==len(batch)+1 and records[-1]=={'done':len(batch)}
   for k,rec in enumerate(records[:-1]):
    assert type(rec.get('i')) is int and rec['i']==k
    expected_type='object' if isinstance(batch[k]['expected'],list) else 'number'
    valid=not rec.get('error') and rec.get('result_type')==expected_type and exact(rec.get('result'),batch[k]['expected']) and exact(rec.get('args_before'),batch[k]['args']) and exact(rec.get('args_after'),batch[k]['args']) and rec.get('alias_edges')==[]
    if spec['variant']!='original':valid=valid and exact(rec.get('result'),original[offset+k])
    observations.append(rec.get('result'));passed+=bool(valid)
    if not valid:failures.append(offset+k)
  if spec['variant']=='original':original=observations
  rows.append({**spec,'checks_passed':passed,'checks_total':len(cases),'failures':failures,'calls':calls})
  (out/'checkpoint.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps({'id':row['id'],'variant':spec['variant'],'passed':passed,'total':len(cases),'failures':failures[:10]}),flush=True)
  assert passed==len(cases) and not failures,'fail closed; no measurement'
report={'schema':'gamma.matrix-kernels.qualification.v1','passed':True,'rows':rows,'checks_passed':sum(r['checks_passed'] for r in rows),'distinct_cases':sum(r['cases'] for r in c['rows']),'elapsed_seconds':time.monotonic()-began,'contract_sha256':sha((D/'contract.json').read_bytes()),'verification_code_sha256':sha(Path(__file__).read_bytes()),'harness_sha256':sha(harness.encode())}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='rows'}),flush=True)
