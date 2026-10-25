"""Explicit TEST ADAPTER: cached dev vectors + synthetic delivery, not model/serving.
Exercises the same Engine and exact state initializer; never opens confirmation.
"""
import argparse,hashlib,json,os,resource,signal,time
from pathlib import Path
from runtime import pinned,module,prepare_state,Engine,sha
class CachedEncoder:
 def __init__(self,queries,vectors,flags):self.queries=queries;self.vectors=vectors;self.flags=flags;self.position=0
 def encode(self,texts,query):
  i=self.position;assert query is True and texts==[self.queries[i]['text']];self.position+=1;self.last_request_info=dict(query=True,rows=1,truncated=[self.flags[i]])
  return self.vectors[i:i+1]
class SyntheticDelivery:
 def __init__(self,original):self.RequestTimer=original.RequestTimer;self.encoded=original.encoded;self.calls=0
 def materialize(self,service,pid,selections,timer):
  # No service include_source request and no candidate bytes. This cannot
  # certify artifact delivery; the separately approved native run must do that.
  self.calls+=1
  return {'javascript':{'status':'SYNTHETIC_NOT_MATERIALIZED'},'python':{'status':'SYNTHETIC_NOT_MATERIALIZED'}},{'synthetic_delivery':True}

def run(f,freeze_sha):
 import numpy as np
 start=time.perf_counter();state=prepare_state(f);ef=pinned(f['encoder_freeze']);queries=pinned(ef['development'])['queries'];cp=pinned(ef['cache_plan']);cache=module('cached_integrated_index',ef['cache_module']);qc=module('cached_integrated_queries',ef['query_cache_module']);vectors,flags=qc.restore_queries(cp,queries,cache,np);assert not any(flags)
 encoder=CachedEncoder(queries,vectors,flags);delivery=SyntheticDelivery(state['delivery']);state['delivery']=delivery;engine=Engine(encoder=encoder,**state);original=pinned(f['development_baseline']);baseline=next(r['arms']['both']['decisions']for r in original['results']if r['policy']==engine.policy);rows=[]
 assert len(queries)==len(baseline)==52, 'development population count mismatch'
 query_ids=[q['query_id'] for q in queries];baseline_ids=[r['query_id'] for r in baseline]
 assert len(set(query_ids))==52 and query_ids==baseline_ids, 'development identity/order mismatch'
 for q,expected in zip(queries,baseline):
  response,summary,selections=engine.request(q['text']);actual=dict(query_id=q['query_id'],status=summary.get('decision_status','abstain'),reason=summary.get('decision_reason'),problem_id=summary.get('decision_problem_id'))
  matches=all(actual[k]==expected.get(k)for k in ('status','reason','problem_id'));assert summary['status']!='error';rows.append(dict(query_id=q['query_id'],matches=matches,expected_status=expected['status'],actual_status=actual['status'],expected_id=expected.get('problem_id'),actual_id=actual['problem_id']))
 return dict(schema='gamma.integrated-cached-test-equivalence.v1',freeze_sha256=freeze_sha,policy=engine.policy,requests=len(rows),adapter_encode_calls=encoder.position,decision_equivalence=all(x['matches']for x in rows),rows=rows,source_payload_reads=0,real_artifact_materializations=0,synthetic_delivery_calls=delivery.calls,model_executions=0,fresh_model_query_encodings=0,confirmation_read=False,recognition_qualified=False,wall_seconds=time.perf_counter()-start,scope='Integration decision equivalence only: cached development vectors and explicitly synthetic delivery adapter. Not fresh encoder or end-to-end artifact evidence.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--freeze',required=True);p.add_argument('--freeze-sha256',required=True);p.add_argument('--output',required=True);a=p.parse_args();resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(59,60));signal.alarm(60);os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1');f=pinned(dict(path=str(Path(a.freeze).resolve()),sha256=a.freeze_sha256));out=Path(a.output);out.mkdir(exist_ok=False)
 try:(out/'report.json').write_text(json.dumps(run(f,a.freeze_sha256),indent=2,sort_keys=True)+'\n')
 except BaseException as e:(out/'failure.json').write_text(json.dumps(dict(error_type=type(e).__name__,freeze_sha256=a.freeze_sha256,confirmation_read=False)));raise
