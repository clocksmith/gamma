"""Cached guard measurement; no encoder, new policy, confirmation or source."""
import argparse,hashlib,importlib.util,json,os,resource,signal,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(s):
 p=Path(s['path']);assert p.is_absolute()and p.stat().st_size<=32*1024**2 and sha(p)==s['sha256'];return json.loads(p.read_text())
def module(name,s):
 assert sha(s['path'])==s['sha256'];spec=importlib.util.spec_from_file_location(name,s['path']);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def fact_set(q):
 return {('positive',k,v)for k,v in q['facts'].items()}|{('negative',k,v)for k,vs in q.get('excluded_values',{}).items()for v in vs}
def extraction_score(parsed,annotations,*,tentative=False):
 out=dict(predicted=0,matched=0,incorrect_reviewed=0,unreviewed=0,gold=0,missed_gold=0)
 for p,a in zip(parsed,annotations):
  predicted=({(e['polarity'],e['facet'],e['value'])for e in p['tentative_evidence']}if tentative else fact_set(p));gold=fact_set(a);unknown=set(a.get('unknown_facets',[]));matched=predicted&gold
  out['predicted']+=len(predicted);out['matched']+=len(matched);out['gold']+=len(gold);out['missed_gold']+=len(gold-predicted)
  for _,k,v in predicted-gold:out['unreviewed'if k in unknown or not a.get('annotation_complete_for_supported_facets',False)else'incorrect_reviewed']+=1
 out['reviewed_precision']=out['matched']/(out['matched']+out['incorrect_reviewed'])if out['matched']+out['incorrect_reviewed']else None
 out['gold_recall']=out['matched']/out['gold']if out['gold']else None
 return out

def veto(baseline,parsed,comparison):
 if baseline['status']=='accepted'and (parsed['conflicts']or comparison['contradictions']):return dict(query_id=baseline['query_id'],status='abstain',reason='description_facet_conflict',problem_id=None)
 return dict(baseline)

