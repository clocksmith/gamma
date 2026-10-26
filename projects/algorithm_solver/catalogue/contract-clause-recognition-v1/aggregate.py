"""Empirical compatibility diagnostics, NOT entailment, veto, or acceptance.
No encoder/cohort/service imports. Caller supplies all rivals and explicitly
scope-resolved query evidence. Missing evidence is UNKNOWN, not false.
"""
import math
import importlib.util
from pathlib import Path
# Exact sibling path, no generic sys.modules name or import-search collision.
_spec=importlib.util.spec_from_file_location('_contract_clause_representation',Path(__file__).with_name('representation.py'))
_representation=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_representation)
ROLES=_representation.ROLES

def aggregate(stable_ids,raw_scores,contracts,query_evidence,similarities,expected_population=4081):
 if len(stable_ids)!=expected_population or len(set(stable_ids))!=expected_population or len(raw_scores)!=expected_population:raise ValueError('complete unique rival population required')
 if any(not math.isfinite(x)for x in raw_scores):raise ValueError('finite raw scores')
 if set(contracts)-set(stable_ids):raise ValueError('unknown contract identity')
 # Exact evidence identity explicitly supplied by extractor; not semantic dedup.
 grouped={};ignored=[]
 for q in query_evidence:
  role=q['role'];key=q['evidence_id'];sign=q.get('polarity')
  if role not in ROLES:raise ValueError('query role')
  if q.get('scope')!='explicit' or type(sign)is not int or sign not in (-1,1):ignored.append(key);continue
  grouped.setdefault(key,[]).append(q)
 active={};conflicts=[]
 for key,rows in sorted(grouped.items()):
  if len({(q['role'],q['polarity'])for q in rows})!=1:conflicts.append(key)
  else:active[key]=rows[0]
 known_pairs={(qid,c['clause_id'])for qid,q in active.items()for rows in contracts.values()for c in rows if q['role']==c['role']}
 if set(similarities)-known_pairs:raise ValueError('unbound similarity pair')
 for value in similarities.values():
  if not math.isfinite(value)or not 0<=value<=1:raise ValueError('compatibility must be normalized0..1; not probability')
 rows=[]
 for pid,raw in zip(stable_ids,raw_scores):
  cs={}
  for c in contracts.get(pid,[]):
   cid=c['clause_id']
   if cid in cs and cs[cid]!=c:raise ValueError('conflicting duplicate clause identity')
   cs[cid]=c
  cs=dict(sorted(cs.items()))
  if any(c['problem_id']!=pid for c in cs.values()):raise ValueError('contract identity binding')
  required={c['role']for c in cs.values()if c['required']};required_ids={cid for cid,c in cs.items()if c['required']};observed_ids={cid for cid in cs if any((qid,cid)in similarities for qid in active)};role_scores={};observed=set()
  for role in sorted(ROLES):
   values=[]
   for qid,q in sorted(active.items()):
    if q['role']!=role:continue
    # For each query evidence identity, strongest compatible positive predicate
    # match per role. Equal-strength opposite signs are unresolved, not votes.
    scored=[(similarities[qid,cid],q['polarity']*c['polarity'])for cid,c in cs.items()if c['role']==role and (qid,cid)in similarities]
    if not scored:continue
    top=max(v for v,sign in scored);signs={sign for v,sign in scored if v==top}
    if len(signs)!=1:continue
    values.append(top*next(iter(signs)))
   if values:role_scores[role]=math.fsum(values)/len(values);observed.add(role)
  signal=math.fsum(role_scores[k]for k in sorted(role_scores))/len(role_scores)if role_scores else None
  rows.append(dict(problem_id=pid,raw_cosine=raw,empirical_compatibility_signal=signal,role_signals=role_scores,required_clause_ids=sorted(required_ids),observed_required_clause_ids=sorted(required_ids&observed_ids),unknown_required_clause_ids=sorted(required_ids-observed_ids),required_roles=sorted(required),observed_required_roles=sorted(required&observed),unknown_required_roles=sorted(required-observed),authority_status='AUTHORITATIVE'if cs else'UNKNOWN',semantic_satisfaction='UNKNOWN'))
 # Raw ranking only. No new weight, margin, threshold, veto, or decision policy.
 order={pid:i for i,pid in enumerate(stable_ids)}
 rows.sort(key=lambda r:(-r['raw_cosine'],order[r['problem_id']]))
 return dict(rows=rows,population=len(rows),ignored_scope_evidence=sorted(set(ignored)),conflicted_evidence=sorted(conflicts),recognition_qualified=False,ranking='unchanged raw cosine; compatibility diagnostics only')
