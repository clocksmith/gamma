import hashlib,importlib.util,pathlib,sys,unittest
from runtime import Engine,normative
BASE=pathlib.Path(__file__).resolve().parent.parent

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
reranker=load('synthetic_integrated_reranker',BASE/'empirical-facet-reranker-v1/rerank.py');delivery=load('synthetic_integrated_delivery',BASE/'persistent-recognition-timing-v1/pipeline.py')
class Encoder:
 def __init__(self):self.calls=0;self.truncated=False
 def encode(self,texts,query):
  assert query is True and len(texts)==1 and isinstance(texts[0],str);self.calls+=1;self.last_request_info=dict(query=True,rows=1,truncated=[self.truncated]);return 'synthetic-vector'
class Index:
 def __init__(self):self.calls=0;self.top=.8
 def scores(self,vector):self.calls+=1;return [self.top]+[.1]*4080
class Service:
 def __init__(self):self.calls=[];self.evidence='normative-typed-effects';self.tamper=False;self.unavailable=False
 def request(self,pid,language=None,include_source=False):
  self.calls.append((pid,language,include_source))
  if include_source and self.unavailable:return dict(status='abstain',reason='source_unavailable')
  if language is None:return dict(status='matched')
  source='synthetic '+language;h=hashlib.sha256(source.encode()).hexdigest();i=dict(status='qualified',evidence_class=self.evidence,source_sha256=h,receipt_sha256='a'*64,problem_contract_sha256='b'*64,contract_scope='synthetic exact domain')
  selection=dict(status='selected',problem_id=pid,language=language,implementation=i);value=dict(status='matched',consumer_selection=selection)
  if include_source:value['artifact']=dict(status='materialized',language=language,bytes=len(source.encode()),source_sha256=h,source_utf8=source+('tamper'if self.tamper else''))
  return value
class Guard:
 @staticmethod
 def parse_query(text):return dict(tentative_evidence=[])
class Feature:
 def __init__(self):self.block=False
 def apply(self,text,b,c):return (dict(status='abstain',reason='synthetic_feature',problem_id=None)if self.block and b['status']=='accepted'else dict(b)),{}
def engine():
 ids=[f'leetcode:{i}'for i in range(1,4082)];e=Encoder();s=Service();idx=Index();features=[Feature()for _ in range(3)];v=Engine(encoder=e,index=idx,ids=ids,service=s,policy=dict(id='c65-m00',min_cosine=.65,min_margin=0),guard=Guard,reranker=reranker,choice=features[0],output=features[1],axis=features[2],contracts={x:dict(facts={},conflicts=[])for x in ids},required={x:{}for x in ids},kinds={x:dict(kind=None)for x in ids},axis_obligation={},delivery=delivery);return v,e,s,idx,features
class Tests(unittest.TestCase):
 def test_fresh_encode_materialize_hash(self):
  v,e,s,idx,features=engine()
  for _ in range(2):
   response,summary,selections=v.request('Synthetic request.');self.assertEqual(response['status'],'artifact_returned');self.assertEqual(summary['response_sha256'],hashlib.sha256(delivery.encoded(response)).hexdigest());self.assertEqual(set(response['artifacts']),{'javascript','python'})
  self.assertEqual(e.calls,2);self.assertEqual(idx.calls,2);self.assertEqual(sum(x[2]for x in s.calls),4)
 def test_truncation_before_ranking(self):
  v,e,s,idx,_=engine();e.truncated=True;response,summary,_=v.request('Synthetic request.');self.assertEqual(response['status'],'abstain');self.assertEqual(idx.calls,0);self.assertFalse(s.calls)
 def test_each_final_feature_blocks_delivery(self):
  for position in range(3):
   v,e,s,idx,fs=engine();fs[position].block=True;response,summary,selections=v.request('Synthetic request.');self.assertEqual(response['status'],'abstain');self.assertFalse(any(x[2]for x in s.calls));self.assertNotIn('artifacts',response);self.assertIsNone(selections)
 def test_normative_class_required(self):
  v,e,s,idx,_=engine();s.evidence='frozen-admitted-typed-effects';response,summary,_=v.request('Synthetic request.');self.assertEqual(response['reason'],'normative_evidence_required');self.assertFalse(any(x[2]for x in s.calls))
 def test_semantic_abstention_precedes_release_evidence(self):
  for position in range(3):
   v,e,s,idx,fs=engine();s.evidence='frozen-admitted-typed-effects';fs[position].block=True;response,summary,selections=v.request('Synthetic request.');self.assertEqual(response['reason'],'synthetic_feature');self.assertFalse(any(x[2]for x in s.calls));self.assertIsNone(selections)
 def test_unknown_input(self):
  v,e,s,idx,_=engine()
  for value in (None,{},'',{'text':'x','expected_id':'leetcode:1'}):self.assertEqual(v.request(value)[0]['status'],'abstain')
  self.assertEqual(e.calls,0)
 def test_raw_cosine_gate(self):
  v,e,s,idx,_=engine();idx.top=.64;self.assertEqual(v.request('Synthetic request.')[0]['status'],'abstain');self.assertFalse(s.calls)
 def test_materialization_tamper(self):
  v,e,s,idx,_=engine();s.tamper=True;response,summary,selection=v.request('Synthetic request.');self.assertEqual(response['status'],'error');self.assertNotIn('artifacts',response);self.assertIsNone(selection)
 def test_full_rivals(self):
  v,e,s,idx,_=engine();self.assertEqual(len(v.ids),4081);self.assertEqual(len(v.contracts),4081)
class OperationalFailureTests(unittest.TestCase):
 def test_nonfinite_scores_no_delivery(self):
  for value in (float('nan'),float('inf'),-float('inf')):
   v,e,s,idx,_=engine();idx.top=value;response,summary,_=v.request('Synthetic request.');self.assertEqual(response['status'],'error');self.assertFalse(any(x[2]for x in s.calls))
 def test_malformed_score_count(self):
  v,e,s,idx,_=engine();idx.scores=lambda vector:[.8];response,summary,_=v.request('Synthetic request.');self.assertEqual(response['status'],'error');self.assertFalse(s.calls)
 def test_delivery_unavailable_error_not_abstention(self):
  v,e,s,idx,_=engine();s.unavailable=True;response,summary,selections=v.request('Synthetic request.');self.assertEqual(response['status'],'error');self.assertEqual(response['error_type'],'ArtifactUnavailable');self.assertIsNone(selections);self.assertNotIn('artifacts',response)
class EncoderAccountingTests(unittest.TestCase):
 def test_actual_invocation_count_on_failure(self):
  v,e,s,idx,_=engine()
  def fail(texts,query):raise RuntimeError('synthetic encoder failure')
  e.encode=fail;response,summary,_=v.request('Synthetic request.');self.assertEqual(response['status'],'error');self.assertEqual(summary['encoder_invocations'],1)
  response,summary,_=v.request(None);self.assertEqual(summary['encoder_invocations'],0)
if __name__=='__main__':unittest.main()