def run(f):
 import numpy as np
 from projects.algorithm_solver.catalogue.empirical_recognition import rank,score_decisions
 from projects.algorithm_solver.catalogue.recognition_documents import pinned_metadata
 from projects.algorithm_solver.catalogue.boundary_policy import authorize_before_open
 for n,h in f['code_sha256'].items():assert sha(HERE/n)==h
 for n,h in f['dependency_code_sha256'].items():assert sha(HERE.parent/n)==h
 gf=read(f['guard_freeze']);guardroot=Path(f['guard_freeze']['path']).parent
 for n,h in gf['code_sha256'].items():assert sha(guardroot/n)==h
 for n,h in gf['dependency_code_sha256'].items():assert sha(HERE.parent/n)==h
 g=module('frozen_document_closed_guard',f['guard_module']);ef=read(f['encoder_freeze']);r=read(f['enriched_result']);cp=read(ef['cache_plan']);queries=read(ef['development'])['queries'];annotation_bundle=read(f['annotations']);gold=annotation_bundle['queries']
 assert annotation_bundle['development_sha256']==ef['development']['sha256'] and annotation_bundle['guard_evaluation']is False and annotation_bundle['confirmation_read']is False
 gold=[dict(a,annotation_complete_for_supported_facets=True)for a in gold]
 for q,a in zip(queries,gold):
  assert a['text_sha256']==hashlib.sha256(q['text'].encode()).hexdigest() and a['guard_output_seen']is False and a['expected_id_used']is False
 assert r['freeze_sha256']==f['encoder_freeze']['sha256'] and r['status']=='completed' and r['matched_service_sha256']==ef['matched_service']['sha256']
 assert len(queries)==len(gold)==52 and [q['query_id']for q in queries]==[a['query_id']for a in gold]
 cache=module('evaluation3_cache',ef['cache_module']);qc=module('evaluation3_query_cache',ef['query_cache_module']);index=cache.restore_index(cp['index'],np);qv,flags=qc.restore_queries(cp,queries,cache,np);assert not any(flags)
 expanded=index.array.copy();parts=[]
 for s in f['delta_arrays']:
  assert sha(s['path'])==s['sha256'];a=np.load(s['path'],allow_pickle=False);cache.validate_array(a,4,np);parts.append(a)
 delta=np.concatenate(parts);assert delta.shape==(48,1024);expanded[ef['replacement_positions']]=delta;ids=cp['index']['stable_ids'];assert len(ids)==4081
 # Gate every semantic authority BEFORE combined document open; no source payload.
 plan=read(ef['new_document_plan']);gate=read(plan['boundary_gate'])
 for a in plan['authorities']:authorize_before_open(a['problem_id'],gate['artifact_paths'],gate['trusted_hashes'],language='javascript',payload_kind='statement')
 bundle=read(ef['new_documents']);assert bundle['stable_ids']==ids and bundle['plan_sha256']==ef['new_document_plan']['sha256']
 contracts={d['problem_id']:g.contract_facts(d)for d in bundle['documents']};parsed=[g.parse_query(q['text'])for q in queries]
 ranks={arm:[rank(s,ids)for s in qv@array.T]for arm,array in [('baseline54_v16',index.array),('expanded102_v16',expanded)]}
 policies=read(ef['policy'])['policy_family'];assert len(policies)==20 and [x['policy']for x in r['results']]==policies
 results=[];reviews=[]
 for row in r['results']:
  item={'policy':row['policy'],'arms':{}}
  for arm in ranks:
   baseline=row[arm+'_decisions'];assert [d['query_id']for d in baseline]==[q['query_id']for q in queries];assert score_decisions(queries,baseline)==row[arm]
   output=[]
   for q,p,ranking,b in zip(queries,parsed,ranks[arm],baseline):
    if b['status']=='accepted':assert b['problem_id']==ranking[0][0]
    comparison=g.compare(p,contracts[ranking[0][0]]);decision=veto(b,p,comparison);output.append(decision)
    if decision!=b:reviews.append(dict(query_id=q['query_id'],policy_id=row['policy']['id'],arm=arm,top_id=ranking[0][0],comparison=comparison,query_evidence=p['evidence'],contract_evidence=contracts[ranking[0][0]]['evidence'],independent_veto_soundness='UNREVIEWED'))
    assert decision['status']!='accepted'or decision==b
   item['arms'][arm]=dict(baseline_metrics=row[arm],guarded_metrics=score_decisions(queries,output),decisions=output)
  results.append(item)
 # Score tentative signed triples separately, without using them as constraints.
 return dict(schema='gamma.cached-clause-guard-result.v3',population=4081,query_count=52,policy_count=20,extraction=extraction_score(parsed,gold),tentative_extraction=extraction_score(parsed,gold,tentative=True),closed_document_count=sum(p['grammar_complete']for p in parsed),queries_with_admissible_facts=sum(bool(fact_set(p))for p in parsed),queries_with_tentative_evidence=sum(bool(p['tentative_evidence'])for p in parsed),tentative_span_count=sum(len(p['tentative_evidence'])for p in parsed),private_parsed_queries=[dict(query_id=q['query_id'],**p)for q,p in zip(queries,parsed)],results=results,private_veto_reviews=reviews,independently_reviewed_sound_veto_count=0,unreviewed_veto_count=len(reviews),confirmation_read=False,encoder_invocations=0,source_payload_reads=0,recognition_qualified=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--freeze',required=True);p.add_argument('--freeze-sha256',required=True);p.add_argument('--output',required=True);a=p.parse_args();resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(59,60));signal.alarm(60);os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1');f=read(dict(path=str(Path(a.freeze).resolve()),sha256=a.freeze_sha256));out=Path(a.output);out.mkdir(exist_ok=False)
 try:(out/'report.json').write_text(json.dumps(run(f),indent=2,sort_keys=True,allow_nan=False)+'\n')
 except BaseException as e:(out/'failure.json').write_text(json.dumps(dict(error_type=type(e).__name__,recognition_qualified=False)));raise
