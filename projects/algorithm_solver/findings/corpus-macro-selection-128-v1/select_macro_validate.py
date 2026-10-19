from pathlib import Path
from collections import defaultdict
import hashlib,json,sys
T=Path('/home/x/Documents/Codex/2026-10-19/task');R=Path('/home/x/deco/gamma/projects/algorithm_solver');P=R/'runs/corpus-macro-analysis-128-v1';O=R/'runs/corpus-macro-selection-128-v1';sys.path[:0]=[str(T),str(R)]
import selection_codec as c
from algsolve import validate
from algsolve.records import Problem,load_hidden_tests
from algsolve.judge import judge,sandbox
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();contract=json.loads((O/'contract.json').read_text());selection=json.loads((O/'selection-summary.json').read_text());checks=[];chosen={};roundtrips=0
for summary in selection['languages']:
 lang=summary['language'];d=O/lang/f"subset-{summary['best_mask']:02d}";book=json.loads((d/'codebook.json').read_text());chosen[lang]=(d,book)
 for row in [r for r in contract['source_rows'] if r['language']==lang]:
  stream=(d/f"{row['id']:04d}.bin").read_bytes();source=c.decode(stream,book);assert hashlib.sha256(source).hexdigest()==row['source_sha256'];roundtrips+=1
 # Canonical replay encoded with the actual selected occurrence set is tested
 # independently below using stored stream operands as registered occurrences.
 sample=(d/'0015.bin').read_bytes();fragment=next(e for e in book['entries'] if e['kind']=='fragment');arity=fragment['variants'][0]['arity'];fid=fragment['id']
 bad=[('missing-end',sample[:-1]),('wrong-version',b'CMA1'+sample[4:]),('trailing-data',sample+b'\0'),('truncated-binding',sample[:40]),('invalid-variant',c.frame(book,[])+bytes([fid,255,0])),('unknown-distinct-bindings',c.frame(book,[])+bytes([fid,0,0])+bytes(range(arity))+b'\0'),('noncanonical-length',sample[:38]+b'\x80\x00'+sample[39:]),('truncated-literal',c.frame(book,[])+b'\x01\x05x'),('invalid-binding-name',c.frame(book,['a b'])+b'\0'),('duplicate-binding-name',c.frame(book,['a','a'])+b'\0')]
 for name,data in bad:
  try:c.decode(data,book)
  except (ValueError,UnicodeError) as e:checks.append(dict(language=lang,case=name,rejected=True,reason=str(e)))
  else:raise AssertionError((lang,name))
 for case,refs,indent in [('aliased-fragment-operands',[0]*arity,0),('indent-overflow',list(range(arity)),65),('out-of-range-distinct-slots',list(range(99,99+arity)),0)]:
  try:c.expand(fragment['variants'][0],['b'+str(i) for i in range(arity)],refs,indent)
  except ValueError as e:checks.append(dict(language=lang,case=case,rejected=True,reason=str(e)))
  else:raise AssertionError(case)
# Independent exhaustive enumeration checks the optimizer's handling of
# overlapping alternatives and actual USED binding-table cost, not DP internals.
optcontrols=[]
for name,identifier,repeats in [('short','x',3),('long','aLongBindingName',3),('four','cursor',4)]:
 line=identifier+' += 1;\n';source=line*repeats;variants=[dict(parts=['',0,' += 1;\n'],arity=1),dict(parts=['',0,' += 1;\n',0,' += 1;\n'],arity=1)]
 b=dict(schema='test-only',language='javascript',kind='semantic',entries=[dict(id=0,kind='end'),dict(id=1,kind='literal_run')]+[dict(id=i+2,kind='text',body=chr(i)) for i in range(128)]+[dict(id=254,kind='fragment',name='step',variants=[variants[0]]),dict(id=255,kind='fragment',name='two_steps',variants=[variants[1]])]);occ=[]
 for i in range(repeats):occ.append(dict(start=i*len(line),text=line,names=[identifier],indent=0,code=254,variant=0,name='step'))
 for i in range(repeats-1):occ.append(dict(start=i*len(line),text=line*2,names=[identifier],indent=0,code=255,variant=0,name='two_steps'))
 minimum=[10**9];paths=[0]
 def enumerate_paths(pos,body_cost,bindings):
  if pos==len(source):minimum[0]=min(minimum[0],len(c.frame(b,sorted(bindings)))+body_cost+1);paths[0]+=1;return
  enumerate_paths(pos+1,body_cost+1,bindings)
  for o in occ:
   if o['start']==pos:enumerate_paths(pos+len(o['text']),body_cost+4,bindings|{identifier})
 enumerate_paths(0,0,set());stream,stats=c.encode(source,b,occ);assert len(stream)==minimum[0] and c.decode(stream,b).decode()==source
 again,_=c.encode(c.decode(stream,b).decode(),b,occ);assert again==stream;optcontrols.append(dict(case=name,segmentations_enumerated=paths[0],independent_minimum_bytes=minimum[0],actual_bytes=len(stream)))
