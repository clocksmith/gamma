import json,time,hashlib,importlib.util,subprocess,statistics,math
from pathlib import Path
C=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('fixed150',C/'load_sources.py');data=importlib.util.module_from_spec(spec);spec.loader.exec_module(data)
D=data.D;ss=data.expanded;meta=data.meta;joint=data.joint;rw=data.rw;audit=data.audit;rank=data.rank;sha=data.sha;write=data.write
rows=[{'id':pid,'variant':v,'text':t} for pid,vs in ss.items() for v,t in vs.items()];write(C/'token-input.json',rows)
limits={'rounds_per_start':8,'trials_per_start':2400,'seconds_per_start':180,'addition_shortlist':16,'removal_shortlist':6,'pair_addition_shortlist':4,'pair_removal_sets':3}
contract={'schema':'gamma.literal-scale150-ast-span-control.v1','problems':150,'source_variants':len(rows),'source_policy':'No new source variants or test access. Reuse all1006 independently qualified alternatives from scale150.','candidate_policy':'Ablation: deeper existing AST plus encoded-span proposals only,48 of each with96 total exact ranking probes per round. Same sources, seeds,8 rounds,2400 legal moves and180 seconds as token arm. No lexical candidates.','limits':limits,'ranking_cap_per_round':96,'ranking_cap_per_width':768,'legal_move_cap_per_width':2400,'wall_limit_per_width_seconds':180,'widths':[7,8],'objective':'Selections then complete package; preserve smaller-storage candidates and matched subsets. No claim of global optimality.','source_manifest_sha256':sha((D/'independent-audit.json').read_bytes()),'no_protected_access':True,'code_hashes':{str(p):sha(p.read_bytes()) for p in [C/'search.py',C/'load_sources.py',C/'token-candidates.cjs']},'success':'Lower selection count or lower package cost under exact reconstruction, unchanged qualified sources, no whole-source/body entries, no unreported subset regression.'}
assert not (C/'contract.json').exists();write(C/'contract.json',contract)
subprocess.run(['node',str(C/'token-candidates.cjs'),str(C/'token-input.json'),str(C/'token-candidates.json')],check=True)
lex=[r['text'] for r in json.loads((C/'token-candidates.json').read_text()) if r['text'] not in data.banned];out=C/'measurement';out.mkdir();records=[]
def group(state,ids,w):
 counts=[len(state['parsed'][pid,state['chosen'][pid]]) for pid in ids];parts=[p for pid in ids for p in state['parsed'][pid,state['chosen'][pid]]]
 return {'denominator':len(ids),'represented':len(counts),'selections':sum(counts),'median':statistics.median(counts),'p95':sorted(counts)[math.ceil(.95*len(counts))-1],'worst':max(counts),'character_fraction':sum(len(p)==1 for p in parts)/len(parts),'payload_bits':w*sum(counts),'framing_bytes':41*len(ids),'packet_bytes':sum(41+(w*n+7)//8 for n in counts)}
def save(label,state,w):
 folder=out/label;metrics=rw.save(folder,ss,meta,state,w,label);metrics.pop('new_source_problems',None);m=json.loads((folder/'manifest.json').read_text());m['metrics']=metrics
 for row in m['programs']:row['entry']=meta[row['id'],row['variant']].get('entry','solve')
 write(folder/'manifest.json',m)
 r={'label':label,'width':w,'metrics':metrics,'shared100':group(state,data.stage['original100_ids'],w),'shared125':group(state,data.stage['prior_ids'],w),'added25':group(state,data.stage['additional_ids'],w),'all150':group(state,sorted(ss),w),'dictionary_sha256':sha((folder/'dictionary.ltd').read_bytes()),'manifest_sha256':sha((folder/'manifest.json').read_bytes())};records.append(r);write(C/'checkpoint.json',records);print(json.dumps({'label':label,**joint.brief(state),**r['all150']}),flush=True)
for w in [7,8]:
 start=time.monotonic();initial=joint.evaluate(ss,json.loads((D/f'measurement/joint-input-{2**w}/dictionary.json').read_text()),w);save(f'control-{2**w}',initial,w);rankings=[]
 def proposals(sources,state,limit):
  pool=list(dict.fromkeys(rw.ast_rank(sources,state['vocab'],data.admitted,48)+[f for f in rw.old_proposals(sources,state,48) if f not in data.banned]))[:96]
  actual=[]
  for f in pool:
   if time.monotonic()-start>=180:break
   actual.append((rank.exact_add(sources,state,f,w),f))
  chosen=[f for m,f in sorted(actual,key=lambda x:(x[0]['selections'],x[0]['package_bytes'],len(x[1]),x[1]))[:limit]];rankings.append({'before':joint.brief(state),'candidates':[{'fragment':f,**m} for m,f in actual],'selected':chosen});return chosen
 joint.proposals=proposals
 final,trace=joint.improve(ss,initial,w,'input',limits);write(out/f'trace-{2**w}.json',{'initial_dictionary':initial['vocab'],**trace,'rankings':rankings});save(f'ast-span-input-{2**w}',final,w)
 candidates=[(initial['package_bytes'],initial['selections'],initial['vocab']),(final['package_bytes'],final['selections'],final['vocab'])];current=set(initial['vocab'])
 for step in trace['rounds']:
  for move in step['attempts']:candidates.append((move['result']['package_bytes'],move['result']['selections'],sorted(current-set(move['remove'])|set(move['add']))))
  if step['accepted']:current=current-set(step['accepted']['remove'])|set(step['accepted']['add']);current-=set(step['pruned_after_move'])
 _,_,v=min(candidates,key=lambda x:(x[0],x[1],x[2]));save(f'ast-span-storage-{2**w}',joint.evaluate(ss,v,w),w)
write(C/'summary.json',{'records':records,'contract_sha256':sha((C/'contract.json').read_bytes()),'scope':'150 known development programs only; not M1 qualification, generalization or autonomous assembly.'})
