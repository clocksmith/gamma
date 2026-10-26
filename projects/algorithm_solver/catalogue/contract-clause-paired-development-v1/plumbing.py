"""Text-only paired fresh-vector plumbing; no service, labels or acceptance."""
import hashlib,importlib.util,math,struct
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
adapter=load('_paired_span_adapter',BASE/'contract-clause-adapter-v1/adapter.py')
encoder_binding=load('_paired_encoder_binding',BASE/'contract-clause-encoder-adapter-v1/encoder_binding.py')
tentative=load('_paired_tentative_rank',BASE/'contract-clause-tentative-v1/rank.py')
def cosine(a,b):
 if len(a)!=len(b)or not a:raise ValueError('vector dimension mismatch')
 x=math.fsum(u*v for u,v in zip(a,b));norm=math.sqrt(math.fsum(u*u for u in a)*math.fsum(v*v for v in b))
 if norm==0 or not math.isfinite(x)or not math.isfinite(norm):raise ValueError('finite nonzero vector')
 value=x/norm
 if not -1-1e-12<=value<=1+1e-12:raise ValueError('cosine arithmetic bounds')
 return min(1.,max(-1.,value)) # only roundoff endpoint correction, not score calibration

def paired_vectors(text,encoder,stable_ids,index_scores,baseline_hybrid,clauses,clause_vectors,expected_bindings,maximum_spans=8):
 """Callbacks are pinned owner code; raw scoring invoked ONCE for both arms.
 No expected identity or cohort lookup accepted. All candidate decisions/gates
 are deliberately outside this non-decision component, pending scope approval.
 """
 if type(maximum_spans)is not int or not 1<=maximum_spans<=8:raise ValueError('frozen span budget at most8')
 parsed=adapter.query(text);spans=parsed['evidence']
 if len(spans)>maximum_spans:return dict(status='error',reason='span_budget_exceeded',request_sha256=parsed['request_sha256'],span_count=len(spans),encoder_calls=0,acceptance_decisions=None)
 vectors=encoder.request(text,spans,parsed['request_sha256']);whole=vectors[0]
 if whole['request_sha256']!=parsed['request_sha256']or whole['text_sha256']!=parsed['request_sha256']:raise ValueError('whole request binding')
 bound=dict(encoder_sha256=whole['encoder_sha256'],prompt_sha256=whole['prompt_sha256'],embedding_dimension=whole['embedding_dimension'],score_units=whole['score_units'])
 if bound!=expected_bindings:raise ValueError('request encoder/prompt binding')
 def verify(v):
  if any(v[k]!=bound[k]for k in bound):raise ValueError('vector encoder/prompt binding')
  data=v['vector']
  if len(data)!=bound['embedding_dimension']or any(type(x)not in(int,float)or not math.isfinite(x)for x in data):raise ValueError('vector dimension/finite')
  if abs(math.sqrt(math.fsum(x*x for x in data))-1)>1e-3:raise ValueError('vector normalization')
  if hashlib.sha256(struct.pack('<'+str(len(data))+'d',*data)).hexdigest()!=v['vector_sha256']:raise ValueError('vector digest mismatch')
 for v in vectors:verify(v)
 if len(vectors)!=1+len(spans):raise ValueError('query vector count')
 qvectors={v['record_id']:v for v in vectors[1:]}
 if set(qvectors)!={q['evidence_id']for q in spans}:raise ValueError('span vector population')
 expected_clauses={r['record_id']:r for r in encoder_binding.clause_inputs(clauses)}
 cvec={}
 for v in clause_vectors:
  verify(v)
  cid=v['record_id']
  if cid not in expected_clauses:raise ValueError('unexpected clause vector')
  source=expected_clauses[cid]
  for key,value in source.items():
   if key!='text'and(key not in v or v[key]!=value):raise ValueError('current clause input/provenance mismatch')
  if 'text'in v and v['text']!=source['text']:raise ValueError('current clause text mismatch')
  if cid in cvec and cvec[cid]!=v:raise ValueError('clause vector identity collision')
  if any(v[k]!=bound[k]for k in bound):raise ValueError('clause/query encoder incompatibility')
  cvec[cid]=v
 if set(cvec)!={c['clause_id']for c in clauses}:raise ValueError('exact clause-vector population')
 pairs=[]
 for q in spans:
  v=qvectors[q['evidence_id']]
  if v['request_sha256']!=parsed['request_sha256']or v['text_sha256']!=q['text_sha256']:raise ValueError('span request/text binding')
  for cid,cv in sorted(cvec.items()):pairs.append(dict(query_evidence_id=q['evidence_id'],clause_id=cid,cosine=cosine(v['vector'],cv['vector'])))
 raw=list(index_scores(whole['vector']));hybrid=list(baseline_hybrid(text,raw))
 ranking=tentative.rerank(stable_ids,raw,hybrid,spans,clauses,pairs,bound,expected_bindings,parsed['request_sha256'])
 return dict(status='ranked',request_sha256=parsed['request_sha256'],raw_vector_sha256=whole['vector_sha256'],same_raw_vector_for_both_arms=True,ranking=ranking,span_count=len(spans),fresh_encoder_rows=len(vectors),acceptance_decisions=None)
