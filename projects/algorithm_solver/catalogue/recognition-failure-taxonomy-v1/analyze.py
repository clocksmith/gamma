"""Frozen cached development diagnostics; mechanical observations are not causes."""
import argparse,hashlib,importlib.util,json,os,resource,signal,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(s):
 p=Path(s['path']);assert p.is_absolute() and p.stat().st_size<=32*1024**2 and sha(p)==s['sha256'];return json.loads(p.read_text())
def module(name,s):
 assert sha(s['path'])==s['sha256'];spec=importlib.util.spec_from_file_location(name,s['path']);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def observations(ranked,q,decision,policy):
 expected=q.get('expected_ids',[])if q.get('expected_id')is None else[q['expected_id']]
 positions={pid:i+1 for i,(pid,_)in enumerate(ranked)};top,score=ranked[0];margin=score-ranked[1][1]
 flags=[]
 if decision['reason']in ('top_identity_not_qualified','both_languages_not_qualified'):flags.append('unavailable_qualified_top_artifact')
 if q['kind']=='positive'and top not in expected:flags.append('distractor_top_identity')
 if decision['reason']=='empirical_confidence_threshold':flags.append('fixed_threshold_abstention')
 if q['kind']!='positive'and decision['status']=='accepted':flags.append('control_acceptance')
 return {'top_id':top,'top_cosine':score,'top_two_margin':margin,'expected_ranks':{pid:positions[pid]for pid in expected},'mechanical_observations':flags,
 'semantic_missing_facts':'UNKNOWN','embedding_representation_cause':'UNKNOWN','output_effect_ambiguity':'UNKNOWN','score_threshold_slack':score-policy['min_cosine'],'margin_threshold_slack':margin-policy['min_margin']}

def run(f):
 import numpy as np
 from projects.algorithm_solver.catalogue.empirical_recognition import rank
 for n,h in f['code_sha256'].items():assert sha(HERE/n)==h
 parent=read(f['encoder_freeze']);report=read(f['result']);cp=read(parent['cache_plan']);queries=read(parent['development'])['queries']
 for n,h in f['dependency_code_sha256'].items():assert sha(HERE.parent/n)==h
 assert report['freeze_sha256']==f['encoder_freeze']['sha256'] and report['status']=='completed'
 assert [r['policy']for r in report['results']]==read(parent['policy'])['policy_family']
 cache=module('taxonomy_cache',parent['cache_module']);qc=module('taxonomy_qcache',parent['query_cache_module'])
 index=cache.restore_index(cp['index'],np);qv,flags=qc.restore_queries(cp,queries,cache,np);assert not any(flags)
 ids=cp['index']['stable_ids'];assert len(ids)==4081 and len(queries)==52
 expanded=index.array.copy();parts=[]
 for s in f['delta_arrays']:
  assert sha(s['path'])==s['sha256'];a=np.load(s['path'],allow_pickle=False);cache.validate_array(a,4,np);parts.append(a)
 delta=np.concatenate(parts);assert delta.shape==(48,1024);expanded[parent['replacement_positions']]=delta
 rankings={arm:[rank(s,ids)for s in qv@a.T]for arm,a in [('baseline54_v16',index.array),('expanded102_v16',expanded)]}
 detail=[];counts={}
 assert len(report['results'])==20
 for row in report['results']:
  p=row['policy'];pid=p['id'];counts[pid]={}
  for arm in rankings:
   ds=row[arm+'_decisions'];assert [d['query_id']for d in ds]==[q['query_id']for q in queries];count={}
   for q,r,d in zip(queries,rankings[arm],ds):
    o=observations(r,q,d,p)
    if d['status']=='accepted':assert d['problem_id']==o['top_id'] and o['score_threshold_slack']>=0 and o['margin_threshold_slack']>=0 and o['top_two_margin']>0
    if d['reason']=='empirical_confidence_threshold':assert o['score_threshold_slack']<0 or o['margin_threshold_slack']<0 or o['top_two_margin']<=0
    for flag in o['mechanical_observations']:count[flag]=count.get(flag,0)+1
    detail.append(dict(query_id=q['query_id'],policy_id=pid,arm=arm,decision=d,**o))
   counts[pid][arm]=count
 return {'schema':'gamma.development-failure-taxonomy.v1','population':4081,'query_count':52,'policy_count':20,'private_per_query':detail,'aggregate_observations':counts,'semantic_taxonomy_unreviewed':True,'causal_inference':False,'recognition_qualified':False,'confirmation_read':False,'encoder_invocations':0}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--freeze',required=True);p.add_argument('--freeze-sha256',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(59,60));signal.alarm(60);os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
 f=read({'path':str(Path(a.freeze).resolve()),'sha256':a.freeze_sha256});out=Path(a.output);out.mkdir(exist_ok=False)
 try:(out/'report.json').write_text(json.dumps(run(f),sort_keys=True,indent=2,allow_nan=False)+'\n')
 except BaseException as e:(out/'failure.json').write_text(json.dumps({'error_type':type(e).__name__,'recognition_qualified':False}));raise
