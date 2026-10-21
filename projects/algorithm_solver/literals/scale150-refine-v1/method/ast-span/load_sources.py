import hashlib,importlib.util,json,math,statistics,time
from pathlib import Path
from collections import defaultdict
D=Path('/home/x/Documents/Codex/2026-10-19/task/literal-scale150-v1');A=D/'attempt-002';R=Path('/home/x/deco/gamma/output/literal-joint-v1');L=R/'projects/algorithm_solver/literals';sha=lambda b:hashlib.sha256(b).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
scale=mod('s150_scale',L/'scale100-v1/search.py');rw=scale.rw;joint=rw.joint;rank=mod('s150_rank',L/'rank-v1/search.py');audit=mod('s150_audit',L/'joint-v1/audit.py')
stage=json.loads((D/'stage-freeze.json').read_text());q=json.loads((A/'qualification/report.json').read_text());g=json.loads((A/'generated/manifest.json').read_text())
assert q['contract_sha256']==sha((A/'contract.json').read_bytes()) and q['generated_manifest_sha256']==sha((A/'generated/manifest.json').read_bytes())
for p,h in stage['inputs'].items():assert sha(Path(p).read_bytes())==h
old,meta,admitted,banned=scale.load(R/'output/literal-row-v1')
for directory in ['literal-window-count-v1','literal-matrix-kernels-v1']:
 report=json.loads((D.parent/directory/'qualification/report.json').read_text());assert report['passed']
 for r in report['rows']:
  if r['variant']=='original':continue
  r={**r,'id':76 if directory=='literal-window-count-v1' else r['id']};text=Path(r['file']).read_text();assert sha(text.encode())==r['sha256'];old[r['id']][r['variant']]=text;meta[r['id'],r['variant']]=r;banned.add(text)
assert len(old)==100
owners125=defaultdict(set)
priorq=json.loads((D.parent/'literal-scale125-v1/attempt-003/qualification/report.json').read_text())
for r in priorq['rows']:
 assert r['passed'];text=Path(r['file']).read_text();assert sha(text.encode())==r['sha256'];old.setdefault(r['id'],{})[r['variant']]=text;meta[r['id'],r['variant']]=r
 banned.update(r.get('excluded',[]));banned.add(text)
 for f in r.get('fragments',[]):owners125[f].add(r['id'])
admitted|={f for f,ids in owners125.items() if len(ids)>=2 and f not in banned}
banned.update(json.loads((D.parent/'literal-scale125-v1/original-bodies.json').read_text()))
assert len(old)==125
fixed={pid:dict(vs) for pid,vs in old.items()};expanded={pid:dict(vs) for pid,vs in old.items()};owners=owners125;new_passed=set();failures=[]
for r in q['rows']:
 if not r['passed']:failures.append({'id':r['id'],'variant':r['variant'],'failures':r['failures']});continue
 text=Path(r['file']).read_text();assert sha(text.encode())==r['sha256'];new_passed.add(r['id']);meta[r['id'],r['variant']]=r
 expanded.setdefault(r['id'],{})[r['variant']]=text
 if r['variant']=='original':fixed.setdefault(r['id'],{})[r['variant']]=text
 banned.update(r.get('excluded',[]));banned.add(text)
 for f in r.get('fragments',[]):owners[f].add(r['id'])
admitted|={f for f,ids in owners.items() if len(ids)>=2 and f not in banned}
# Whole-body exclusions also cover original entrypoint names; these strings
# only constrain the candidate pool and never enter the decoder implicitly.
body_exclusions=json.loads((D/'original-bodies.json').read_text());banned.update(body_exclusions)
admitted-=banned
