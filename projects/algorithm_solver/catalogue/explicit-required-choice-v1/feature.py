"""Empirical abstention on explicit unresolved contract-required choices.
Not a normative interpretation gate; absent extraction always stays UNKNOWN.
"""
import hashlib,json,re
VERSION='gamma.explicit-required-choice.v1'
def sha(text):return hashlib.sha256(text.encode()).hexdigest()
def span(text,start,end,rule,field='query'):return dict(start=start,end=end,span=text[start:end],text_sha256=sha(text),rule=rule,field=field)

# Exact reviewed objective adapters: no title or ID inference.
OBJECTIVES={
 'Maximum length of a contiguous strictly increasing run; singleton runs have length one.':{'adjacency':'contiguous'},
 'Match each source at its index in original s. Replace matching spans by corresponding targets simultaneously; leave nonmatches unchanged.':{'replacement_coordinate_frame':'original'},
 'Minimum full-height path sum starting anywhere in the first row; each next row changes column by -1, 0 or 1 within bounds.':{'between_row_moves':'next-row-column-delta-at-most-one'},
 'Lexicographically minimum leaf-to-root letter sequence; when one sequence prefixes another, the shorter sequence is smaller.':{'tree_reading_direction':'toward-root','tree_path_endpoints':'leaf-to-root'},
 'Maximum resulting sum after exactly k sign inversions, each choosing any index; an index may be chosen repeatedly.':{'operation_count':'exactly-k','index_reuse':'allowed'},
}
def obligations(doc):
 if doc.get('authority',{}).get('knowledge_class')!='reviewed-normative-contract':return {}
 out={};text=doc['text']
 for m in re.finditer(r'^(Objective|Input domain): (.+)$',text,re.M):
  value=json.loads(m.group(2));found={}
  if m.group(1)=='Objective'and isinstance(value,str):found=OBJECTIVES.get(value,{})
  if m.group(1)=='Input domain'and isinstance(value,dict)and value.get('shape')=='n by n':found={'matrix_shape':'square'}
  for facet,v in found.items():out[facet]=dict(value=v,evidence=span(text,m.start(2),m.end(2),'reviewed-obligation',m.group(1)),authority_sha256=doc['authority'].get('authority_sha256'))
 return out

UNRESOLVED=(
 r'(?:I|we) have not (?:yet )?(?:specified|defined|decided|said) (?P<body>.+)',
 r'(?P<body>.+) (?:is|are) (?:unspecified|undefined|undecided)',
 r'(?P<body>.+) (?:has|have) not (?:yet )?been (?:specified|defined|decided)',
)
# Full typed uncertainty bodies; unexplained modifiers are not harvested.
BODY_RULES=(
 (r'whether (?:(?:selected )?(?:elements|positions) (?:must be|are) )?(?:adjacent|contiguous) (?:or|versus) (?:may )?(?:skip positions|skip elements|(?:be )?gapped|contiguous|adjacent)', 'adjacency', {'contiguous':r'\b(?:adjacent|contiguous)\b','gapped':r'\b(?:skip positions|skip elements|gapped)\b'}),
 (r'whether (?:offsets|indices) (?:refer to|use) (?:the )?(?:initial|original) (?:text|string) or (?:are updated after each replacement|(?:the )?(?:updated|current|modified) (?:text|string))','replacement_coordinate_frame',{'original':r'\b(?:initial|original)\b','evolving':r'\b(?:updated|current|modified)\b'}),
 (r'whether to read (?:from|toward|towards) (?:the )?root or (?:from|toward|towards) (?:the )?root','tree_reading_direction',{'from-root':r'\bfrom\b','toward-root':r'\b(?:toward|towards)\b'}),
 (r'(?:whether )?(?:exactly|precisely|at most) k(?: operations)? (?:versus|or|vs) (?:exactly|precisely|at most) k(?: operations)?','operation_count',{'exactly-k':r'\b(?:exactly|precisely) k\b','at-most-k':r'\bat most k\b'}),
)
TOPICS={
 'matrix_shape':r'(?:the )?(?:table|grid|matrix) shape',
 'between_row_moves':r'(?:the )?(?:allowed|permitted) moves between rows',
 'tree_path_endpoints':r'which endpoints (?:qualify|are allowed)',
 'index_reuse':r'whether (?:an? )?index (?:may|can) be reused',
}
def typed_body(body):
 pieces=re.split(r',\s*(?:and|or)\s+|\s+and\s+',body.strip().rstrip(','),flags=re.I);found={}
 for piece in pieces:
  piece=piece.strip();recognized=False
  for pattern,facet,values in BODY_RULES:
   if re.fullmatch(pattern,piece,re.I|re.ASCII):
    recognized=True;mentioned=sorted(v for v,p in values.items()if re.search(p,piece,re.I))
    if len(mentioned)>=2:found[facet]=mentioned
  for facet,pattern in TOPICS.items():
   if re.fullmatch(pattern,piece,re.I|re.ASCII):recognized=True;found[facet]=['explicitly-unresolved']
  if not recognized:return {}
 return found

