"""Synthetic-only span adapter. No model, cohort, retrieval, or decisions."""
import hashlib,json,math,re
ROLES=('input_domain','output_identity','output_shape','objective','effects','preconditions')
# Finite complete-clause recognizers; no generic substring harvesting.
RULES=(
 (r'return an input index','output_identity','input_index',1),
 (r'return the input elements','output_identity','input_element',1),
 (r'return an integer','output_shape','scalar_integer',1),
 (r'return all paths','output_shape','path_collection',1),
 (r'modify the input','effects','input_mutation',1),
 (r'do not modify the input','effects','input_mutation',-1),
 (r'the input is a directed graph','input_domain','directed_graph',1),
 (r'the input is an undirected graph','input_domain','directed_graph',-1),
)
def sha(data):return hashlib.sha256(data).hexdigest()
def normalized_cosine(value):
 """Explicit affine compatibility mapping, NOT probability or entailment.
 Orthogonal cosine0 maps .5. No clipping or silently accepting invalid scores.
 """
 if type(value)not in (float,int)or not math.isfinite(value)or not -1<=value<=1:raise ValueError('finite cosine in[-1,1] required')
 return (value+1)/2

def query(text):
 if not isinstance(text,str)or not text.strip()or len(text.encode())>32768:raise ValueError('nonempty bounded request text required')
 h=sha(text.encode());pieces=[]
 # Preserve exact original text offsets; no normalized-text offset projection.
 for m in re.finditer(r'[^.!?;\n]+(?:[.!?;\n]|$)|[.!?;\n]',text):
  start,end=m.span();body=text[start:end];left=len(body)-len(body.lstrip());right=len(body.rstrip());start+=left;end=start+right-left
  if start>=end:continue
  raw=text[start:end];content=raw[:-1]if raw[-1:]in '.!?;\n'else raw
  hits=[(role,predicate,sign)for pattern,role,predicate,sign in RULES if re.fullmatch(pattern,content.strip(),re.IGNORECASE)]
  # Question/semicolon boundaries never establish assertion scope.
  if raw[-1:]in '?;':hits=[]
  pieces.append((start,end,hits))
 closed=bool(pieces)and all(len(hits)==1 for _,_,hits in pieces)
 signs={}
 for _,_,hits in pieces:
  for role,predicate,sign in hits:signs.setdefault((role,predicate),set()).add(sign)
 conflict=any(len(values)>1 for values in signs.values())
 closed=closed and not conflict
 rows=[]
 for start,end,hits in pieces:
  exact=text[start:end];key=sha(json.dumps([h,start,end],separators=(',',':')).encode());r=dict(evidence_id=key,request_sha256=h,span=[start,end],text=exact,text_sha256=sha(exact.encode()),offset_unit='Unicode codepoints in exact original request',track='grounded_grammar'if closed else'tentative',scope='explicit'if closed else'UNKNOWN',polarity=hits[0][2]if closed else None,role=hits[0][0]if closed else None,predicate=hits[0][1]if closed else None)
  # All prose retained as tentative evidence; finite grammar admission is NOT
  # prerequisite for a future explicitly empirical interpretation mode.
  if not closed:r['role_hypotheses']=list(ROLES)
  rows.append(r)
 return dict(request_sha256=h,document_closed_grammar=closed,evidence=rows,unknown_scope=not closed,conflicting_predicates=conflict,recognition_decision=None)

def unique(rows,key):
 out={}
 for row in rows:
  identity=row[key]
  if identity in out and out[identity]!=row:raise ValueError('conflicting provenance identity')
  out[identity]=row
 return dict(sorted(out.items()))

def contract(clause_rows,purposes=None):
 """Preserve pinned clause provenance. Purpose is explicit external annotation,
 never inferred from required=True, title, or a role like preconditions.
 """
 purposes={}if purposes is None else purposes
 clause_rows=list(unique(clause_rows,'clause_id').values())
 ids={c['clause_id']for c in clause_rows}
 if set(purposes)-ids:raise ValueError('purpose refers to absent clause')
 out=[]
 for c in sorted(clause_rows,key=lambda c:c['clause_id']):
  purpose=purposes.get(c['clause_id'],'UNKNOWN')
  if purpose not in ('task_identifying','carried_domain_or_api','UNKNOWN'):raise ValueError('explicit purpose category')
  required_keys={'authority_sha256','field','field_sha256','span','text','problem_id','role','polarity','required','clause_id'}
  if not required_keys<=set(c):raise ValueError('missing exact authority provenance')
  out.append(dict(c,obligation_purpose=purpose,request_repetition_required=False))
 return out

def compatibility_observations(query_result,clause_rows,cosines):
 """Two separate tracks; tentative evidence is never relabeled explicit.
 Pairwise scores cover supplied observations only; missing pairs remain UNKNOWN.
 No role inference, polarity inference, elimination, aggregation or acceptance.
 """
 qs=unique(query_result['evidence'],'evidence_id');cs=unique(clause_rows,'clause_id');out=[]
 for (qid,cid),cosine in sorted(cosines.items()):
  if qid not in qs or cid not in cs:raise ValueError('unbound evidence pair')
  q=qs[qid];c=cs[cid]
  out.append(dict(query_evidence_id=qid,clause_id=cid,track=q['track'],query_span=q['span'],request_sha256=q['request_sha256'],authority_sha256=c['authority_sha256'],authority_field=c['field'],authority_span=c['span'],cosine=cosine,normalized_compatibility=normalized_cosine(cosine),query_polarity=q['polarity'],query_scope=q['scope'],contract_polarity=c['polarity'],semantic_entailment='UNKNOWN'))
 return out
