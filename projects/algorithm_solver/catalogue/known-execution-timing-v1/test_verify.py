import copy,json,tempfile,unittest
from pathlib import Path
import verify as v
class Oracle:
 encoded=staticmethod(lambda x:(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n').encode())
 validate=staticmethod(lambda p,a:None)
 expected=staticmethod(lambda p,a:1)
 exact=staticmethod(lambda a,b:type(a)is type(b)and a==b)
 parse=staticmethod(lambda raw,n:[json.loads(raw)])
 @staticmethod
 def check_batch(pid,lang,cases,info,raw,offset):
  return (1,[])if info['exit_code']==0 and not info['timed_out']and not info['output_limit_exceeded']and json.loads(raw)=={'result':1}else(0,['bad'])
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.f={'probes':[{'id':i,'args':[],'expected':1}for i in(802,875,2406)]};self.q={'sources':{}};rows=[]
  for r in range(5):
   for p in self.f['probes']:
    for l in ('javascript','python'):
     i=p['id'];stem=f'{r}-{l}-{i}';out=Oracle.encoded({'result':1});info={'stem':stem,'id':i,'repeat':r,'language':l,'exit_code':0,'timed_out':False,'output_limit_exceeded':False,'stdout_sha256':v.sha(out),'stderr_sha256':v.sha(b'')}
     (self.root/(stem+'.stdout')).write_bytes(out);(self.root/(stem+'.stderr')).write_bytes(b'');(self.root/(stem+'.observation.json')).write_text(json.dumps(info));self.q['sources'][f'{l}:{i}']={'sha256':'a'*64};response=Oracle.encoded({'status':'verified','result':1});t={k:1 for k in ['retrieval_and_hash','input_admission','isolated_execution','verification','response_serialization']};t['end_to_end']=5
     rows.append({'repeat':r,'problem_id':f'leetcode:{i}','language':l,'status':'verified','candidate_executions':1,'source_sha256':'a'*64,'observation':info,'response_sha256':v.sha(response),'response_bytes':len(response),'timing_seconds':t})
  self.report={'rows':rows,'candidate_calls':30,'all_verified':True,'per_language':{l:v.distribution([5]*15)for l in ('javascript','python')}}
 def tearDown(self):self.tmp.cleanup()
 def check(self):return v.verify_rows(self.report,self.f,self.q,self.root,Oracle)
 def test_valid(self):self.check()
 def test_missing(self):
  (self.root/'0-python-802.stdout').unlink()
  with self.assertRaises(FileNotFoundError):self.check()
 def test_tampered(self):
  (self.root/'0-python-802.stdout').write_text('{}')
  with self.assertRaises(ValueError):self.check()
 def test_duplicate_row(self):
  self.report['rows'][1]=copy.deepcopy(self.report['rows'][0])
  with self.assertRaises(ValueError):self.check()
 def test_failure_record(self):
  (self.root/'failure.json').write_text('{}')
  with self.assertRaises(ValueError):self.check()
 def test_failure_status(self):
  row=self.report['rows'][0];row['observation']['exit_code']=1;(self.root/'0-javascript-802.observation.json').write_text(json.dumps(row['observation']))
  with self.assertRaises(ValueError):self.check()
 def test_timing(self):
  self.report['rows'][0]['timing_seconds']['end_to_end']=8
  with self.assertRaises(ValueError):self.check()
 def test_response(self):
  self.report['rows'][0]['response_sha256']='0'*64
  with self.assertRaises(ValueError):self.check()
if __name__=='__main__':unittest.main()
