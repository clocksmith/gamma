"""Bounded joint choice of verified source alternatives and exact fixed strings."""
import argparse,json,sys,time,math,statistics,hashlib,re
from pathlib import Path
from collections import defaultdict

def admissible(text,sources):
 if not text:return False
 owners=set()
 for key,variants in sources.items():
  for source in variants.values():
   if source.strip() in text:return False
   if text in source:owners.add(key)
 if len(owners)>=2:return True
 lines=[line for line in text.splitlines() if line.strip()]
 return bool(owners) and len(lines)<=2 and len(text.encode())<=160 and not (('function solve(' in text or 'const solve =' in text) and ('return ' in text or len(lines)>1)) and not re.match(r'^\s*\(?values(?:,\s*[A-Za-z_$][\w$]*)*\)?\s*=>',text)

def main():
 p=argparse.ArgumentParser();p.add_argument('--pilot',type=Path,required=True);p.add_argument('--generated',type=Path,required=True);p.add_argument('--qualification',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--max-trials',type=int,default=74);p.add_argument('--max-seconds',type=int,default=180);a=p.parse_args();assert 1<=a.max_trials<=74 and 1<=a.max_seconds<=180;a.output.mkdir(exist_ok=False);(a.output/'encodings').mkdir();(a.output/'packets').mkdir();(a.output/'pools').mkdir()
 sys.path[:0]=[str(a.pilot),str(a.pilot/'pass2/working')]
 from literals import shortest_encode,dictionary_bytes,digest,json_bytes,pieces,merged_dictionary
 from bitpack import encode,decode
 manifest=json.loads((a.generated/'manifest.json').read_text());qualification=json.loads(a.qualification.read_text());admitted={(r['problem'],r['source_sha256']) for r in qualification['rows'] if r['passed']};sources={}
 for key,variants in manifest['variants'].items():
  sources[key]={}
  for name,row in variants.items():
   source=(a.generated/row['file']).read_text();assert digest(source.encode())==row['sha256']
   if (key,row['sha256']) in admitted:sources[key][name]=source
 assert len(sources)==20 and all(sources.values())
 fixed={key:{'baseline':v['baseline']} for key,v in sources.items()};all_text=[s for v in sources.values() for s in v.values()];base_text=[v['baseline'] for v in fixed.values()]
 contract={'schema':'gamma.functional-literals-search.v1','max_dictionary_trials':a.max_trials,'prior_sweep_trials':46,'combined_trial_ceiling':120,'admission_revision':'Reject unique anonymous entrypoint arrows as well as named entrypoint-body fragments; retain full unused pool during deletion; add matched fixed-source AST control','max_seconds':a.max_seconds,'entry_budgets':[16,32,64,128,256],'source_count':sum(map(len,sources.values())),'source_manifest_sha256':digest((a.generated/'manifest.json').read_bytes()),'qualification_sha256':digest(a.qualification.read_bytes()),'implementation_sha256':digest(Path(__file__).read_bytes()),'admission':'Non-diagnostic strings exclude complete programs. Unique fragments: at most two nonempty lines and 160 UTF-8 bytes; unique entrypoint prefixes cannot contain their body. Larger fragments require two distinct problem owners. AST pieces are flattened strings, never holes/nonterminals.','search':'Exact shortest segmentation chooses a complete verified alternative per problem. Enumerated initial dictionaries then bounded deletion trials; no claim of global optimality.','cost':'LTD1 dictionary plus LTV1 packets; all helpers/wrappers counted. 41 framing bytes/program; padding and dictionary IDs counted. Human metadata/duplicate readable views and shared decoder source reported separately.','cpu_threads':1,'ram_limit_bytes':8*1024**3,'artifact_budget_bytes':512*1024**2,'autonomous':False,'protected_evaluation':False};(a.output/'contract.json').write_bytes(json_bytes(contract));start=time.perf_counter();rows=[];states={};seen={};pools={}
 def measure(pool,options):
  pool=sorted(set(pool));programs={}
  if not pool:return {'literals':[],'programs':{}}
  for key,variants in sorted(options.items()):
   choices=[]
   for name,text in sorted(variants.items()):
    try:sequence=shortest_encode(text,pool)
    except ValueError:continue
    choices.append((len(sequence),len(text.encode()),name,sequence,text))
   if choices:
    _,_,name,sequence,text=min(choices);programs[key]={'variant':name,'sequence':sequence,'source_sha256':digest(text.encode()),'source_bytes':len(text.encode())}
  used=sorted({i for r in programs.values() for i in r['sequence']});remap={v:i for i,v in enumerate(used)}
  for row in programs.values():row['sequence']=[remap[i] for i in row['sequence']]
  return {'literals':[pool[i] for i in used],'programs':programs}
 def evaluate(pool,method,options=sources,parent=None,removed=None,diagnostic=False):
  identity=digest(json_bytes({'pool':sorted(set(pool)),'options':'fixed' if options is fixed else 'joint'}))[:20]
  if identity in seen:return seen[identity]
  if len(rows)>=a.max_trials or time.perf_counter()-start>=a.max_seconds:return None
  began=time.perf_counter();state=measure(pool,options);vocab=state['literals'];dictionary=dictionary_bytes(vocab) if vocab else b'';counts=[len(r['sequence']) for r in state['programs'].values()];owners=defaultdict(set)
  for key,row in state['programs'].items():
   for i in row['sequence']:owners[i].add(key)
  metrics={'coverage':len(counts),'literal_count':len(vocab),'dictionary_bytes':len(dictionary),'total_selections':sum(counts),'median_selections':statistics.median(counts) if counts else None,'worst_selections':max(counts,default=0),'cross_program_literals':sum(len(v)>1 for v in owners.values()),'cross_program_selections':sum(sum(len(owners[i])>1 for i in row['sequence']) for row in state['programs'].values()),'whole_program_literals':sum(any(text==s for s in all_text) for text in vocab)}
  costs=[]
  for budget in contract['entry_budgets']:
   width=int(math.log2(budget));cost={'budget':budget,'width':width,'feasible':bool(vocab) and len(vocab)<=budget}
   if cost['feasible']:
    packets=[encode(vocab,row['sequence'],width) for row in state['programs'].values()];cost.update(selection_bits=width*sum(counts),padding_bits=sum((-width*n)%8 for n in counts),framing_bytes=41*len(counts),packet_bytes=sum(map(len,packets)),total_package_bytes=len(dictionary)+sum(map(len,packets)))
   costs.append(cost)
  record={'id':identity,'method':method,'parent':parent,'removed':removed,'diagnostic':diagnostic,'candidate_pool_count':len(set(pool)),'candidate_pool_sha256':digest(json_bytes(sorted(set(pool)))),'metrics':metrics,'costs':costs,'elapsed_seconds':time.perf_counter()-began}
  packet={**state,'record':record};raw=json_bytes(packet);(a.output/'encodings'/f'{identity}.json').write_bytes(raw);record['encoding_json_bytes']=len(raw);rows.append(record);states[identity]=state;seen[identity]=record;pools[identity]=sorted(set(pool));(a.output/'pools'/f'{identity}.json').write_bytes(json_bytes(pools[identity]));return record
 def nonwhole(pool):return sorted(p for p in set(pool) if admissible(p,sources))
 chars=sorted(set(''.join(all_text)));fixed_chars=sorted(set(''.join(base_text)))
 evaluate(fixed_chars,'fixed-characters',fixed);evaluate(chars,'joint-characters')
 evaluate(base_text,'fixed-whole-program-diagnostic',fixed,diagnostic=True)
 evaluate([min(v.values(),key=lambda s:(len(s.encode()),s)) for v in sources.values()],'joint-whole-program-diagnostic',diagnostic=True)
 evaluate(sorted(base_text)[:16],'sixteen-whole-program-coverage-diagnostic',fixed,diagnostic=True)
 ast_pools=json.loads((a.generated/'fragments.json').read_text());ast_pool=nonwhole(p for group in ast_pools.values() for p in group)
 evaluate(ast_pool,'joint-AST-and-three-line-spans');fixed_ast=nonwhole(p for key,group in ast_pools.items() if key.endswith('/baseline') for p in group);evaluate(fixed_ast,'fixed-AST-and-three-line-spans',fixed)
 fixed_lines=nonwhole(p for s in base_text for p in pieces(s,'lines'));evaluate(fixed_lines+fixed_chars,'fixed-lines-and-characters',fixed)
 for step in [0,16,32,64,128]:
  for label,texts,options in [('fixed',base_text,fixed),('joint',all_text,sources)]:
   pool=nonwhole(merged_dictionary(texts,'lexical',step,False))
   evaluate(pool,label+f'-lexical-merges-{step}',options)
   if label=='joint':evaluate(pool+ast_pool,label+f'-lexical-plus-AST-{step}',options)
 # Exact resegmentation after each deletion; every attempted candidate retained.
 trace=[]
 for budget,allowance in [(64,0),(128,8),(256,32)]:
  seeds=[r for r in rows if not r['diagnostic'] and r['metrics']['coverage']==20 and r['metrics']['literal_count']<=budget]
  if not seeds:trace.append({'budget':budget,'status':'no-complete-seed'});continue
  current=min(seeds,key=lambda r:(r['metrics']['total_selections'],r['metrics']['dictionary_bytes'],r['id']));limit=current['metrics']['total_selections']+allowance;accepted=[]
  for _ in range(1):
   candidate_states=[];vocab=states[current['id']]['literals']
   for literal in sorted(vocab,key=lambda t:(-len(t.encode()),t))[:16]:
    trial=evaluate([s for s in pools[current['id']] if s!=literal],f'deletion-budget-{budget}',parent=current['id'],removed=literal)
    if trial is None:break
    m=trial['metrics'];old=current['metrics']
    if m['coverage']==20 and m['literal_count']<=budget and m['total_selections']<=limit and m['dictionary_bytes']<old['dictionary_bytes']:candidate_states.append(trial)
   if not candidate_states:break
   current=min(candidate_states,key=lambda r:(r['metrics']['dictionary_bytes'],r['metrics']['total_selections'],r['id']));accepted.append(current['id'])
  trace.append({'budget':budget,'selection_allowance':allowance,'selection_limit':limit,'accepted':accepted,'final':current['id']})
 def dominates(a,b):
  aa=a['metrics'];bb=b['metrics'];keys=['literal_count','dictionary_bytes','total_selections'];return all(aa[k]<=bb[k] for k in keys) and any(aa[k]<bb[k] for k in keys)
 complete=[r for r in rows if r['metrics']['coverage']==20 and r['metrics']['literal_count']<=256];frontier=[];frontier_states=set()
 for r in complete:
  identity=digest(json_bytes(states[r['id']]))
  if identity not in frontier_states and not any(dominates(other,r) for other in complete):frontier.append(r);frontier_states.add(identity)
 # Persist actual bit packets for every feasible measured state at each declared width.
 for record in rows:
  state=states[record['id']]
  for cost in record['costs']:
   if not cost['feasible']:continue
   folder=a.output/'packets'/record['id']/str(cost['budget']);folder.mkdir(parents=True);raw=dictionary_bytes(state['literals']);(folder/'dictionary.ltd').write_bytes(raw)
   for key,row in state['programs'].items():
    packet=encode(state['literals'],row['sequence'],cost['width']);text=decode(raw,packet);assert digest(text.encode())==row['source_sha256'];(folder/(key+'.ltv')).write_bytes(packet)
 summary={'schema':'gamma.functional-literals-result.v1','trials':rows,'frontier_ids':[r['id'] for r in frontier],'traces':trace,'dictionary_trials':len(rows),'elapsed_seconds':time.perf_counter()-start,'stopped_at':'trial_budget' if len(rows)>=a.max_trials else 'time_budget' if time.perf_counter()-start>=a.max_seconds else 'enumerated_schedule_complete','scope':'Finite candidate/source pool; no global optimum or autonomous synthesis claim.'};(a.output/'summary.json').write_bytes(json_bytes(summary));print(json.dumps({'trials':len(rows),'seconds':summary['elapsed_seconds'],'stop':summary['stopped_at'],'frontier':[{'id':r['id'],'method':r['method'],**r['metrics']} for r in frontier]},indent=2))
if __name__=='__main__':main()
