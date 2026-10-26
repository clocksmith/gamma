import importlib.util,pathlib,tempfile,unittest,json,hashlib
from cache import cached_clauses,validate_vectors
from plumbing import paired_vectors
BASE=pathlib.Path(__file__).resolve().parent.parent
s=importlib.util.spec_from_file_location('_fake_bound_encoder',BASE/'contract-clause-encoder-adapter-v1/encoder_binding.py');eb=importlib.util.module_from_spec(s);s.loader.exec_module(eb)
IDENTITY=dict(encoder_manifest_sha256='a'*64,cpu_manifest_sha256='b'*64,native_python_sha256='c'*64)
class Fake:
 def __init__(self):self.__dict__.update(IDENTITY);self.calls=0;self.fail=None
 def encode(self,texts,query):
  self.calls+=1
  if self.calls==self.fail:raise RuntimeError('synthetic failure')
  self.last_request_info=dict(rows=len(texts),query=query,truncated=[False]*len(texts));return [[1.]+[0.]*1023 for _ in texts]
def inputs(n):return [dict(record_id=str(i),text='synthetic'+str(i),text_sha256=eb.sha(('synthetic'+str(i)).encode()),prompt_sha256=eb.PROMPT_SHA256,query=False)for i in range(n)]
class Tests(unittest.TestCase):
 def test_incremental_resume_and_tamper(self):
  f=Fake();e=eb.BoundEncoder(f,IDENTITY,eb.PROMPT_SHA256);identity=dict(encoder_sha256=e.encoder_sha256,prompt_sha256=eb.PROMPT_SHA256,dimension=1024,revision_sha256='d'*64)
  with tempfile.TemporaryDirectory()as td:
   path=pathlib.Path(td)/'cache';f.fail=2;gates=[]
   with self.assertRaises(RuntimeError):cached_clauses(inputs(5),e,path,identity,lambda b:gates.append(len(b)))
   self.assertTrue((path/'failure-1.json').exists());f.fail=None;v,h=cached_clauses(inputs(5),e,path,identity,lambda b:gates.append(len(b)),resume=True);self.assertEqual(len(v),5);self.assertEqual(f.calls,3);self.assertNotIn('text',v[0]);self.assertEqual(gates,[4,1,4,1])
   (path/'0000.json').write_text('{}')
   with self.assertRaises(ValueError):cached_clauses(inputs(5),e,path,identity,lambda b:None,resume=True)
 def test_single_raw_vector_both_arms_fresh_each_request(self):
  f=Fake();e=eb.BoundEncoder(f,IDENTITY,eb.PROMPT_SHA256);c=dict(clause_id='c',problem_id='p1',role='effects',authority_sha256='a'*64,field='effects',field_sha256='b'*64,span=[0,4],text='test',polarity=1,required=False);cv=e.encode_records(eb.clause_inputs([c]),False);bound=dict(encoder_sha256=e.encoder_sha256,prompt_sha256=eb.PROMPT_SHA256,embedding_dimension=1024,score_units='raw_cosine_-1_to_1');ids=['p1']+[str(i)for i in range(4080)];calls=[]
  def scores(v):calls.append(v);return [.6]+[.5]*4080
  for _ in range(2):
   r=paired_vectors('Return an integer.',e,ids,scores,lambda text,raw:raw,[c],cv,bound);self.assertTrue(r['same_raw_vector_for_both_arms']);self.assertEqual(r['ranking']['population'],4081);self.assertIsNone(r['acceptance_decisions'])
  self.assertEqual(len(calls),2);self.assertEqual(f.calls,3)
 def test_same_id_clause_provenance_tamper(self):
  f=Fake();e=eb.BoundEncoder(f,IDENTITY,eb.PROMPT_SHA256);c=dict(clause_id='c',problem_id='p1',role='effects',authority_sha256='a'*64,field='effects',field_sha256='b'*64,span=[0,4],text='test',polarity=1,required=False);cv=e.encode_records(eb.clause_inputs([c]),False);bound=dict(encoder_sha256=e.encoder_sha256,prompt_sha256=eb.PROMPT_SHA256,embedding_dimension=1024,score_units='raw_cosine_-1_to_1');ids=['p1']+[str(i)for i in range(4080)]
  for key,value in [('text','changed'),('authority_sha256','f'*64),('field','different'),('field_sha256','f'*64),('span',[1,5])]:
   with self.assertRaises(ValueError):paired_vectors('Return an integer.',e,ids,lambda v:[.5]*4081,lambda t,r:r,[dict(c,**{key:value})],cv,bound)
  bad=dict(cv[0],query=True)
  with self.assertRaises(ValueError):paired_vectors('Return an integer.',e,ids,lambda v:[.5]*4081,lambda t,r:r,[c],[bad],bound)
 def test_cache_full_provenance_binding(self):
  f=Fake();e=eb.BoundEncoder(f,IDENTITY,eb.PROMPT_SHA256);source=dict(inputs(1)[0],authority_sha256='a'*64,field='effect',field_sha256='b'*64,span=[0,4]);rows=e.encode_records([source],False)
  for key,value in [('authority_sha256','f'*64),('field','other'),('field_sha256','f'*64),('span',[1,5]),('query',True)]:
   with self.assertRaises(ValueError):validate_vectors(rows,[dict(source,**{key:value})],e.encoder_sha256,eb.PROMPT_SHA256,1024)
 def test_span_overflow_no_encoding(self):
  f=Fake();e=eb.BoundEncoder(f,IDENTITY,eb.PROMPT_SHA256);r=paired_vectors('Return an integer. '*9,e,[],None,None,[],[],{});self.assertEqual(r['reason'],'span_budget_exceeded');self.assertEqual(f.calls,0)
if __name__=='__main__':unittest.main()
