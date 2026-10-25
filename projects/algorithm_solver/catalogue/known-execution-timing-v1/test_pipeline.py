import hashlib,unittest
from pipeline import request
class Service:
 def __init__(self,status='matched'):self.status=status
 def request(self,*a,**kw):return {'status':self.status,'artifact':{'source_utf8':'source','source_sha256':hashlib.sha256(b'source').hexdigest()}}
class Tests(unittest.TestCase):
 def call(self,**kw):
  a=dict(service=Service(),problem_id='example',language='python',args=[1],source_sha256=hashlib.sha256(b'source').hexdigest(),admit=lambda a,answer:None,execute=lambda s,a:{'value':2},verify=lambda a,o:o['value']);a.update(kw);return request(**a)
 def test_full_path(self):
  r=self.call();self.assertEqual(r['status'],'verified');self.assertEqual(r['candidate_executions'],1);self.assertGreater(r['response_bytes'],0);self.assertGreaterEqual(r['timing_seconds']['end_to_end'],0)
 def test_unmatched_does_not_execute(self):
  def bad(*a):raise AssertionError('must not execute')
  self.assertEqual(self.call(service=Service('abstained'),execute=bad)['candidate_executions'],0)
 def test_identity_failure_before_execution(self):
  with self.assertRaises(ValueError):self.call(source_sha256='0'*64)
 def test_domain_failure_before_execution(self):
  def deny(a,answer):raise ValueError('invalid domain')
  def bad(*a):raise AssertionError('must not execute')
  with self.assertRaises(ValueError):self.call(admit=deny,execute=bad)
 def test_bad_output_never_served(self):
  def deny(a,o):raise ValueError('oracle mismatch')
  with self.assertRaises(ValueError):self.call(verify=deny)
if __name__=='__main__':unittest.main()
