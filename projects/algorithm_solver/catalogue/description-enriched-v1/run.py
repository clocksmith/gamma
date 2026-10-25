"""Development-only delta encoding; no confirmation path or stage exists."""
import argparse, hashlib, json, os, resource, signal, time
from pathlib import Path

BASE=Path(__file__).resolve().parent.parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(spec):
 raw=Path(spec['path']).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=spec['sha256']:raise ValueError('input pin mismatch')
 return json.loads(raw)
def save(path,value):
 tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');os.replace(tmp,path)
def alignment(old,new):
 if len(old)!=4081 or [r['problem_id']for r in old]!=[r['problem_id']for r in new]:raise ValueError('full competitor identity/order required')
 if len({r['problem_id']for r in old})!=4081:raise ValueError('duplicate identities')
 changed=[i for i,(a,b)in enumerate(zip(old,new))if a['text']!=b['text']]
 if len(changed)!=54:raise ValueError('expected exact54 changed documents')
 for a,b in zip(old,new):
  if hashlib.sha256(b['text'].encode()).hexdigest()!=b['document_sha256']:raise ValueError('document hash mismatch')
  if hashlib.sha256(a['text'].encode()).hexdigest()!=b['baseline_document_sha256']:raise ValueError('baseline hash mismatch')
 return changed

def check_array(array,n,np):
 if array.shape!=(n,1024) or not np.isfinite(array).all() or not np.allclose(np.linalg.norm(array,axis=1),1,atol=1e-4):raise ValueError('invalid embedding')

def encode_cached(encoder,rows,query,root,identity,np,progress):
 root.mkdir(exist_ok=True);arrays=[];metadata=[]
 for start in range(0,len(rows),4):
  batch=rows[start:start+4];ap=root/f'{start:04d}.npy';rp=root/f'{start:04d}.json'
  binding={'identity':identity,'query':query,'rows':rows[start:start+4]}
  bind=hashlib.sha256(json.dumps(binding,sort_keys=True).encode()).hexdigest()
  if ap.exists() or rp.exists():
   if not(ap.exists() and rp.exists()):raise ValueError('incomplete cache pair retained; use new output')
   info=json.loads(rp.read_bytes())
   if info['binding_sha256']!=bind or sha(ap)!=info['array_sha256']:raise ValueError('delta cache changed')
   a=np.load(ap,allow_pickle=False)
  else:
   a=encoder.encode([r['text']for r in batch],query=query)
   check_array(a,len(batch),np)
   with ap.open('xb')as f:np.save(f,a,allow_pickle=False)
   info={'binding_sha256':bind,'array_sha256':sha(ap),'request':encoder.last_request_info,'ids':[r['problem_id']for r in batch]}
   save(rp,info)
  check_array(a,len(batch),np)
  if len(info['request']['truncated'])!=len(batch):raise ValueError('token metadata length')
  arrays.append(a);metadata.extend({'id':r['problem_id'],'request':info['request'],'batch_offset':j}for j,r in enumerate(batch))
  save(progress,{'phase':'queries'if query else'changed_documents','completed':start+len(batch),'total':len(rows)})
 return np.concatenate(arrays),metadata

