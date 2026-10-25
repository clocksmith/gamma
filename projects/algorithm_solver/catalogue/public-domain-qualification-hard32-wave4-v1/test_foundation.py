import unittest
from itertools import product
from math import comb
from oracle import expected,validate,stable,MOD
class Tests(unittest.TestCase):
 def test_examples(self):
  for p,a,w in[(2709,[[2,3,6]],True),(2709,[[3,9,5]],False),(2781,['cbaaaabc',['aaa','cb']],4),(2953,['igigee',2],3),(3003,['accca',2],3),(3041,[[2,1,5,1,1]],3),(3093,[['abcd','bcd','xbcd'],['cd','bcd','xyz']],[1,1,1]),(3130,[3,3,2],14)]:self.assertEqual(expected(p,a),w)
 def test_compositions_against_binary_enumeration(self):
  for n in range(2,11):
   counts={}
   for a in product((0,1),repeat=n):
    z=a.count(0);o=n-z
    if not z or not o:continue
    longest=run=1
    for i in range(1,n):run=run+1 if a[i]==a[i-1]else 1;longest=max(longest,run)
    for limit in range(longest,n+1):counts[z,o,limit]=counts.get((z,o,limit),0)+1
   for z in range(1,n):
    for limit in range(1,n+1):self.assertEqual(stable(z,n-z,limit),counts.get((z,n-z,limit),0))
 def test_modular_extremes(self):
  self.assertEqual(stable(1000,1000,1000),comb(2000,1000)%MOD)
  self.assertEqual(stable(1000,1000,1),2)
  self.assertEqual(stable(1000,998,1),0)
 def test_invalid(self):
  for p,a in[(2709,[[0]]),(2781,['a',[]]),(2953,['a',2]),(3003,['a',0]),(3041,[[1000001]]),(3093,[[],['a']]),(3130,[0,1,1])]:
   with self.assertRaises(ValueError):validate(p,a)
 def test_suffix_ties(self):self.assertEqual(expected(3093,[['x','a','a','ba'],['a','z','ba']]),[1,0,3])
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

class SingletonPolicyTests(unittest.TestCase):
 def test_exact_3130_singleton_before_execution(self):
  import qualify as q
  from cases import build
  c=build()
  self.assertEqual(len(list(q.batches(c[3130]))),len(c[3130]))
  self.assertTrue(all(x.get('singleton')is True for x in c[3130]))
  self.assertTrue(all('singleton'not in x for pid,rows in c.items()if pid!=3130 for x in rows))
