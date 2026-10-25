"""Frozen metadata-only postdecision experiment, original20hybrid policies."""
import argparse,hashlib,json,os,resource,signal,time
from pathlib import Path
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(s):
 p=Path(s['path']);assert p.is_absolute()and p.stat().st_size<=32*1024**2 and sha(p)==s['sha256'];return json.loads(p.read_text())

def run(f,freeze_sha):
 from projects.algorithm_solver.catalogue.empirical_recognition import score_decisions
 from projects.algorithm_solver.catalogue.boundary_policy import authorize_before_open
 from feature import obligations,apply,explicit_unknowns
 start=time.perf_counter();cpu=time.process_time()
 for n,h in f['code_sha256'].items():assert sha(HERE/n)==h
 for n,h in f['dependency_code_sha256'].items():assert sha(HERE.parent/n)==h
 original=read(f['reranker_result']);rf=read(f['reranker_freeze']);assert original['freeze_sha256']==f['reranker_freeze']['sha256']and original['code_sha256']==rf['code_sha256']
 for n,h in rf['code_sha256'].items():assert sha(Path(f['reranker_freeze']['path']).parent/n)==h
 read(f['reranker_independent_review']);ef=read(f['encoder_freeze']);queries=read(ef['development'])['queries'];assert len(queries)==52
 plan=read(ef['new_document_plan']);gate=read(plan['boundary_gate'])
 for a in plan['authorities']:authorize_before_open(a['problem_id'],gate['artifact_paths'],gate['trusted_hashes'],language='javascript',payload_kind='statement')
 bundle=read(ef['new_documents']);assert bundle['plan_sha256']==ef['new_document_plan']['sha256']and bundle['population']==4081;required={d['problem_id']:obligations(d)for d in bundle['documents']};assert len(required)==4081
 policy=read(ef['policy'])['policy_family'];assert len(policy)==20 and [x['policy']for x in original['results']]==policy
 results=[];reviews=[]
 for row in original['results']:
  baseline=row['hybrid_decisions'];assert [x['query_id']for x in baseline]==[q['query_id']for q in queries];assert score_decisions(queries,baseline)==row['hybrid_metrics'];out=[]
  for q,b in zip(queries,baseline):
   output,analysis=apply(q['text'],b,required.get(b.get('problem_id'),{}));out.append(output)
   if output!=b:reviews.append(dict(query_id=q['query_id'],policy_id=row['policy']['id'],selected_id=b['problem_id'],evidence=analysis,independent_semantic_review='PENDING'))
   assert output['status']!='accepted'or output==b
  results.append(dict(policy=row['policy'],baseline_metrics=row['hybrid_metrics'],feature_metrics=score_decisions(queries,out),baseline_decisions=baseline,feature_decisions=out))
 return dict(schema='gamma.explicit-required-choice-result.v1',status='completed',freeze_sha256=freeze_sha,code_sha256=f['code_sha256'],input_sha256={k:v['sha256']for k,v in f.items()if isinstance(v,dict)and 'path'in v and 'sha256'in v},population=4081,query_count=52,policy_count=20,explicit_unresolved_query_count=sum(bool(explicit_unknowns(q['text'])['choices'])for q in queries),private_trigger_reviews=reviews,results=results,wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,source_payload_reads=0,encoder_invocations=0,ranking_reruns=0,confirmation_read=False,recognition_qualified=False,semantic_proof=False,scope='Empirical abstention on explicit unresolved selected-contract obligations, not proof from missing extraction or global task absence.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--freeze',required=True);p.add_argument('--freeze-sha256',required=True);p.add_argument('--output',required=True);a=p.parse_args();resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(59,60));signal.alarm(60);f=read(dict(path=str(Path(a.freeze).resolve()),sha256=a.freeze_sha256));out=Path(a.output);out.mkdir(exist_ok=False)
 try:(out/'report.json').write_text(json.dumps(run(f,a.freeze_sha256),indent=2,sort_keys=True,allow_nan=False)+'\n')
 except BaseException as e:(out/'failure.json').write_text(json.dumps(dict(error_type=type(e).__name__,freeze_sha256=a.freeze_sha256,recognition_qualified=False)));raise
