from pathlib import Path
from dataclasses import replace
import hashlib,json,sys,importlib.util
ROOT=Path('/home/x/deco/gamma/projects/algorithm_solver');TASK=Path('/home/x/Documents/Codex/2026-10-19/task');PACK=TASK/'js-corpus-wave-001';OUT=ROOT/'runs/js-corpus-b01-b02-review-128-v1'
sys.path[:0]=[str(ROOT),str(ROOT/'findings/js-exact-integer-transport-128-v1')]
from algsolve import validate
from algsolve.records import Problem,load_hidden_tests
from algsolve.judge import judge,sandbox
import exact_integer

def module(name):
 spec=importlib.util.spec_from_file_location(name,TASK/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
contracts=module('b01-b02-contracts');domains=module('b01-b02-domains')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def write(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def pyexecute(source,p,tests):
 payload={'entry':p.entry,'calls':[{'args':t.args,'kwargs':t.kwargs} for t in tests]}
 raw=sandbox.run_python('harness.py',files={'harness.py':judge.HARNESS_PATH.read_text(),'candidate.py':source,'calls.json':json.dumps(payload)},limits=sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=65536))
 return judge._score_functional(raw,tests),raw
manifest=json.loads((PACK/'manifest.json').read_text());assert sha(PACK/'manifest.json')=='af62e96fb59049cd782f481a0e21b71c6a2f66174035d92b18ea9d5a3ef11ae9'
for p,h in manifest['inputs_sha256'].items():assert sha(p)==h
ids=[1,9,17,23,30,33,39,45,50]
problems={p['uid']:Problem.from_dict(p) for l in (ROOT/'data/derived/problems.jsonl').read_text().splitlines() if (p:=json.loads(l))['uid'] in [f'lcd:{n}' for n in ids]}
OUT.mkdir()
source9=(ROOT/'runs/js-corpus-b01-b02-review-128-v1/0009-exact-integer-successor.js').read_text()
(OUT/'0009-exact-integer-successor.js').write_text(source9)
write(OUT/'contract.json',dict(runner_sha256=sha(__file__),contracts_sha256=sha(TASK/'b01-b02-contracts.py'),domains_sha256=sha(TASK/'b01-b02-domains.py'),helper_sha256=sha(PACK/'qualify.py'),manifest_sha256=sha(PACK/'manifest.json'),exact_transport_sha256=sha(exact_integer.__file__),exact_harness_sha256=sha(exact_integer.HARNESS),source9_sha256=sha(OUT/'0009-exact-integer-successor.js'),scope='Separate successor contracts:9 native BigInt arithmetic;23 declared nested-node input decoding;30 outer-order comparison. Six other failed full sets remain unqualified; classify all cases by published domains. No expected rewrites or production changes.',chunk_cases=1,cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,output_bytes=65536))
print('[run-contract] run_name=b01-b02-contract-review pairs_input_spec=frozen-assignment resume_from=none resume_stage=none decode=separate-reviewed-contracts eval_dataset_paths=9-assigned-problems device=cpu schedule=serial runtime_mode=cpu+linux-sandbox sweep_mode=none',flush=True)
records=[]
for n in ids:
 row=next(r for r in manifest['rows'] if r['id']==n);p=problems[f'lcd:{n}'];b=ROOT/'runs/js-corpus-wave-001'/row['batch_id'];packet=json.loads(Path(row['problem_packet']).read_text());source=source9 if n==9 else (b/f'{n:04d}-role-style.js').read_text();py=Path(row['python_source']).read_text();tests=load_hidden_tests(p);meta=row['independent_test_sets'][0];assert digest(tests)==meta['sha256']
 if n==30:assert 'any order' in packet['statement'].lower()
 dest=OUT/f'{n:04d}';dest.mkdir();results=[];quarantine=[]
 for group,rawtests in [('public',packet['public_tests']),('independent',tests)]:
  for i,test in enumerate(rawtests):
   before=digest(test);ts=contracts.prepare(p,[test]) if n in [23,30] else validate.functional_tests([test]);bad=domains.reasons(n,test['args']) if n not in [9,23,30] else []
   if bad:quarantine.append(dict(group=group,index=i,input=test['args'],expected=test['expected'],reasons=bad))
   # Invalid-domain cases retain original failure evidence. Re-execute all failing
   # chunks one case at a time to diagnose without changing oracles.
   pv,pr=pyexecute(py,p,ts)
   if n==50:
    # Ordinary floating contract must not use the exact-integer output gate.
    calls={'method':p.entry['method'],'params':p.params,'calls':[{'args':t.args,'capture_args':False} for t in ts]}
    jr=sandbox.run(['/usr/bin/node','--jitless','--max-old-space-size=64','harness.cjs'],files={'harness.cjs':(ROOT/'findings/source-corpus-js-py-128-v3/return_harness.cjs').read_text(),'candidate.cjs':source,'calls.json':json.dumps(calls)},limits=sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=65536));jv=judge._score_functional(jr,ts)
   else:jv,jr,payload=exact_integer.execute(source,p.entry['method'],p.params,ts)
   assert digest(test)==before
   rec=dict(group=group,index=i,raw_test_sha256=before,domain_reasons=bad,python=pv.to_dict(),javascript=jv.to_dict(),expected_unchanged=True)
   write(dest/f'{group}-{i:03d}-receipt.json',rec)
   if not jv.passed or not pv.passed:
    (dest/f'{group}-{i:03d}-python.jsonl').write_bytes(pr.stdout);(dest/f'{group}-{i:03d}-javascript.jsonl').write_bytes(jr.stdout)
   results.append(rec)
 valid=[r for r in results if not r['domain_reasons']];failed=[r for r in results if not r['python']['passed'] or not r['javascript']['passed']]
 record=dict(id=n,key=row['key'],source=str(OUT/'0009-exact-integer-successor.js') if n==9 else str(b/f'{n:04d}-role-style.js'),source_sha256=hashlib.sha256(source.encode()).hexdigest(),python_sha256=sha(row['python_source']),packet_sha256=sha(row['problem_packet']),independent_total=len(tests),public_total=len(packet['public_tests']),qualified=n in [9,23,30] and not failed,valid_domain_passed=all(r['python']['passed'] and r['javascript']['passed'] for r in valid),valid_independent=sum(r['group']=='independent' for r in valid),quarantined_independent=sum(r['group']=='independent' for r in quarantine),all_failures_outside_domain=all(r['domain_reasons'] for r in failed),results=results)
 write(dest/'quarantine.json',quarantine);write(dest/'review.json',record);records.append(record)
 print(n,'qualified',record['qualified'],'valid',record['valid_independent'],'quarantined',record['quarantined_independent'],'valid_pass',record['valid_domain_passed'],'failures',len(failed),flush=True)
write(OUT/'summary.json',dict(contract_sha256=sha(OUT/'contract.json'),reviews=records,autonomous_new_solves=0,protected_opened=False))
