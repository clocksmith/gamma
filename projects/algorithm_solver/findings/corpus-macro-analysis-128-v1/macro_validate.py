from pathlib import Path
from types import SimpleNamespace
import hashlib,json,sys,subprocess,copy
T=Path('/home/x/Documents/Codex/2026-10-19/task');R=Path('/home/x/deco/gamma/projects/algorithm_solver');O=R/'runs/corpus-macro-analysis-128-v1';sys.path[:0]=[str(T),str(R)]
import macro_codec as codec
from algsolve import validate
from algsolve.records import Problem,load_hidden_tests
from algsolve.judge import judge,sandbox
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
contract=json.loads((O/'contract.json').read_text());manifest=json.loads((T/'js-corpus-wave-001/manifest.json').read_text());ids=[15,18,102,103,107]
problems={p['uid']:Problem.from_dict(p) for line in (R/'data/derived/problems.jsonl').read_text().splitlines() if (p:=json.loads(line))['uid'] in [f'lcd:{n}' for n in ids]}
for row in contract['source_rows']:assert sha(row['source'])==row['source_sha256']
checks=[]
for lang in ['javascript','python']:
 b=json.loads((O/lang/'semantic-codebook.json').read_text());row=next(r for r in contract['source_rows'] if r['language']==lang and r['id']==102);stream=(O/lang/'semantic/0102.bin').read_bytes();assert codec.decode(stream,b)==Path(row['source']).read_bytes()
 samples=[('missing-end',stream[:-1]),('wrong-header',b'BAD!'+stream[4:]),('trailing-data',stream+b'\0'),('truncated-binding',stream[:40]),('invalid-variant',codec.frame(b,[])+bytes([254,255,0])),('unknown-binding',codec.frame(b,[])+bytes([254,0,0,0,0,0,0,0,0,0])),('noncanonical-length',stream[:38]+b'\x80\x00'+stream[39:]),('truncated-literal',codec.frame(b,[])+b'\x01\x05x')]
 whole=json.loads((O/lang/'whole-codebook.json').read_text());samples.append(('unknown-whole-id',codec.frame(whole,[])+bytes([255,0])))
 for name,data in samples:
  try:codec.decode(data,whole if name=='unknown-whole-id' else b)
  except (ValueError,UnicodeError):checks.append(dict(language=lang,case=name,rejected=True))
  else:raise AssertionError((lang,name,'not rejected'))
 # Identifier substitution rejects repeated handles, bad indentation and unknown slots.
 variant=b['entries'][-2]['variants'][0]
 for case,slots,indent in [('aliasing-handles',[0]*variant['arity'],0),('indent-overflow',list(range(variant['arity'])),65),('missing-binding',[99]*variant['arity'],0)]:
  try:codec.expand(variant,['x'+str(i) for i in range(variant['arity'])],slots,indent)
  except ValueError:checks.append(dict(language=lang,case=case,rejected=True))
  else:raise AssertionError(case)
results=[]
print('[run-contract] run_name=corpus-macro-reconstruction pairs_input_spec=frozen94-development-pairs resume_from=none resume_stage=none decode=deterministic-byteexact eval_dataset_paths=15,18,102,103,107-public+existing-independent device=cpu schedule=serial runtime_mode=cpu+linux-sandbox sweep_mode=none',flush=True)
for n in ids:
 row=next(r for r in manifest['rows'] if r['id']==n);p=problems[f'lcd:{n}'];packet=json.loads(Path(row['problem_packet']).read_text());tests=load_hidden_tests(p);evidence=[]
 assert hashlib.sha256(json.dumps(tests,sort_keys=True,separators=(',',':')).encode()).hexdigest()==row['independent_test_sets'][0]['sha256']
 for lang in ['javascript','python']:
  book=json.loads((O/lang/'semantic-codebook.json').read_text());stream=(O/lang/'semantic'/f'{n:04d}.bin').read_bytes();src=codec.decode(stream,book).decode();frozen=next(r for r in contract['source_rows'] if r['id']==n and r['language']==lang);assert hashlib.sha256(src.encode()).hexdigest()==frozen['source_sha256']
  if lang=='javascript':subprocess.run(['node','--check'],input=src,text=True,capture_output=True,check=True)
  else:compile(src,'candidate.py','exec')
  for group,rawtests in [('public',packet['public_tests']),('independent',tests)]:
   for start in range(0,len(rawtests),8):
    ts=validate.functional_tests(rawtests[start:start+8]);limit=sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=65536)
    if lang=='python':
     payload=dict(entry=p.entry,calls=[dict(args=t.args,kwargs=t.kwargs) for t in ts]);raw=sandbox.run_python('harness.py',files={'harness.py':judge.HARNESS_PATH.read_text(),'candidate.py':src,'calls.json':json.dumps(payload)},limits=limit)
    else:
     payload=dict(method=p.entry['method'],params=p.params,calls=[dict(args=t.args,capture_args=False) for t in ts]);raw=sandbox.run(['/usr/bin/node','--jitless','--max-old-space-size=64','harness.cjs'],files={'harness.cjs':(R/'findings/source-corpus-js-py-128-v3/return_harness.cjs').read_text(),'candidate.cjs':src,'calls.json':json.dumps(payload)},limits=limit)
    assert all('expected' not in v for v in payload['calls']);verdict=judge._score_functional(raw,ts);evidence.append(dict(language=lang,group=group,offset=start,verdict=verdict.to_dict()));assert verdict.passed,(n,lang,group,start,verdict)
 rec=dict(id=n,key=row['key'],public_cases=len(packet['public_tests']),independent_cases=len(tests),both_languages_passed=True,source_byte_identity_preserves_algorithm_interface_mutation_and_aliasing=True,results=evidence);results.append(rec);print(n,'both languages passed',len(tests),'independent +',len(packet['public_tests']),'public',flush=True)
report=dict(schema='algsolve.macro-reconstruction-validation.v1',codec_sha256=sha(T/'macro_codec.py'),runner_sha256=sha(__file__),malformed_stream_controls=checks,malformed_controls_passed=len(checks),problem_pairs=len(results),independent_cases_per_language=sum(r['independent_cases'] for r in results),public_cases_per_language=sum(r['public_cases'] for r in results),results=results,autonomous_solves=0,protected_opened=False)
(O/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print('controls',len(checks),'independent',report['independent_cases_per_language'],'public',report['public_cases_per_language'])
