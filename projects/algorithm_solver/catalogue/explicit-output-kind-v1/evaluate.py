"""Frozen three-arm metadata ablation, no ranking/model/query encoding."""
import argparse,hashlib,json,resource,signal,time
from pathlib import Path
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(s):
 p=Path(s['path']);assert p.is_absolute()and p.stat().st_size<=32*1024**2 and sha(p)==s['sha256'];return json.loads(p.read_text())

def run(f,freeze_sha):
 from projects.algorithm_solver.catalogue.empirical_recognition import score_decisions
 from projects.algorithm_solver.catalogue.boundary_policy import authorize_before_open
 start=time.perf_counter();cpu=time.process_time()
 for n,h in f['code_sha256'].items():assert sha(HERE/n)==h
 for n,h in f['dependency_code_sha256'].items():assert sha(HERE.parent/n)==h
 cf=read(f['choice_freeze'])
 for n,h in cf['code_sha256'].items():assert sha(Path(f['choice_freeze']['path']).parent/n)==h
 from feature import contract_kind,apply as output_apply
 from axis944 import authority_obligation,apply as axis_apply
 ef=read(f['encoder_freeze']);queries=read(ef['development'])['queries'];assert len(queries)==52
 plan=read(ef['new_document_plan']);gate=read(plan['boundary_gate'])
 for a in plan['authorities']:authorize_before_open(a['problem_id'],gate['artifact_paths'],gate['trusted_hashes'],language='javascript',payload_kind='statement')
 bundle=read(ef['new_documents']);assert bundle['plan_sha256']==ef['new_document_plan']['sha256']and bundle['population']==4081;contracts={d['problem_id']:contract_kind(d)for d in bundle['documents']};assert len(contracts)==4081
 # External approval and correction receipts bind prospective944 integration.
 review=read(f['authority_review']);correction_review=read(f['correction_review']);assert review['authority_sha256']==f['authority944']['sha256']and correction_review['correction_sha256']==f['correction944']['sha256']
 items={}
 for key in ('authority944','clarification944','correction944'):
  authorize_before_open('leetcode:944',gate['artifact_paths'],gate['trusted_hashes'],language='javascript',payload_kind='statement');items[key]=read(f[key])
 assert items['correction944']['supersedes_field']['sha256']==f['clarification944']['sha256']
 obligation=authority_obligation(items['authority944'],f['authority944']['sha256'])
 baseline=read(f['choice_result']);assert baseline['freeze_sha256']==f['choice_freeze']['sha256']and baseline['code_sha256']==cf['code_sha256'];read(f['choice_independent_review'])
 policies=read(ef['policy'])['policy_family'];assert len(policies)==20 and [r['policy']for r in baseline['results']]==policies
 results=[];reviews=[]
 for row in baseline['results']:
  prior=row['feature_decisions'];assert [x['query_id']for x in prior]==[q['query_id']for q in queries]and score_decisions(queries,prior)==row['feature_metrics'];arms={name:[]for name in ('axis944_only','output_only','both')}
  for q,b in zip(queries,prior):
   contract=contracts.get(b.get('problem_id'),dict(kind=None,evidence=[],status='UNKNOWN'));axis,ae=axis_apply(q['text'],b,obligation);out,oe=output_apply(q['text'],b,contract);both,be=axis_apply(q['text'],out,obligation)
   for name,value,evidence in [('axis944_only',axis,ae),('output_only',out,oe),('both',both,dict(output=oe,axis=be))]:
    arms[name].append(value);assert value['status']!='accepted'or value==b
    if value!=b:reviews.append(dict(query_id=q['query_id'],policy_id=row['policy']['id'],arm=name,selected_id=b['problem_id'],evidence=evidence,independent_semantic_review='PENDING'))
  results.append(dict(policy=row['policy'],baseline_metrics=row['feature_metrics'],baseline_decisions=prior,arms={name:dict(metrics=score_decisions(queries,values),decisions=values)for name,values in arms.items()}))
 return dict(schema='gamma.explicit-output-axis-ablation-result.v1',status='completed',freeze_sha256=freeze_sha,code_sha256=f['code_sha256'],input_sha256={k:v['sha256']for k,v in f.items()if isinstance(v,dict)and 'path'in v and 'sha256'in v},population=4081,query_count=52,policy_count=20,results=results,private_trigger_reviews=reviews,wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,source_payload_reads=0,model_executions=0,ranking_reruns=0,confirmation_read=False,recognition_qualified=False,semantic_proof=False,historical102_modified=False,scope='Separate944-only/output-only/both empirical abstention arms; explicit selected-contract evidence only, no omission veto or globalabsence claim.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--freeze',required=True);p.add_argument('--freeze-sha256',required=True);p.add_argument('--output',required=True);a=p.parse_args();resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(59,60));signal.alarm(60);f=read(dict(path=str(Path(a.freeze).resolve()),sha256=a.freeze_sha256));out=Path(a.output);out.mkdir(exist_ok=False)
 try:(out/'report.json').write_text(json.dumps(run(f,a.freeze_sha256),indent=2,sort_keys=True,allow_nan=False)+'\n')
 except BaseException as e:(out/'failure.json').write_text(json.dumps(dict(error_type=type(e).__name__,freeze_sha256=a.freeze_sha256,recognition_qualified=False)));raise
