import unittest
from oracle import validate,expected,compare
class Tests(unittest.TestCase):
 def test_examples(self):
  for p,a,w in [(1894,[[5,1,5],22],0),(1911,[[4,2,5,3]],7),(1921,[[1,1,2,3],[1,1,1,1]],1),(1953,[[5,2,1]],7),(1976,[2,[[1,0,10]]],1),(2079,[[2,2,3,3],5],14),(2131,[['lc','cl','gg']],6),(2135,[['ant','act','tack'],['tack','act','acti']],2)]:self.assertEqual(expected(p,a),w)
 def test_invalid(self):
  for p,a in [(1894,[[1],0]),(1911,[[True]]),(1921,[[1],[1,2]]),(1953,[[0]]),(1976,[3,[[0,1,1]]]),(1976,[2,[[0,1,1],[1,0,2]]]),(2079,[[2],1]),(2131,[['Aa']]),(2135,[['aa'],['ab']])]:
   with self.assertRaises(ValueError):validate(p,a)
 def test_large_valid_not_claimed_total_oracle(self):
  a=[[2,1,3]*10];validate(1911,a)
  with self.assertRaises(ValueError):expected(1911,a)
 def test_path_count_modulo(self):
  layers=[[0]]+[[2*i-1,2*i]for i in range(1,31)]+[[61]]
  self.assertEqual(expected(1976,[62,[[u,v,1]for left,right in zip(layers,layers[1:])for u in left for v in right]]),pow(2,30,10**9+7))
 def test_types_effects(self):
  a=[[1],1];r={'result':0,'result_type':'int','args_before':a,'args_after':a,'alias_edges':[]}
  self.assertTrue(compare(1894,a,0,r,'python')[0]);r['result']=False;self.assertFalse(compare(1894,a,0,r,'python')[0])
 def test_singleton_graph(self):self.assertEqual(expected(1976,[1,[]]),1)
if __name__=='__main__':unittest.main()

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
