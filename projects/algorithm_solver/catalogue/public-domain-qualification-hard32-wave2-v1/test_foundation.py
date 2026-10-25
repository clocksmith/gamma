import unittest,math,itertools
from decimal import Decimal
from oracle import IDS,expected,validate,compare,geometric,reachable
class Tests(unittest.TestCase):
 def test_examples(self):
  for pid,args,want in[(1521,[[9,12,3,7,15],5],2),(1542,['3242415'],5),(1585,['84532','34852'],True),(1585,['12345','12435'],False),(1713,[[5,1,3],[9,4,2,3,4]],2),(2111,[[4,1,5,2,6,2],3],2),(2127,[[2,2,1,2]],3),(2127,[[3,0,1,4,1]],4)]:self.assertEqual(expected(pid,args),want)
 def test_geometry(self):
  self.assertEqual(Decimal(geometric([[0,1],[1,0],[1,2],[2,1]])),4)
  self.assertAlmostEqual(float(geometric([[0,0],[1,0],[0,1]])),math.sqrt(2+math.sqrt(3)),places=13)
  self.assertEqual(Decimal(geometric([[0,0],[1,0],[2,0]])),2)
  self.assertEqual(Decimal(geometric([[0,0]]*2+[[3,4]])),5)
  self.assertAlmostEqual(float(geometric([[0,0],[1,0],[100,1]])),1+math.hypot(99,1),places=12)
 def test_tolerance_not_exact_float(self):
  args=[[[0,0],[3,4]]];want=expected(1515,args)
  for value,ok in((5.,True),(5.000009,True),(5.000011,False),(float('nan'),False),(float('inf'),False),(True,False)):
   row={'result':value,'result_type':'float','args_before':args,'args_after':args,'alias_edges':[]};self.assertEqual(compare(1515,args,want,row,'python')[0],ok)
 def test_invalid(self):
  for p,a in((1788,[[1,1]]),(1515,[[[0,101]]]),(1515,[[[True,1]]]),(1521,[[0],0]),(1542,['a']),(1585,['1','11']),(1713,[[1,1],[1]]),(2111,[[2],1]),(2127,[[0,1]])):
   with self.assertRaises(ValueError):validate(p,a)
 def test_bfs_matches_all_substring_sorts(self):
  for s in map(''.join,itertools.product('012',repeat=4)):
   seen={s};todo=[s]
   for x in todo:
    for a in range(4):
     for b in range(a+1,5):
      y=x[:a]+''.join(sorted(x[a:b]))+x[b:]
      if y not in seen:seen.add(y);todo.append(y)
   self.assertEqual(set(reachable(s)),seen)
 def test_cases_and_caps(self):
  import qualify as q
  from cases import build
  for pid,cases in build().items():
   for _,batch in q.batches(cases):
    self.assertLessEqual(len(batch),1 if pid==1515 else 32);self.assertLessEqual(len(q.encoded(q.make_packet(batch))),1800000);self.assertLessEqual(1024+sum(q.observation_bound(x)for x in batch),3900000)
  with self.assertRaises(ValueError):list(q.batches([{'args':['x'*1800000],'expected':1}]))
 def test_code_pins_are_statement_free(self):
  import qualify as q
  from pathlib import Path
  from unittest.mock import patch
  paths=[]
  def read(path):paths.append(path);return b'synthetic code fixture'
  with patch.object(Path,'read_bytes',read):q.pins()
  self.assertTrue(paths);self.assertTrue(all(p.suffix not in('.json','.md')for p in paths))
 def test_statement_gate_order(self):
  import qualify as q
  from pathlib import Path
  from unittest.mock import patch
  events=[]
  def gate(pid,*a,**k):events.append((pid,k.get('payload_kind')))
  def read(path):
   ids=[int(path.stem)]if path.parent.name=='semantics'else list(IDS)
   self.assertEqual(events,[(f'leetcode:{i}','statement')for i in ids]);events.clear();return b'synthetic statement'
  with patch('catalogue.boundary_policy.authorize_before_open',gate),patch.object(Path,'read_bytes',read):self.assertEqual(len(q.statement_pins({'artifact_paths':{},'trusted_hashes':{}})),len(IDS)+3)
if __name__=='__main__':unittest.main()
