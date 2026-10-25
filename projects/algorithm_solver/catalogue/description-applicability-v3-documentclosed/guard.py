"""Partial span-grounded clause extraction; no open-world semantic closure."""
import hashlib,importlib.util,json,re,sys
from pathlib import Path
P=Path(__file__).resolve().parent.parent/'description-applicability-v2/guard.py'
PIN='1eb26189faecc10cbf87ab74a16f2685b1df66e275780ba9cc6582e862711edb'
if hashlib.sha256(P.read_bytes()).hexdigest()!=PIN:raise ValueError('predecessor guard drift')
# Successor freeze pins this imported predecessor and its existing authority deps.
spec=importlib.util.spec_from_file_location('clause_guard_predecessor',P);old=importlib.util.module_from_spec(spec);sys.modules[spec.name]=old;spec.loader.exec_module(old)
Facet=old.Facet;VERSION='gamma.description-applicability.v3.4'
FACETS=old.FACETS+('output_cardinality','result_order','input_contiguity','output_measure')
# Patterns describe local imperative/positive clauses, not complete descriptions.
# Conditional, quoted and unsupported negation scopes are withheld wholesale.
RULES=(
 (r'(?:\b(?:a|the) (?:list|array) of distinct integers\b|^\s*no (?:number|value) is repeated\s*$|\bcyclic shift of a strictly ascending(?: numeric)? array\b)','input_distinctness','distinct'),
 (r'\b(?:return|output)(?: the| its| an?| all)? (?:minimum|smallest|maximum|largest)? ?(?:value|values)\b','returned_entity','value'),
 (r'\b(?:return|output)(?: the| an?| all)? (?:index|indices)\b','returned_entity','index'),
 (r'\b(?:return|output) (?:the )?(?:number of positions|length)\b','output_measure','count'),
 (r'\b(?:report|return) the length\b','output_measure','count'),
 (r'\b(?:contiguous|adjacent positions)\b','input_contiguity','contiguous'),
 (r'\b(?:return|output) (?:a |an )?integer\b','result_shape','scalar-integer'),
 (r'\b(?:return|output) (?:an )?integer array\b','result_shape','integer-array'),
 (r'\b(?:return|output) (?:the )?(?:resulting )?matrix\b','result_shape','integer-matrix'),
 (r'\b(?:two-item answer|two-item result|two-value answer)\b','output_cardinality','2'),
 (r'\b(?:duplicated|duplicate) value first, missing value second\b','result_order','duplicate-then-missing'),
 (r'\b(?:update|mutate) the (?:provided|supplied|input) (?:image|array|matrix)\b','input_mutation','required'),
 (r'\breturn (?:that|the) same (?:outer|input) array\b','output_alias','input'),
 (r'\breturn the resulting matrix using the supplied matrix root\b','output_alias','input'),
 (r'\b(?:return|output) a (?:new|fresh) array\b','output_alias','fresh'),
 (r'\bdo not mutate (?:the )?input\b','input_mutation','forbidden'),
)
NEGATIVE=(
 (r'\bnot (?:its|the|an?) index\b','returned_entity','index'),
 (r'\bnot (?:the )?values(?: themselves)?\b','returned_entity','value'),
 (r'\bnot a subsequence with gaps\b','input_contiguity','gapped'),
)

def item(text,m,facet,value,rule,polarity='positive',field='query'):
 return dict(facet=facet,value=value,field=field,start=m.start(),end=m.end(),span=m.group(),text_sha256=old.sha(text.encode()),rule=rule,polarity=polarity)

