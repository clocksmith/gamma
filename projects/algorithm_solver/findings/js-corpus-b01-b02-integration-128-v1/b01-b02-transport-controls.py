from pathlib import Path
from types import SimpleNamespace
import json,hashlib,sys,importlib.util
T=Path('/home/x/Documents/Codex/2026-10-19/task');R=Path('/home/x/deco/gamma/projects/algorithm_solver');OUT=R/'runs/js-corpus-b01-b02-review-128-v1';sys.path[:0]=[str(R),str(R/'findings/js-exact-integer-transport-128-v1')]
from algsolve.judge import judge,sandbox
import exact_integer
spec=importlib.util.spec_from_file_location('contract',T/'b01-b02-contracts.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
manifest=json.loads((T/'js-corpus-wave-001/manifest.json').read_text());rows={r['id']:r for r in manifest['rows']};records=[]
def pyexecute(source,p,tests):
 raw=sandbox.run_python('harness.py',files={'harness.py':judge.HARNESS_PATH.read_text(),'candidate.py':source,'calls.json':json.dumps(dict(entry=p.entry,calls=[dict(args=t.args,kwargs=t.kwargs) for t in tests]))},limits=sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=65536));return judge._score_functional(raw,tests)
for lists in [[[1]],[[1],[0]],[[1,1],[1,1]],[[],[-3,-1],[0,0,4]],[[-10,0,10],[-10,1,11]],[[],[],[3]],[[2],[1],[0],[-1]],[[1,4,7],[2,5,8],[3,6,9]]]:
 row=rows[23];p=SimpleNamespace(uid='lcd:23',slug=row['slug'],entry=row['entry'],params=row['params']);values=sorted(v for a in lists for v in a);ts=c.prepare(p,[dict(args=[lists],expected={'__list_node__':values})]);py=pyexecute(Path(row['python_source']).read_text(),p,ts);source=(R/'runs/js-corpus-wave-001/W001-B01/0023-role-style.js').read_text();js,raw,payload=exact_integer.execute(source,p.entry['method'],p.params,ts);assert py.passed and js.passed;assert 'expected' not in json.loads(payload);records.append(dict(kind='nested-node',input=lists,oracle='independent flatten plus numerical sort with multiplicity',python=py.to_dict(),javascript=js.to_dict()))
row=rows[30];p=SimpleNamespace(uid='lcd:30',slug=row['slug'],entry=row['entry']);ts=c.prepare(p,[dict(args=['ababab',['ab']],expected=[0,2,4])]);fixtures=[([4,2,0],True),([0,2],False),([0,2,4,4],False),([0,2,True],False),(['0',2,4],False),([0,2,6],False)]
for actual,accepted in fixtures:
 py=pyexecute('class Solution:\n def findSubstring(self,s,words):\n  return '+repr(actual)+'\n',p,ts);js,raw,payload=exact_integer.execute('function findSubstring(s, words) {return '+json.dumps(actual)+';}',p.entry['method'],row['params'],ts);assert py.passed==js.passed==accepted;records.append(dict(kind='index-order-adversarial',observed=actual,expected_acceptance=accepted,python=py.to_dict(),javascript=js.to_dict()))
report=dict(runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),nested_node_fixtures=8,order_adversarial_fixtures=6,language_executions=28,all_expected_outcomes=True,records=records)
with (OUT/'transport-controls.json').open('x') as f:json.dump(report,f,indent=2)
print('8 independent nonempty nested-list cases and 6 comparator fixtures passed in both runtimes')
