"""Incremental exact clause-vector cache; no model construction or decisions."""
import hashlib,json,math,os,struct
from pathlib import Path
from projects.algorithm_solver.catalogue.public_batch_adapter import bounded_regular_read

def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def save(path,value):
 temp=path.with_suffix('.tmp')
 with temp.open('xb')as f:f.write(canonical(value));f.flush();os.fsync(f.fileno())
 os.replace(temp,path)
def validate_vectors(rows,inputs,encoder_sha,prompt_sha,dimension):
 if len(rows)!=len(inputs):raise ValueError('cache row count')
 for row,source in zip(rows,inputs):
  for key,value in source.items():
   if key!='text'and(key not in row or row[key]!=value):raise ValueError('cache full input/provenance binding')
  if 'text'in row and row['text']!=source['text']:raise ValueError('cache text mismatch')
  if sha(source['text'].encode())!=source['text_sha256']:raise ValueError('current input text digest')
  if row['encoder_sha256']!=encoder_sha or row['prompt_sha256']!=prompt_sha or row['embedding_dimension']!=dimension or row['score_units']!='raw_cosine_-1_to_1':raise ValueError('cache encoder/units')
  v=row['vector']
  if len(v)!=dimension or any(type(x)not in(int,float)or not math.isfinite(x)for x in v)or abs(math.sqrt(math.fsum(x*x for x in v))-1)>1e-3:raise ValueError('cache vector')
  if sha(struct.pack('<'+str(dimension)+'d',*v))!=row['vector_sha256']:raise ValueError('cache vector hash')

def cached_clauses(inputs,encoder,output,identity,authorize_chunk,resume=False):
 """identity includes encoder_sha256,prompt_sha256,dimension,revision_sha256.
 Exact completed chunks only are resumable. Unrecorded/orphan chunks fail closed.
 Callback reruns authority gates before each input chunk's encoding/cache read.
 """
 out=Path(output);job=dict(identity=identity,input_records_sha256=sha(canonical(inputs)),count=len(inputs),chunk_size=4);job_sha=sha(canonical(job));progress=out/'progress.json'
 if resume:
  state=json.loads(bounded_regular_read(str(progress)))
  if state['job']!=job or state['job_sha256']!=job_sha:raise ValueError('cache identity drift')
 else:
  out.mkdir(exist_ok=False);state=dict(job=job,job_sha256=job_sha,completed=[]);save(progress,state)
 result=[]
 try:
  for offset in range(0,len(inputs),4):
   batch=inputs[offset:offset+4];authorize_chunk(batch);number=offset//4;path=out/f'{number:04d}.json'
   if number<len(state['completed']):
    raw=bounded_regular_read(str(path));receipt=state['completed'][number]
    if sha(raw)!=receipt['sha256']or receipt['chunk']!=number:raise ValueError('cache chunk tamper')
    chunk=json.loads(raw)
    if chunk['job_sha256']!=job_sha or chunk['chunk']!=number:raise ValueError('cache chunk identity')
    rows=chunk['vectors']
   else:
    if path.exists():raise ValueError('unrecorded chunk; owner review required')
    rows=encoder.encode_records(batch,False)
    # Cache has vectors + input/provenance digests, never authority text.
    rows=[{k:v for k,v in r.items()if k!='text'}for r in rows]
    validate_vectors(rows,batch,identity['encoder_sha256'],identity['prompt_sha256'],identity['dimension'])
    chunk=dict(job_sha256=job_sha,chunk=number,vectors=rows);save(path,chunk);state['completed'].append(dict(chunk=number,sha256=sha(canonical(chunk))));save(progress,state)
   validate_vectors(rows,batch,identity['encoder_sha256'],identity['prompt_sha256'],identity['dimension']);result.extend(rows)
  if len(state['completed'])!=(len(inputs)+3)//4:raise ValueError('cache extra chunks')
  return result,job_sha
 except BaseException as exc:
  # Separate failure evidence; completed receipts remain available for exact resume.
  failure=out/('failure-'+str(len(state['completed']))+'.json')
  if not failure.exists():save(failure,dict(error_type=type(exc).__name__,job_sha256=job_sha,completed_chunks=len(state['completed'])))
  raise
