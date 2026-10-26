"""One prospective uncalibrated empirical signal. No encoding or decisions."""
import math
ROLES=frozenset(('input_domain','output_identity','output_shape','objective','effects','preconditions'))
WEIGHT=.05

def unique(rows,key):
 out={}
 for row in rows:
  identity=row[key]
  if not isinstance(identity,str)or not identity:raise ValueError('nonempty provenance identity')
  if identity in out and out[identity]!=row:raise ValueError('provenance identity collision')
  out[identity]=row
 return dict(sorted(out.items()))
def finite(value,lo,hi):
 if type(value)not in (int,float)or not math.isfinite(value)or not lo<=value<=hi:raise ValueError('finite score in declared units required')
 return value

def rerank(stable_ids,raw_cosines,existing_hybrid_scores,query_spans,clauses,pairs,bindings,expected_bindings,expected_request_sha256,expected_population=4081):
 """pairs are rows with query_evidence_id,clause_id,cosine.
 Bindings assert exact existing encoder/prompt/dimension and RAW cosine units.
 Caller must verify those assertions against actual cached/encoder provenance.
 Missing observations and missing authority are separately UNKNOWN, never false.
 """
 if bindings!=expected_bindings:raise ValueError('encoder/prompt/score binding mismatch')
 if set(bindings)!={'encoder_sha256','prompt_sha256','embedding_dimension','score_units'}or bindings['score_units']!='raw_cosine_-1_to_1':raise ValueError('explicit cosine provenance required')
 if type(bindings['embedding_dimension'])is not int or bindings['embedding_dimension']<=0:raise ValueError('positive embedding dimension')
 for name in ('encoder_sha256','prompt_sha256'):
  if not isinstance(bindings[name],str)or len(bindings[name])!=64 or any(c not in '0123456789abcdef'for c in bindings[name]):raise ValueError('exact provenance hash')
 if any(not isinstance(pid,str)or not pid for pid in stable_ids):raise ValueError('nonempty string rival identities required')
 if not isinstance(expected_request_sha256,str)or len(expected_request_sha256)!=64 or any(c not in '0123456789abcdef'for c in expected_request_sha256):raise ValueError('exact request digest required')
 if len(stable_ids)!=expected_population or len(set(stable_ids))!=expected_population or len(raw_cosines)!=expected_population or len(existing_hybrid_scores)!=expected_population:raise ValueError('complete rival vectors required')
 for x in raw_cosines:finite(x,-1,1)
 for x in existing_hybrid_scores:finite(x,-1.05,1.05)
 qs=unique(query_spans,'evidence_id');cs=unique(clauses,'clause_id');universe=set(stable_ids)
 for q in qs.values():
  if q.get('request_sha256')!=expected_request_sha256:raise ValueError('mixed or unexpected request identity')
  if not {'request_sha256','span','text_sha256','track','scope','polarity'}<=set(q):raise ValueError('query provenance missing')
 for c in cs.values():
  if c['problem_id']not in universe or c['role']not in ROLES:raise ValueError('clause rival/role binding')
  if not {'authority_sha256','field','field_sha256','span','text','polarity','required'}<=set(c):raise ValueError('authority provenance missing')
 observations={}
 for p in pairs:
  key=(p['query_evidence_id'],p['clause_id']);value=finite(p['cosine'],-1,1)
  if key[0]not in qs or key[1]not in cs:raise ValueError('unbound observation')
  if key in observations and observations[key]!=value:raise ValueError('conflicting repeated observation')
  observations[key]=value
 by_pid={}
 for cid,c in cs.items():by_pid.setdefault(c['problem_id'],{}).setdefault(c['role'],[]).append(cid)
 rows=[]
 for pos,(pid,raw,hybrid)in enumerate(zip(stable_ids,raw_cosines,existing_hybrid_scores)):
  authority_roles=by_pid.get(pid,{});maxima={};observed_clause_ids=set()
  for role,cids in sorted(authority_roles.items()):
   values=[]
   for qid in qs:
    for cid in cids:
     if (qid,cid)in observations:values.append(observations[qid,cid]);observed_clause_ids.add(cid)
   if values:maxima[role]=max(values)
  mean=math.fsum(maxima[k]for k in sorted(maxima))/len(maxima)if maxima else None
  signal=mean-raw if mean is not None else 0.;adjustment=WEIGHT*signal;adjusted=hybrid+adjustment
  finite(signal,-2,2);finite(adjustment,-.1,.1);finite(adjusted,-1.150000000000001,1.150000000000001)
  ids={cid for cids in authority_roles.values()for cid in cids}
  rows.append(dict(problem_id=pid,stable_position=pos,raw_cosine=raw,existing_hybrid_score=hybrid,tentative_adjusted_score=adjusted,tentative_signal=signal,tentative_adjustment=adjustment,role_max_raw_cosines=maxima,observed_role_mean_raw_cosine=mean,authority_status='AUTHORITATIVE'if ids else'UNKNOWN',unobserved_authoritative_roles=sorted(set(authority_roles)-set(maxima)),absent_authority_roles=sorted(ROLES-set(authority_roles)),observed_clause_ids=sorted(observed_clause_ids),unobserved_clause_ids=sorted(ids-observed_clause_ids),semantic_entailment='UNKNOWN'))
 def order(field):return [r['problem_id']for r in sorted(rows,key=lambda r:(-r[field],r['stable_position']))]
 return dict(rows=rows,raw_ranking=order('raw_cosine'),existing_hybrid_ranking=order('existing_hybrid_score'),tentative_adjusted_ranking=order('tentative_adjusted_score'),population=len(rows),bindings=dict(bindings),request_sha256=expected_request_sha256,weight=WEIGHT,calibrated=False,recognition_qualified=False,acceptance_decisions=None)
