"""Actual service/decision APIs with synthetic receipts, texts and fake vectors."""
import copy,hashlib,importlib.util,json,pathlib,tempfile,unittest
from engine import Predictor,aligned_hybrid,load,BASE
from evaluation import evaluate
from projects.algorithm_solver.catalogue import test_catalogue as synthetic_catalogue
from projects.algorithm_solver.catalogue.catalogue import digest
from projects.algorithm_solver.catalogue.known_spec_service import KnownSpecService
bound=load('_e2e_bound',BASE/'contract-clause-encoder-adapter-v1/encoder_binding.py');cache=load('_e2e_cache',BASE/'contract-clause-paired-development-v1/cache.py');rerank=load('_e2e_original_rerank',BASE/'empirical-facet-reranker-v1/rerank.py');runtime=load('_e2e_normative',BASE/'integrated-recognition-policy-v1/runtime.py')
IDENTITY=dict(encoder_manifest_sha256='a'*64,cpu_manifest_sha256='b'*64,native_python_sha256='c'*64)
class Fake:
 def __init__(self):self.__dict__.update(IDENTITY);self.calls=0
 def encode(self,texts,query):self.calls+=1;self.last_request_info=dict(query=query,rows=len(texts),truncated=[False]*len(texts));return [[1.]+[0.]*1023 for _ in texts]
def service_fixture(root):
 u,c,_=synthetic_catalogue.Catalogue().fixture();ids=['a','b']+[f'rival:{i}'for i in range(4079)];u['eligible_problem_ids']=ids;c['universe_sha256']=digest(u);c['schema']='gamma.dual-language-catalogue.v2';c['evidence_policy']=dict(schema='gamma.catalogue-evidence-policy.v1',allowed_classes=['normative-typed-effects'],scope_rule='exact-bound-contract-only');receipts={}
 for row in c['problems']:
  pid=row['problem_id'];declared=dict(problem_id=pid,domain='Synthetic reviewed domain.',result={'objective':'Synthetic result.'},local_effects={},statement_sha256='d'*64);contract=dict(schema='gamma.reviewed-public-batch-contract.v1',reviewed_statement_contract=declared,authority_review_sha256='e'*64,qualification_freeze_sha256='f'*64)
  for lang,impl in row['implementations'].items():
   impl.update(problem_contract_sha256=digest(contract),evidence_class='normative-typed-effects',contract_scope='Synthetic reviewed statement domain',caveats=['Synthetic finite tests are not universal proof.'],provenance={'public_batch':{'problem_contract':copy.deepcopy(contract)}});impl['interface']=dict(impl['interface'],typed_contract=impl['problem_contract_sha256']);impl['interface_sha256']=digest(impl['interface']);r={k:impl[k]for k in ('source_sha256','problem_contract_sha256','interface_sha256','runtime_sha256','tests_sha256','effects_sha256')};r.update(canonical_variant_id=impl['canonical_variant_id'],provenance_sha256=digest(impl['provenance']),problem_id=pid,language=lang,verdict='qualified',evidence_class='normative-typed-effects',independent_verifier=True,contract_scope=impl['contract_scope'],caveats=impl['caveats']);rid=digest(r);receipts[rid]=r;impl['receipt_sha256']=rid
 for pid in ids[2:]:c['problems'].append(dict(problem_id=pid,implementations={lang:dict(status='missing',reason='synthetic unavailable; remains rival')for lang in ('javascript','python')}))
 def write(n,v):
  p=root/n;p.write_text(json.dumps(v));return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 return ids,KnownSpecService(dict(schema='gamma.known-spec-service.v2',universe=write('universe',u),catalogue=write('catalogue',c),verified_receipts=write('receipts',receipts)))
class Tests(unittest.TestCase):
 def test_cache_scoring_real_service_all20_then_evaluation(self):
  with tempfile.TemporaryDirectory()as td:
   root=pathlib.Path(td);ids,service=service_fixture(root);fake=Fake();encoder=bound.BoundEncoder(fake,IDENTITY,bound.PROMPT_SHA256);clause=dict(clause_id='clause-a',problem_id='a',role='objective',authority_sha256='a'*64,field='result',field_sha256='b'*64,span=[0,4],text='test',polarity=1,required=False);inputs=bound.clause_inputs([clause]);bindings=dict(encoder_sha256=encoder.encoder_sha256,prompt_sha256=bound.PROMPT_SHA256,embedding_dimension=1024,score_units='raw_cosine_-1_to_1');vectors,_=cache.cached_clauses(inputs,encoder,root/'cache',dict(encoder_sha256=encoder.encoder_sha256,prompt_sha256=bound.PROMPT_SHA256,dimension=1024,revision_sha256='c'*64),lambda batch:None);policies=json.loads((BASE/'description-empirical-v1/policy-freeze.json').read_text())['policy_family'];contracts={pid:dict(facts={},conflicts=[])for pid in ids};calls=[]
   def baseline(text,raw):return rerank.rerank(raw,ids,contracts,dict(tentative_evidence=[]),object())
   def scores(vector):calls.append(1);return [.9,.4]+[.1]*4079
   predictor=Predictor(encoder=encoder,stable_ids=ids,index_scores=scores,baseline_ranker=baseline,clauses=[clause],clause_vectors=vectors,bindings=bindings,policies=policies,service=service,decide_hybrid=rerank.decide_hybrid,semantic_chain=lambda text,d:d,normative=runtime.normative,authorize_statement=lambda pid,lang:None)
   predictions=[predictor.request('Return an integer.')for _ in range(72)]
   # Only AFTER all predictions do evaluator annotations enter this test path.
   labels=[dict(kind='positive',target_id='a',artifact_eligible=None)for _ in range(48)]+[dict(kind='selected_contract_contrast',target_id='a'if i<12 else'b')for i in range(24)];report=evaluate(predictions,labels,policies);self.assertEqual(len(report['results']),20);self.assertEqual(len(calls),72);self.assertEqual(fake.calls,73)
   for row in report['results']:
    for m in row['arms'].values():self.assertEqual(m['positive_accepted_identity_correct'],48);self.assertEqual(m['contrast_target_conflict_accept'],12);self.assertEqual(m['contrast_other_rival_accept_UNRESOLVED'],12);self.assertEqual(m['errors'],0)
   self.assertFalse(report['global_absence_assumed']);self.assertFalse(report['recognition_qualified'])
 def test_sorted_hybrid_mapped_back_to_stable_ids(self):self.assertEqual(aligned_hybrid(['b','a'],dict(hybrid=[('a',.9),('b',.3)])),[.3,.9])
 def test_missing_hybrid_identity_rejected(self):
  with self.assertRaises(ValueError):aligned_hybrid(['a','b'],dict(hybrid=[('a',.9),('a',.2)]))
 def test_real_index_shape_and_python_score_units(self):
  import os
  os.environ['OPENBLAS_NUM_THREADS']='1'
  import numpy as np
  owner=load('_test_owner_index',pathlib.Path(__file__).with_name('owner.py'));artifacts=load('_test_real_index',BASE/'persistent-recognition-timing-v1/artifacts.py');array=np.zeros((4081,1024),dtype=np.float32);array[:,0]=1;index=artifacts.FullIndex(array,np);scores=owner.index_scores(index,[1.]+[0.]*1023,np,4081);self.assertEqual(len(scores),4081);self.assertIs(type(scores[0]),float);self.assertEqual(scores[0],1.)
if __name__=='__main__':unittest.main()

