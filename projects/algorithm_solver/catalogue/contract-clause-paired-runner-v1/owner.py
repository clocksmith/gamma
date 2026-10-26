"""Pinned owner construction; no cohort imports. Encoder remains lazy."""
import hashlib,importlib.util,json
from pathlib import Path
from projects.algorithm_solver.catalogue.public_batch_adapter import bounded_regular_read
HERE=Path(__file__).resolve().parent;BASE=HERE.parent

def sha(b):return hashlib.sha256(b).hexdigest()
def pinned(spec):
 b=bounded_regular_read(spec['path'],maximum_bytes=8*1024**2)
 if sha(b)!=spec['sha256']:raise ValueError('artifact pin drift')
 return json.loads(b)
def module(name,path):
 spec=importlib.util.spec_from_file_location('_paired_owner_'+name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def verified(spec):
 f=pinned(spec)
 for base,key in ((HERE,'files'),(BASE,'dependency_code_sha256')):
  for name,h in f[key].items():
   if Path(name).is_absolute()or '..'in Path(name).parts:raise ValueError('unsafe frozen code path')
   if sha(bounded_regular_read(str(base/name)))!=h:raise ValueError('frozen code drift')
 return f

def index_scores(index,vector,np,population):
 scores=index.scores(np.asarray([vector],dtype=np.float32))
 if scores.shape!=(population,):raise ValueError('index score shape')
 return scores.tolist() # exact stable-ID order, native Python floats for API

def build(f):
 from projects.algorithm_solver.catalogue.boundary_policy import authorize_before_open
 from projects.algorithm_solver.catalogue.known_spec_service import KnownSpecService
 from projects.algorithm_solver.catalogue.cpu_encoder import PinnedCPUEncoder
 original=pinned(f['integrated_freeze']);ir=module('original_runtime',BASE/'integrated-recognition-policy-v1/runtime.py');state=ir.prepare_state(original);ef=pinned(original['encoder_freeze'])
 state['service']=KnownSpecService.from_config(f['matched_service']['path'],f['matched_service']['sha256'])
 if set(state['service']._universe['eligible_problem_ids'])!=set(state['ids']):raise ValueError('v25 universe drift')
 selection=pinned(f['packet_selection']);gate=pinned(dict(path=selection['gate_config_path'],sha256=selection['gate_config_sha256']))
 def authorize(pid,lang='javascript'):return authorize_before_open(pid,gate['artifact_paths'],gate['trusted_hashes'],language=lang,payload_kind='statement')
 for pid in selection['selected_problem_ids']:authorize(pid)
 prepared=pinned(f['prepared_clauses'])
 if prepared['revision']['stable_ids']!=state['ids']or prepared['revision']['unchanged102_documents_sha256']!=ef['new_documents']['sha256']:raise ValueError('unchanged index/document binding')
 binding=module('encoder_binding',BASE/'contract-clause-encoder-adapter-v1/encoder_binding.py');inputs=binding.clause_inputs(prepared['clauses'])
 if len(inputs)!=104:raise ValueError('exact104clause inputs required')
 if inputs!=prepared['encoder_inputs']or prepared['prompt_sha256']!=binding.PROMPT_SHA256:raise ValueError('clause prompt/input drift')
 cpu=PinnedCPUEncoder(ef['model_root'],encoder_manifest=ef['encoder_manifest']['path'],encoder_manifest_sha256=ef['encoder_manifest']['sha256'],cpu_manifest=ef['cpu_manifest']['path'],cpu_manifest_sha256=ef['cpu_manifest']['sha256'],native_python_sha256=ef['encoder_cache_identity']['native_python_sha256'],threads=2,batch_size=4)
 expected=dict(encoder_manifest_sha256=ef['encoder_manifest']['sha256'],cpu_manifest_sha256=ef['cpu_manifest']['sha256'],native_python_sha256=ef['encoder_cache_identity']['native_python_sha256']);encoder=binding.BoundEncoder(cpu,expected,binding.PROMPT_SHA256);cache=module('clause_cache',BASE/'contract-clause-paired-development-v1/cache.py')
 identity=dict(encoder_sha256=encoder.encoder_sha256,prompt_sha256=binding.PROMPT_SHA256,dimension=1024,revision_sha256=prepared['revision_sha256'])
 byid={c['clause_id']:c for c in prepared['clauses']}
 def chunk_gate(batch):
  for pid in sorted({byid[r['record_id']]['problem_id']for r in batch}):authorize(pid)
 def predictor(vectors):
  import numpy as np
  engine=module('engine',HERE/'engine.py');policies=pinned(f['policies'])['policy_family']
  def baseline(text,raw):return state['reranker'].rerank(raw,state['ids'],state['contracts'],state['guard'].parse_query(text),state['guard'])
  def semantic(text,decision):
   pid=decision.get('problem_id');decision,_=state['choice'].apply(text,decision,state['required'].get(pid,{}));decision,_=state['output'].apply(text,decision,state['kinds'].get(pid,dict(kind=None,evidence=[],status='UNKNOWN')));decision,_=state['axis'].apply(text,decision,state['axis_obligation']);return decision
  return engine.Predictor(encoder=encoder,stable_ids=state['ids'],index_scores=lambda v:index_scores(state['index'],v,np,len(state['ids'])),baseline_ranker=baseline,clauses=prepared['clauses'],clause_vectors=vectors,bindings=dict(encoder_sha256=encoder.encoder_sha256,prompt_sha256=binding.PROMPT_SHA256,embedding_dimension=1024,score_units='raw_cosine_-1_to_1'),policies=policies,service=state['service'],decide_hybrid=state['reranker'].decide_hybrid,semantic_chain=semantic,normative=ir.normative,authorize_statement=authorize)
 return dict(encoder=encoder,inputs=inputs,cache=cache,cache_identity=identity,chunk_gate=chunk_gate,predictor=predictor,policy_family=pinned(f['policies'])['policy_family'])