RESOLVED_TOPICS={
 'matrix_shape':r'(?:the )?(?:grid|matrix|table) is (?:square|rectangular)',
 'replacement_coordinate_frame':r'(?:offsets|indices) (?:use|refer to) (?:the )?(?:original|initial|updated|current|modified) (?:text|string)',
 'tree_reading_direction':r'read (?:from|toward|towards) (?:the )?root',
 'tree_path_endpoints':r'only (?:leaf-to-root|root-to-leaf) paths qualify',
 'index_reuse':r'(?:an? )?index (?:may|can|cannot|must not) be reused',
 'operation_count':r'(?:exactly|at most) k operations (?:are required|are allowed)',
 'between_row_moves':r'(?:the )?(?:allowed|permitted) moves between rows change column by (?:at most one|exactly one)',
 'adjacency':r'(?:selected )?(?:positions|elements) (?:must be|are) (?:adjacent|contiguous|gapped)',
}

def explicit_unknowns(text):
 if type(text)is not str or not text.strip()or len(text.encode())>32768:raise ValueError('bounded description required')
 # Conservative context rejection is a false-negative safeguard, not a proof
 # that all other arbitrary-language scope is understood.
 if re.search(r'["“”`?\']|\b(?:if|unless|example|quoted|quotation|ignore|instruction|hypothetical)\b',text,re.I):return dict(choices=[],context_status='UNKNOWN')
 if re.search(r'\b(?:I|we) have (?:now )?(?:specified|defined|decided)\b|\b(?:choose|resolved|however)\b|\bbut (?:now|use|require)\b',text,re.I):return dict(choices=[],context_status='UNKNOWN_RESOLUTION_SCOPE')
 choices=[]
 for sentence in re.finditer(r'[^.;\n]+',text):
  raw=sentence.group();left=len(raw)-len(raw.lstrip());clause=raw.strip();start=sentence.start()+left
  for pattern in UNRESOLVED:
   match=re.fullmatch(pattern,clause,re.I|re.ASCII)
   if not match:continue
   found=typed_body(match.group('body'))
   for facet,values in found.items():choices.append(dict(facet=facet,alternatives=values,evidence=span(text,start,start+len(clause),'explicit-unresolved-declaration')))
 # Direct typed resolutions apply to the same facet, in either sentence order.
 resolved=[]
 for sentence in re.finditer(r'[^.;\n]+',text):
  clause=sentence.group().strip()
  for facet,pattern in RESOLVED_TOPICS.items():
   if re.fullmatch(pattern,clause,re.I|re.ASCII):resolved.append(facet)
 choices=[choice for choice in choices if choice['facet']not in resolved]
 # A separately stated generic resolution conservatively suspends this feature.
 for sentence in re.finditer(r'[^.;\n]+',text):
  clause=sentence.group().strip()
  if any(re.fullmatch(pattern,clause,re.I|re.ASCII)for pattern in UNRESOLVED):continue
  if re.fullmatch(r'use .+|.+ (?:is|are) required|.+ (?:must|shall) .+',clause,re.I|re.ASCII):return dict(choices=[],context_status='UNKNOWN_RESOLUTION_SCOPE')
 return dict(choices=choices,resolved_facets=sorted(set(resolved)),context_status='PARTIAL_EMPIRICAL')

def apply(description,baseline,contract_obligations):
 analysis=explicit_unknowns(description);matches=[]
 for choice in analysis['choices']:
  obligation=contract_obligations.get(choice['facet'])
  if obligation is None:continue
  # Enumerated alternatives matter only if the contract's value is one of them.
  if choice['alternatives']!=['explicitly-unresolved']and obligation['value']not in choice['alternatives']:continue
  matches.append(dict(query=choice,contract=obligation))
 output=dict(baseline)
 if baseline['status']=='accepted'and matches:
  output=dict(status='abstain',reason='explicit_required_choice_unresolved',problem_id=None,clarification_questions=[],semantic_proof=False,mode='empirical-required-choice')
  if 'query_id'in baseline:output['query_id']=baseline['query_id']
 return output,dict(feature_version=VERSION,matches=matches,analysis=analysis,baseline_numeric_diagnostics={k:baseline[k]for k in ('selected_raw_cosine','selected_hybrid_score','adjusted_margin','raw_selected_vs_best_other_margin','raw_global_top_margin')if k in baseline},semantic_proof=False,absence_of_extraction_means='UNKNOWN',scope='Empirical abstention feature, not normative semantic gate')