def tentative_query(text):
 if type(text)is not str or not text.strip()or len(text.encode())>32768:raise ValueError('nonempty bounded query required')
 evidence=[];unknown=[]
 for sentence in re.finditer(r'[^.;\n]+',text):
  local=sentence.group();start=sentence.start();covered=[False]*len(local)
  # Do not infer facts under hypotheticals, reported/quoted commands or broad negation.
  if re.search(r'\b(?:if|when|unless|whether|might|may|instead|either|or|except|never|without|avoid|example|suppose|could|should|non|reject|false|incorrect|instruction|asked|said|says|claim)\b|["“”?]',local,re.I):
   unknown.append(dict(start=start,end=sentence.end(),span=local,reason='unsupported_scope'));continue
  direct=bool(re.match(r'\s*(?:return|output|report|update|mutate|do not mutate)\b',local,re.I))
  declaration=bool(re.fullmatch(r'\s*no (?:number|value) is repeated\s*',local,re.I)) or bool(re.match(r'\s*(?:a|the) (?:list|array) of distinct integers\b',local,re.I))
  standalone_negative=any(re.fullmatch(pattern,local.strip(),re.I) for pattern,_,_ in NEGATIVE)
  if not (direct or declaration or standalone_negative):
   unknown.append(dict(start=start,end=sentence.end(),span=local,reason='unsupported_clause_head'));continue
  negatives=list(re.finditer('|'.join('(?:'+x[0]+')'for x in NEGATIVE)+r'|\bdo not mutate (?:the )?input\b',local,re.I))
  negtokens=list(re.finditer(r'\b(?:not|no|cannot|dont|don.t)\b',local,re.I))
  # No-number-is-repeated is explicitly supported, other no scopes stay unknown.
  negatives+=list(re.finditer(r'\bno (?:number|value) is repeated\b|\bno repeats\b',local,re.I))
  if any(not any(m.start()<=n.start()<m.end()for m in negatives)for n in negtokens):
   unknown.append(dict(start=start,end=sentence.end(),span=local,reason='unsupported_negation_scope'));continue
  candidates=[]
  for polarity,rules in [('positive',RULES),('negative',NEGATIVE)]:
   for i,(pattern,facet,value)in enumerate(rules):
    for m in re.finditer(pattern,local,re.I):
     prefix=local[:m.start()]
     if polarity=='positive' and prefix.strip() and not re.search(r'\band\s*$',prefix,re.I):continue
     if polarity=='negative' and not standalone_negative and not re.search(r',\s*$',prefix):continue
     # Prevent integer prefix falsely classifying an integer array.
     if facet=='result_shape'and value=='scalar-integer'and re.match(r'\s+array\b',local[m.end():],re.I):continue
     # Positive rules may not borrow tokens from an explicit negative clause.
     if polarity=='positive'and any(m.start()<n.end()and m.end()>n.start()for n in negatives)and not (facet=='input_mutation'and value=='forbidden')and facet!='input_distinctness':continue
     e=item(local,m,facet,value,f'{polarity}-clause-{i}',polarity);e.update(start=start+m.start(),end=start+m.end(),text_sha256=old.sha(text.encode()));candidates.append(e)
     for j in range(m.start(),m.end()):covered[j]=True
  evidence+=candidates
  # Retain every unsupported non-space/non-punctuation run with original offsets.
  j=0
  while j<len(local):
   if covered[j]or local[j].isspace()or local[j]in ',:':j+=1;continue
   k=j+1
   while k<len(local)and not covered[k]:k+=1
   end=k
   while end>j and local[end-1].isspace():end-=1
   unknown.append(dict(start=start+j,end=start+end,span=local[j:end],reason='unsupported_remainder'));j=k
 vals={};excluded={}
 for e in evidence:(vals if e['polarity']=='positive'else excluded).setdefault(e['facet'],set()).add(e['value'])
 conflicts=sorted(k for k,v in vals.items()if len(v)>1 or v&excluded.get(k,set()))
 return dict(facts={k:next(iter(v))for k,v in vals.items()if len(v)==1 and k not in conflicts},excluded_values={k:sorted(v)for k,v in excluded.items()},conflicts=conflicts,evidence=evidence,unsupported_spans=unknown,grammar_complete=bool(evidence)and not unknown and not conflicts,query_sha256=old.sha(text.encode()),semantic_proof=False)

# Only complete independently delimited clauses produce hard constraints.
# Partial spans remain useful for coverage diagnostics, never contradiction.
FULL_RULES=tuple((p,f,v)for p,f,v in old.QUERY_RULES if f!='returned_entity')+(
 (r'(?:return|output) (?:the )?(?:minimum |maximum |smallest |largest )?input (?:value|values|element|elements)','returned_entity','value'),
 (r'(?:return|output) (?:the |an? )?(?:index|indices)','returned_entity','index'),
 (r'(?:return|output) (?:the )?(?:length|number of positions)','output_measure','count'),
 (r'(?:the )?selected run is contiguous','input_contiguity','contiguous'),
 (r'(?:the )?input elements are distinct','input_distinctness','distinct'),
 (r'(?:return|output) (?:a )?two-item array','output_cardinality','2'),
 (r'(?:return|output) (?:the )?duplicate value first, missing value second','result_order','duplicate-then-missing'),
 (r'(?:update|mutate) the (?:provided|supplied|input) (?:image|array|matrix)','input_mutation','required'),
 (r'return (?:that|the) same (?:outer|input) array','output_alias','input'),
)
FULL_NEG=(
 (r'(?:do )?not (?:return|output) (?:the |an? )?(?:index|indices)','returned_entity','index'),
 (r'(?:do )?not (?:return|output) (?:the )?input (?:value|values|element|elements)','returned_entity','value'),
)

