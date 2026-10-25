import unittest
from oracle import validate,expected
from cases import build
class Tests(unittest.TestCase):
 def test_build(self):self.assertEqual(len(build()),8)
 def test_domains(self):
  for pid,args in((2138,['a',True,'a']),(2248,[[[1,1]]]),(2351,['abc']),(2383,[1,1,[1],[1,2]]),(2432,[2,[[0,1],[0,2]]]),(2432,[1,[[0,1]]]),(2475,[[1,2]]),(2500,[[[1],[]]]),(2506,[['A']])):
   with self.assertRaises(ValueError):validate(pid,args)
 def test_pad_only_final(self):self.assertEqual(expected(2138,['abc',2,'z']),['ab','cz'])
 def test_earliest_second_not_first(self):self.assertEqual(expected(2351,['abccba']),'c')
 def test_strict_competition(self):self.assertEqual(expected(2383,[1,1,[1],[1]]),2)
 def test_task_not_worker_sum(self):self.assertEqual(expected(2432,[2,[[0,3],[1,7],[0,10]]]),1)
 def test_intersection_sorted(self):self.assertEqual(expected(2248,[[[3,1],[1,3]]]),[1,3])
 def test_delete_by_round(self):self.assertEqual(expected(2500,[[[3,1],[2,4]]]),6)
 def test_set_not_frequency(self):self.assertEqual(expected(2506,[['ab','aabb','ba']]),3)
class PacketBounds(unittest.TestCase):
 def test_singleton_packet_cap(self):
  from qualify import batches
  with self.assertRaisesRegex(ValueError,'singleton'):
   list(batches([{'args':['x'*1500000]}]))
 def test_packet_boundary_and_split(self):
  from qualify import batches,make_packet,encoded
  empty={'args':['']};overhead=len(encoded(make_packet([empty])))
  case={'args':['x'*(1500000-overhead)]}
  self.assertEqual(len(encoded(make_packet([case]))),1500000)
  self.assertEqual(len(list(batches([case]))),1)
  chunks=list(batches([{'args':['x'*600000]}]*3))
  self.assertEqual(len(chunks),3)
  self.assertTrue(all(len(encoded(make_packet(b)))<=1500000 for _,b in chunks))
if __name__=='__main__':unittest.main()
