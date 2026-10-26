"""Injected existing CPU encoder interface; never constructs/loads a model here."""
import hashlib,json,math,struct
from projects.algorithm_solver.catalogue.cpu_encoder import QUERY_INSTRUCTION
DIMENSION=1024
PROMPT={'schema':'gamma.contract-clause-prompts.v1','query_instruction':QUERY_INSTRUCTION,'query_and_span_text':'Exact original text; existing encoder query=True','clause_template':'Role: {role}\nContract clause: {text}','clause_query_flag':False,'dimension':DIMENSION,'score_units':'raw_cosine_-1_to_1'}
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
PROMPT_SHA256=sha(canonical(PROMPT))
def clause_inputs(clauses):
 out=[];seen={}
 for c in sorted(clauses,key=lambda c:c['clause_id']):
  cid=c['clause_id']
  if cid in seen:
   if seen[cid]!=c:raise ValueError('clause provenance collision')
   continue
  seen[cid]=c;text=PROMPT['clause_template'].format(role=c['role'],text=c['text']);out.append(dict(record_id=cid,text=text,text_sha256=sha(text.encode()),authority_sha256=c['authority_sha256'],field=c['field'],field_sha256=c['field_sha256'],span=c['span'],prompt_sha256=PROMPT_SHA256,query=False))
 return out
class BoundEncoder:
 def __init__(self,encoder,expected_identity,expected_prompt_sha256):
  if expected_prompt_sha256!=PROMPT_SHA256:raise ValueError('prompt mismatch')
  names=('encoder_manifest_sha256','cpu_manifest_sha256','native_python_sha256')
  if set(expected_identity)!=set(names)or any(getattr(encoder,k,None)!=expected_identity[k]for k in names):raise ValueError('existing encoder identity mismatch')
  self.encoder=encoder;self.identity=dict(expected_identity);self.encoder_sha256=sha(canonical(self.identity));self.calls=0
 def encode_records(self,records,query):
  if type(query)is not bool or len(records)>64:raise ValueError('bounded explicit encoder mode')
  ids=set()
  for r in records:
   if r['record_id']in ids or r['text_sha256']!=sha(r['text'].encode())or r['query']is not query or r['prompt_sha256']!=PROMPT_SHA256:raise ValueError('record/prompt identity')
   ids.add(r['record_id'])
  self.calls+=1;vectors=self.encoder.encode([r['text']for r in records],query=query);info=self.encoder.last_request_info
  if not isinstance(info,dict)or info.get('rows')!=len(records)or info.get('query')is not query or len(info.get('truncated',[]))!=len(records)or any(type(x)is not bool for x in info['truncated']):raise ValueError('encoder request metadata')
  if any(info['truncated']):raise ValueError('truncated input; no partial semantic vectors admitted')
  if hasattr(vectors,'tolist'):vectors=vectors.tolist()
  if len(vectors)!=len(records):raise ValueError('vector row count')
  out=[]
  for r,vector in zip(records,vectors):
   if len(vector)!=DIMENSION or any(type(x)not in (int,float)or not math.isfinite(x)for x in vector):raise ValueError('vector dimensions/finite values')
   norm=math.sqrt(math.fsum(x*x for x in vector))
   if abs(norm-1)>1e-3:raise ValueError('expected normalized existing encoder vectors')
   out.append(dict(r,vector=list(vector),vector_sha256=sha(struct.pack('<'+str(DIMENSION)+'d',*vector)),encoder_sha256=self.encoder_sha256,embedding_dimension=DIMENSION,score_units='raw_cosine_-1_to_1'))
  return out
 def request(self,text,span_records,expected_request_sha256):
  if not isinstance(text,str)or not text.strip()or sha(text.encode())!=expected_request_sha256:raise ValueError('exact request mismatch')
  records=[dict(record_id='whole-request:'+expected_request_sha256,text=text,text_sha256=expected_request_sha256,request_sha256=expected_request_sha256,prompt_sha256=PROMPT_SHA256,query=True,span=[0,len(text)])]
  for s in span_records:
   start,end=s['span']
   if s['request_sha256']!=expected_request_sha256 or type(start)is not int or type(end)is not int or not 0<=start<end<=len(text)or s['text']!=text[start:end]or s['text_sha256']!=sha(s['text'].encode()):raise ValueError('span/request provenance mismatch')
   records.append(dict(record_id=s['evidence_id'],text=s['text'],text_sha256=s['text_sha256'],request_sha256=expected_request_sha256,prompt_sha256=PROMPT_SHA256,query=True,span=s['span']))
  return self.encode_records(records,True)
