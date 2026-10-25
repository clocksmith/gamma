import unittest
from oracle import validate,expected,compare
class Tests(unittest.TestCase):
 def test_examples(self):
  for p,a,w in[(2170,[[3,1,3,2,4,3]],3),(2186,['leetcode','coats'],7),(2256,[[2,5,3,9,5,3]],3),(2433,[[5,2,0,3,1]],[5,7,2,3,2]),(2587,[[2,-1,0,1,-3,3,-3]],6),(2597,[[2,4,6],2],4),(2602,[[3,1,6,8],[1,5]],[14,10]),(2860,[[1,1]],2)]:self.assertEqual(expected(p,a),w)
 def test_invalid(self):
  for p,a in[(2170,[[0]]),(2186,['a','']),(2256,[[-1]]),(2433,[[True]]),(2587,[[1000001]]),(2597,[[1]*19,1]),(2602,[[1],[0]]),(2860,[[1]])]:
   with self.assertRaises(ValueError):validate(p,a)
 def test_xor_round_trip(self):
  for pref in([0],[5,2,0,3,1],[1000000,0]*20):
   out=expected(2433,[pref]);v=0;got=[]
   for x in out:v^=x;got.append(v)
   self.assertEqual(got,pref)
 def test_duplicate_indices(self):self.assertEqual(expected(2597,[[1]*18,1000]),(1<<18)-1)
 def test_list_effect_and_types(self):
  a=[[1],[2]];r={'result':[1],'result_type':'list','args_before':a,'args_after':a,'alias_edges':[]}
  self.assertTrue(compare(2602,a,[1],r,'python')[0]);r['result']=[True];self.assertFalse(compare(2602,a,[1],r,'python')[0])
 def test_partial_oracle(self):
  a=[[1,2]*100];validate(2170,a)
  with self.assertRaises(ValueError):expected(2170,a)
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
