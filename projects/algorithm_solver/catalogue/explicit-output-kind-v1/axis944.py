"""Linked944 authority integration: explicit unresolved sorting-axis only."""
import hashlib,importlib.util,re,sys
from pathlib import Path
P=Path(__file__).resolve().parent.parent/'explicit-required-choice-v1/feature.py'
PIN='e48c55f5a93bf0337fca0b85a278c6939782327aba270722eefe624cd42daf16'
if hashlib.sha256(P.read_bytes()).hexdigest()!=PIN:raise ValueError('existing choice feature drift')
sp=importlib.util.spec_from_file_location('axis944_existing_choice',P);choice=importlib.util.module_from_spec(sp);sys.modules[sp.name]=choice;sp.loader.exec_module(choice)
TERMS={'each column':'independent-columns','columns independently':'independent-columns','each row':'within-rows','the list of whole rows':'row-sequence','whole rows':'row-sequence'}
TERM='(?:'+'|'.join(re.escape(k)for k in TERMS)+')'
AXIS=re.compile(r'whether (?:sorted|sorting) (?:means|applies to) (?P<a>'+TERM+r')(?:,\s*(?P<b>'+TERM+r'))?,?\s+(?:or|versus)\s+(?P<c>'+TERM+r')',re.I|re.ASCII)

def authority_obligation(authority,artifact_sha):
 if authority.get('problem_id')!='leetcode:944' or authority.get('qualification_created')is not False:raise ValueError('reviewed944 statement-only authority')
 clauses={x['id']:x for x in authority['clauses']};fact=clauses['sorting_axis']['fact']
 if fact!='Evaluate each column independently in original top-to-bottom row order.':raise ValueError('exact reviewed sorting-axis clause')
 return dict(value='independent-columns',artifact_sha256=artifact_sha,clause_id='sorting_axis',evidence=dict(start=0,end=len(fact),span=fact,text_sha256=choice.sha(fact),field='authority.clauses[sorting_axis].fact'))

def extract(text):
 context=choice.explicit_unknowns(text)
 if context['context_status'].startswith('UNKNOWN'):return []
 # Explicitly resolved axis, in either order, prevents an unresolved claim.
 segments=list(re.finditer(r'[^.;\n]+',text))
 for s in segments:
  if re.fullmatch(r'\s*(?:sort each (?:column|row) independently|sorting means (?:each column|each row|whole rows|the list of whole rows)|the sorting axis is (?:independent columns|within rows|whole rows|row-sequence))\s*',s.group(),re.I|re.ASCII):return []
 found=[]
 for s in segments:
  clause=s.group().strip();start=s.start()+len(s.group())-len(s.group().lstrip())
  for pattern in choice.UNRESOLVED:
   m=re.fullmatch(pattern,clause,re.I|re.ASCII)
   if not m:continue
   body=m.group('body');axis=AXIS.fullmatch(body);values=[]
   if axis:values=sorted({TERMS[v.lower()]for v in axis.groupdict().values()if v})
   elif re.fullmatch(r'(?:the )?sorting axis',body,re.I):values=['explicitly-unresolved']
   if len(values)>=2 or values==['explicitly-unresolved']:found.append(dict(facet='sorting_axis',alternatives=values,evidence=choice.span(text,start,start+len(clause),'explicit-sorting-axis-uncertainty')))
 return found

def apply(text,baseline,obligation):
 evidence=extract(text)if baseline.get('problem_id')=='leetcode:944'else[];matches=[x for x in evidence if x['alternatives']==['explicitly-unresolved']or obligation['value']in x['alternatives']];out=dict(baseline)
 if baseline['status']=='accepted'and matches:
  out=dict(status='abstain',reason='explicit_sorting_axis_unresolved',problem_id=None,clarification_questions=[],semantic_proof=False,mode='empirical-required-choice')
  if 'query_id'in baseline:out['query_id']=baseline['query_id']
 return out,dict(query_evidence=matches,contract_obligation=obligation if matches else None,semantic_proof=False,missing_extraction='UNKNOWN/no-op')
