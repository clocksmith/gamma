"""Bounded B03/B04 contract review; preserves every historical artifact."""
from pathlib import Path
import hashlib,json,math,sys
ROOT=Path('/home/x/deco/gamma/projects/algorithm_solver')
FIND=ROOT/'findings/js-corpus-b03-b04-integration-128-v1'
OUT=ROOT/'runs/js-corpus-contract-review-128-v1'
PACK=Path('/home/x/Documents/Codex/2026-10-19/task/js-corpus-wave-001')
sys.path[:0]=[str(ROOT),str(FIND),str(ROOT/'findings/js-exact-integer-transport-128-v1')]
from algsolve import validate
from algsolve.records import Problem,load_hidden_tests
from algsolve.judge import judge,sandbox
import exact_integer
import subset_order_v2
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def write(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def run_py(source,p,tests):
 calls={'entry':p.entry,'calls':[{'args':t.args,'kwargs':t.kwargs} for t in tests]}
 raw=sandbox.run_python('harness.py',files={'harness.py':judge.HARNESS_PATH.read_text(),'candidate.py':source,'calls.json':json.dumps(calls)},limits=sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=65536))
 return judge._score_functional(raw,tests),raw,calls
def observations(raw):
 return [r for line in raw.stdout.decode().splitlines() if 'i' in (r:=json.loads(line))]
manifest=json.loads((PACK/'manifest.json').read_text());assert sha(PACK/'manifest.json')=='af62e96fb59049cd782f481a0e21b71c6a2f66174035d92b18ea9d5a3ef11ae9'
for p,h in manifest['inputs_sha256'].items():assert sha(p)==h
problems={p['uid']:Problem.from_dict(p) for l in (ROOT/'data/derived/problems.jsonl').read_text().splitlines() if (p:=json.loads(l))['uid'] in [f'lcd:{n}' for n in [60,65,74,78,81,87,90,115]]}
contract=dict(schema='algsolve.owner-contract-review.v1',runner_sha256=sha(__file__),subset_correction_sha256=sha(FIND/'subset_order_v2.py'),subset_controls_sha256=sha(FIND/'test_subset_order_v2.py'),subset_controls_passed=8,shared_helper_sha256=sha(PACK/'qualify.py'),judge_sha256=sha(ROOT/'algsolve/judge/judge.py'),comparator_sha256=sha(ROOT/'algsolve/judge/functional_semantics.py'),python_harness_sha256=sha(judge.HARNESS_PATH),exact_transport_sha256=sha(exact_integer.__file__),javascript_harness_sha256=sha(exact_integer.HARNESS),scope='Review seven contracts; correct only outer-order comparison for pinned78/90; separately review115 precision. No historical source/test edits.',comparison_change={'ids':[78,90],'from':'return','to':'return:unordered_outer','expected_values':'unchanged','scope':'outer order only; retain inner order, types and multiplicity'},chunk_cases=1,limits=dict(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,output_bytes=65536,node_heap_MiB=64),training=False,protected_opened=False)
write(OUT/'contract.json',contract)
print('[run-contract] run_name=js-corpus-contract-review-128-v1 pairs_input_spec=frozen-assigned-sources resume_from=none resume_stage=none decode=exact-integer+declared-outer-order eval_dataset_paths=seven-reviewed-contracts+115-controls device=cpu schedule=serial runtime_mode=cpu+linux-sandbox sweep_mode=none',flush=True)
reviews=[]
for n in [60,65,74,78,81,87,90]:
 batch='W001-B03' if n<76 else 'W001-B04';b=ROOT/'runs/js-corpus-wave-001'/batch
 row=next(r for r in manifest['rows'] if r['batch_id']==batch and r['id']==n)
 p=problems[f'lcd:{n}'];tests=load_hidden_tests(p);meta=row['independent_test_sets'][0];assert len(tests)==meta['tests'] and digest(tests)==meta['sha256']
 packet=json.loads(Path(row['problem_packet']).read_text());py_source=Path(row['python_source']).read_text();js_source=(b/f'{n:04d}-role-style.js').read_text();diagnosis=json.loads((b/f'{n:04d}-failure-diagnosis.json').read_text());dest=OUT/f'{n:04d}';dest.mkdir()
 record=dict(id=n,key=row['key'],statement_packet=row['problem_packet'],statement_packet_sha256=row['problem_packet_sha256'],attribution=packet['attribution'],python_source=row['python_source'],python_source_sha256=row['python_source_sha256'],javascript_source=str(b/f'{n:04d}-role-style.js'),javascript_source_sha256=sha(b/f'{n:04d}-role-style.js'),historical_diagnosis_sha256=sha(b/f'{n:04d}-failure-diagnosis.json'))
 if n not in [78,90]:
  details=[]
  for case in diagnosis['failures']:
   t=tests[case['index']];ts=validate.functional_tests([t]);py,pyraw,_=run_py(py_source,p,ts);js,jsraw,_=exact_integer.execute(js_source,p.entry['method'],p.params,ts)
   (dest/f"case-{case['index']}-python.jsonl").write_bytes(pyraw.stdout);(dest/f"case-{case['index']}-javascript.jsonl").write_bytes(jsraw.stdout)
   details.append(dict(index=case['index'],input=t['args'],expected=t['expected'],compare=t.get('compare','return'),python_actual=observations(pyraw)[0],javascript_actual=observations(jsraw)[0],python_verdict=py.to_dict(),javascript_verdict=js.to_dict(),domain_conflict=case['outside_declared_domain']))
  record.update(classification='test-domain mismatch, not an established in-domain candidate or comparator defect',failing_cases=details,candidate_changed=False,expected_changed=False,disposition='Keep failed historical qualification. Python matches the stored expected result on out-of-contract input; this does not establish a mathematically valid oracle outside its preconditions. No domain filtering or candidate compatibility hack applied.')
 else:
  assert 'return the solution in any order' in packet['statement'].lower()
  results=[];historical_conflicts=[]
  for group,rawtests in [('public',packet['public_tests']),('independent',tests)]:
   for i,test in enumerate(rawtests):
    original_digest=digest(test);ts=subset_order_v2.prepare(p,[test]);py,pyraw,_=run_py(py_source,p,ts);js,jsraw,_=exact_integer.execute(js_source,p.entry['method'],p.params,ts)
    assert digest(test)==original_digest
    (dest/f'{group}-{i:03d}-python.jsonl').write_bytes(pyraw.stdout);(dest/f'{group}-{i:03d}-javascript.jsonl').write_bytes(jsraw.stdout)
    rec=dict(group=group,index=i,python=py.to_dict(),javascript=js.to_dict(),python_stdout_sha256=hashlib.sha256(pyraw.stdout).hexdigest(),javascript_stdout_sha256=hashlib.sha256(jsraw.stdout).hexdigest(),raw_test_sha256=original_digest,expected_unchanged=True)
    write(dest/f'{group}-{i:03d}-receipt.json',rec);results.append(rec)
    if group=='public' or i in [c['independent_index'] for c in diagnosis['identical_input_order_conflicts']]:
     oldts=validate.functional_tests([test]);historical_conflicts.append(dict(group=group,index=i,input=test['args'],expected=test['expected'],python_actual=observations(pyraw)[0],javascript_actual=observations(jsraw)[0],original_ordered_python=judge._score_functional(pyraw,oldts).to_dict(),original_ordered_javascript=exact_integer.score_result(jsraw,oldts).to_dict()))
  record.update(classification='shared wave evaluation contract defect: exact outer order contradicts pinned any-order statement',correction='separately versioned subset_order_v2, scoped to uid/slug/method, one-case transport',qualified_under_v2=all(r['python']['passed'] and r['javascript']['passed'] for r in results),public_total=len(packet['public_tests']),public_passed=sum(r['javascript']['tests_passed'] for r in results if r['group']=='public'),independent_total=len(tests),python_independent_passed=sum(r['python']['tests_passed'] for r in results if r['group']=='independent'),javascript_independent_passed=sum(r['javascript']['tests_passed'] for r in results if r['group']=='independent'),comparison_conflicts=historical_conflicts,identical_input_conflicts=diagnosis['identical_input_order_conflicts'],results=results,expected_changed=False,candidate_changed=False,catalog_integration='Separate review result; requested33 plus115 integration remains independently scoped.')
  print(n,'corrected',record['qualified_under_v2'],record['javascript_independent_passed'],'/',len(tests),flush=True)
 write(dest/'review.json',record);reviews.append(record)
