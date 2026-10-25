import unittest
from itertools import product
from oracle import expected,validate,compare,rational,game
class Tests(unittest.TestCase):
 def test_examples(self):
  rows=[(798,[[2,3,1,4,0]],3),(801,[[1,3,5,4],[1,2,3,7]],1),(899,['cba',1],'acb'),(899,['baaca',3],'aaabc'),(913,[[[2,5],[3],[0,4,5],[1,4,5],[2,3],[0,2,3]]],0),(913,[[[1,2],[0,2],[0,1]]],1),(928,[[[1,1,0],[1,1,1],[0,1,1]],[0,1]],1),(972,['0.9(9)','1.'],True),(1397,[2,'aa','da','b'],51),(1434,[[[3,4],[4,5],[5]]],1)]
  for p,a,w in rows:
   with self.subTest(pid=p):self.assertEqual(expected(p,a),w)
 def test_invalid(self):
  rows=[(798,[[1]]),(798,[[True]]),(801,[[2,1],[2,1]]),(899,['A',1]),(913,[[[2],[3],[0],[1]]]),(928,[[[1,0],[1,1]],[0]]),(972,['01','1']),(972,['1.()','1']),(972,['1.(12345)','1']),(972,['１','1']),(1397,[1,'z','a','b']),(1434,[[[1,1]]])]
  for p,a in rows:
   with self.subTest(pid=p),self.assertRaises(ValueError):validate(p,a)
 def test_exact_geometric_series(self):
  from fractions import Fraction
  self.assertEqual(rational('0.1(6)'),Fraction(1,6));self.assertEqual(rational('9999.9999(9999)'),10000)
  self.assertNotEqual(rational('9999.9999(9999)'),rational('9999.9999(9998)'))
 def test_partition_oracle_against_assignment_products(self):
  for hats in ([[1,2],[1,2],[2,3]],[[1,3,4],[2,3],[1,4]],[[40],[40]],[[1,2,3]]*3):
   direct=sum(len(set(a))==len(a)for a in product(*hats))
   self.assertEqual(expected(1434,[hats]),direct)
 def test_game_cat_win_and_draw(self):
  self.assertEqual(expected(913,[[[3],[2],[1,3],[0,2]]]),2)
  self.assertEqual(expected(913,[[[2,5],[3],[0,4,5],[1,4,5],[2,3],[0,2,3]]]),0)
 def test_type_and_effects(self):
  args=['0','0'];row={'result':True,'result_type':'bool','args_before':args,'args_after':args,'alias_edges':[]}
  self.assertTrue(compare(972,args,True,row,'python')[0]);row['result']=1;self.assertFalse(compare(972,args,True,row,'python')[0])
  row['result']=True;row['args_after']=['1','0'];self.assertFalse(compare(972,args,True,row,'python')[0])
 def test_cases_and_packet_caps(self):
  from cases import build
  from qualify import batches,encoded,make_packet
  for rows in build().values():
   flattened=[]
   for offset,batch in batches(rows):
    self.assertEqual(offset,len(flattened));self.assertLessEqual(len(batch),32);self.assertLessEqual(len(encoded(make_packet(batch))),1500000);flattened+=batch
   self.assertEqual(flattened,rows)
if __name__=='__main__':unittest.main()