# Full canonical replay checks for the winning books: rebuild all registered
# occurrences from the frozen candidates, without using stored encoded choices.
menu=json.loads((O/'candidate-menu.json').read_text());canonical=0
for lang,(d,b) in chosen.items():
 byname={e['name']:e for e in b['entries'] if e['kind']=='fragment'}
 for row in [r for r in contract['source_rows'] if r['language']==lang]:
  source=Path(row['source']).read_text();occ=[]
  for m in menu:
   if m['language']!=lang or m['name'] not in byname:continue
   entry=byname[m['name']]
   for variant,g in enumerate(m['groups']):
    for x in g['occurrence_records']:
     if x['id']!=row['id']:continue
     names=[n for n in x['identifiers'] if n not in m['fixed_global_names']];template,indent=c.template(x['text'],names);assert template==entry['variants'][variant];start=x.get('start')
     if start is None:start=source.index(x['text'],sum(len(s) for s in source.splitlines(keepends=True)[:x['line']-1]))
     occ.append(dict(start=len(source[:start].encode()),text=x['text'],names=names,indent=indent,code=entry['id'],variant=variant,name=m['name']))
  encoded,_=c.encode(source,b,occ);assert encoded==(d/f"{row['id']:04d}.bin").read_bytes();canonical+=1
ids=[15,18,102,103,107,1512,1748];problems={p['uid']:Problem.from_dict(p) for line in (R/'data/derived/problems.jsonl').read_text().splitlines() if (p:=json.loads(line))['uid'] in [f'lcd:{n}' for n in ids]};results=[];guard=[]
limit=sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=65536)
def execute(lang,source,p,tests):
 if lang=='python':
  payload=dict(entry=p.entry,calls=[dict(args=t.args,kwargs=t.kwargs) for t in tests]);raw=sandbox.run_python('harness.py',files={'harness.py':judge.HARNESS_PATH.read_text(),'candidate.py':source,'calls.json':json.dumps(payload)},limits=limit)
 else:
  payload=dict(method=p.entry['method'],params=p.params,calls=[dict(args=t.args,capture_args=False) for t in tests]);raw=sandbox.run(['/usr/bin/node','--jitless','--max-old-space-size=64','harness.cjs'],files={'harness.cjs':(R/'findings/source-corpus-js-py-128-v3/return_harness.cjs').read_text(),'candidate.cjs':source,'calls.json':json.dumps(payload)},limits=limit)
 assert all('expected' not in call for call in payload['calls']);return raw
print('[run-contract] run_name=selected-macro-validation pairs_input_spec=winning-books resume_from=none resume_stage=none decode=deterministic eval_dataset_paths=seven-consumed-development-problems device=cpu schedule=serial runtime_mode=cpu+linux-sandbox sweep_mode=none',flush=True)
for n in ids:
 p=problems[f'lcd:{n}'];rawtests=load_hidden_tests(p);public=p.public_tests;rows=[]
 for lang,(d,b) in chosen.items():
  source=c.decode((d/f'{n:04d}.bin').read_bytes(),b).decode()
  for group,tests in [('public',public),('independent',rawtests)]:
   for i in range(0,len(tests),8):
    ts=validate.functional_tests(tests[i:i+8]);raw=execute(lang,source,p,ts);v=judge._score_functional(raw,ts);rows.append(dict(language=lang,group=group,offset=i,verdict=v.to_dict()));assert v.passed,(n,lang,group,i,v)
  if n in [1512,1748]:
   args=[None,'x',[-1],[1000001],[True],[1.5],[0]*20001];tests=[judge.FunctionalTest(args=[a],expected=None) for a in args];raw=execute(lang,source,p,tests);observations=[json.loads(line) for line in raw.stdout.decode().splitlines()];assert raw.ok and observations[-1]=={'done':len(args)}
   expected='TypeError' if lang=='javascript' else 'ValueError';assert all(v.get('error')==expected for v in observations[:-1]);guard.append(dict(id=n,language=lang,cases=len(args),expected_exception=expected,all_rejected=True,stdout_sha256=hashlib.sha256(raw.stdout).hexdigest()))
 results.append(dict(id=n,independent_cases=len(rawtests),public_cases=len(public),both_languages_passed=True,results=rows));print(n,'passed both languages',len(rawtests),'independent',len(public),'public',flush=True)
for key,h in contract['baseline_codebooks'].items():lang,kind=key.split('/');assert sha(P/lang/f'{kind}-codebook.json')==h
report=dict(codec_sha256=sha(T/'selection_codec.py'),runner_sha256=sha(__file__),selected_source_roundtrips=roundtrips,selected_canonical_stream_roundtrips=canonical,all_subset_source_roundtrips=4512,malformed_controls=checks,optimizer_controls=optcontrols,guard_rejection_controls=guard,independent_cases_per_language=sum(r['independent_cases'] for r in results),public_cases_per_language=sum(r['public_cases'] for r in results),results=results,all_baselines_unchanged=True,autonomous_solves=0)
(O/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print('Validation complete',report['independent_cases_per_language'],report['public_cases_per_language'])
