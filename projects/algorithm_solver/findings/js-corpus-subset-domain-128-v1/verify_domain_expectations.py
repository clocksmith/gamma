from pathlib import Path
import hashlib,json,sys
ROOT=Path('/home/x/deco/gamma/projects/algorithm_solver');FIND=ROOT/'findings/js-corpus-subset-domain-128-v1';OUT=ROOT/'runs/js-corpus-subset-domain-128-v1';PACK=Path('/home/x/Documents/Codex/2026-10-19/task/js-corpus-wave-001')
sys.path[:0]=[str(ROOT),str(FIND)]
from algsolve.records import Problem,load_hidden_tests
from independent_domain_oracles import ORACLES
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
digest=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
manifest=json.loads((PACK/'manifest.json').read_text());rows={r['id']:r for r in manifest['rows'] if r['id'] in ORACLES}
problems={int(p['uid'].split(':')[1]):Problem.from_dict(p) for line in (ROOT/'data/derived/problems.jsonl').read_text().splitlines() if (p:=json.loads(line))['uid'] in [f'lcd:{n}' for n in ORACLES]}
seal=dict(oracle_module_sha256=sha(FIND/'independent_domain_oracles.py'),controls_sha256=sha(FIND/'test_independent_domain_oracles.py'),controls_passed=5,selection_sha256={str(n):sha(OUT/f'{n:04d}-selection-seal.json') for n in ORACLES},policy='Check the already sealed valid-domain existing expectations using independent formulations. Do not alter inputs, expectations, candidates or selection. These are oracle checks, not added solving cases.')
with (OUT/'oracle-verification-seal.json').open('x') as f:json.dump(seal,f,indent=2)
reports=[]
for n,oracle in ORACLES.items():
 row=rows[n];packet=json.loads(Path(row['problem_packet']).read_text());groups={'public':packet['public_tests'],'independent':load_hidden_tests(problems[n])};selection=json.loads((OUT/f'{n:04d}-selection-seal.json').read_text());results=[]
 for group,selected in selection['groups'].items():
  for item in selected:
   if not item['valid']:continue
   t=groups[group][item['index']];assert digest(t)==item['test_sha256'];observed=oracle(*t['args']);equal=type(observed) is type(t['expected']) and observed==t['expected']
   results.append(dict(group=group,index=item['index'],test_sha256=item['test_sha256'],matches_original_expected=equal,independent_observed=observed))
 report=dict(id=n,all_expected_verified=all(r['matches_original_expected'] for r in results),public_checked=sum(r['group']=='public' for r in results),independent_checked=sum(r['group']=='independent' for r in results),results=results)
 with (OUT/f'{n:04d}-independent-oracle-verification.json').open('x') as f:json.dump(report,f,indent=2)
 reports.append(report);print(n,report['all_expected_verified'],report['independent_checked'],flush=True)
with (OUT/'independent-oracle-summary.json').open('x') as f:json.dump(dict(seal_sha256=sha(OUT/'oracle-verification-seal.json'),rows=reports),f,indent=2)
