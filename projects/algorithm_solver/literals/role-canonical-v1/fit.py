"""Frozen source-as-data representation/init comparison; never executes candidates."""
import argparse,importlib.util,json,time
from collections import Counter,defaultdict
from pathlib import Path
HERE=Path(__file__).resolve().parent
LIT=HERE.parent
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
joint=module('role_joint_search',LIT/'joint-composable-v1/search.py')
verify=module('role_independent_verifier',HERE/'verify.py')
q=verify.replay;b=joint.b;compare=joint.compare
CONFIG={**joint.CONFIG,'cpu_seconds':60}
SEED_CPU_SECONDS=10

def fresh_seed(texts,capacity,banned):
 if capacity not in (128,256):raise ValueError('unsupported capacity')
 started=time.process_time();streams={pid:list(text) for pid,text in texts.items()};learned=[];trace=[]
 while len(learned)<capacity-len(joint.ALPHABET):
  if time.process_time()-started>SEED_CPU_SECONDS:raise TimeoutError('fresh seed CPU budget exceeded')
  counts=Counter();owners=defaultdict(set)
  for pid,stream in streams.items():
   for pair in zip(stream,stream[1:]):counts[pair]+=1;owners[pair].add(pid)
  eligible=[pair for pair in counts if len(owners[pair])>=2 and len(''.join(pair))<=64 and ''.join(pair) not in banned and ''.join(pair) not in learned]
  if not eligible:break
  pair=min(eligible,key=lambda pair:(-counts[pair],len(''.join(pair)),pair));piece=''.join(pair);learned.append(piece)
  merged=0
  for pid,stream in streams.items():
   out=[];i=0
   while i<len(stream):
    if tuple(stream[i:i+2])==pair:out.append(piece);i+=2;merged+=1
    else:out.append(stream[i]);i+=1
   streams[pid]=out
  trace.append({'piece':piece,'owners':sorted(owners[pair]),'pair_occurrences':counts[pair],'nonoverlap_merges':merged})
 if time.process_time()-started>SEED_CPU_SECONDS:raise TimeoutError('fresh seed CPU budget exceeded')
 return joint.ALPHABET+sorted(learned),{'accepted_merges':len(learned),'trace':trace,'cpu_seconds':time.process_time()-started,'termination':'capacity' if len(learned)==capacity-96 else 'no-eligible-pair'}

def pins():
 paths=[HERE/n for n in ('fit.py','FITTER_FREEZE.md','test_fit.py','qualify.py','verify.py','parser.mjs','bindings.mjs','canonicalize.mjs','FREEZE.md')]
 result={str(p.relative_to(LIT)):b.sha(p.read_bytes()) for p in paths};result.update(joint.pins());return result

def gate(inputs,prior_path,format_report,role_report,node_path):
 prior_raw=prior_path.read_bytes();prior=json.loads(prior_raw)
 pilot_raw=Path('/workspace/shared/gamma-role-canonical-pilot-20261025/inputs.json').read_bytes();pilot=json.loads(pilot_raw)
 if b.sha(pilot_raw)!=q.INPUTS_SHA256 or b.sha(prior_raw)!=pilot['prior_contract_sha256']:raise ValueError('pretransformation reference freeze drift')
 spec,population,references,baseline,adapted=joint.pool_gate(inputs,Path(prior['baseline_report']),[Path(r['report']) for r in prior['adapted_reports']])
 if population!=prior['population'] or references!=prior['references'] or baseline['report_sha256']!=prior['baseline_report_sha256'] or adapted!=prior['adapted_reports']:raise ValueError('reference qualification pool drift')
 variants={'reference':{}};proofs={}
 for pid in q.IDS:
  key=str(pid);ref=next(r for r in population[key] if r['label']==references[key])
  if ref!=pilot['references'][key]:raise ValueError('reference identity differs from pilot')
  variants['reference'][key]={'path':ref['path'],'sha256':ref['sha256'],'fallback':False}
 for mode,path in [('format',format_report),('role',role_report)]:
  proof=verify.verify(inputs,path,allow_failed=False,node_path=node_path)
  if proof['qualified']!=32:raise ValueError('complete pilot qualification required')
  contract=json.loads((path.parent/'contract.json').read_text())
  if contract['mode']!=mode:raise ValueError('transformation arm mismatch')
  variants[mode]={pid:{'path':str(path.parent/(pid+'.js')),**row} for pid,row in contract['sources'].items()}
  proofs[mode]={'report':str(path),'report_sha256':proof['report_sha256'],'checks':proof['checks'],'executions':proof['executions']}
 return variants,proofs,[r for r in spec['files'] if r['kind']=='dictionary']

