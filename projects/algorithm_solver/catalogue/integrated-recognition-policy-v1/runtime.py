"""Label-free persistent description→fresh encoder→4081 rivals→artifact pipeline."""
import hashlib,importlib.util,json,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pinned(s):
 p=Path(s['path']);assert p.is_absolute()and p.stat().st_size<=32*1024**2 and sha(p)==s['sha256'];return json.loads(p.read_text())
def module(name,s):
 assert sha(s['path'])==s['sha256'];sp=importlib.util.spec_from_file_location(name,s['path']);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m

def normative(selections,pid):
 if set(selections)!= {'javascript','python'}:return False
 for language,s in selections.items():
  i=s.get('implementation',{})
  if s.get('status')!='selected'or s.get('problem_id')!=pid or s.get('language')!=language or i.get('status')!='qualified'or i.get('evidence_class')!='normative-typed-effects':return False
  if not isinstance(i.get('contract_scope'),str)or not i['contract_scope']:return False
  for k in ('receipt_sha256','source_sha256','problem_contract_sha256'):
   if not isinstance(i.get(k),str)or len(i[k])!=64 or any(c not in '0123456789abcdef'for c in i[k]):return False
 return True

class Engine:
 def __init__(self,*,encoder,index,ids,service,policy,guard,reranker,choice,output,axis,contracts,required,kinds,axis_obligation,delivery):
  if len(ids)!=4081 or len(set(ids))!=4081 or set(contracts)!=set(ids)or set(required)!=set(ids)or set(kinds)!=set(ids):raise ValueError('full4081 index/authority alignment')
  self.__dict__.update(locals());self.__dict__.pop('self')
 def request(self,text):
  timer=self.delivery.RequestTimer();summary=dict(candidate_executions=0,encoder_invocations=0,clarification_questions=[],recognition_qualified=False);selections=None;decision=None
  try:
   if type(text)is not str or not text.strip()or len(text.encode())>32768:
    response=dict(status='abstain',reason='unsupported_description_input',clarification_questions=[])
   else:
    summary['query_sha256']=hashlib.sha256(text.encode()).hexdigest()
    def encode_once():
     summary['encoder_invocations']+=1
     return self.encoder.encode([text],query=True)
    vector=timer.call('fresh_query_encoding',encode_once);info=self.encoder.last_request_info
    if not isinstance(info,dict)or info.get('query')is not True or info.get('rows')!=1 or len(info.get('truncated',[]))!=1 or type(info['truncated'][0])is not bool:raise ValueError('query encoding/truncation metadata')
    summary['truncated']=info['truncated'][0];summary['token_counts_before_truncation']=info.get('token_counts_before_truncation')
    if info['truncated'][0]:response=dict(status='abstain',reason='truncated_query',clarification_questions=[])
    else:
     parsed=timer.call('tentative_extraction',lambda:self.guard.parse_query(text));ranking=timer.call('full4081_empirical_ranking',lambda:self.reranker.rerank(self.index.scores(vector),self.ids,self.contracts,parsed,self.guard))
     decision=timer.call('raw_cosine_adjusted_margin_and_qualified_metadata',lambda:self.reranker.decide_hybrid(ranking,self.policy,self.service))
     summary.update(population=4081,raw_top_id=ranking['baseline'][0][0],hybrid_top_id=ranking['hybrid'][0][0],selected_raw_cosine=decision['selected_raw_cosine'],adjusted_margin=decision['adjusted_margin'],raw_selected_vs_best_other_margin=decision['raw_selected_vs_best_other_margin'])
     pid=decision.get('problem_id');decision,_=timer.call('required_choice',lambda:self.choice.apply(text,decision,self.required.get(pid,{})))
     decision,_=timer.call('explicit_output_kind',lambda:self.output.apply(text,decision,self.kinds.get(pid,dict(kind=None,evidence=[],status='UNKNOWN'))))
     decision,_=timer.call('explicit944_axis',lambda:self.axis.apply(text,decision,self.axis_obligation))
     if decision['status']=='accepted'and not normative(decision['implementations'],decision['problem_id']):decision=dict(status='abstain',reason='normative_evidence_required')
     summary['decision_status']=decision['status'];summary['decision_problem_id']=decision.get('problem_id');summary['decision_reason']=decision.get('reason')
     if decision['status']!='accepted':response=dict(status='abstain',reason=decision.get('reason'),clarification_questions=[])
     else:
      selections=decision['implementations'];artifacts,metadata=self.delivery.materialize(self.service,decision['problem_id'],selections,timer)
      if artifacts is None:
       response=dict(status='error',error_type='ArtifactUnavailable',reason=metadata.get('reason'),clarification_questions=[]);selections=None
      else:
       summary['artifacts']=metadata;response=dict(status='artifact_returned',problem_id=decision['problem_id'],artifacts=artifacts,clarification_questions=[])
   if 'decision_status'not in summary:summary.update(decision_status='abstain'if response['status']=='abstain'else'error',decision_reason=response.get('reason',response.get('error_type')),decision_problem_id=None)
   wire=timer.call('response_serialization',lambda:self.delivery.encoded(response));summary.update(status=response['status'],reason=response.get('reason'),problem_id=response.get('problem_id'),response_sha256=hashlib.sha256(wire).hexdigest(),response_bytes=len(wire),error_type=response.get('error_type'))
  except (TimeoutError,KeyboardInterrupt,SystemExit):raise
  except Exception as error:
   response=dict(status='error',error_type=type(error).__name__,clarification_questions=[]);summary.update(status='error',error_type=type(error).__name__,failed_stage=timer.active);selections=None
  summary['timing_seconds']=timer.finish()
  # Source-bearing response and selected metadata are private caller outputs.
  # Report writers must serialize only summary, never response/selection payloads.
  return response,summary,selections

