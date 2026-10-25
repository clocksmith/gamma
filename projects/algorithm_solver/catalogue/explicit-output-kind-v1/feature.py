"""Empirical selected-contract output-kind conflict; never global task absence."""
import hashlib,json,re
VERSION='gamma.explicit-output-kind.v1'
def digest(text):return hashlib.sha256(text.encode()).hexdigest()
def evidence(text,start,end,rule,field='query'):return dict(start=start,end=end,span=text[start:end],text_sha256=digest(text),rule=rule,field=field)

QUERY_KINDS=(
 (r'(?:return|output|provide) (?:a |the )?complete (?:(?:admission|event|operation) )?log(?: with timestamps)?','record-collection'),
 (r'(?:return|output|provide) all (?:tied )?(?:paths|routes)','path-collection'),
 (r'(?:return|output|provide) (?:the )?best (?:route|path) and (?:its|a) (?:bonus )?flag','route-and-flag'),
 (r'(?:return|output) (?:an? |the )?(?:integer|number|count|scalar|probability)','numeric-scalar'),
 (r'(?:return|output) (?:the )?(?:number|count) of (?:paths|routes|events|admissions)','numeric-scalar'),
)

def query_kinds(text):
 if type(text)is not str or not text.strip()or len(text.encode())>32768:raise ValueError('bounded description required')
 # Reported/quoted examples and conditional introductions can scope later clauses.
 if re.search(r'["“”`?]|(?<!\w)[\'‘’]|[\'‘’](?!\w)|\b(?:example|quoted|quotation|ignore|instruction|hypothetical|claim|instead|actually|rather|correction|revised|debugging|debug|optional|optionally|diagnostic|rejected)\b|\bonly if\b',text,re.I):return dict(kinds=[],evidence=[],status='UNKNOWN_CONTEXT')
 segments=list(re.finditer(r'[^.;\n]+',text))
 if any(re.match(r'\s*(?:if|unless|when)\b',m.group(),re.I)for m in segments):return dict(kinds=[],evidence=[],status='UNKNOWN_CONDITIONAL_SCOPE')
 items=[]
 for segment in segments:
  local=segment.group();heads=[0]+[m.end()for m in re.finditer(r'\band\s+(?=(?:return|output|provide)\b)',local,re.I)]
  for offset in heads:
   piece=local[offset:];leading=len(piece)-len(piece.lstrip());piece=piece.strip();start=segment.start()+offset+leading
   prefix=local[:offset]
   if re.search(r'\b(?:not|never|avoid|without|instead|if|unless|whether)\b',prefix,re.I):continue
   for i,(pattern,kind)in enumerate(QUERY_KINDS):
    if re.fullmatch(pattern,piece,re.I|re.ASCII):items.append(dict(kind=kind,evidence=evidence(text,start,start+len(piece),f'complete-output-clause-{i}')))
 kinds=sorted({x['kind']for x in items})
 if len(kinds)>1:return dict(kinds=[],evidence=items,status='UNKNOWN_CONFLICTING_REQUESTS')
 return dict(kinds=kinds,evidence=items,status='PARTIAL_EMPIRICAL')

def contract_kind(doc):
 if doc.get('authority',{}).get('knowledge_class')!='reviewed-normative-contract':return dict(kind=None,evidence=[],status='UNKNOWN')
 items=[]
 for m in re.finditer(r'^Result: (.+)$',doc['text'],re.M):
  result=json.loads(m.group(1));typ=result.get('type')if isinstance(result,dict)else None
  if typ in ('integer','int','real','float','number'):items.append(evidence(doc['text'],m.start(1),m.end(1),'structured-numeric-result','Result'))
 return dict(kind='numeric-scalar'if items else None,evidence=items,authority_sha256=doc['authority'].get('authority_sha256'),status='REVIEWED'if items else'UNKNOWN')

def apply(text,baseline,contract):
 query=query_kinds(text);conflict=contract['kind']=='numeric-scalar'and bool(query['kinds'])and query['kinds'][0]in ('record-collection','path-collection','route-and-flag')
 result=dict(baseline)
 if baseline['status']=='accepted'and conflict:
  result=dict(status='abstain',reason='explicit_output_kind_conflict',problem_id=None,clarification_questions=[],semantic_proof=False,mode='empirical-output-kind')
  if 'query_id'in baseline:result['query_id']=baseline['query_id']
 return result,dict(feature_version=VERSION,query=query,contract=contract,conflict=conflict,semantic_proof=False,unknown_means='No abstention from missing or unrecognized extraction',global_out_of_catalogue_absence_proven=False)
