"""Reusable text-only predictor wiring, separate from evaluator labels."""
import importlib.util
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
paired=load('_runner_paired',BASE/'contract-clause-paired-development-v1/plumbing.py')
decisions=load('_runner_decisions',BASE/'contract-clause-paired-development-v1/decision.py')

def aligned_hybrid(stable_ids,ranking):
 pairs=ranking['hybrid']
 if len(pairs)!=len(stable_ids)or len({pid for pid,_ in pairs})!=len(pairs)or {pid for pid,_ in pairs}!=set(stable_ids):raise ValueError('hybrid full-rival identity mismatch')
 scores=dict(pairs);return [scores[pid]for pid in stable_ids]

class Predictor:
 def __init__(self,*,encoder,stable_ids,index_scores,baseline_ranker,clauses,clause_vectors,bindings,policies,service,decide_hybrid,semantic_chain,normative,authorize_statement):
  if len(policies)!=20 or len({p['id']for p in policies})!=20:raise ValueError('exact20 policy family required')
  self.encoder=encoder;self.ids=stable_ids;self.index_scores=index_scores;self.baseline_ranker=baseline_ranker;self.clauses=clauses;self.vectors=clause_vectors;self.bindings=bindings;self.policies=policies;self.service=service;self.decide=decide_hybrid;self.chain=semantic_chain;self.normative=normative;self.gate=authorize_statement
 def request(self,text):
  before=self.encoder.calls
  try:
   result=paired.paired_vectors(text,self.encoder,self.ids,self.index_scores,lambda t,raw:aligned_hybrid(self.ids,self.baseline_ranker(t,raw)),self.clauses,self.vectors,self.bindings)
   if result['status']!='ranked':return dict(result,actual_encoder_calls=self.encoder.calls-before)
   ranking=result['ranking'];out=decisions.paired_decisions(text,ranking,self.policies,self.service,self.decide,self.chain,self.normative,self.gate)
   # Metadata-only source-free response: no implementation/contract text payload.
   rows=[]
   for entry in out:
    arms={}
    for name,d in entry['arms'].items():
     top=ranking['existing_hybrid_ranking'if name=='baseline'else'tentative_adjusted_ranking'][0]
     arms[name]=dict(status=d['status'],reason=d.get('reason'),problem_id=d.get('problem_id'),semantic_top_id=top,selected_raw_cosine=d.get('selected_raw_cosine'),adjusted_margin=d.get('adjusted_margin'),artifact_bytes_materialized=False)
    rows.append(dict(policy=entry['policy'],arms=arms))
   return dict(status='completed',request_sha256=result['request_sha256'],actual_encoder_calls=self.encoder.calls-before,fresh_encoder_rows=result['fresh_encoder_rows'],span_count=result['span_count'],same_raw_vector_for_both_arms=True,population=ranking['population'],decisions=rows,recognition_qualified=False)
  except (TimeoutError,KeyboardInterrupt,SystemExit):raise
  except Exception as e:return dict(status='error',error_type=type(e).__name__,actual_encoder_calls=self.encoder.calls-before,recognition_qualified=False)
