"""Evaluator-only normalized labels. No predictor/model imports."""

def evaluate(predictions,annotations,policies):
 if len(predictions)!=len(annotations):raise ValueError('population mismatch')
 result=[]
 for policy in policies:
  arms={}
  for arm in ('baseline','tentative'):
   m=dict(requests=len(predictions),positives=0,contrasts=0,positive_top_identity_correct=0,positive_accepted_identity_correct=0,positive_wrong_identity_accept=0,positive_abstention=0,eligible_positive_accept=0,ineligible_positive_accept=0,unknown_eligibility_positive_accept=0,contrast_target_conflict_accept=0,contrast_other_rival_accept_UNRESOLVED=0,contrast_abstention=0,errors=0)
   for prediction,label in zip(predictions,annotations):
    kind=label['kind'];target=label['target_id']
    if kind not in ('positive','selected_contract_contrast'):raise ValueError('explicit label semantics required')
    m['positives'if kind=='positive'else'contrasts']+=1
    if prediction['status']!='completed':m['errors']+=1;continue
    matches=[r for r in prediction['decisions']if r['policy']==policy]
    if len(matches)!=1:raise ValueError('policy identity mismatch')
    d=matches[0]['arms'][arm]
    if kind=='positive':
     m['positive_top_identity_correct']+=int(d['semantic_top_id']==target)
     if d['status']=='abstain':m['positive_abstention']+=1
     elif d['status']=='accepted':
      if d['problem_id']==target:
       m['positive_accepted_identity_correct']+=1;eligibility=label.get('artifact_eligible');m['eligible_positive_accept'if eligibility is True else'ineligible_positive_accept'if eligibility is False else'unknown_eligibility_positive_accept']+=1
      else:m['positive_wrong_identity_accept']+=1
     else:m['errors']+=1
    elif d['status']=='abstain':m['contrast_abstention']+=1
    elif d['status']=='accepted':m['contrast_target_conflict_accept'if d['problem_id']==target else'contrast_other_rival_accept_UNRESOLVED']+=1
    else:m['errors']+=1
   arms[arm]=m
  result.append(dict(policy=policy,arms=arms))
 return dict(results=result,recognition_qualified=False,global_absence_assumed=False,artifact_delivery_tested=False,scope='Paired development diagnostic; selected-target contrasts do not prove global absence.')