def freeze(inputs,prior_path,format_report,role_report,node_path,output):
 if output.resolve().is_relative_to(HERE.parents[3]):raise ValueError('private freeze must be outside repository')
 variants,proofs,dictionaries=gate(inputs,prior_path,format_report,role_report,node_path)
 contract={'schema':'gamma.role-canonical.fit.v1','ids':q.IDS,'variants':variants,'qualification':proofs,'prior_contract':str(prior_path),'prior_contract_sha256':b.sha(prior_path.read_bytes()),'dictionary_inputs':dictionaries,'config':CONFIG,'seed_cpu_seconds':SEED_CPU_SECONDS,'capacities':[128,256],'initializations':['inherited','fresh'],'representations':['reference','format','role'],'objective':'selection','code_sha256':pins(),'m1_population':500,'fit_population':32,'protected_access':False,'m1_qualified':False}
 output.mkdir(parents=True,exist_ok=False);b.write(output/'contract.json',contract);return contract

def read_variants(variants):
 out={}
 for representation,rows in variants.items():
  texts={}
  for pid,row in rows.items():
   source=Path(row['path']).read_bytes()
   if b.sha(source)!=row['sha256']:raise ValueError('qualified source drift')
   texts[pid]=source.decode('utf8')
  compare.validate_texts(texts);out[representation]=texts
 return out

