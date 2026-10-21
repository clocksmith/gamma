import json,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent;P=Path('/home/x/deco/gamma/projects/algorithm_solver');sha=lambda b:hashlib.sha256(b).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
c=json.loads((D/'stage-freeze.json').read_text());(D/'inputs').mkdir();rows=[]
for r in c['rows']:
 i=r['implementation'];src=(P/i['source']).read_bytes();assert sha(src)==i['source_sha256'];rp=P/i['qualification_receipt'];raw=rp.read_bytes()
 if i.get('qualification_receipt_sha256'):assert sha(raw)==i['qualification_receipt_sha256']
 receipt=json.loads(raw);metadata=receipt.get('independent_test_sets',receipt.get('test_metadata',[]));extra={}
 if r['id']==115:
  p=P/'runs/js-exact-integer-115-128-v1/contract.json';sc=json.loads(p.read_text());metadata=sc['tests'];extra={'numeric_contract':sc['numeric_contract'],'contract_sha256':sha(p.read_bytes())}
 tests=[]
 for m in metadata:
  rawtests=Path(m['absolute_path']).read_bytes();part=json.loads(rawtests)
  forms=[rawtests,json.dumps(part,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode(),json.dumps(part,sort_keys=True,ensure_ascii=False).encode()]
  assert m['sha256'] in [sha(b) for b in forms];tests.extend(part)
 assert len(tests)==i['independent_cases'] and len(tests)>0
 assert all(set(t)<={'args','expected','compare'} and t.get('compare','return')=='return' for t in tests)
 sf=f"inputs/{r['id']}.js";tf=f"inputs/{r['id']}-tests.json";(D/sf).write_bytes(src);write(D/tf,tests)
 rows.append({**r,'source_file':sf,'source_sha256':sha(src),'test_file':tf,'test_sha256':sha((D/tf).read_bytes()),'cases':len(tests),'receipt_sha256':sha(raw),'test_metadata':metadata,'extra':extra})
L=Path('/home/x/deco/gamma/output/literal-joint-v1/projects/algorithm_solver/literals')
codes=[D/'prepare.py',D/'generate.cjs',D/'harness.cjs',D/'qualify.py',L/'scale-v2/generate.cjs',L/'rewrite-v1/generate.cjs',L/'pass3/generate.cjs',L/'rewrite-v1/fragment-proposals.cjs']
write(D/'contract.json',{'schema':'gamma.literal-scale125-inputs.v1','stage_sha256':sha((D/'stage-freeze.json').read_bytes()),'rows':rows,'limits':c['limits'],'code_hashes':{str(p):sha(p.read_bytes()) for p in codes},'comparison':'Unchanged return oracle plus original result/type, mutation and alias-topology parity. Runtime node wrappers are input/output serialization only; no source helper injected. Large integer transport exact and unsafe integers fail closed.'})
print(json.dumps({'problems':len(rows),'distinct_cases':sum(r['cases'] for r in rows),'contract_sha256':sha((D/'contract.json').read_bytes())}))
