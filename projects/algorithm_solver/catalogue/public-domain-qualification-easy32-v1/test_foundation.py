import unittest
from oracle import expected,validate,compare,valid_no_zero_pair
from cases import build
class Tests(unittest.TestCase):
 def test_regenerate(self):
  cases=build();self.assertEqual(len(cases),8);self.assertTrue(all(cases.values()))
 def test_nonunique_pair(self):
  args=[11];want=expected(1317,args)
  for result in([2,9],[3,8],[8,3],[9,2]):
   r={'result':result,'result_type':'list','args_before':args,'args_after':args,'alias_edges':[]}
   self.assertTrue(compare(1317,args,want,r,'python')[0])
  for result in([1,10],[True,10],[0,11],[5,5],[2.,9],{'a':2,'b':9},[2,9,0]):self.assertFalse(valid_no_zero_pair(11,result))
 def test_strict_domain(self):
  for pid,args in((1317,[True]),(1351,[[[0,1]]]),(1351,[[[0],[1]]]),(1470,[[1,2],True]),(1556,[2**31]),(1598,[['a.b/']]),(1598,[['abcdefghij/']]),(1716,[0]),(1800,[[0]]),(1854,[[[1950,1950]]])):
   with self.assertRaises(ValueError):validate(pid,args)
 def test_malformed_matrix(self):
  for grid in([1],[[1],[]],[],[[True]]):
   with self.assertRaises(ValueError):validate(1351,[grid])
 def test_bank_week_boundary(self):
  self.assertEqual([expected(1716,[n])for n in(1,7,8,14)], [1,28,30,63])
 def test_exclusive_death_earliest_tie(self):
  self.assertEqual(expected(1854,[[[1950,1951],[1951,1952]]]),1950)
 def test_folder_root_and_names(self):
  self.assertEqual(expected(1598,[['../','./','0/','ab9/','../']]),1)
 def test_format_boundaries(self):
  self.assertEqual([expected(1556,[n])for n in(0,999,1000,2**31-1)],['0','999','1.000','2.147.483.647'])
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
