"""One fixed-weight cached development experiment; annotations never rank."""
import argparse,hashlib,importlib.util,json,os,resource,signal,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(s):
 p=Path(s['path']);assert p.is_absolute()and p.stat().st_size<=32*1024**2 and sha(p)==s['sha256'];return json.loads(p.read_text())
def module(n,s):
 assert sha(s['path'])==s['sha256'];sp=importlib.util.spec_from_file_location(n,s['path']);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);return m

def run(f,freeze_sha):
 start=time.perf_counter();cpu=time.process_time()
 import numpy as np
 from projects.algorithm_solver.catalogue.empirical_recognition import decide,score_decisions
 from projects.algorithm_solver.catalogue.boundary_policy import authorize_before_open
 from projects.algorithm_solver.catalogue.known_spec_service import KnownSpecService
 from rerank import rerank,decide_hybrid
 for n,h in f['code_sha256'].items():assert sha(HERE/n)==h
 for n,h in f['dependency_code_sha256'].items():assert sha(HERE.parent/n)==h
 ef=read(f['encoder_freeze']);history=read(f['enriched_result']);parsed_report=read(f['parsed_result']);gf=read(f['guard_freeze'])
 for n,h in gf['code_sha256'].items():assert sha(Path(f['guard_freeze']['path']).parent/n)==h
 g=module('empirical_rerank_guard',f['guard_module']);cp=read(ef['cache_plan']);queries=read(ef['development'])['queries'];parsed=parsed_report['private_parsed_queries']
 assert len(queries)==len(parsed)==52 and [q['query_id']for q in queries]==[q['query_id']for q in parsed]
 for q,p in zip(queries,parsed):assert hashlib.sha256(q['text'].encode()).hexdigest()==p['query_sha256']
 cache=module('rerank_index_cache',ef['cache_module']);qc=module('rerank_query_cache',ef['query_cache_module']);index=cache.restore_index(cp['index'],np);qv,flags=qc.restore_queries(cp,queries,cache,np);assert not any(flags)
 expanded=index.array.copy();parts=[]
 for s in f['delta_arrays']:
  assert sha(s['path'])==s['sha256'];a=np.load(s['path'],allow_pickle=False);cache.validate_array(a,4,np);parts.append(a)
 delta=np.concatenate(parts);assert delta.shape==(48,1024);expanded[ef['replacement_positions']]=delta;ids=cp['index']['stable_ids'];assert len(ids)==4081
 plan=read(ef['new_document_plan']);gate=read(plan['boundary_gate'])
 for a in plan['authorities']:authorize_before_open(a['problem_id'],gate['artifact_paths'],gate['trusted_hashes'],language='javascript',payload_kind='statement')
 bundle=read(ef['new_documents']);assert bundle['stable_ids']==ids and bundle['plan_sha256']==ef['new_document_plan']['sha256'];contracts={d['problem_id']:g.contract_facts(d)for d in bundle['documents']}
 rankings=[rerank(scores,ids,contracts,p,g)for scores,p in zip(qv@expanded.T,parsed)]
 service=KnownSpecService.from_config(ef['matched_service']['path'],ef['matched_service']['sha256']);policies=read(ef['policy'])['policy_family'];assert len(policies)==20 and [x['policy']for x in history['results']]==policies
 results=[]
 for policy,prior in zip(policies,history['results']):
  baseline=[decide(r['baseline'],policy,service)for r in rankings];hybrid=[decide_hybrid(r,policy,service)for r in rankings]
  compact=lambda d,qid:dict(query_id=qid,status=d['status'],reason=d.get('reason'),problem_id=d.get('problem_id'))
  compactbase=[compact(d,q['query_id'])for q,d in zip(queries,baseline)]
  assert compactbase==prior['expanded102_v16_decisions'] and score_decisions(queries,baseline)==prior['expanded102_v16']
  results.append(dict(policy=policy,baseline_metrics=score_decisions(queries,baseline),hybrid_metrics=score_decisions(queries,hybrid),baseline_decisions=compactbase,hybrid_decisions=[dict(compact(d,q['query_id']),selected_raw_cosine=d['selected_raw_cosine'],selected_hybrid_score=d['selected_hybrid_score'],adjusted_margin=d['adjusted_margin'],raw_selected_vs_best_other_margin=d['raw_selected_vs_best_other_margin'],raw_global_top_margin=d['raw_global_top_margin'])for q,d in zip(queries,hybrid)]))
 return dict(schema='gamma.empirical-facet-reranker-result.v1',freeze_sha256=freeze_sha,code_sha256=f['code_sha256'],input_sha256={k:v['sha256']for k,v in f.items()if isinstance(v,dict)and 'path'in v and 'sha256'in v},status='completed',weight=.05,population=4081,query_count=52,policy_count=20,queries_with_tentative_facets=sum(bool(r['signed_facets']['facts']or r['signed_facets']['excluded_values'])for r in rankings),top_identity_changes=sum(r['baseline'][0][0]!=r['hybrid'][0][0]for r in rankings),private_query_diagnostics=[dict(query_id=q['query_id'],baseline_top_id=r['baseline'][0][0],hybrid_top_id=r['hybrid'][0][0],signed_facets=r['signed_facets'],dropped_conflicts=r['dropped_conflicts'])for q,r in zip(queries,rankings)],results=results,wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,source_availability_ranking_filter=False,semantic_proof=False,recognition_qualified=False,confirmation_read=False,encoder_invocations=0,source_payload_reads=0,candidate_executions=0,margin_semantics='Adjusted-score margin; cosine gate uses actual selected raw cosine',scope='Fixed empirical bonus; title-only unknown rivals unchanged, never eliminated. Authored development, no risk certificate.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--freeze',required=True);p.add_argument('--freeze-sha256',required=True);p.add_argument('--output',required=True);a=p.parse_args();resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(59,60));signal.alarm(60);os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1');f=read(dict(path=str(Path(a.freeze).resolve()),sha256=a.freeze_sha256));out=Path(a.output);out.mkdir(exist_ok=False)
 try:(out/'report.json').write_text(json.dumps(run(f,a.freeze_sha256),indent=2,sort_keys=True,allow_nan=False)+'\n')
 except BaseException as e:(out/'failure.json').write_text(json.dumps(dict(error_type=type(e).__name__,freeze_sha256=a.freeze_sha256,recognition_qualified=False)));raise
