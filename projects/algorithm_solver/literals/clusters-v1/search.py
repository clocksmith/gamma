"""Fit-only bounded static-string dictionaries; exact segmentation, explicit costs."""
import argparse,collections,hashlib,json,math,re,statistics,sys,time,struct
from pathlib import Path
sha=lambda b:hashlib.sha256(b).hexdigest()
jbytes=lambda x:(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n').encode()
def trie(vocab):
 root={}
 for i,s in enumerate(vocab):
  node=root
  for c in s:node=node.setdefault(c,{})
  node[None]=i
 return root

def encode_text(text,tree):
 n=len(text);cost=[n+1]*(n+1);edge=[None]*n;cost[n]=0
 for pos in range(n-1,-1,-1):
  node=tree;j=pos
  while j<n and text[j] in node:
   node=node[text[j]];j+=1
   if None in node and (cost[j]+1<cost[pos] or cost[j]+1==cost[pos] and (edge[pos] is None or node[None]<edge[pos][0])):cost[pos]=cost[j]+1;edge[pos]=(node[None],j)
 if cost[0]>n:raise ValueError('unrepresentable')
 result=[];pos=0
 while pos<n:
  i,pos=edge[pos];result.append(i)
 return result

def structural_groups(signatures):
 groups=[{i} for i in sorted(signatures)];similarities={}
 for i in signatures:
  for j in signatures:
   if i<j:similarities[(i,j)]=len(signatures[i]&signatures[j])/max(1,len(signatures[i]|signatures[j]))
 merges=[]
 while len(groups)>4:
  choices=[]
  for a in range(len(groups)):
   for b in range(a+1,len(groups)):
    score=max(similarities[tuple(sorted((i,j)))] for i in groups[a] for j in groups[b]);choices.append((-score,tuple(sorted(groups[a]|groups[b])),a,b))
  neg,members,a,b=min(choices);merges.append({'members':members,'similarity':-neg});merged=groups[a]|groups[b];groups=[g for k,g in enumerate(groups) if k not in [a,b]]+[merged];groups.sort(key=lambda g:tuple(sorted(g)))
 return groups,merges

def main():
 p=argparse.ArgumentParser();p.add_argument('--pilot',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parent;c=json.loads((root/'contract.json').read_text());a.output.mkdir(exist_ok=False);(a.output/'encodings').mkdir();(a.output/'pools').mkdir();(a.output/'packets').mkdir();sys.path[:0]=[str(a.pilot),str(a.pilot/'pass2/working')]
 from literals import dictionary_bytes,pieces,merged_dictionary
 from bitpack import encode,decode
 manifest=json.loads((root/'fit-generated-v1/manifest.json').read_text());assert manifest['generator_sha256']==sha((root/'generate.cjs').read_bytes());reports=[json.loads((root/f/'report.json').read_text()) for f in ['fit-qualification-v1','fit-input-policy-recheck']];qualified={}
 for report in reports:
  for row in report['rows']:qualified[(row['id'],row['variant'])]=row
 assert len(qualified)==144 and all(r['passed'] for r in qualified.values())
 sources=collections.defaultdict(dict);source_hashes={}
 for row in manifest['rows']:
  if row['variant']=='original':continue
  text=(root/'fit-generated-v1'/row['file']).read_text();assert sha(text.encode())==row['sha256'];sources[row['id']][row['variant']]=text;source_hashes[f"{row['id']}/{row['variant']}"]=row['sha256']
 fit=set(i for cluster in c['clusters'].values() for i in cluster['fit']);assert set(sources)==fit
 features=json.loads((root/'fit-generated-v1/features.json').read_text());signatures={i:set(features[f'{i:04d}/canonical']['structural_signatures']) for i in fit};groups,merges=structural_groups(signatures);group_of={i:k for k,g in enumerate(groups) for i in g}
 (a.output/'structural-clusters.json').write_bytes(jbytes({'method':'Single-link agglomeration of Jaccard AST signatures with identifier/literal values erased ONLY for proposal similarity; emitted strings retain every concrete byte. Stop at four groups.','groups':[sorted(g) for g in groups],'merges':merges,'fit_only':True}))
 started=time.monotonic();records=[];states={};pools={};seen={}
 def options(ids,arm):return {i:{v:t for v,t in sources[i].items() if arm=='joint' or v==arm} for i in sorted(ids)}
 def evaluate(pool,ids,arm,method,diagnostic=False,parent=None):
  if len(records)>=c['max_dictionary_trials'] or time.monotonic()-started>=c['max_search_wall_seconds']:return None
  vocab=sorted(set(pool));opts=options(ids,arm);identity=sha(jbytes({'pool':vocab,'ids':sorted(ids),'arm':arm}))[:20]
  if identity in seen:return seen[identity]
  began=time.monotonic();tree=trie(vocab);programs={}
  for i,variants in opts.items():
   choices=[]
   for v,text in variants.items():
    try:seq=encode_text(text,tree)
    except ValueError:continue
    choices.append((len(seq),len(text.encode()),v,seq,text))
   if choices:
    _,_,v,seq,text=min(choices);programs[str(i)]={'variant':v,'source_sha256':sha(text.encode()),'sequence':seq}
  # Charge every stored entry, including fallback characters; no free dormant alphabet.
  owners=collections.defaultdict(set)
  for i,row in programs.items():
   for index in row['sequence']:owners[index].add(i)
  counts=[len(row['sequence']) for row in programs.values()];dictionary=dictionary_bytes(vocab);width=max(4,(len(vocab)-1).bit_length());feasible=len(vocab)<=256;costs=[]
  for budget in c['entry_budgets']:
   w=int(math.log2(budget));ok=len(vocab)<=budget
   cost={'budget':budget,'bits_per_selection':w,'feasible':ok}
   if ok:
    packets={i:encode(vocab,row['sequence'],w) for i,row in programs.items()};cost.update(selection_bits=sum(counts)*w,framing_bytes=41*len(counts),padding_bits=sum((-w*n)%8 for n in counts),cluster_selector_bits=0,control_bits=0,packet_bytes=sum(map(len,packets.values())),total_package_bytes=len(dictionary)+sum(map(len,packets.values())))
   costs.append(cost)
  fulls={text for vs in sources.values() for text in vs.values()};metrics={'coverage':len(programs),'target':len(ids),'literal_count':len(vocab),'dictionary_bytes':len(dictionary),'utf8_literal_bytes':sum(len(s.encode()) for s in vocab),'total_selections':sum(counts),'median_selections':statistics.median(counts) if counts else None,'worst_selections':max(counts,default=0),'cross_problem_literals':sum(len(o)>=2 for o in owners.values()),'shared_selections':sum(sum(len(owners[index])>=2 for index in row['sequence']) for row in programs.values()),'whole_program_literals':sum(s in fulls for s in vocab),'unused_entries':len(vocab)-len(owners)}
  record={'id':identity,'method':method,'arm':arm,'problem_ids':sorted(ids),'diagnostic':diagnostic,'parent':parent,'metrics':metrics,'costs':costs,'elapsed_seconds':time.monotonic()-began};state={'literals':vocab,'programs':programs,'record':record};(a.output/'encodings'/f'{identity}.json').write_bytes(jbytes(state));(a.output/'pools'/f'{identity}.json').write_bytes(jbytes(vocab));records.append(record);states[identity]=state;pools[identity]=vocab;seen[identity]=record;return record
 def proposals(ids,arm):
  opts=options(ids,arm);owners=collections.defaultdict(set);occ=collections.Counter();alltext=[t for vs in opts.values() for t in vs.values()];chars=set(''.join(alltext));full=set(alltext)
  for i,vs in opts.items():
   for variant,text in vs.items():
    for frag in features[f'{i:04d}/{variant}']['fragments']+pieces(text,'lexical'):
     if frag not in full and len(frag)<=240 and not ('function solve' in frag and '{' in frag and '\n' in frag.strip()):owners[frag].add(i)
  for frag,own in owners.items():
   if len(own)==1 and (len(frag.encode())>100 or len([x for x in frag.splitlines() if x.strip()])>2):continue
   occ[frag]=sum(max(text.count(frag) for text in opts[i].values()) for i in own)
  allowed={s for s in occ if len(s)>1}|chars
  def rank(mode):
   def score(s):
    saving=occ[s]*max(0,len(s)-1);cross=len({group_of[i] for i in owners[s]});value=saving/(len(s.encode())+4) if mode=='storage' else saving*(1+0.15*max(0,cross-1));return (-value,-len(owners[s]),s)
   return sorted(allowed-chars,key=score)
  return chars,rank,allowed
 seeds={};cluster_ids={name:set(v['fit']) for name,v in c['clusters'].items()};sets={**cluster_ids,'joint-fit':fit}
 for arm in ['normalized','canonical','joint']:
  for label,ids in sets.items():
   chars,rank,allowed=proposals(ids,arm);evaluate(chars,ids,arm,label+':characters')
   for mode in ['storage','input']:
    for budget in [64,128,256]:
     if len(chars)>budget:continue
     rec=evaluate(chars|set(rank(mode)[:budget-len(chars)]),ids,arm,f'{label}:AST-ranked-{mode}-{budget}');seeds[(arm,label,mode,budget)]=rec
 # Fixed strings proposed by adjacent lexical pair merges, charged and constrained by same cap.
 for arm in ['normalized','canonical']:
  texts=[sources[i][arm] for i in sorted(fit)];chars=set(''.join(texts))
  for step in [0,32,64]:
   pool=merged_dictionary(texts,'lexical',step,True);pool=sorted(set(pool)-chars,key=lambda s:(-sum(t.count(s) for t in texts)*max(0,len(s)-1)/(len(s.encode())+4),s));evaluate(chars|set(pool[:max(0,256-len(chars))]),fit,arm,f'joint-fit:lexical-merges-{step}')
 for arm in ['normalized','canonical']:evaluate([sources[i][arm] for i in sorted(fit)],fit,arm,'whole-program-charged-diagnostic',True)
 separate=[];union_records=[]
 for arm in ['normalized','canonical','joint']:
  for mode in ['storage','input']:
   pair=[seeds.get((arm,label,mode,128)) for label in cluster_ids]
   if any(x is None for x in pair):continue
   total_entries=sum(x['metrics']['literal_count'] for x in pair);selectors=len(fit);dictionary_total=sum(x['metrics']['dictionary_bytes'] for x in pair);selection_bits=packet_bytes=padding=0
   for rec in pair:
    cost=next(x for x in rec['costs'] if x['budget']==128);selection_bits+=cost['selection_bits'];packet_bytes+=cost['packet_bytes'];padding+=cost['padding_bits']
   # One packed selector sidecar, counted once, with program order in the declared packet format.
   row={'arm':arm,'mode':mode,'dictionary_ids':[x['id'] for x in pair],'combined_entry_budget':256,'combined_entries':total_entries,'coverage':sum(x['metrics']['coverage'] for x in pair),'dictionary_bytes':dictionary_total,'total_selections':sum(x['metrics']['total_selections'] for x in pair),'selection_bits':selection_bits,'cluster_selector_bits':selectors,'selector_padding_bits':(-selectors)%8,'selector_bytes':(selectors+7)//8,'selector_framing_bytes':8,'packet_bytes':packet_bytes,'padding_bits':padding,'framing_bytes':41*len(fit),'control_bits':0,'total_package_bytes':dictionary_total+packet_bytes+(selectors+7)//8+8};separate.append(row)
   selector_folder=a.output/'separate';selector_folder.mkdir(exist_ok=True);selector_values=[int(i not in next(iter(cluster_ids.values()))) for i in sorted(fit)];payload=bytes(sum(bit<<(7-k) for k,bit in enumerate(selector_values[j:j+8])) for j in range(0,len(selector_values),8));selector_packet=b'LTS1'+struct.pack('>I',len(selector_values))+payload;name=f'{arm}-{mode}.lts';(selector_folder/name).write_bytes(selector_packet);row['selector_file']='separate/'+name;row['cluster_order']=list(cluster_ids);row['program_order']=sorted(fit)
   union=sorted(set(s for rec in pair for s in pools[rec['id']]));rec=evaluate(union,fit,arm,f'naive-deduplicated-union:{arm}:{mode}');union_records.append(rec['id'])
 # Bounded local add/remove/swap proposals around the joint source-choice seeds.
 chars,rank,allowed=proposals(fit,'joint');optimization=[]
 for objective in ['storage','input']:
  candidates=[r for r in records if r['problem_ids']==sorted(fit) and r['arm']=='joint' and not r['diagnostic'] and r['metrics']['coverage']==len(fit) and r['metrics']['literal_count']<=256]
  key=lambda r:(next(x['total_package_bytes'] for x in r['costs'] if x['budget']==256),r['metrics']['total_selections']) if objective=='storage' else (r['metrics']['total_selections'],r['metrics']['dictionary_bytes'])
  current=min(candidates,key=key);initial=current['id'];trials=[]
  for round_no in range(2):
   state=states[current['id']];frequency=collections.Counter(index for row in state['programs'].values() for index in row['sequence']);removals=sorted([s for s in state['literals'] if len(s)>1],key=lambda s:(frequency[state['literals'].index(s)]*max(0,len(s)-1)/(len(s.encode())+4),s))[:6]
   additions=[s for s in rank(objective) if s not in state['literals']][:6];neighbors=[]
   for k,remove in enumerate(removals):
    pool=set(state['literals'])-{remove}
    if objective=='input' and additions:pool.add(additions[k%len(additions)])
    rec=evaluate(pool,fit,'joint',f'optimized-merge:{objective}:round-{round_no}',parent=current['id'])
    if rec:trials.append(rec['id']);neighbors.append(rec)
   if not neighbors:break
   best=min([current]+neighbors,key=key)
   if key(best)>=key(current):break
   current=best
  optimization.append({'objective':objective,'start':initial,'final':current['id'],'attempted':trials})
 complete=[r for r in records if r['problem_ids']==sorted(fit) and r['metrics']['coverage']==len(fit) and r['metrics']['literal_count']<=256]
 keys=['literal_count','dictionary_bytes','total_selections'];frontier=[r['id'] for r in complete if not any(all(o['metrics'][k]<=r['metrics'][k] for k in keys) and any(o['metrics'][k]<r['metrics'][k] for k in keys) for o in complete)]
 for record in records:
  state=states[record['id']]
  for cost in record['costs']:
   if not cost['feasible']:continue
   folder=a.output/'packets'/record['id']/str(cost['budget']);folder.mkdir(parents=True);raw=dictionary_bytes(state['literals']);(folder/'dictionary.ltd').write_bytes(raw)
   for i,row in state['programs'].items():
    packet=encode(state['literals'],row['sequence'],cost['bits_per_selection']);assert sha(decode(raw,packet).encode())==row['source_sha256'];(folder/(i+'.ltv')).write_bytes(packet)
 comparison={'schema':'gamma.cluster-search.v1','trials':records,'separate_modes':separate,'union_ids':union_records,'optimization':optimization,'frontier_ids':frontier,'dictionary_trials':len(records),'elapsed_seconds':time.monotonic()-started,'stopped_at':'trial_ceiling' if len(records)>=c['max_dictionary_trials'] else 'time_ceiling' if time.monotonic()-started>=c['max_search_wall_seconds'] else 'enumerated_schedule_complete'};(a.output/'summary.json').write_bytes(jbytes(comparison))
 # Freeze candidate selection for heldback independently of later heldback outcomes.
 selected={}
 for arm in ['normalized','canonical','joint']:
  eligible=[r for r in complete if r['arm']==arm and not r['diagnostic']]
  for objective in ['storage','input']:
   key=lambda r:(next(x['total_package_bytes'] for x in r['costs'] if x['budget']==256),r['metrics']['total_selections']) if objective=='storage' else (r['metrics']['total_selections'],r['metrics']['dictionary_bytes'])
   selected[arm+'-'+objective]=min(eligible,key=key)['id']
 freeze={'schema':'gamma.cluster-vocabulary-freeze.v1','contract_sha256':sha((root/'contract.json').read_bytes()),'source_hashes':source_hashes,'fit_qualification_reports':[sha((root/f/'report.json').read_bytes()) for f in ['fit-qualification-v1','fit-input-policy-recheck']],'selected':selected,'union_ids':union_records,'separate_modes':separate,'all_candidate_hashes':{r['id']:sha((a.output/'encodings'/f"{r['id']}.json").read_bytes()) for r in records},'implementation_sha256':{name:sha((root/name).read_bytes()) for name in ['generate.cjs','checks.py','verify.py','search.py','evaluate-heldback.py']},'heldback_source_bodies_accessed':False,'search_summary_sha256':sha((a.output/'summary.json').read_bytes())};(root/'vocabulary-freeze.json').write_bytes(jbytes(freeze));print(json.dumps({'trials':len(records),'seconds':comparison['elapsed_seconds'],'stop':comparison['stopped_at'],'selected':{k:{'id':v,**seen[v]['metrics']} for k,v in selected.items()}},indent=2))
if __name__=='__main__':main()
