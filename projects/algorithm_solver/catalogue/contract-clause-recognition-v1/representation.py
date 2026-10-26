"""Exact field-span representation; no web-offset invention or semantic parser."""
import hashlib,json
from pathlib import Path
from projects.algorithm_solver.catalogue.public_batch_adapter import bounded_regular_read
ROLES=frozenset(('input_domain','output_identity','output_shape','objective','effects','preconditions'))
def digest(data):return hashlib.sha256(data).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def load_authority(path,expected_sha256,problem_id,authorize_before_open,maximum_bytes=1048576):
 """Caller supplies existing live boundary gate; gate executes BEFORE any payload read."""
 authorize_before_open(problem_id)
 data=bounded_regular_read(path,maximum_bytes=maximum_bytes)
 if digest(data)!=expected_sha256:raise ValueError('authority hash mismatch')
 authority=json.loads(data)
 if authority['problem_id']!=problem_id:raise ValueError('authority identity mismatch')
 return authority,digest(data)
def clauses(authority,authority_sha256):
 """Explicit structured fields + operator-authored spans, not inferred obligations.
 Offsets are Unicode codepoint offsets in the pinned JSON field value, NOT
 original web-page offsets. Required is authority data, never title inference.
 """
 if len(authority_sha256)!=64 or any(c not in '0123456789abcdef' for c in authority_sha256):raise ValueError('authority digest')
 fields=authority['fields'];result={}
 for spec in authority['clauses']:
  role=spec['role'];polarity=spec['polarity'];field=spec['field'];start,end=spec['span'];text=fields[field]
  if role not in ROLES or type(polarity)is not int or polarity not in (-1,1):raise ValueError('typed clause')
  if not isinstance(text,str)or type(start)is not int or type(end)is not int or not 0<=start<end<=len(text):raise ValueError('field span')
  if type(spec['required'])is not bool:raise ValueError('required must be explicit boolean')
  row=dict(problem_id=authority['problem_id'],authority_sha256=authority_sha256,field=field,field_sha256=digest(text.encode()),span=[start,end],text=text[start:end],role=role,polarity=polarity,required=spec['required'])
  # Exact identity only: no claim that paraphrases/correlated clauses deduplicate.
  row['clause_id']=digest(canonical(row));result[row['clause_id']]=row
 return [result[k]for k in sorted(result)]
