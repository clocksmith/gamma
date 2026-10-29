"""Pinned external encoder protocol and exact reusable binary-vector storage.

No encoder runs without an explicit operator-supplied command/hash/model contract.
No model download, query-time document embedding, or cross-purpose retrieval occurs.
"""
import hashlib,json,math,os
from pathlib import Path
import struct,subprocess

REQUIRED=('schema','command','commandFile','commandFileSha256','encoderIdentity','recipe','dimensions')
IDENTITY=('modelId','modelRevision','modelManifestSha256','tokenizerManifestSha256','adapterSha256','runtimeManifestSha256','pooling','normalization','dtype','documentInstruction','queryInstruction','maxTokens','truncation')

def raw(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(data):return hashlib.sha256(data).hexdigest()
def file_ref(path,relative=None):
 data=Path(path).read_bytes();return {'path':relative or str(path),'sha256':sha(data),'bytes':len(data),'mediaType':'application/json' if Path(path).suffix=='.json' else 'application/octet-stream'}
def checked_ref(root,ref):
 path=(Path(root)/ref['path']).resolve();root=Path(root).resolve()
 if root not in path.parents:raise ValueError('Vector file escapes index root')
 data=path.read_bytes()
 if len(data)!=ref['bytes'] or sha(data)!=ref['sha256']:raise ValueError('Vector integrity mismatch')
 return data

def build(destination,rows,contract_path=None,baseline_path=None):
 destination=Path(destination);out=destination/'generated/embeddings';out.mkdir(parents=True,exist_ok=True)
 plan={'schema':'study.embedding-plan.v1','inputs':len(rows),'purposes':{k:sum(r['purpose']==k for r in rows) for k in ('problem-discovery','solution-study','artifact-search')},'status':'blocked-missing-encoder-identity','reason':'Supply a pinned existing encoder contract; no weights are downloaded or old execution provenance invented.','newVectors':0,'reusedVectors':0}
 if contract_path is None:
  (out/'plan.json').write_bytes(raw(plan));return plan
 contract=json.loads(Path(contract_path).read_bytes())
 if set(REQUIRED)-set(contract) or contract['schema']!='study.encoder-contract.v1':raise ValueError('Incomplete encoder contract')
 from jsonschema import Draft202012Validator
 from schema import SCHEMA
 Draft202012Validator({**SCHEMA,'oneOf':[{'$ref':'#/$defs/EncoderContract'}]}).validate(contract)
 identity=contract['encoderIdentity']
 if set(identity)!=set(IDENTITY):raise ValueError('Exact complete encoder execution identity required')
 for key in IDENTITY:
  if key.endswith('Sha256') and (not isinstance(identity[key],str) or len(identity[key])!=64 or any(c not in '0123456789abcdef' for c in identity[key])):raise ValueError('Missing encoder hash: '+key)
 if contract['recipe']!={'chunker':'codepoint-window-v1','maxCharacters':1200,'overlapCharacters':100}:raise ValueError('Recipe does not match migrated text chunking')
 dimensions=contract['dimensions']
 if not isinstance(dimensions,int) or isinstance(dimensions,bool) or not 1<=dimensions<=65536:raise ValueError('Invalid vector dimension')
 fingerprint=sha(raw({'identity':identity,'recipe':contract['recipe'],'dimensions':dimensions,'encoderProgramSha256':contract['commandFileSha256']}))
 cache={}
 if baseline_path:
  baseline=json.loads(Path(baseline_path).read_bytes())
  if baseline.get('schema')!='study.embedding-release.v1':raise ValueError('Unsupported baseline index')
  for manifest_ref in baseline['indexes']:
   blob=checked_ref(Path(baseline_path).parent,manifest_ref);index=json.loads(blob)
   vectors=checked_ref(Path(baseline_path).parent,index['vectors'])
   declared=sha(raw({'identity':index['encoderIdentity'],'recipe':index['recipe'],'dimensions':index['dimensions'],'encoderProgramSha256':index['encoderProgramSha256']}))
   if index['encoderFingerprint']!=declared:raise ValueError('Baseline encoder identity is inconsistent')
   if index['encoderFingerprint']!=fingerprint:continue
   if index['encoding']!='float32-le' or index['dimensions']!=dimensions or len(vectors)!=len(index['entries'])*dimensions*4:raise ValueError('Malformed vector layout')
   if sorted(e['vectorRow'] for e in index['entries'])!=list(range(len(index['entries']))):raise ValueError('Duplicate or missing vector rows')
   for entry in index['entries']:
    row=entry['vectorRow']
    if not isinstance(row,int) or not 0<=row<len(index['entries']):raise ValueError('Vector row outside index')
    vector=vectors[row*dimensions*4:(row+1)*dimensions*4]
    if not all(math.isfinite(v) for v in struct.unpack('<'+'f'*dimensions,vector)):raise ValueError('Nonfinite baseline vector')
    cache[index['purpose'],entry['textSha256']]=vector
 for r in rows:
  if sha(r['text'].encode())!=r['textSha256']:raise ValueError('Embedding text hash mismatch')
 needed={(r['purpose'],r['textSha256']):r for r in rows if (r['purpose'],r['textSha256']) not in cache}
 if needed:
  command_file=Path(contract['commandFile']).resolve()
  if sha(command_file.read_bytes())!=contract['commandFileSha256']:raise ValueError('Pinned encoder program changed')
  command=contract['command']
  if not isinstance(command,list) or not command or not all(isinstance(x,str) for x in command):raise ValueError('Explicit encoder argv required')
  # The pinned file must actually be one of the command arguments/executable.
  if not any(Path(x).is_absolute() and Path(x).resolve()==command_file for x in command):raise ValueError('Pinned encoder file is not in argv')
  batch=list(needed.values());request={'schema':'study.embedding-request.v1','encoderIdentity':identity,'dimensions':dimensions,'inputs':[{'id':r['id'],'purpose':r['purpose'],'text':r['text'],'textSha256':r['textSha256']} for r in batch]}
  process=subprocess.run(command,input=raw(request),capture_output=True,timeout=120)
  if process.returncode:raise ValueError('Encoder failed: '+process.stderr.decode(errors='replace')[-700:])
  if len(process.stdout)>256*1024**2:raise ValueError('Encoder output exceeds bound')
  response=json.loads(process.stdout)
  if response.get('encoderIdentity')!=identity:raise ValueError('Encoder did not attest the pinned execution identity')
  by_id={x['id']:x for x in response.get('vectors',[])}
  if len(response.get('vectors',[]))!=len(batch) or len(by_id)!=len(batch) or set(by_id)!={r['id'] for r in batch}:raise ValueError('Missing/duplicate/extra encoded input')
  for r in batch:
   item=by_id[r['id']];vector=item['values']
   if item.get('textSha256')!=r['textSha256'] or len(vector)!=dimensions or not all(type(v) in (int,float) and math.isfinite(v) for v in vector):raise ValueError('Invalid encoded vector')
   if identity['normalization']=='l2' and not math.isclose(sum(v*v for v in vector),1.0,rel_tol=1e-4,abs_tol=1e-4):raise ValueError('Encoder returned an unnormalized vector')
   packed=struct.pack('<'+'f'*dimensions,*vector)
   if not all(math.isfinite(v) for v in struct.unpack('<'+'f'*dimensions,packed)):raise ValueError('Vector overflows float32')
   cache[r['purpose'],r['textSha256']]=packed
 indexes=[];reused=sum((r['purpose'],r['textSha256']) not in needed for r in rows)
 for purpose in ('problem-discovery','solution-study','artifact-search'):
  selected=[r for r in rows if r['purpose']==purpose];entries=[];vectors=bytearray()
  for row,r in enumerate(selected):
   vectors.extend(cache[purpose,r['textSha256']]);entries.append({k:v for k,v in r.items() if k!='text'});entries[-1]['vectorRow']=row
  vector_file=out/(purpose+'.f32');vector_file.write_bytes(vectors)
  index={'schema':'study.embedding-index.v1','purpose':purpose,'encoderFingerprint':fingerprint,'encoderProgramSha256':contract['commandFileSha256'],'encoderIdentity':identity,'recipe':contract['recipe'],'dimensions':dimensions,'encoding':'float32-le','distance':'cosine' if identity['normalization']=='l2' else 'dot-product','entries':entries,'vectors':file_ref(vector_file,vector_file.name),'access':'private-migration-output; source publication permissions remain separate'}
  path=out/(purpose+'.json');path.write_bytes(raw(index));indexes.append(file_ref(path,path.name))
 release={'schema':'study.embedding-release.v1','indexes':indexes};(out/'release.json').write_bytes(raw(release));plan.update(status='built',reason='Exact vectors built/reused with pinned encoder identity',newVectors=len(needed),reusedVectors=reused,release='generated/embeddings/release.json');(out/'plan.json').write_bytes(raw(plan));return plan
