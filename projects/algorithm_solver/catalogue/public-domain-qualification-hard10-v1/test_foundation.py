import unittest
from oracle import expected,validate,compare
class Tests(unittest.TestCase):
 def test_examples(self):
  rows=[(10,['ab','.*'],True),(42,[[4,2,0,3,2,5]],9),(84,[[2,1,5,6,2,3]],10),(85,[[['1','0'],['1','1']]],2),(123,[[3,3,5,0,0,3,1,4]],6),(546,[[1,3,2,2,2,3,4,3,1]],23),(564,['123'],'121'),(992,[[1,2,1,2,3],2],7),(1074,[[[1,-1],[-1,1]],0],5),(1187,[[1,5,3,6,7],[1,3,2,4]],1)]
  for pid,args,want in rows:
   with self.subTest(pid=pid):self.assertEqual(expected(pid,args),want)
 def test_invalid(self):
  rows=[(10,['','a']),(10,['a','a**']),(42,[[True]]),(84,[[]]),(85,[[[1]]]),(123,[[-1]]),(546,[[0]]),(564,['01']),(564,['１']),(992,[[1],2]),(1074,[[None],0]),(1187,[[1],[]])]
  for pid,args in rows:
   with self.subTest(pid=pid),self.assertRaises(ValueError):validate(pid,args)
 def test_type_effect_guard(self):
  row={'result':True,'result_type':'bool','args_before':['a','a'],'args_after':['a','a'],'alias_edges':[]}
  self.assertTrue(compare(10,['a','a'],True,row,'python')[0]);row['result']=1
  self.assertFalse(compare(10,['a','a'],True,row,'python')[0])
 def test_large_formula(self):
  self.assertEqual(expected(564,['9'*18]),'1'+'0'*17+'1')
  self.assertEqual(expected(1187,[[0]*2000,list(range(2000))]),1999)
  self.assertEqual(expected(992,[[1]*20000,1]),200010000)
 def test_cases_and_packet_caps(self):
  from cases import build
  from qualify import batches,encoded,make_packet
  for rows in build().values():
   flattened=[]
   for offset,batch in batches(rows):
    self.assertEqual(offset,len(flattened));self.assertLessEqual(len(batch),32);self.assertLessEqual(len(encoded(make_packet(batch))),1500000);flattened+=batch
   self.assertEqual(flattened,rows)
if __name__=='__main__':unittest.main()
