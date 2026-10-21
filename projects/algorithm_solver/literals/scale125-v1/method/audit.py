"""Independent host replay and forward-DP/source-choice audit; never runs sources."""
import json,hashlib,importlib.util,math,statistics,sys,re
from pathlib import Path
from collections import defaultdict
D=Path(__file__).resolve().parent;A=D/'attempt-003';R=Path('/home/x/deco/gamma/output/literal-joint-v1');L=R/'projects/algorithm_solver/literals';sys.path.insert(0,str(L.parent))
from algsolve.judge.judge import FunctionalTest,_matches
sha=lambda b:hashlib.sha256(b).hexdigest()
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
audit=module('a125_forward',L/'joint-v1/audit.py')
def exact(a,b):
 if isinstance(a,bool) or isinstance(b,bool):return type(a)==type(b) and a==b
 if isinstance(a,(float,int)) and isinstance(b,(float,int)):return a==b
 if type(a)!=type(b):return False
 if isinstance(a,list):return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
 if isinstance(a,dict):return a.keys()==b.keys() and all(exact(v,b[k]) for k,v in a.items())
 return a==b
def expected(x):
 if isinstance(x,list):return [expected(v) for v in x]
 if isinstance(x,dict):
  if x=={'__list_node__':[]} or x=={'__tree_node__':[]}:return None
  return {k:expected(v) for k,v in x.items()}
 return x
c=json.loads((A/'contract.json').read_text());q=json.loads((A/'qualification/report.json').read_text());stage=json.loads((D/'stage-freeze.json').read_text());summary=json.loads((D/'summary.json').read_text());count=0;logs=0;aliases=0
for spec in c['rows']:
 tests=json.loads((A/spec['test_file']).read_text());assert sha((A/spec['test_file']).read_bytes())==spec['test_sha256'];original=None
 rows=sorted((r for r in q['rows'] if r['id']==spec['id']),key=lambda r:(r['variant']!='original',r['variant']))
 for r in rows:
  assert sha(Path(r['file']).read_bytes())==r['sha256'] and r['passed'];seen=[]
  for call in r['calls']:
   assert call['exit_code']==0 and not call['timed_out']
   for ext in ['stdout','stderr']:
    raw=(A/'qualification/observations'/f"{call['stem']}.{ext}").read_bytes();assert sha(raw)==call[ext+'_sha256'];logs+=1
   lines=[json.loads(x) for x in (A/'qualification/observations'/f"{call['stem']}.stdout").read_bytes().splitlines()];assert lines[-1]=={'done':len(lines)-1}
   for k,rec in enumerate(lines[:-1]):
    assert set(rec)=={'i','result','result_type','args_before','args_after','alias_edges'} and rec['i']==k
    case=tests[len(seen)];value=rec['result'];kind=rec['result_type']
    if kind=='bigint':assert isinstance(value,dict) and set(value)=={'__gamma_bigint_v1__'} and re.fullmatch(r'-?(0|[1-9][0-9]*)',value['__gamma_bigint_v1__']);value=int(value['__gamma_bigint_v1__'])
    elif kind=='boolean':assert type(value)==bool
    elif kind=='number':assert type(value) in [int,float] and (not isinstance(value,int) or abs(value)<=2**53-1)
    elif kind=='string':assert isinstance(value,str)
    else:assert kind=='object' and (value is None or isinstance(value,(dict,list)))
    assert _matches(FunctionalTest(args=case['args'],expected=expected(case['expected']),compare='return'),{'result':value})
    observation={k:v for k,v in rec.items() if k!='i'}
    if original is not None:assert exact(observation,original[len(seen)])
    aliases+=bool(rec['alias_edges']);seen.append(observation);count+=1
  assert len(seen)==len(tests)
  if r['variant']=='original':original=seen
assert count==q['checks_total']==15272
# Rebuild the complete source alternatives from their qualified receipts.
sources=defaultdict(dict);meta={}
for r in json.loads((R/'output/literal-row-v1/pool.json').read_text())['rows']:sources[r['id']][r['variant']]=Path(r['file']).read_text();meta[r['id'],r['variant']]=r
for name in ['literal-window-count-v1','literal-matrix-kernels-v1']:
 for r in json.loads((D.parent/name/'qualification/report.json').read_text())['rows']:
  if r['variant']=='original':continue
  pid=76 if name=='literal-window-count-v1' else r['id'];sources[pid][r['variant']]=Path(r['file']).read_text();meta[pid,r['variant']]=r
for r in q['rows']:
 if r['passed']:sources[r['id']][r['variant']]=Path(r['file']).read_text();meta[r['id'],r['variant']]=r
for pid,vs in sources.items():
 for v,t in vs.items():assert sha(t.encode())==meta[pid,v]['sha256']
packets=0;choices=0
for record in summary['records']:
 folder=D/'measurement'/record['label'];m=json.loads((folder/'manifest.json').read_text());d=(folder/'dictionary.ltd').read_bytes();vocab=json.loads((folder/'dictionary.json').read_text());w=record['width'];ss={pid:{v:t for v,t in vs.items() if pid in stage['prior_ids'] or not record['label'].startswith('frozen-original') or v=='original'} for pid,vs in sources.items()}
 scored,selected=audit.score(ss,vocab,w)
 for key in ['selections','package_bytes','dictionary_bytes','packet_bytes']:assert scored[key]==record['metrics'][key]
 for r in m['programs']:
  packet=(folder/f"{r['id']}.ltv").read_bytes();text,words,seq,width=audit.packet_audit.unpack(d,packet);assert text==ss[r['id']][r['variant']] and width==w and seq==r['sequence'];assert selected[r['id']]==(r['variant'],len(seq));assert sha(text.encode())==r['source_sha256'];packets+=1;choices+=1
 for f in vocab:
  if len(f)>1:assert sum(any(f in t for t in vs.values()) for vs in sources.values())>=2
 assert len(vocab)<=2**w
assert packets==1000
size=sum(p.stat().st_size for p in D.rglob('*') if p.is_file());assert size<stage['limits']['max_artifact_bytes']
result={'passed':True,'oracle_and_original_parity_replays':count,'native_log_hashes_verified':logs,'records_with_observed_aliasing':aliases,'packets_independently_decoded':packets,'source_choices_independently_minimized':choices,'source_alternatives':sum(map(len,sources.values())),'qualification_sha256':sha((A/'qualification/report.json').read_bytes()),'summary_sha256':sha((D/'summary.json').read_bytes()),'audit_code_sha256':sha(Path(__file__).read_bytes()),'artifact_bytes':size}
(D/'independent-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
