import unittest
from oracle import validate,expected,compare,zero_swaps_small
from cases import build
class Tests(unittest.TestCase):
 def test_case_regeneration(self):
  a=build();self.assertEqual(len(a),16);self.assertTrue(all(a.values()))
 def test_strict_numeric(self):
  for pid,args in((3894,[False]),(3908,[1,1.0]),(4000,[1,True]),(4020,[True,[0]]),(3898,[[[False]]])):
   with self.assertRaises(ValueError):validate(pid,args)
 def test_malformed(self):
  for pid,args in((3898,[[1]]),(4024,[[1],[0,0]]),(4010,[[1]]),(3931,['a1']),(4030,['A'])):
   with self.assertRaises(ValueError):validate(pid,args)
 def test_boundaries(self):
  self.assertEqual([expected(3894,[x])for x in(0,29,30,31,90,91)],['Green','Invalid','Orange','Red','Red','Invalid'])
  self.assertFalse(expected(3908,[0,0]));self.assertTrue(expected(3908,[100,0]))
 def test_ties_stop(self):
  self.assertEqual(expected(4024,[[[1,0,1],[-1,0,1]],[0,0]]),0)
  self.assertEqual(expected(3921,[['W']*10+['6']]),[0,10])
 def test_duplicate_indices(self):
  self.assertEqual(expected(3912,[[2,1,2]]),[2,2]);self.assertEqual(expected(4010,[[7,7]]),1)
 def test_exact_types_effects(self):
  record={'result':1,'result_type':'int','args_before':[1],'args_after':[1],'alias_edges':[]}
  self.assertFalse(compare(3894,[1],True,record,'python')[0])
  record={'result':[1],'result_type':'list','args_before':[[1]],'args_after':[[2]],'alias_edges':[]}
  self.assertFalse(compare(3925,[[1]],[1],record,'python')[0])
 def test_swap_constructive_bound(self):
  from itertools import product
  for n in range(1,7):
   for bits in product((0,1),repeat=n):self.assertEqual(zero_swaps_small(bits),sum(a!=b for a,b in zip(bits,sorted(bits,reverse=True)))//2)
if __name__=='__main__':unittest.main()
