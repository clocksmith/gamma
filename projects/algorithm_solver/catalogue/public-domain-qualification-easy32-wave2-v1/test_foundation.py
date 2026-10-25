import unittest
from oracle import validate,expected,compare
from cases import build
class Tests(unittest.TestCase):
 def test_cases(self):self.assertEqual(len(build()),8)
 def test_types_domains(self):
  for pid,args in((1880,['k','a','a']),(1893,[[[1,2]],True,3]),(1897,[['']]),(1952,[True]),(2000,['a','ab']),(2011,[['+X+']]),(2094,[[1,2,True]]),(2108,[['A']])):
   with self.assertRaises(ValueError):validate(pid,args)
 def test_word_leading_zeros(self):self.assertTrue(expected(1880,['aaa','aab','b']))
 def test_coverage_gap_endpoints(self):
  self.assertFalse(expected(1893,[[[1,2],[4,5]],1,5]));self.assertTrue(expected(1893,[[[1,2],[3,5]],1,5]))
 def test_character_divisibility(self):
  self.assertTrue(expected(1897,[['ab','ba']]));self.assertFalse(expected(1897,[['a','ab']]))
 def test_divisors_not_only_squares(self):
  self.assertEqual([expected(1952,[n])for n in(1,4,9,16,25)], [False,True,True,False,True])
 def test_first_occurrences(self):
  self.assertEqual(expected(2000,['abaca','a']),'abaca');self.assertEqual(expected(2108,[['ab','aa','aba']]),'aa')
 def test_digit_positions_multiplicity_and_order(self):
  self.assertEqual(expected(2094,[[2,2,2]]),[222]);self.assertEqual(expected(2094,[[0,0,2]]),[200]);self.assertEqual(expected(2094,[[1,3,5]]),[])
 def test_boolean_not_integer_result(self):
  args=[4];r={'result':1,'result_type':'bool','args_before':args,'args_after':args,'alias_edges':[]}
  self.assertFalse(compare(1952,args,True,r,'python')[0])
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
