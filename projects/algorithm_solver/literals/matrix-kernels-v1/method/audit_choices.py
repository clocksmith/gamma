import hashlib,importlib.util,json
from pathlib import Path
D=Path(__file__).resolve().parent;L=Path('/home/x/deco/gamma/output/literal-joint-v1/projects/algorithm_solver/literals');R=L.parents[2]
sha=lambda b:hashlib.sha256(b).hexdigest()
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
scale=mod('choice_scale',L/'scale100-v1/search.py');audit=mod('choice_audit',L/'joint-v1/audit.py');ss,_,_,_=scale.load(R/'output/literal-row-v1');observations=0
for folder,pid in [(D.parent/'literal-window-count-v1',76),(D,None)]:
 q=json.loads((folder/'qualification/report.json').read_text());assert q['passed']
 for r in q['rows']:
  assert r['checks_passed']==r['checks_total'] and not r['failures']
  for call in r['calls']:
   assert call['exit_code']==0 and not call['timed_out']
   for ext in ['stdout','stderr']:
    assert sha((folder/'qualification/observations'/(call['stem']+'.'+ext)).read_bytes())==call[ext+'_sha256'];observations+=1
  if r['variant']=='original':continue
  text=Path(r['file']).read_text();assert sha(text.encode())==r['sha256'];ss[pid if pid else r['id']][r['variant']]=text
assert len(ss)==100 and sum(map(len,ss.values()))==680
checks=[]
for width in [7,8]:
 b=2**width;trace=json.loads((D/f'reselection/trace-{b}.json').read_text());vocab=json.loads((D/f'reselection/packages/source-only-{b}/dictionary.json').read_text())
 for step,fragment in enumerate(trace['removed_unused']):
  vocab.remove(fragment);cost,chosen=audit.score(ss,vocab,width)
  rec=next(r for r in trace['removal_trials'] if r['step']==step and r['fragment_sha256']==sha(fragment.encode()))
  for k,v in cost.items():assert rec[k]==v,(step,k,v,rec[k])
  checks.append({'width':width,'deletion_step':step,'passed':True})
 for label in ['joint-input','joint-storage']:
  folder=D/f'reselection/packages/{label}-{b}';vocab=json.loads((folder/'dictionary.json').read_text());m=json.loads((folder/'manifest.json').read_text());cost,chosen=audit.score(ss,vocab,width)
  for k,v in cost.items():assert m['metrics'][k]==v
  for r in m['programs']:assert chosen[r['id']]==(r['variant'],r['selections'])
  checks.append({'width':width,'label':label,'independent_source_choices':100,'passed':True})
result={'passed':True,'checks':checks,'independently_replayed_deletions':12,'independently_selected_sources':400,'variants':680,'verified_observation_files':observations,'code_sha256':sha(Path(__file__).read_bytes())}
(D/'choice-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