def parse_query(text):
 tentative=tentative_query(text);items=[];unknown=[]
 for segment in re.finditer(r'[^.;\n]+',text):
  start,end=segment.span()
  while start<end and text[start].isspace():start+=1
  while end>start and text[end-1].isspace():end-=1
  clause=text[start:end];matches=[]
  for polarity,rules in [('positive',FULL_RULES),('negative',FULL_NEG)]:
   for i,(pattern,facet,value)in enumerate(rules):
    if re.fullmatch(pattern,clause,re.I|re.ASCII):
     matches.append(dict(facet=facet,value=value,field='query',start=start,end=end,span=clause,text_sha256=old.sha(text.encode()),rule=f'complete-{polarity}-{i}',polarity=polarity,admissible=True))
  # One explicit coordinated exclusion form, consumed entirely.
  pair=re.fullmatch(r'(?:return|output) (?:the )?input (?:value|values|element|elements), not (?:the |their )?indices',clause,re.I|re.ASCII)
  if pair:
   for polarity,value in [('positive','value'),('negative','index')]:matches.append(dict(facet='returned_entity',value=value,field='query',start=start,end=end,span=clause,text_sha256=old.sha(text.encode()),rule='complete-input-value-not-index',polarity=polarity,admissible=True))
  if matches:items+=matches
  elif clause:unknown.append(dict(start=start,end=end,span=clause,reason='clause_not_completely_parsed'))
 if unknown:
  # An unknown clause may govern any other clause across delimiters.
  tentative['evidence'] += [dict(e,admissible=False)for e in items]
  items=[]
 vals={};excluded={}
 for e in items:(vals if e['polarity']=='positive'else excluded).setdefault(e['facet'],set()).add(e['value'])
 conflicts=sorted(k for k,v in vals.items()if len(v)>1 or v&excluded.get(k,set()))
 return dict(facts={k:next(iter(v))for k,v in vals.items()if len(v)==1 and k not in conflicts},excluded_values={k:sorted(v)for k,v in excluded.items()},conflicts=conflicts,evidence=items,tentative_evidence=[dict(x,admissible=False)for x in tentative['evidence']],unsupported_spans=unknown,grammar_complete=bool(items)and not unknown and not conflicts,query_sha256=old.sha(text.encode()),semantic_proof=False)

def contract_facts(doc):
 if doc.get('authority',{}).get('knowledge_class')=='title-only':return dict(facts={},conflicts=[],evidence=[])
 c=old.contract_facts(doc);text=doc['text'];extra=[]
 for m in re.finditer(r'^Result: (.+)$',text,re.M):
  result=json.loads(m.group(1))
  if isinstance(result,dict)and type(result.get('length'))is int:extra.append(item(text,m,'output_cardinality',str(result['length']),'structured-result-length',field='Result'))
 for pattern,facet,value in [(r'Duplicate value first, missing value second\.','result_order','duplicate-then-missing'),(r'Maximum length of a contiguous strictly increasing run; singleton runs have length one\.','input_contiguity','contiguous'),(r'Maximum length of a contiguous strictly increasing run; singleton runs have length one\.','output_measure','count')]:
  for m in re.finditer(pattern,text):extra.append(item(text,m,facet,value,'explicit-authority-objective',field='Objective/Result'))
 scope=doc.get('authority',{}).get('scope','')
 for pattern,facet,value in [(r'Inputs preserved; no mutable input/result aliases\.','input_mutation','forbidden'),(r'Inputs preserved; no mutable input/result aliases\.','output_alias','fresh'),(r'832 mutates supplied image and returns same root','input_mutation','required'),(r'832 mutates supplied image and returns same root','output_alias','input')]:
  if pattern.startswith('832 ') and doc.get('problem_id')!='leetcode:832':continue
  for m in re.finditer(pattern,scope):extra.append(item(scope,m,facet,value,'reviewed-local-effects',field='authority.scope'))
 for e in extra:
  k=e['facet'];v=e['value']
  if k in c['facts']and c['facts'][k]!=v:c['conflicts'].append(k);c['facts'].pop(k)
  elif k not in c['conflicts']:c['facts'][k]=v
 c['evidence']+=extra;return c

def compare(q,c):
 report=old.compare(q,c);facets=report['facets']
 for k in FACETS:
  if k in q['conflicts']or k in c['conflicts']:facets[k]=Facet.UNKNOWN.value;continue
  cv=c['facts'].get(k);qv=q['facts'].get(k)
  if cv is not None and cv in q.get('excluded_values',{}).get(k,[]):facets[k]=Facet.VIOLATED.value
  elif k not in old.FACETS:facets[k]=(Facet.UNKNOWN if cv is None or qv is None else Facet.SATISFIED if cv==qv else Facet.VIOLATED).value
 report['contradictions']=[k for k,v in facets.items()if v==Facet.VIOLATED.value];report['overall']=(Facet.VIOLATED if report['contradictions']else Facet.UNKNOWN if Facet.UNKNOWN.value in facets.values()else Facet.SATISFIED).value;return report

def guarded_decide(text,ranked,policy,service,ids,contracts,*,truncated=False):
 if len(ranked)!=len(ids)or {x[0]for x in ranked}!=set(ids)or set(contracts)!=set(ids):raise ValueError('complete unchanged universe required')
 if list(ranked)!=old.rank([x[1]for x in ranked],[x[0]for x in ranked]):raise ValueError('canonical ranking required')
 q=parse_query(text);v=compare(q,contracts[ranked[0][0]])
 if q['conflicts']or v['contradictions']:d=dict(status='abstain',reason='description_facet_conflict',clarification_questions=[])
 else:d=old.decide(ranked,policy,service,truncated=truncated)
 return dict(d,guard=v,query_analysis=q,guard_version=VERSION,recognition_qualified=False,semantic_proof=False)