def prepare_state(f):
 for name,h in f['code_sha256'].items():assert sha(HERE/name)==h
 for name,h in f['dependency_code_sha256'].items():assert sha(BASE/name)==h
 for s in f['modules'].values():assert sha(s['path'])==s['sha256']
 ef=pinned(f['encoder_freeze']);policy=pinned(f['policy'])['policy'];assert policy=={'id':'c65-m00','min_cosine':.65,'min_margin':0.0}
 import numpy as np
 from projects.algorithm_solver.catalogue.boundary_policy import authorize_before_open
 from projects.algorithm_solver.catalogue.known_spec_service import KnownSpecService
 mods={k:module('integrated_'+k,s)for k,s in f['modules'].items()};cp=pinned(ef['cache_plan']);cache=mods['cache'];index=cache.restore_index(cp['index'],np);parts=[]
 for spec in f['delta_arrays']:
  assert sha(spec['path'])==spec['sha256'];a=np.load(spec['path'],allow_pickle=False);cache.validate_array(a,4,np);parts.append(a)
 delta=np.concatenate(parts);assert delta.shape==(48,1024);index.array[ef['replacement_positions']]=delta;cache.validate_array(index.array,4081,np);ids=cp['index']['stable_ids']
 plan=pinned(ef['new_document_plan']);gate=pinned(plan['boundary_gate'])
 for a in plan['authorities']:authorize_before_open(a['problem_id'],gate['artifact_paths'],gate['trusted_hashes'],language='javascript',payload_kind='statement')
 bundle=pinned(ef['new_documents']);assert bundle['stable_ids']==ids and bundle['plan_sha256']==ef['new_document_plan']['sha256']
 for key in ('authority944','clarification944','correction944'):
  authorize_before_open('leetcode:944',gate['artifact_paths'],gate['trusted_hashes'],language='javascript',payload_kind='statement');value=pinned(f[key])
  if key=='authority944':axis_obligation=mods['axis'].authority_obligation(value,f[key]['sha256'])
 service=KnownSpecService.from_config(ef['matched_service']['path'],ef['matched_service']['sha256']);assert set(service._universe['eligible_problem_ids'])==set(ids)
 docs=bundle['documents'];return dict(index=index,ids=ids,service=service,policy=policy,guard=mods['guard'],reranker=mods['reranker'],choice=mods['choice'],output=mods['output'],axis=mods['axis'],contracts={d['problem_id']:mods['guard'].contract_facts(d)for d in docs},required={d['problem_id']:mods['choice'].obligations(d)for d in docs},kinds={d['problem_id']:mods['output'].contract_kind(d)for d in docs},axis_obligation=axis_obligation,delivery=mods['delivery'])

def build(f):
 ef=pinned(f['encoder_freeze'])
 if Path(sys.executable)!=Path(ef['python'])or sha(Path(sys.executable).resolve())!=ef['encoder_cache_identity']['native_python_sha256']:raise ValueError('pinned native runtime required')
 state=prepare_state(f)
 from projects.algorithm_solver.catalogue.cpu_encoder import PinnedCPUEncoder
 encoder=PinnedCPUEncoder(ef['model_root'],encoder_manifest=ef['encoder_manifest']['path'],encoder_manifest_sha256=ef['encoder_manifest']['sha256'],cpu_manifest=ef['cpu_manifest']['path'],cpu_manifest_sha256=ef['cpu_manifest']['sha256'],native_python_sha256=ef['encoder_cache_identity']['native_python_sha256'],threads=2,batch_size=4);encoder._load()
 return Engine(encoder=encoder,**state)
