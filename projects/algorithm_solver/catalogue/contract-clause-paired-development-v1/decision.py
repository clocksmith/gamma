"""Same selected-candidate gates for each paired arm. No evaluation labels."""
import hashlib,json

def abstain(reason):return dict(status='abstain',reason=reason,clarification_questions=[])
def registered_scope(pid,selections,service,authorize_statement):
 """Reuse existing pinned service/receipt validation; never a cohort registry.
 Live gate precedes each selected contract extraction. Known reviewed schemas
 establish declared statement scope, not correctness proof or query execution.
 """
 from projects.algorithm_solver.catalogue.catalogue import digest,hash_value
 semantic=[];scope_records={}
 for lang in ('javascript','python'):
  value=service.request(pid,language=lang,include_source=False)
  if value.get('consumer_selection')!=selections.get(lang):return dict(status='UNKNOWN')
  selected=selections[lang];impl=selected.get('implementation',{})
  if selected.get('problem_id')!=pid or impl.get('evidence_class')!='normative-typed-effects'or not hash_value(impl.get('receipt_sha256'))or not impl.get('contract_scope'):return dict(status='UNKNOWN')
  authorize_statement(pid,lang)
  provenance=impl.get('provenance',{});batch=provenance.get('public_batch',{}).get('problem_contract');foundation=provenance.get('public_foundation',{}).get('problem_contract')
  if isinstance(batch,dict)and batch.get('schema')=='gamma.reviewed-public-batch-contract.v1':
   if digest(batch)!=impl.get('problem_contract_sha256')or not hash_value(batch.get('authority_review_sha256'))or not hash_value(batch.get('qualification_freeze_sha256')):return dict(status='UNKNOWN')
   contract=batch.get('reviewed_statement_contract',{})
   if contract.get('problem_id')!=pid:return dict(status='UNKNOWN')
   result=contract.get('result')
   if isinstance(result,dict)and result.get('finite_evidence_scope'):return dict(status='UNSUPPORTED_FINITE_SCOPE')
   if not all(k in contract for k in ('domain','result','local_effects','statement_sha256')):return dict(status='UNKNOWN')
   semantic.append(digest(contract))
  elif isinstance(foundation,dict)and foundation.get('schema')=='gamma.reviewed-official-foundation-contract.v1':
   if digest(foundation)!=impl.get('problem_contract_sha256')or foundation.get('problem_id')!=pid or not hash_value(foundation.get('official_contract_sha256')):return dict(status='UNKNOWN')
   if not all(k in foundation for k in ('official_preconditions','official_result','local_policy')):return dict(status='UNKNOWN')
   if isinstance(foundation['official_result'],dict)and foundation['official_result'].get('finite_evidence_scope'):return dict(status='UNSUPPORTED_FINITE_SCOPE')
   semantic.append(digest({k:foundation[k]for k in ('problem_id','official_contract_sha256','official_preconditions','official_result','local_policy')}))
  else:return dict(status='UNKNOWN')
  scope_records[lang]=dict(contract_scope=impl['contract_scope'],caveats=impl.get('caveats'),receipt_sha256=impl['receipt_sha256'],problem_contract_sha256=impl['problem_contract_sha256'])
 if len(set(semantic))!=1:return dict(status='UNKNOWN')
 return dict(status='SUPPORTED_STATEMENT_DOMAIN',semantic_contract_sha256=semantic[0],qualification_scopes=scope_records)

def paired_decisions(text,ranking,policies,service,decide_hybrid,semantic_chain,normative,authorize_statement):
 rows={r['problem_id']:r for r in ranking['rows']};raw={pid:r['raw_cosine']for pid,r in rows.items()};baseline=[(pid,raw[pid])for pid in ranking['raw_ranking']];out=[]
 for policy in policies:
  arms={}
  for arm,order_key,score_key in (('baseline','existing_hybrid_ranking','existing_hybrid_score'),('tentative','tentative_adjusted_ranking','tentative_adjusted_score')):
   ordered=ranking[order_key];h=[(pid,rows[pid][score_key])for pid in ordered];decision=decide_hybrid(dict(baseline=baseline,hybrid=h,raw_cosines=raw),policy,service)
   # Call independently for THIS arm's selected candidate. Never reuse baseline.
   decision=semantic_chain(text,decision)
   if decision['status']=='accepted':
    pid=decision['problem_id'];selected=decision['implementations']
    if not normative(selected,pid):decision=abstain('normative_evidence_required')
    else:
     scope=registered_scope(pid,selected,service,authorize_statement)
     if scope['status']!='SUPPORTED_STATEMENT_DOMAIN':decision=abstain('artifact_scope_'+scope['status'].lower())
   # Observations are metadata decisions only; no include_source/materialization.
   arms[arm]=decision
  out.append(dict(policy=policy,arms=arms))
 return out