def run(inputs,frozen,output,node_path):
 contract=json.loads((frozen/'contract.json').read_text())
 if contract['schema']!='gamma.role-canonical.fit.v1' or contract['code_sha256']!=pins() or contract['config']!=CONFIG or contract['seed_cpu_seconds']!=SEED_CPU_SECONDS:raise ValueError('frozen fit code drift')
 if contract.get('ids')!=q.IDS or contract.get('capacities')!=[128,256] or contract.get('initializations')!=['inherited','fresh'] or contract.get('representations')!=['reference','format','role'] or contract.get('objective')!='selection' or contract.get('fit_population')!=32 or contract.get('m1_population')!=500 or contract.get('protected_access') is not False or contract.get('m1_qualified') is not False:raise ValueError('frozen 12-arm population/scope drift')
 variants,proofs,dictionaries=gate(inputs,Path(contract['prior_contract']),Path(contract['qualification']['format']['report']),Path(contract['qualification']['role']['report']),node_path)
 if variants!=contract['variants'] or proofs!=contract['qualification'] or dictionaries!=contract['dictionary_inputs']:raise ValueError('qualification changed after freeze')
 if output.resolve().is_relative_to(HERE.parents[3]):raise ValueError('private output must be outside repository')
 output.mkdir(parents=True,exist_ok=False);b.write(output/'contract.json',contract)
 report={'schema':'gamma.role-canonical.results.v1','status':'running','contract_sha256':b.sha(b.encoded(contract)),'fits':{},'profiles':[],'candidate_executions':0,'fit_population':32,'m1_population':500,'protected_access':False,'m1_qualified':False}
 try:
  texts_by_rep=read_variants(variants)
  banned=set().union(*(joint.banned_strings(texts) for texts in texts_by_rep.values()))
  inherited={}
  for row in dictionaries:
   vocab=json.loads(joint.compact.verified(inputs,row))
   if isinstance(vocab,dict):vocab=vocab.get('literals',vocab.get('entries'))
   if type(vocab)is not list or vocab[:96]!=joint.ALPHABET or len(set(vocab))!=len(vocab) or len(vocab)>row['width'] or set(vocab)&banned:raise ValueError('illegal inherited dictionary')
   inherited[row['width']]=joint.ALPHABET+sorted(vocab[96:])
  sealed={}
  for representation in contract['representations']:
   texts=texts_by_rep[representation];owned={pid+':fixed':text for pid,text in texts.items()};owners={key:key.split(':')[0] for key in owned};groups={pid:[pid+':fixed'] for pid in texts};refs={pid:pid+':fixed' for pid in texts}
   pool,stats=joint.build_pool(owned,owners,banned,CONFIG['pool_per_bucket']);b.write(output/(representation+'-pool.json'),{'entries':pool,'buckets':stats})
   for capacity in contract['capacities']:
    for initialization in contract['initializations']:
     name=f'{representation}-{initialization}-{capacity}';b.write(output/'progress.json',{'active_arm':name,'completed_arms':list(sealed),'measurement_started':False})
     if initialization=='fresh':initial,seed=fresh_seed(texts,capacity,banned)
     else:initial=inherited[capacity];seed={'kind':'unchanged-pinned-inherited','accepted_merges':0}
     dictionary,choices,fit=joint.optimize(owned,groups,refs,initial,pool,capacity,'selection',CONFIG)
     if set(dictionary)&banned or len(set(dictionary))!=len(dictionary) or choices!=refs:raise ValueError('illegal sealed dictionary/source choice')
     sealed[name]={'representation':representation,'initialization':initialization,'capacity':capacity,'width':7 if capacity==128 else 8,'initial_dictionary':initial,'dictionary':dictionary}
     report['fits'][name]={'seed':seed,**fit}
     b.write(output/'progress.json',{'completed_arms':list(sealed),'fits':report['fits'],'measurement_started':False})
  seal_raw=b.encoded(sealed);(output/'sealed-arms.json').write_bytes(seal_raw);report['sealed_arms_sha256']=b.sha(seal_raw)
  for name,arm in sealed.items():
   representation=arm['representation'];texts=texts_by_rep[representation]
   for phase,key in [('seed','initial_dictionary'),('optimized','dictionary')]:
    summary,artifacts=compare.measure(texts,arm[key],arm['width']);summary.update({'all_helpers_and_adapters_included_in_source':True,'uncharged_helper_bytes':0,'reference_fallbacks':sum(row['fallback'] for row in variants[representation].values())})
    directory=output/(name+'-'+phase);directory.mkdir();(directory/'dictionary.bin').write_bytes(artifacts['dictionary'])
    for pid,packet in artifacts['packets'].items():(directory/(pid+'.packet')).write_bytes(packet)
    b.write(directory/'measurement.json',summary);report['profiles'].append({'arm':name,'phase':phase,**{k:v for k,v in summary.items() if k!='per_problem'}})
  if contract['code_sha256']!=pins() or read_variants(variants)!=texts_by_rep:raise ValueError('frozen code/source changed during experiment')
  report['status']='completed'
 except Exception as error:report['status']='failed';report['error']=type(error).__name__+': '+str(error)
 b.write(output/'results.json',report);return report

if __name__=='__main__':
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
 f=sub.add_parser('freeze');f.add_argument('--prior-contract',type=Path,required=True);f.add_argument('--format-report',type=Path,required=True);f.add_argument('--role-report',type=Path,required=True)
 r=sub.add_parser('run');r.add_argument('--freeze',type=Path,required=True)
 for x in (f,r):x.add_argument('--inputs',type=Path,required=True);x.add_argument('--node-path',type=Path,required=True);x.add_argument('--output',type=Path,required=True)
 a=p.parse_args();result=freeze(a.inputs,a.prior_contract,a.format_report,a.role_report,a.node_path,a.output) if a.command=='freeze' else run(a.inputs,a.freeze,a.output,a.node_path)
 print(json.dumps({'status':result.get('status','frozen'),'m1_qualified':False}));raise SystemExit(0 if result.get('status','frozen')!='failed' else 2)