#115: inspect and bind prior transport/solution artifacts; add independent combinatorial precision probes.
prior=ROOT/'runs/js-exact-integer-115-128-v1';oldcontract=json.loads((prior/'contract.json').read_text());oldsummary=json.loads((prior/'summary.json').read_text())
for rel,h in oldcontract['runner_files_sha256'].items():assert sha(ROOT/rel)==h
assert sha(prior/'candidate.js')==oldcontract['source_sha256'] and oldsummary['qualified'] and oldsummary['independent_passed']==oldsummary['python_independent_passed']==101
row=next(r for r in manifest['rows'] if r['id']==115);p=problems['lcd:115'];py_source=Path(row['python_source']).read_text();source=(prior/'candidate.js').read_text();checks=[]
for length,chosen in [(5,2),(60,30),(100,50),(100,100),(100,101)]:
 expected=math.comb(length,chosen) if chosen<=length else 0
 ts=[judge.FunctionalTest(args=['a'*length,'a'*chosen],expected=expected)];py,pyraw,_=run_py(py_source,p,ts);js,jsraw,payload=exact_integer.execute(source,p.entry['method'],p.params,ts)
 assert 'expected' not in json.loads(payload) and all('expected' not in c for c in json.loads(payload)['calls'])
 checks.append(dict(source_length=length,target_length=chosen,expected=expected,oracle='Python math.comb, independently derived from repeated-character combinatorics',python=py.to_dict(),javascript=js.to_dict(),native_bigint_tag_used=exact_integer.TAG.encode() in jsraw.stdout))
review115=dict(id=115,accepted=all(c['python']['passed'] and c['javascript']['passed'] for c in checks),prior_contract_sha256=sha(prior/'contract.json'),prior_summary_sha256=sha(prior/'summary.json'),source_sha256=sha(prior/'candidate.js'),all_prior_runner_hashes_match=True,prior_independent_cases=101,prior_public_cases=2,prior_input_preservation_probes=4,exact_integer_contract='Actual Python ints beyond2^53-1 use canonical native-BigInt tags. Unsafe integral Number output is rejected, never rounded. Original host expectations remain exact Python integers. Source uses BigInt count recurrence with safe-Number return only after range check.',scope='Finite ASCII-string development corpus; native BigInt-capable runtime required for broad-count cases. No global transport or production recognition change.',independent_precision_controls=checks,original_blocked_attempts_preserved=True)
write(OUT/'115-contract-review.json',review115);write(OUT/'review-summary.json',dict(contract_sha256=sha(OUT/'contract.json'),reviews=reviews,review115=review115))
print('115 exact-integer review accepted',review115['accepted'],flush=True)
