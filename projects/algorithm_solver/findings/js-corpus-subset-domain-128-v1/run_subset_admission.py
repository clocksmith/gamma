"""Fresh subset admission and explicitly scoped domain-regression review."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path('/home/x/deco/gamma/projects/algorithm_solver');FIND=ROOT/'findings/js-corpus-subset-domain-128-v1';OUT=ROOT/'runs/js-corpus-subset-domain-128-v1';PACK=Path('/home/x/Documents/Codex/2026-10-19/task/js-corpus-wave-001')
sys.path[:0]=[str(ROOT),str(FIND),str(ROOT/'findings/js-corpus-b03-b04-integration-128-v1'),str(ROOT/'findings/js-exact-integer-transport-128-v1')]
from algsolve import validate
from algsolve.records import Problem,load_hidden_tests
from algsolve.judge import judge,sandbox
import exact_integer,subset_order_v2,domain_contracts_v1
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
digest=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def write(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def run_py(source,p,tests):
 payload=json.dumps({'entry':p.entry,'calls':[{'args':t.args,'kwargs':t.kwargs} for t in tests]})
 raw=sandbox.run_python('harness.py',files={'harness.py':judge.HARNESS_PATH.read_text(),'candidate.py':source,'calls.json':payload},limits=sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=65536))
 return judge._score_functional(raw,tests),raw
manifest=json.loads((PACK/'manifest.json').read_text());assert sha(PACK/'manifest.json')=='af62e96fb59049cd782f481a0e21b71c6a2f66174035d92b18ea9d5a3ef11ae9'
for path,want in manifest['inputs_sha256'].items():assert sha(path)==want
ids=[60,65,74,78,81,87,90];rows={r['id']:r for r in manifest['rows'] if r['id'] in ids}
problems={int(p['uid'].split(':')[1]):Problem.from_dict(p) for line in (ROOT/'data/derived/problems.jsonl').read_text().splitlines() if (p:=json.loads(line))['uid'] in [f'lcd:{n}' for n in ids]}
raw_path=ROOT/'data/raw/doocs__leetcode/solution/result.json';htmlrows=json.loads(raw_path.read_text());selected={};inputs={}
for n in ids:
 row=rows[n];p=problems[n];packet=json.loads(Path(row['problem_packet']).read_text());tests=load_hidden_tests(p);meta=row['independent_test_sets'][0];assert len(tests)==meta['tests'] and digest(tests)==meta['sha256']
 groups={'public':packet['public_tests'],'independent':tests};inputs[n]=groups
 if n in [78,90]:continue
 html=next(r for r in htmlrows if r['question_title_slug']==packet['slug'])
 if n in [74,81]:assert '-10<sup>4</sup>' in html['content_en']
 (OUT/f'{n:04d}-pinned-statement.html').write_text(html['content_en'])
 selection=dict(id=n,statement_packet_sha256=sha(row['problem_packet']),corroborating_html_sha256=sha(OUT/f'{n:04d}-pinned-statement.html'),raw_doocs_snapshot_sha256=sha(raw_path),classifier_sha256=sha(FIND/'domain_contracts_v1.py'),selection_basis='Only argument shape, types, bounds and structural preconditions; expected outputs and pass/fail never used.',groups={})
 for group,cases in groups.items():
  selection['groups'][group]=[dict(index=i,test_sha256=digest(t),valid=not (reasons:=domain_contracts_v1.reasons(n,t['args'])),reasons=reasons) for i,t in enumerate(cases)]
 write(OUT/f'{n:04d}-selection-seal.json',selection);selected[n]=selection
 # Preserve every quarantined test in full, including cases both languages previously passed.
 quarantine=[dict(group=g,index=x['index'],reasons=x['reasons'],original_test=groups[g][x['index']]) for g,items in selection['groups'].items() for x in items if not x['valid']]
 write(OUT/f'{n:04d}-quarantine.json',quarantine)
contract=dict(schema='algsolve.subset-admission-domain-review.v1',runner_sha256=sha(__file__),old58_catalog_sha256=sha(ROOT/'findings/js-corpus-b03-b04-integration-128-v1/catalog.json'),subset_comparator_sha256=sha(subset_order_v2.__file__),base_multiset_comparator_sha256=sha(ROOT/'algsolve/judge/functional_semantics.py'),domain_classifier_sha256=sha(FIND/'domain_contracts_v1.py'),domain_control_groups_passed=7,selection_seals={str(n):sha(OUT/f'{n:04d}-selection-seal.json') for n in selected},shared_helper_sha256=sha(PACK/'qualify.py'),scope='Admit only78/90 under existing isolatedv2 outer-order comparator after fresh both-language reruns. Five other IDs get explicitly labeled valid-published-domain regression results; no deletion or automatic catalog promotion.',oracle_policy='Original expected values and raw test files unchanged.78/90 alone use separately versioned unordered-outer comparison.',limits=dict(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,output_bytes=65536,node_heap_MiB=64,concurrency=1),training=False,protected_opened=False)
write(OUT/'contract.json',contract)
print('[run-contract] run_name=js-corpus-subset-domain-128-v1 pairs_input_spec=frozen-assigned-sources resume_from=none resume_stage=none decode=declared-outer-order+explicit-domain-mask eval_dataset_paths=existing-seven-ID-cases device=cpu schedule=serial runtime_mode=cpu+linux-sandbox sweep_mode=none',flush=True)
# Independent adversarial fixtures exercise actual Python and JavaScript transport/scoring.
wanted=[[],[1],[2],[1,2]];multiplicity=[[],[1],[1,1]]
controls=[('reorder',wanted,wanted[::-1],True),('missing',wanted,wanted[:-1],False),('extra_duplicate',wanted,wanted+[[1]],False),('duplicate_replaces_missing',wanted,[[],[1],[1],[1,2]],False),('wrong_element',wanted,[[],[1],[3],[1,2]],False),('bool_instead_of_int',[[1]],[[True]],False),('string_instead_of_int',[[1]],[['1']],False),('inner_order_strict',[[1,2]],[[2,1]],False),('inner_multiplicity_preserved',multiplicity,multiplicity[::-1],True),('inner_multiplicity_lost',multiplicity,[[],[1],[1]],False),('wrong_shape',wanted,{},False),('empty_subset_missing',[[]],[],False)]
control_results=[]
from types import SimpleNamespace
fake=SimpleNamespace(entry={'class':'Solution','method':'f'})
for name,expected,actual,accepted in controls:
 tests=[judge.FunctionalTest(args=[],expected=expected,compare='return:unordered_outer')]
 py,raw=run_py('class Solution:\n def f(self):\n  return '+repr(actual)+'\n',fake,tests)
 js,raw,payload=exact_integer.execute('function f(){return '+json.dumps(actual)+';}','f',[],tests)
 assert py.passed==js.passed==accepted,(name,py,js)
 control_results.append(dict(name=name,expected_acceptance=accepted,python=py.to_dict(),javascript=js.to_dict()))
write(OUT/'comparator-adversarial-controls.json',dict(fixtures=12,language_executions=24,all_expected_outcomes=True,results=control_results))
summaries=[]
for n in ids:
 p=problems[n];row=rows[n];b=ROOT/'runs/js-corpus-wave-001'/row['batch_id'];dest=OUT/f'{n:04d}';dest.mkdir();source=(b/f'{n:04d}-role-style.js').read_text();python=Path(row['python_source']).read_text();results=[]
 for group,cases in inputs[n].items():
  indices=list(range(len(cases))) if n in [78,90] else [x['index'] for x in selected[n]['groups'][group] if x['valid']]
  step=1 if n in [78,90] else 16
  for start in range(0,len(indices),step):
   chosen=indices[start:start+step];rawtests=[cases[i] for i in chosen];tests=subset_order_v2.prepare(p,rawtests) if n in [78,90] else validate.functional_tests(rawtests)
   py,pyraw=run_py(python,p,tests);js,jsraw,_=exact_integer.execute(source,p.entry['method'],p.params,tests)
   record=dict(group=group,original_indices=chosen,python=py.to_dict(),javascript=js.to_dict(),raw_tests_sha256=digest(rawtests))
   (dest/f'{group}-{start:03d}-python.jsonl').write_bytes(pyraw.stdout);(dest/f'{group}-{start:03d}-javascript.jsonl').write_bytes(jsraw.stdout);write(dest/f'{group}-{start:03d}-receipt.json',record);results.append(record)
  print(n,group,sum(r['javascript']['tests_passed'] for r in results if r['group']==group),'/',len(indices),flush=True)
 summary=dict(id=n,key=row['key'],qualified=bool(results) and all(r['python']['passed'] and r['javascript']['passed'] for r in results),qualification_scope='complete unchanged existing test collections under outer-orderv2' if n in [78,90] else 'explicit valid-published-domain subset of existing consumed development tests only; not complete historical test collection',original_independent_total=len(inputs[n]['independent']),evaluated_independent=sum(r['javascript']['tests_total'] for r in results if r['group']=='independent'),python_independent_passed=sum(r['python']['tests_passed'] for r in results if r['group']=='independent'),javascript_independent_passed=sum(r['javascript']['tests_passed'] for r in results if r['group']=='independent'),public_total=len(inputs[n]['public']),public_evaluated=sum(r['javascript']['tests_total'] for r in results if r['group']=='public'),public_passed=sum(r['javascript']['tests_passed'] for r in results if r['group']=='public'),source=str(b/f'{n:04d}-role-style.js'),source_sha256=sha(b/f'{n:04d}-role-style.js'),python_source=row['python_source'],python_source_sha256=sha(row['python_source']),test_metadata=row['independent_test_sets'],results=results)
 summary['quarantined_independent']=summary['original_independent_total']-summary['evaluated_independent'];summary['catalog_admission_authorized']=n in [78,90]
 write(dest/'summary.json',summary);summaries.append(summary)
write(OUT/'summary.json',dict(rows=summaries,adversarial_controls_sha256=sha(OUT/'comparator-adversarial-controls.json'),contract_sha256=sha(OUT/'contract.json'),old58_catalog_unchanged=sha(ROOT/'findings/js-corpus-b03-b04-integration-128-v1/catalog.json')==contract['old58_catalog_sha256'],raw_oracles_unchanged=all(sha(p)==h for p,h in manifest['inputs_sha256'].items())))
print('Fresh review complete',[(r['id'],r['qualified'],r['evaluated_independent'],r['quarantined_independent']) for r in summaries],flush=True)
