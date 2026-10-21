import hashlib,importlib.util,json,math,statistics,time
from pathlib import Path
from collections import defaultdict
D=Path(__file__).resolve().parent;A=D/'attempt-002';R=Path('/home/x/deco/gamma/output/literal-joint-v1');L=R/'projects/algorithm_solver/literals';sha=lambda b:hashlib.sha256(b).hexdigest()
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
unsupported=sorted(set(stage['additional_ids'])-new_passed);out=D/'measurement';out.mkdir();began=time.monotonic();records=[];packets=0
limits={'rounds_per_start':2,'trials_per_start':504,'seconds_per_start':120,'addition_shortlist':12,'removal_shortlist':4,'pair_addition_shortlist':4,'pair_removal_sets':2}
search_contract={'stage_sha256':sha((D/'stage-freeze.json').read_bytes()),'qualification_sha256':sha((A/'qualification/report.json').read_bytes()),'sources':len(meta),'new_qualified':len(new_passed),'unsupported':unsupported,'limits':limits,'rank_candidates_per_round':48,'max_ranking_probes_per_width':96,'total_score_probes_per_width_cap':600,'source_selection':'Exact DP for every valid source variant, shortest count then source bytes then stable variant name.','objective':'Selections then complete package; retain smaller-package tested alternatives.','widths':[7,8],'source_policy':'No new source transformations or case access during search. Every helper character counted.','code_hashes':{str(p):sha(p.read_bytes()) for p in [Path(__file__),L/'rank-v1/search.py',L/'joint-v1/search.py',L/'scale100-v1/search.py',L/'rewrite-v1/search.py',D/'original-bodies.json']}}
write(D/'search-contract.json',search_contract)
def group(m,vocab,ids,width):
 rows=[r for r in m['programs'] if r['id'] in ids];counts=[r['selections'] for r in rows];single=sum(sum(len(vocab[i])==1 for i in r['sequence']) for r in rows);payload=width*sum(counts);packet=sum(41+(width*n+7)//8 for n in counts)
 return {'denominator':len(ids),'represented':len(rows),'unsupported':sorted(set(ids)-{r['id'] for r in rows}),'selections':sum(counts),'median':statistics.median(counts) if counts else None,'p95':sorted(counts)[math.ceil(.95*len(counts))-1] if counts else None,'worst':max(counts,default=None),'character_fraction':single/sum(counts) if counts else None,'payload_bits':payload,'packet_bytes':packet,'framing_bytes':41*len(rows),'padding_bits':8*(packet-41*len(rows))-payload}
def save(label,ss,state,w):
 global packets
 folder=out/label;metrics=rw.save(folder,ss,meta,state,w,label);metrics.pop('new_source_problems',None);m=json.loads((folder/'manifest.json').read_text());m['metrics']=metrics;raw=(folder/'dictionary.ltd').read_bytes();size=len(raw)
 for r in m['programs']:
  r['entry']=meta[r['id'],r['variant']].get('entry','solve');pkt=(folder/f"{r['id']}.ltv").read_bytes();text,v,seq,width=audit.packet_audit.unpack(raw,pkt);assert text==ss[r['id']][r['variant']] and sha(text.encode())==r['source_sha256'];assert seq==r['sequence'] and len(seq)==audit.minimum_count(text,v) and width==w;packets+=1;size+=len(pkt)
 assert size==metrics['package_bytes'] and metrics['whole_program_literals']==0 and not set(state['vocab'])&banned
 write(folder/'manifest.json',m)
 record={'label':label,'width':w,'metrics':metrics,'shared100':group(m,state['vocab'],stage['original100_ids'],w),'shared125':group(m,state['vocab'],stage['prior_ids'],w),'stage125_added25':group(m,state['vocab'],stage['stage125_added_ids'],w),'added25':group(m,state['vocab'],stage['additional_ids'],w),'all150':group(m,state['vocab'],stage['prior_ids']+stage['additional_ids'],w),'dictionary_sha256':sha(raw),'manifest_sha256':sha((folder/'manifest.json').read_bytes())};records.append(record);write(D/'measurement-checkpoint.json',{'records':records,'packets_verified':packets});print(json.dumps({'label':label,**record['all150'],'package_bytes':size}),flush=True)
for w in [7,8]:
 budget=2**w;v=json.loads((D.parent/f'literal-scale125-v1/measurement/joint-input-{budget}/dictionary.json').read_text())
 shared=joint.evaluate(old,v,w);assert shared['selections']=={7:16099,8:9836}[w]
 frozen=joint.evaluate(fixed,v,w);save(f'frozen-original-{budget}',fixed,frozen,w)
 normalized=joint.evaluate(expanded,v,w);save(f'frozen-normalized-{budget}',expanded,normalized,w)
 rankings=[];width_start=time.monotonic()
 def proposals(ss,state,limit):
  pool=list(dict.fromkeys(rw.ast_rank(ss,state['vocab'],admitted,24)+[f for f in rw.old_proposals(ss,state,24) if f not in banned]))[:48]
  actual=[]
  for f in pool:
   if time.monotonic()-width_start>=120:break
   actual.append((rank.exact_add(ss,state,f,w),f))
  selected=[f for m,f in sorted(actual,key=lambda x:(x[0]['selections'],x[0]['package_bytes'],len(x[1]),x[1]))[:limit]]
  rankings.append({'before':joint.brief(state),'candidates':[{'fragment':f,**m} for m,f in actual],'selected':selected});return selected
 joint.proposals=proposals
 final,trace=joint.improve(expanded,normalized,w,'input',limits);write(out/f'trace-{budget}.json',{'initial_dictionary':normalized['vocab'],'initial':joint.brief(normalized),**trace,'rankings':rankings})
 save(f'joint-input-{budget}',expanded,final,w)
 # A storage alternative is selected only from already measured, legal moves.
 candidates=[(normalized['package_bytes'],normalized['selections'],normalized['vocab']),(final['package_bytes'],final['selections'],final['vocab'])];current=set(normalized['vocab'])
 for step in trace['rounds']:
  for move in step['attempts']:
   vv=current-set(move['remove'])|set(move['add']);candidates.append((move['result']['package_bytes'],move['result']['selections'],sorted(vv)))
  if step['accepted']:current=current-set(step['accepted']['remove'])|set(step['accepted']['add']);current-=set(step['pruned_after_move'])
 _,_,sv=min(candidates,key=lambda x:(x[0],x[1],x[2]));storage=joint.evaluate(expanded,sv,w);save(f'joint-storage-{budget}',expanded,storage,w)
 # Independent forward scoring verifies all chosen source alternatives.
 exact,chosen=audit.score(expanded,final['vocab'],w)
 assert all(final[k]==exact[k] for k in ['selections','package_bytes','dictionary_bytes','packet_bytes'])
 assert all(chosen[pid][0]==v for pid,v in final['chosen'].items())
write(D/'summary.json',{'records':records,'failures':failures,'unsupported_problems':unsupported,'packets_verified':packets,'elapsed_seconds':time.monotonic()-began,'search_contract_sha256':sha((D/'search-contract.json').read_bytes()),'qualification_sha256':sha((A/'qualification/report.json').read_bytes()),'scope':'150 exposed development problems; all failures retained. Exact representation, not autonomous solving or M1 qualification.','milestone1_qualified':False,'artifact_bytes':sum(p.stat().st_size for p in D.rglob('*') if p.is_file())})
