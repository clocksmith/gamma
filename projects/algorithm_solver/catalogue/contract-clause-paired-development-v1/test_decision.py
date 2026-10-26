import unittest,copy
from decision import paired_decisions,registered_scope
from projects.algorithm_solver.catalogue.catalogue import digest
class Service:
 def __init__(self):self.calls=[];self.selections={}
 def request(self,pid,language=None,include_source=False):
  assert not include_source;self.calls.append((pid,language));return dict(consumer_selection=self.selections[pid][language])
def selected(pid,finite=False):
 contract=dict(problem_id=pid,domain='synthetic domain',result=dict(objective='synthetic objective'),local_effects={},statement_sha256='b'*64)
 if finite:contract['result']['finite_evidence_scope']='Synthetic finite fixtures only'
 wrapped=dict(schema='gamma.reviewed-public-batch-contract.v1',reviewed_statement_contract=contract,authority_review_sha256='c'*64,qualification_freeze_sha256='d'*64)
 return {lang:dict(problem_id=pid,language=lang,implementation=dict(evidence_class='normative-typed-effects',receipt_sha256='e'*64,contract_scope='Reviewed synthetic statement domain',problem_contract_sha256=digest(wrapped),provenance={'public_batch':{'problem_contract':copy.deepcopy(wrapped)}}))for lang in ('javascript','python')}
class Tests(unittest.TestCase):
 def test_each_arm_gates_its_selected_candidate(self):
  service=Service();service.selections={'p1':selected('p1'),'p2':selected('p2')};seen=[];gates=[]
  def decide(r,p,s):
   pid=r['hybrid'][0][0];return dict(status='accepted',problem_id=pid,implementations=s.selections[pid])
  def chain(text,d):seen.append(d['problem_id']);return d
  ranking=dict(rows=[dict(problem_id='p1',raw_cosine=.8,existing_hybrid_score=.8,tentative_adjusted_score=.7),dict(problem_id='p2',raw_cosine=.7,existing_hybrid_score=.7,tentative_adjusted_score=.9)],raw_ranking=['p1','p2'],existing_hybrid_ranking=['p1','p2'],tentative_adjusted_ranking=['p2','p1']);r=paired_decisions('synthetic',ranking,[{}],service,decide,chain,lambda s,p:True,lambda pid,lang:gates.append((pid,lang)));self.assertEqual(seen,['p1','p2']);self.assertEqual(r[0]['arms']['baseline']['problem_id'],'p1');self.assertEqual(r[0]['arms']['tentative']['problem_id'],'p2');self.assertEqual(len(gates),4)
 def test_generic_finite_and_unknown_scope(self):
  s=Service();s.selections={'any-rival':selected('any-rival',True)};self.assertEqual(registered_scope('any-rival',s.selections['any-rival'],s,lambda *a:None)['status'],'UNSUPPORTED_FINITE_SCOPE')
  s.selections={'any-rival':selected('any-rival')};s.selections['any-rival']['javascript']['implementation']['provenance']={};self.assertEqual(registered_scope('any-rival',s.selections['any-rival'],s,lambda *a:None)['status'],'UNKNOWN')
 def test_scope_mismatch_not_reused_baseline(self):
  s=Service();s.selections={'p':selected('p')};s.selections['p']['python']['implementation']['problem_contract_sha256']='0'*64;self.assertEqual(registered_scope('p',s.selections['p'],s,lambda *a:None)['status'],'UNKNOWN')

class RealServiceIntegration(unittest.TestCase):
 def test_real_decide_and_known_catalogue_selection(self):
  import tempfile,pathlib,json,hashlib,importlib.util
  from projects.algorithm_solver.catalogue.test_catalogue import Catalogue
  from projects.algorithm_solver.catalogue.known_spec_service import KnownSpecService
  u,c,old=Catalogue().fixture();c['schema']='gamma.dual-language-catalogue.v2';c['evidence_policy']=dict(schema='gamma.catalogue-evidence-policy.v1',allowed_classes=['normative-typed-effects'],scope_rule='exact-bound-contract-only');receipts={}
  for row in c['problems']:
   pid=row['problem_id'];synthetic=selected(pid)
   for lang,impl in row['implementations'].items():
    impl.update({k:v for k,v in synthetic[lang]['implementation'].items()if k!='receipt_sha256'});impl['caveats']=['Synthetic scope caveat'];impl['interface']=dict(impl['interface'],typed_contract=impl['problem_contract_sha256']);impl['interface_sha256']=digest(impl['interface']);receipt={k:impl[k]for k in ('source_sha256','problem_contract_sha256','interface_sha256','runtime_sha256','tests_sha256','effects_sha256')};receipt.update(canonical_variant_id=impl['canonical_variant_id'],provenance_sha256=digest(impl['provenance']),problem_id=pid,language=lang,verdict='qualified',evidence_class='normative-typed-effects',independent_verifier=True,contract_scope=impl['contract_scope'],caveats=impl['caveats']);rid=digest(receipt);receipts[rid]=receipt;impl['receipt_sha256']=rid
  with tempfile.TemporaryDirectory()as td:
   def write(name,value):
    p=pathlib.Path(td)/name;p.write_text(json.dumps(value));return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
   service=KnownSpecService(dict(schema='gamma.known-spec-service.v2',universe=write('u',u),catalogue=write('c',c),verified_receipts=write('r',receipts)))
   path=pathlib.Path(__file__).resolve().parent.parent/'empirical-facet-reranker-v1/rerank.py';spec=importlib.util.spec_from_file_location('_real_test_rerank',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
   ranking=dict(baseline=[('a',.9),('b',.4)],hybrid=[('a',.9),('b',.4)],raw_cosines={'a':.9,'b':.4});d=module.decide_hybrid(ranking,dict(min_cosine=.65,min_margin=0),service);self.assertEqual(d['status'],'accepted');self.assertEqual(d['implementations']['javascript']['status'],'selected');self.assertEqual(registered_scope('a',d['implementations'],service,lambda *a:None)['status'],'SUPPORTED_STATEMENT_DOMAIN')

   for field,value in [('contract_scope','changed scope'),('caveats',['changed caveat'])]:
    bad=copy.deepcopy(c);bad['problems'][0]['implementations']['javascript'][field]=value
    with self.assertRaises(ValueError):KnownSpecService(dict(schema='gamma.known-spec-service.v2',universe=write('u',u),catalogue=write('bad',bad),verified_receipts=write('r',receipts)))
if __name__=='__main__':unittest.main()