def run(args):
 f=read({'path':args.freeze,'sha256':args.freeze_sha256})
 if f['schema']!='gamma.description-enriched-execution.v1':raise ValueError('freeze schema')
 for p,h in f['code_sha256'].items():
  if sha(BASE/p)!=h:raise ValueError('code drift: '+p)
 started=time.monotonic();cpu0=time.process_time()
 resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,8*1024**3));resource.setrlimit(resource.RLIMIT_CPU,(300,305))
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('240s wall budget')));signal.alarm(240)
 available=int(next(l.split()[1]for l in Path('/proc/meminfo').read_text().splitlines()if l.startswith('MemAvailable:')))*1024
 if available<5*1024**3:raise RuntimeError('less than5GiB memory headroom')
 old=read(f['baseline'])['documents'];new=read(f['documents'])['documents'];changed=alignment(old,new)
 policy=read(f['policy']);phase1=read(f['phase1']);queries=read(f['development'])['queries']
 if len(queries)!=52 or f['development']['sha256']!=policy['development_sha256']:raise ValueError('development cohort mismatch')
 if len(policy['policy_family'])!=20:raise ValueError('fixed20 policy family required')
 import numpy as np
 from projects.algorithm_solver.catalogue.cpu_encoder import PinnedCPUEncoder
 from projects.algorithm_solver.catalogue.known_spec_service import KnownSpecService
 from projects.algorithm_solver.catalogue.empirical_recognition import rank,decide,score_decisions,select_policy
 output=Path(args.output);output.mkdir(exist_ok=True)
 identity=read(f['baseline_identity'])
 if hashlib.sha256(Path(f['baseline_identity']['path']).read_bytes()).hexdigest()!=phase1['cache_identity_sha256']:raise ValueError('phase1 cache identity')
 if identity!=f['encoder_cache_identity'] or identity['encoder_adapter_sha256']!=sha(BASE/'cpu_encoder.py') or identity['index_sha256']!=f['baseline']['sha256'] or identity['threads']!=2 or identity['batch_size']!=4:raise ValueError('encoder reuse identity mismatch')
 matrices=[]
 for chunk in phase1['chunks']:
  start=chunk['start'];root=Path(f['baseline_cache']);ap=root/f'{start:04d}.npy';rp=root/f'{start:04d}.json'
  info=read({'path':str(rp),'sha256':chunk['receipt_sha256']})
  if sha(ap)!=chunk['array_sha256'] or info['sha256']!=sha(ap) or info['start']!=start or info['ids']!=[r['problem_id']for r in old[start:start+64]]:raise ValueError('baseline chunk mismatch')
  if len(info['request']['truncated'])!=len(info['ids']) or any(info['request']['truncated'][j] for j in range(len(info['ids'])) if start+j not in changed):raise ValueError('truncated reused title prevents full index')
  a=np.load(ap,allow_pickle=False);check_array(a,len(info['ids']),np);matrices.append(a)
 if [c['start']for c in phase1['chunks']]!=list(range(0,4081,64)):raise ValueError('incomplete cache')
 docs=np.concatenate(matrices);check_array(docs,4081,np)
 encoder=PinnedCPUEncoder(args.model_root,encoder_manifest=BASE/'ENCODER-PROVISIONING-PROPOSAL-v1.json',encoder_manifest_sha256=identity['encoder_manifest_sha256'],cpu_manifest=BASE/'CPU-ENVIRONMENT-PROPOSAL-v1.json',cpu_manifest_sha256=identity['cpu_manifest_sha256'],native_python_sha256=identity['native_python_sha256'],threads=2,batch_size=4)
 delta,dm=encode_cached(encoder,[new[i]for i in changed],False,output/'documents-cache',identity,np,output/'progress.json')
 if any(x['request']['truncated'][x['batch_offset']]for x in dm):
  save(output/'blocked.json',{'reason':'truncated_index_document','full_index_run':False,'document_metadata':dm});return
 docs[changed]=delta
 qrows=[{'problem_id':q['query_id'],'text':q['text']}for q in queries]
 vectors,qm=encode_cached(encoder,qrows,True,output/'queries-cache',identity,np,output/'progress.json')
 service=KnownSpecService.from_config(f['service']['path'],f['service']['sha256'])
 rankings=[rank(s,[r['problem_id']for r in new])for s in vectors@docs.T];results=[]
 for p in policy['policy_family']:
  decisions=[decide(r,p,service,truncated=qm[i]['request']['truncated'][qm[i]['batch_offset']])for i,r in enumerate(rankings)]
  metrics=score_decisions(queries,decisions);metrics['control_abstentions']=metrics['control_count']-metrics['control_accepts'];metrics['accepted_total']=metrics['correct_accepts']+metrics['wrong_positive_accepts']+metrics['control_accepts']
  results.append({'policy':p,'metrics':metrics,'decisions':decisions})
 for p,h in f['code_sha256'].items():
  if sha(BASE/p)!=h:raise ValueError('end code drift')
 report={'schema':'gamma.description-enriched-development.v1','freeze_sha256':args.freeze_sha256,'population':4081,'reused_title_vectors':4027,'new_document_vectors':54,'query_vectors':52,'full_index_run':True,'results':results,'selected_policy':select_policy(results),'document_metadata':dm,'query_metadata':qm,'encoder_identity':encoder.identity(),'wall_seconds':time.monotonic()-started,'cpu_seconds':time.process_time()-cpu0,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'prior_resources':f['prior_resources'],'population_risk_certificate':False,'confirmation_read':False,'source_availability_ranking_filter':False,'sampling':'authored/non-IID development iteration after title-only failure; not independent confirmation'}
 save(output/'development.json',report);save(output/'selection.json',{'freeze_sha256':args.freeze_sha256,'development_report_sha256':sha(output/'development.json'),'selected_policy':report['selected_policy']})
 signal.alarm(0)
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for key in ['freeze','freeze-sha256','model-root','output']:p.add_argument('--'+key,required=True)
 run(p.parse_args())
