import unittest
from oracle import expected,validate,compare,lcp_matrix,beautiful
class Tests(unittest.TestCase):
 def test_examples(self):
  rows=[(2132,[[[0,0],[0,0]],2,2],True),(2267,[[['(',')']]],True),(2290,[[[0,1,0]]],1),(2426,[[3,2,5],[2,2,1],1],3),(2565,['abacaba','bzaa'],1),(2569,[[1,0,1],[0,0,0],[[1,1,1],[2,1,0],[3,0,0]]],[3]),(2573,[lcp_matrix('abab')],'abab'),(2663,['abcz',26],'abda')]
  for p,a,w in rows:self.assertEqual(expected(p,a),w)
 def test_invalid(self):
  for p,a in[(2132,[[[0]],0,1]),(2267,[[['x']]]),(2290,[[[1,0]]]),(2426,[[1],[1],0]),(2565,['','a']),(2569,[[0],[0],[[1,0,1]]]),(2573,[[[2]]]),(2663,['aba',4])]:
   with self.assertRaises(ValueError):validate(p,a)
 def test_exact_integer_marker(self):
  args=[[1],[0],[[3,0,0]]];want=[9007199254740993];r={'result':[{'__gamma_bigint_v1__':'9007199254740993'}],'result_type':'object','args_before':args,'args_after':args,'alias_edges':[]}
  self.assertTrue(compare(2569,args,want,r,'javascript')[0]);r['result']=[9007199254740992];self.assertFalse(compare(2569,args,want,r,'javascript')[0])
  for x in('01','+1','1.0','1e2','-0'):
   r['result']=[{'__gamma_bigint_v1__':x}];self.assertFalse(compare(2569,args,[1],r,'javascript')[0])
 def test_large_exact_superposition(self):
  self.assertEqual(expected(2569,[[1]*100000,[0]*100000,[[2,1000000,0]]*92000+[[3,0,0]]]),[9200000000000000])
 def test_lcp_constraints(self):
  self.assertEqual(expected(2573,[[[1,1],[0,1]]]),'')
  self.assertEqual(expected(2573,[[[27-i if i==j else 0 for j in range(27)]for i in range(27)]]),'')
 def test_boolean_not_integer(self):
  a=[[[0]],1,1];r={'result':1,'result_type':'boolean','args_before':a,'args_after':a,'alias_edges':[]};self.assertFalse(compare(2132,a,True,r,'javascript')[0])


class TransportPolicyTests(unittest.TestCase):
 def test_gate_order_and_code_only_pins(self):
  import qualify as q
  from pathlib import Path
  from unittest.mock import patch
  from oracle import IDS
  reads=[]
  with patch.object(Path,'read_bytes',lambda p:reads.append(p)or b'code'):q.pins()
  self.assertTrue(all(p.suffix not in('.json','.md')for p in reads))
  events=[]
  def gate(pid,*a,**k):events.append((pid,k.get('payload_kind')))
  def read(p):
   ids=[int(p.stem)]if p.parent.name=='semantics'else list(IDS)
   self.assertEqual(events,[(f'leetcode:{i}','statement')for i in ids]);events.clear();return b'metadata'
  with patch('catalogue.boundary_policy.authorize_before_open',gate),patch.object(Path,'read_bytes',read):q.statement_pins({'artifact_paths':{},'trusted_hashes':{}})
 def test_complete_fixture_packets(self):
  import qualify as q
  from cases import build
  for cases in build().values():
   for _,b in q.batches(cases):
    self.assertLessEqual(len(b),32);self.assertLessEqual(len(q.encoded(q.make_packet(b))),1800000);self.assertLessEqual(1024+sum(q.observation_bound(x)for x in b),3900000)

class BigIntPackingTests(unittest.TestCase):
 def test_all_small_integers_may_be_bigints(self):
  import qualify as q
  c={'args':[[1],[0],[[3,0,0]]],'expected':[1]*10000}
  tagged=[{'__gamma_bigint_v1__':'1'}]*10000
  self.assertGreaterEqual(q.observation_bound(c),2*len(q.encoded(c['args']))+len(q.encoded(tagged))+1024)

class CrossLanguageIntegerTransportTests(unittest.TestCase):
 def record(self,args,value,language):
  return {'result':value,'result_type':'list'if language=='python'else'object','args_before':args,'args_after':args,'alias_edges':[]}
 def test_both_languages_exact_large_signed_values(self):
  args=[[1],[0],[[3,0,0]]]
  for language in('python','javascript'):
   for n in(9007199254740993,-9007199254740993,9199700000100000):
    r=self.record(args,[{'__gamma_bigint_v1__':str(n)}],language)
    self.assertTrue(compare(2569,args,[n],r,language)[0])
 def test_malformed_and_type_drift_rejected(self):
  args=[[1],[0],[[3,0,0]]]
  for language in('python','javascript'):
   bad=[True,1.0,{'__gamma_bigint_v1__':'01'},{'__gamma_bigint_v1__':'+1'},{'__gamma_bigint_v1__':'-0'},{'__gamma_bigint_v1__':'1.0'},{'__gamma_bigint_v1__':1},{'__gamma_bigint_v1__':'1','extra':0},9007199254740993]
   for value in bad:self.assertFalse(compare(2569,args,[1],self.record(args,[value],language),language)[0])
   r=self.record(args,[{'__gamma_bigint_v1__':'1'}],language);r['result_type']='tuple';self.assertFalse(compare(2569,args,[1],r,language)[0])
 def test_other_problem_does_not_decode_marker(self):
  args=[[0,0],[0,0],0]
  for language,kind in(('python','int'),('javascript','number')):
   r=self.record(args,{'__gamma_bigint_v1__':'1'},language);r['result_type']=kind
   self.assertFalse(compare(2426,args,1,r,language)[0])

if __name__=='__main__':unittest.main()
