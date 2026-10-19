"""Separately sealed evaluation of B05's exact115 candidate; no live helper edit."""
from pathlib import Path
import datetime,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from algsolve import validate
from algsolve.records import Problem,load_hidden_tests
from algsolve.judge import judge
import exact_integer
FIND=Path(__file__).parent;OUT=ROOT/'runs/js-exact-integer-115-128-v1'
PACK=Path('/home/x/Documents/Codex/2026-10-19/task/js-corpus-wave-001')
B05=ROOT/'runs/js-corpus-wave-001/W001-B05';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def write(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def main():
 assignment=json.loads((PACK/'W001-B05/assignment.json').read_text());assert sha(PACK/'manifest.json')==assignment['manifest_sha256']
 item=next(r for r in assignment['rows'] if r['id']==115);original=json.loads((B05/'0115/attempt-002/receipt.json').read_text())
 sourcepath=B05/'0115/attempt-002/candidate.js';assert sha(sourcepath)==original['source_sha256']
 assert sha(item['python_source'])==item['python_source_sha256'] and sha(item['problem_packet'])==item['problem_packet_sha256']
 helper_sha=sha(PACK/'qualify.py');assert helper_sha==json.loads((PACK/'handoff-checks.json').read_text())['runner_sha256']
 OUT.mkdir();source=sourcepath.read_text();python=Path(item['python_source']).read_text();(OUT/'candidate.js').write_text(source)
 contract=dict(schema='algsolve.exact-integer-successor.v1',name=OUT.name,problem_id=115,key=item['key'],scope='Separate development qualification;115 remains excluded from integrated24-entry catalog pending coordinator/owner review.',base_integration_commit='fe026a27880283b7591cc0c133f9aa300f6fb38e',source_sha256=sha(sourcepath),python_source_sha256=item['python_source_sha256'],tests=item['independent_test_sets'],previous_blocked_receipt_sha256=sha(B05/'0115/attempt-002/receipt.json'),shared_wave_helper_sha256=helper_sha,runner_files_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),FIND/'exact_integer.py',FIND/'harness.cjs',FIND/'test_exact_integer.py',ROOT/'algsolve/judge/judge.py',ROOT/'algsolve/judge/sandbox.py',ROOT/'algsolve/test_corrections.py']},numeric_contract={'tag':exact_integer.TAG,'digits':4096,'input':'Python integers within +/- (2^53-1) remain Number; larger Python integers become canonical tagged decimal strings, decoded only to native BigInt. Floats are never promoted to integers. Reserved tag collisions fail closed.','output':'Native BigInt becomes tagged canonical decimal; host decodes to exact Python int before unchanged judge comparison. Unsafe integral Number and nonfinite outputs rejected. Safe Number/float/bool/null/array/object and existing node wrappers retain transport.','expected':'Mathematical expected values and comparison modes are unchanged and remain exclusively host-side.','controls':'Seven independently specified software test groups passed before this case execution.'},limits={'concurrency':1,'scope_cpu_quota_percent':100,'scope_memory_MiB':1536,'chunk_cases':16,'sandbox_wall_seconds':8,'sandbox_cpu_seconds':3,'node_heap_MiB':64,'sandbox_memory_MiB':1024,'output_bytes':65536},training=False,protected_opened=False,downloads=False,production_helper_changed=False)
 write(OUT/'contract.json',contract);write(FIND/'contract.json',contract)
 write(OUT/'software-checks.json',dict(test_groups=7,passed=7,wall_seconds=2.649,command='PYTHONPATH=projects/algorithm_solver .venv_rocm/bin/python -m unittest discover -s projects/algorithm_solver/findings/js-exact-integer-transport-128-v1 -p test_exact_integer.py -v',source_sha256=sha(FIND/'test_exact_integer.py'),cases='Exact and adjacent integer boundaries, nested values, nodes, mutation, malformed/duplicate tags, unsafe Number rejection, v1 compatibility and failure priority.'))
 raw=next(json.loads(l) for l in (ROOT/'data/derived/problems.jsonl').read_text().splitlines() if json.loads(l)['uid']=='lcd:115');p=Problem.from_dict(raw)
 tests=load_hidden_tests(p);meta=item['independent_test_sets'][0];assert len(tests)==meta['tests']==101 and digest(tests)==meta['sha256']
 packet=json.loads(Path(item['problem_packet']).read_text());public=packet['public_tests'];groups=[('public',public),('independent',tests)];results=[]
 print('[run-contract] run_name='+OUT.name+' pairs_input_spec=frozen-W001-B05-115 resume_from=none resume_stage=none decode=exact-tagged-integer eval_dataset_paths=unchanged101-independent-cases device=cpu schedule=serial runtime_mode=cpu+linux-sandbox sweep_mode=none',flush=True)
 for name,raw_tests in groups:
  for offset in range(0,len(raw_tests),16):
   chunk=raw_tests[offset:offset+16];ts=validate.functional_tests(chunk)
   py=validate.judge_problem(p,python,chunk,wall_seconds=8).to_dict()
   js,raw_result,payload=exact_integer.execute(source,p.entry['method'],p.params,ts)
   (OUT/f'{name}-{offset:03d}-stdout.jsonl').write_bytes(raw_result.stdout)
   record=dict(group=name,offset=offset,python=py,javascript=js.to_dict(),raw_stdout_sha256=hashlib.sha256(raw_result.stdout).hexdigest(),input_only_payload_sha256=hashlib.sha256(payload.encode()).hexdigest())
   results.append(record);write(OUT/f'{name}-{offset:03d}-receipt.json',record)
   print(name,offset,py['passed'],js.passed,js.tests_passed,js.tests_total,flush=True)
 probes=[judge.FunctionalTest(args=t['args'],expected=t['args'][i],compare=f'arg:{i}') for t in public for i in range(len(t['args']))]
 mutation,_,_=exact_integer.execute(source,p.entry['method'],p.params,probes);write(OUT/'input-preservation.json',mutation.to_dict())
 qualified=all(x['python']['passed'] and x['javascript']['passed'] for x in results) and mutation.passed
 summary=dict(schema='algsolve.exact-integer-successor-result.v1',problem=115,qualified=qualified,public_passed=sum(x['javascript']['tests_passed'] for x in results if x['group']=='public'),public_total=len(public),independent_passed=sum(x['javascript']['tests_passed'] for x in results if x['group']=='independent'),independent_total=101,python_independent_passed=sum(x['python']['tests_passed'] for x in results if x['group']=='independent'),input_preservation=mutation.to_dict(),contract_sha256=sha(OUT/'contract.json'),source_sha256=sha(sourcepath),tests_sha256=meta['sha256'],results=results,original_blocked_receipt_preserved=True,shared_helper_unchanged=sha(PACK/'qualify.py')==helper_sha,integrated_catalog_unique=24,separate_successor_qualified_unique=int(qualified),combined_distinct_evidence_unique=24+int(qualified),production_promotion=False,autonomous_new_solves=0)
 assert summary['shared_helper_unchanged'];write(OUT/'summary.json',summary);write(FIND/'summary.json',summary)
 print(json.dumps({k:v for k,v in summary.items() if k not in ['results','input_preservation']},indent=2))
if __name__=='__main__':main()
