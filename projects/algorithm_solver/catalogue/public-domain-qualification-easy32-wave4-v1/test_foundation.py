import unittest
from oracle import expected,validate
from cases import build
class Tests(unittest.TestCase):
 def test_build(self):self.assertEqual(len(build()),8)
 def test_domains(self):
  for pid,args in((2520,[10]),(2566,[0]),(2644,[[1],[0]]),(2739,[1,0]),(2778,[[True]]),(2828,[[''], 'a']),(2848,[[[2,1]]]),(2917,[[2**31],1])):
   with self.assertRaises(ValueError):validate(pid,args)
 def test_repeated_digits(self):self.assertEqual(expected(2520,[121]),2)
 def test_leading_zero_remap(self):self.assertEqual(expected(2566,[90]),99)
 def test_all_zero_scores_tie(self):self.assertEqual(expected(2644,[[7],[4,3]]),3)
 def test_transfer_after_emptying_fifth_liter(self):self.assertEqual(expected(2739,[5,1]),60)
 def test_one_based_indices(self):self.assertEqual(expected(2778,[[1,2,3,4]]),21)
 def test_inclusive_endpoints(self):self.assertEqual(expected(2848,[[[1,2],[2,3]]]),3)
 def test_high_bit_and_k(self):self.assertEqual(expected(2917,[[2**30,0],1]),2**30);self.assertEqual(expected(2917,[[2**30,0],2]),0)
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
