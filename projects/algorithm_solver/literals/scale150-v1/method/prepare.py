import json,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent;P=Path('/home/x/deco/gamma/projects/algorithm_solver');sha=lambda b:hashlib.sha256(b).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
c=json.loads((D/'stage-freeze.json').read_text());(D/'inputs').mkdir();rows=[]
for r in c['rows']:
 i=r['implementation'];src=(P/i['source']).read_bytes();assert sha(src)==i['source_sha256'];rp=P/i['qualification_receipt'];raw=rp.read_bytes()
 if i.get('qualification_receipt_sha256'):assert sha(raw)==i['qualification_receipt_sha256']
 receipt=json.loads(raw);metadata=receipt.get('independent_test_sets',receipt.get('test_metadata',[]));extra={}
 if r['id'] in [23,30]:
  home=P/'runs/js-corpus-b01-b02-review-128-v1';old=home/'frozen-package/manifest.json';manifest=json.loads(old.read_text());mrow=next(x for x in manifest['rows'] if x['id']==r['id']);metadata=mrow['independent_test_sets']
  assert sha(old.read_bytes())=='af62e96fb59049cd782f481a0e21b71c6a2f66174035d92b18ea9d5a3ef11ae9'
  assert receipt['qualified'] and receipt['quarantined_independent']==0 and receipt['valid_independent']==i['independent_cases']
  adapter=home/'executed-tooling/b01-b02-contracts.py';assert sha(adapter.read_bytes())=='47ebe492f9ce6246fafe64d457e42fce67c437595e37f36be450fa1a1d648e18'
  extra={'reviewed_adapter_sha256':sha(adapter.read_bytes()),'historical_quarantined_cases':0,'adapter':'nested list node input' if r['id']==23 else 'return:unordered_outer; result ordering still compared to original'}
 tests=[]
 for m in metadata:
  rawtests=Path(m['absolute_path']).read_bytes();part=json.loads(rawtests)
  forms=[rawtests,json.dumps(part,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode(),json.dumps(part,sort_keys=True,ensure_ascii=False).encode()]
  assert m['sha256'] in [sha(b) for b in forms];tests.extend(part)
 if r['id'] in [23,30]:
  records=[x for x in receipt['results'] if x['group']=='independent'];assert len(records)==len(tests)
  for k,(t,rec) in enumerate(zip(tests,records)):
   assert rec['index']==k and not rec['domain_reasons'] and rec['expected_unchanged'] and rec['javascript']['passed']
   assert sha(json.dumps(t,sort_keys=True,separators=(',',':')).encode())==rec['raw_test_sha256']
  if r['id']==30:
   tests=[{**t,'compare':'return:unordered_outer'} for t in tests]
  else:
   def node(v):
    if v is None:return None
    if isinstance(v,list):return {'__list_node__':v}
    assert isinstance(v,dict) and set(v)=={'__list_node__'};return v
   tests=[{**t,'args':[[node(v) for v in t['args'][0]]]} for t in tests]
 assert len(tests)==i['independent_cases'] and len(tests)>0
 assert all(set(t)<={'args','expected','compare'} and t.get('compare','return') in ['return','return:unordered_outer'] for t in tests)
 sf=f"inputs/{r['id']}.js";tf=f"inputs/{r['id']}-tests.json";(D/sf).write_bytes(src);write(D/tf,tests)
 rows.append({**r,'source_file':sf,'source_sha256':sha(src),'test_file':tf,'test_sha256':sha((D/tf).read_bytes()),'cases':len(tests),'receipt_sha256':sha(raw),'test_metadata':metadata,'extra':extra})
L=Path('/home/x/deco/gamma/output/literal-joint-v1/projects/algorithm_solver/literals')
codes=[D/'prepare.py',D/'generate.cjs',D/'harness.cjs',D/'qualify.py',D/'repair-contract.json',L/'scale-v2/generate.cjs',L/'rewrite-v1/generate.cjs',L/'pass3/generate.cjs',L/'rewrite-v1/fragment-proposals.cjs']
write(D/'contract.json',{'schema':'gamma.literal-scale150-inputs.v1','stage_sha256':sha((D/'stage-freeze.json').read_bytes()),'rows':rows,'limits':c['limits'],'code_hashes':{str(p):sha(p.read_bytes()) for p in codes},'comparison':'Unchanged return oracle plus original result/type, mutation and alias-topology parity. Runtime node wrappers are input/output serialization only; no source helper injected. Large integer transport exact and unsafe integers fail closed.'})
print(json.dumps({'problems':len(rows),'distinct_cases':sum(r['cases'] for r in rows),'contract_sha256':sha((D/'contract.json').read_bytes())}))
