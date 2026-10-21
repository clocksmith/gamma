import hashlib,importlib.util,itertools,json,time
from pathlib import Path
D=Path(__file__).resolve().parent;R=Path('/home/x/deco/gamma/output/literal-joint-v1');L=R/'projects/algorithm_solver/literals'
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
scale=mod('matrix_scale',L/'scale100-v1/search.py');rw=scale.rw;joint=rw.joint;audit=mod('matrix_audit',L/'joint-v1/audit.py')
c=json.loads((D/'contract.json').read_text());q=json.loads((D/'qualification/report.json').read_text());assert q['passed'] and q['contract_sha256']==sha((D/'contract.json').read_bytes())
for group in ['code_hashes','inputs']:
 for p,h in c[group].items():assert sha(Path(p).read_bytes())==h
old,meta,_,banned=scale.load(R/'output/literal-row-v1');assert len(old)==100 and sum(map(len,old.values()))==674
wq=json.loads((D.parent/'literal-window-count-v1/qualification/report.json').read_text());assert wq['passed']
rankstates={}
for width in [7,8]:
 vocab=json.loads((R/f'output/literal-rank-v1/exact-{2**width}/dictionary.json').read_text());state=joint.evaluate(old,vocab,width);assert state['selections']=={7:11558,8:6963}[width];rankstates[width]=vocab
for r in wq['rows']:
 if r['variant']=='original':continue
 text=Path(r['file']).read_text();assert sha(text.encode())==r['sha256'];old[76][r['variant']]=text;meta[76,r['variant']]=r
new={pid:dict(vs) for pid,vs in old.items()}
for r in q['rows']:
 if r['variant']=='original':continue
 text=Path(r['file']).read_text();assert sha(text.encode())==r['sha256'];new[r['id']][r['variant']]=text;meta[r['id'],r['variant']]=r
fragments=json.loads((D/'fragments.json').read_text());assert len(fragments)==6 and sha((D/'fragments.json').read_bytes())==c['fragments_sha256']
for r in fragments:
 assert r['literal'] not in banned and sha(r['literal'].encode())==r['sha256']
 assert len({pid for pid,vs in new.items() if any(r['literal'] in x for x in vs.values())})>=2
parts=[r['literal'] for r in fragments];began=time.monotonic();records=[];all_trials=[];audited=0;(D/'packages').mkdir()
def save(label,ss,state,width):
 global audited
 folder=D/'packages'/label;metrics=rw.save(folder,ss,meta,state,width,label);m=json.loads((folder/'manifest.json').read_text());raw=(folder/'dictionary.ltd').read_bytes();total=len(raw)
 for r in m['programs']:
  pkt=(folder/(str(r['id'])+'.ltv')).read_bytes();text,vocab,seq,w=audit.packet_audit.unpack(raw,pkt);total+=len(pkt)
  assert w==width and text==ss[r['id']][r['variant']] and sha(text.encode())==r['source_sha256']
  assert seq==r['sequence'] and len(seq)==audit.minimum_count(text,vocab);audited+=1
 assert total==metrics['package_bytes'] and metrics['whole_program_literals']==0
 row={'label':label,'metrics':metrics,'programs':[{k:r[k] for k in ['id','variant','selections','source_sha256']} for r in m['programs']],'dictionary_sha256':sha(raw),'manifest_sha256':sha((folder/'manifest.json').read_bytes())};records.append(row)
 write(D/'checkpoint.json',{'records':records,'audited':audited});print(json.dumps({'label':label,**joint.brief(state),'median':metrics['median_selections'],'p95':metrics['p95_selections'],'characters':metrics['single_character_selection_fraction']}),flush=True)
for width in [7,8]:
 start=time.monotonic();vocab=rankstates[width];baseline=joint.evaluate(old,vocab,width);assert baseline['selections']=={7:11549,8:6938}[width]
 save(f'baseline-{2**width}',old,baseline,width)
 source=joint.evaluate(new,vocab,width);save(f'source-only-{2**width}',new,source,width)
 pruned,removed=joint.prune(old,baseline,width);save(f'pruned-control-{2**width}',old,pruned,width)
 seed=joint.evaluate(new,pruned['vocab'],width);save(f'pruned-source-{2**width}',new,seed,width)
 candidates=[];trials=[]
 for mask in range(64):
  assert time.monotonic()-start<c['limits']['search_seconds_per_width']
  additions=[parts[i] for i in range(6) if mask>>i&1];v=set(seed['vocab'])|set(additions)
  if len(v)>2**width:trials.append({'mask':mask,'status':'over-cap'});continue
  state=joint.evaluate(new,v,width,seed);candidates.append((mask,state));trials.append({'mask':mask,'status':'measured','fragments':[i for i in range(6) if mask>>i&1],**joint.brief(state)})
 by_input=min(candidates,key=lambda p:(p[1]['selections'],p[1]['package_bytes'],p[0]));by_storage=min(candidates,key=lambda p:(p[1]['package_bytes'],p[1]['selections'],p[0]))
 dictionary_only=joint.evaluate(old,by_input[1]['vocab'],width);save(f'dictionary-only-{2**width}',old,dictionary_only,width)
 save(f'joint-input-{2**width}',new,by_input[1],width);save(f'joint-storage-{2**width}',new,by_storage[1],width)
 pareto=[r for r in trials if r['status']=='measured' and not any(t['status']=='measured' and t['selections']<=r['selections'] and t['package_bytes']<=r['package_bytes'] and (t['selections']<r['selections'] or t['package_bytes']<r['package_bytes']) for t in trials)]
 trace={'width':width,'removed_unused':removed,'trials':trials,'best_input_mask':by_input[0],'best_storage_mask':by_storage[0],'pareto':pareto,'elapsed_seconds':time.monotonic()-start};write(D/f'trace-{2**width}.json',trace);all_trials.append(trace)
size=sum(p.stat().st_size for p in D.rglob('*') if p.is_file());assert size<c['limits']['max_artifact_bytes']
result={'schema':'gamma.matrix-kernels.measurement.v1','records':records,'packets_independently_decoded':audited,'dictionary_trials':sum(len(x['trials']) for x in all_trials),'pareto_by_width':{str(x['width']):x['pareto'] for x in all_trials},'elapsed_seconds':time.monotonic()-began,'artifact_bytes':size,'contract_sha256':sha((D/'contract.json').read_bytes()),'qualification_sha256':sha((D/'qualification/report.json').read_bytes()),'code_sha256':sha(Path(__file__).read_bytes()),'scope':'676 fixed existing qualified alternatives including window successor, four new independently qualified sources; 100 exposed problems; no autonomous claim. Exact exhaustive search restricted to six predeclared fragments, not global optimality.','milestone1_qualified':False,'private_artifacts':True}
write(D/'summary.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ['records','pareto_by_width']}),flush=True)
