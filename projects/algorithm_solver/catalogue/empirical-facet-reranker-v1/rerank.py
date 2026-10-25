"""Fixed empirical score adjustment; no semantic proof, elimination or fitting."""
import math
from projects.algorithm_solver.catalogue.empirical_recognition import rank,decide
WEIGHT=.05
VERSION='gamma.empirical-facet-reranker.v1'

def signed_facets(parsed):
 positive={};negative={}
 for e in parsed['tentative_evidence']:
  (positive if e['polarity']=='positive'else negative).setdefault(e['facet'],set()).add(e['value'])
 conflicts={k for k,vs in positive.items()if len(vs)>1 or vs&negative.get(k,set())}
 return dict(facts={k:next(iter(v))for k,v in positive.items()if k not in conflicts},excluded_values={k:sorted(v)for k,v in negative.items()if k not in conflicts},conflicts=[]),sorted(conflicts)

def agreement(q,contract,guard):
 facets=set(q['facts'])|set(q['excluded_values']);denom=max(1,len(facets));total=0
 for facet in facets:
  if facet in contract['conflicts']:continue
  value=contract['facts'].get(facet)
  if value is None:continue
  if value in q['excluded_values'].get(facet,[]):total-=1;continue
  if facet not in q['facts']:continue # Not excluded does not prove positive support.
  single=dict(facts={facet:q['facts'][facet]},excluded_values={},conflicts=[])
  # Input-order compatibility can require an independently supported distinctness premise.
  if facet=='input_order'and 'input_distinctness'in q['facts']:single['facts']['input_distinctness']=q['facts']['input_distinctness']
  verdict=guard.compare(single,contract)['facets'][facet]
  if verdict==guard.Facet.SATISFIED.value:total+=1
  elif verdict==guard.Facet.VIOLATED.value:total-=1
 return total/denom

def rerank(scores,ids,contracts,parsed,guard,*,expected_population=4081):
 if len(ids)!=expected_population or len(set(ids))!=expected_population or set(contracts)!=set(ids):raise ValueError('entire unchanged rival universe required')
 baseline=rank(scores,ids);raw=dict(baseline);q,conflicts=signed_facets(parsed)
 adjustment={pid:WEIGHT*agreement(q,contracts[pid],guard)for pid in ids};hybrid=rank([raw[pid]+adjustment[pid]for pid in ids],ids)
 assert {p for p,_ in hybrid}==set(ids)and all(abs(x)<=WEIGHT+1e-12 for x in adjustment.values())
 return dict(baseline=baseline,hybrid=hybrid,raw_cosines=raw,adjustments=adjustment,signed_facets=q,dropped_conflicts=conflicts)

def decide_hybrid(ranking,policy,service):
 """Raw-cosine threshold and adjusted-margin threshold, without float translation.

 Only after both gates pass, ask the existing service for the same qualified
 identity/language selections as empirical_recognition.decide. No source read.
 """
 h=ranking['hybrid'];pid=h[0][0];raw=ranking['raw_cosines'][pid];margin=h[0][1]-h[1][1]
 c,m=policy['min_cosine'],policy['min_margin']
 if type(c)not in (int,float)or type(m)not in (int,float)or not -1<=c<=1 or not 0<=m<=2:raise ValueError('policy threshold')
 result=dict(status='abstain',clarification_questions=[],mode='empirical-authored-cohort',semantic_proof=False)
 if raw<c or margin<=0 or margin<m:result['reason']='empirical_confidence_threshold'
 else:
  value=service.request(pid,include_source=False)
  if value['status']!='matched':result['reason']='top_identity_not_qualified'
  else:
   selected={}
   for language in ('javascript','python'):
    value=service.request(pid,language=language,include_source=False)
    if value['status']!='matched'or value.get('consumer_selection',{}).get('status')!='selected':result['reason']='both_languages_not_qualified';break
    selected[language]=value['consumer_selection']
   else:result=dict(status='accepted',problem_id=pid,implementations=selected,clarification_questions=[],mode='empirical-authored-cohort',semantic_proof=False,cosine=raw,margin=margin,applicability='Exact returned implementation contracts only; identity inferred empirically, never proven by tentative facets.')
 other_raw=max(score for candidate,score in ranking['raw_cosines'].items()if candidate!=pid)
 return dict(result,score_policy_version=VERSION,selected_raw_cosine=raw,selected_hybrid_score=h[0][1],adjusted_margin=margin,raw_selected_vs_best_other_margin=raw-other_raw,raw_global_top_margin=ranking['baseline'][0][1]-ranking['baseline'][1][1],semantic_proof=False)
