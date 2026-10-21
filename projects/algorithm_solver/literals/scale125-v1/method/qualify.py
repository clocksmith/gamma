import json,hashlib,time,sys
from pathlib import Path
D=Path(__file__).resolve().parent;L=Path('/home/x/deco/gamma/output/literal-joint-v1/projects/algorithm_solver/literals');sys.path[:0]=[str(L.parent),str(L)]
from algsolve.judge import sandbox
from algsolve.judge.judge import FunctionalTest,_matches
from verify_execution import strict_object
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def exact(a,b):
 if isinstance(a,bool) or isinstance(b,bool):return type(a)==type(b) and a==b
 if isinstance(a,(int,float)) and isinstance(b,(int,float)):return a==b
 if type(a)!=type(b):return False
 if isinstance(a,list):return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
 if isinstance(a,dict):return a.keys()==b.keys() and all(exact(a[k],b[k]) for k in a)
 return a==b
def normalize(x):
 if isinstance(x,list):return [normalize(v) for v in x]
 if isinstance(x,dict):
  if x=={'__list_node__':[]} or x=={'__tree_node__':[]}:return None
  if set(x)=={'__gamma_bigint_v1__'}:return int(x['__gamma_bigint_v1__'])
  return {k:normalize(v) for k,v in x.items()}
 return x
def judge(case,rec,prior=None):
 observed={k:rec.get(k) for k in ['result','result_type','args_before','args_after','alias_edges','error']}
 expected=normalize(case['expected']);actual=normalize(rec.get('result'))
 valid=not rec.get('error') and _matches(FunctionalTest(args=case['args'],expected=expected,compare=case.get('compare','return')),{'result':actual})
 if isinstance(expected,int) and not isinstance(expected,bool) and abs(expected)>2**53-1:valid=valid and rec.get('result_type')=='bigint'
 return valid and (prior is None or exact(observed,prior)),observed
if __name__=='__main__':
 c=json.loads((D/'contract.json').read_text());m=json.loads((D/'generated/manifest.json').read_text());assert m['contract_sha256']==sha((D/'contract.json').read_bytes())
 for p,h in c['code_hashes'].items():assert sha(Path(p).read_bytes())==h
 q=D/'qualification';q.mkdir();(q/'observations').mkdir();rows=[];start=time.monotonic();harness=(D/'harness.cjs').read_text();stopped=False
 for spec in c['rows']:
  tests=json.loads((D/spec['test_file']).read_text());assert sha((D/spec['test_file']).read_bytes())==spec['test_sha256'];prior=None;original_ok=False
  variants=sorted((r for r in m['rows'] if r['id']==spec['id']),key=lambda r:(r['variant']!='original',r['variant']))
  for r in variants:
   if time.monotonic()-start>c['limits']['qualification_seconds']:stopped=True;break
   source=Path(r['file']).read_text();assert sha(source.encode())==r['sha256'];passed=0;failures=[];calls=[];obs=[]
   for off in range(0,len(tests),16):
    batch=tests[off:off+16];payload={'entry':r['entry'],'calls':[{'args':t['args']} for t in batch]}
    result=sandbox.run(['/usr/bin/node','--jitless','--single-threaded','--max-old-space-size=64','harness.cjs'],files={'program.js':source,'inputs.json':json.dumps(payload),'harness.cjs':harness},limits=sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=4*1024**2))
    stem=f"{r['id']}-{r['variant']}-{off}"
    for ext,data in [('stdout',result.stdout),('stderr',result.stderr)]:(q/'observations'/f'{stem}.{ext}').write_bytes(data)
    calls.append({'stem':stem,'exit_code':result.exit_code,'timed_out':result.timed_out,'wall_seconds':result.wall_seconds,'stdout_sha256':sha(result.stdout),'stderr_sha256':sha(result.stderr)})
    try:
     assert result.ok,'sandbox failure';records=[json.loads(line,object_pairs_hook=strict_object,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x))) for line in result.stdout.splitlines()];assert len(records)==len(batch)+1 and records[-1]=={'done':len(batch)}
     for k,rec in enumerate(records[:-1]):
      assert type(rec.get('i')) is int and rec['i']==k
      valid,o=judge(batch[k],rec,None if r['variant']=='original' else prior[off+k]);obs.append(o);passed+=bool(valid)
      if not valid:failures.append({'case':off+k,'reason':'oracle_or_original_effect_alias_numeric_parity','error':rec.get('error')})
    except Exception as e:
     failures.append({'offset':off,'reason':'execution_or_protocol','detail':str(e)});obs.extend([None]*(off+len(batch)-len(obs)))
   if r['variant']=='original':prior=obs;original_ok=passed==len(tests) and not failures
   rows.append({**r,'passed':original_ok and passed==len(tests) and not failures,'checks_passed':passed,'checks_total':len(tests),'failures':failures,'calls':calls})
   write(q/'checkpoint.json',{'rows':rows,'elapsed_seconds':time.monotonic()-start})
  print(json.dumps({'id':spec['id'],'sources':len(variants),'passed':sum(r['passed'] for r in rows if r['id']==spec['id'])}),flush=True)
  if stopped:break
 report={'rows':rows,'new_problem_denominator':25,'total_problem_denominator':125,'qualified_new_problems':len({r['id'] for r in rows if r['passed']}),'source_count':len(rows),'passed_sources':sum(r['passed'] for r in rows),'distinct_cases':sum(r['cases'] for r in c['rows']),'checks_passed':sum(r['checks_passed'] for r in rows),'checks_total':sum(r['checks_total'] for r in rows),'elapsed_seconds':time.monotonic()-start,'budget_stopped':stopped,'contract_sha256':sha((D/'contract.json').read_bytes()),'generated_manifest_sha256':sha((D/'generated/manifest.json').read_bytes())}
 write(q/'report.json',report);print(json.dumps({k:v for k,v in report.items() if k!='rows'}))
