import copy
import unittest
from oracle import expected,validate,compare
from cases import build

class FoundationTests(unittest.TestCase):
 def test_graph(self):
  self.assertEqual(expected(802,[[[1],[2],[1],[]]]),[3])
  self.assertEqual(expected(802,[[[1,2],[2],[]]]),[0,1,2])
 def test_fuel(self):
  self.assertEqual(expected(871,[100,10,[[10,60],[20,30],[30,30],[60,40]]]),2)
  self.assertEqual(expected(871,[100,1,[]]),-1)
 def test_integer_tasks(self):
  self.assertEqual(expected(875,[[3,6,7,11],8]),4)
  self.assertEqual(expected(1438,[[8,2,4,7],4]),2)
  self.assertEqual(expected(1547,[7,[1,3,4,5]]),16)
  self.assertEqual(expected(1547,[101,list(range(1,101))]),680)
 def test_tree(self):
  self.assertEqual(expected(2246,[[-1,2,0],'aba']),2)
  self.assertEqual(expected(2246,[[-1,0,0,1,1,2],'abacbe']),3)
 def test_intervals_prefix(self):
  self.assertEqual(expected(2406,[[[1,2],[2,3]]]),2)
  self.assertEqual(expected(2416,[['abc','ab','bc','b']]),[5,4,3,2])
 def test_invalid(self):
  bad=[(802,[[[]]]),(802,[[[],[]]]),(2246,[[-1.0],'a']),(802,[[1]]),(802,[[None]]),(802,[[[1],[0,0]]]),(871,[5,1,[[2,1],[1,1]]]),(875,[[True],1]),(1438,[[0],0]),(1547,[5,[1,1]]),(2246,[[-1,2,1],'abc']),(2406,[[[2,1]]]),(2416,[['A']])]
  for pid,args in bad:
   with self.subTest(pid=pid),self.assertRaises(ValueError):validate(pid,args)
 def test_typed_effects(self):
  args=[[1,2],2];want=expected(875,args)
  row={'result':want,'result_type':'int','args_before':copy.deepcopy(args),'args_after':copy.deepcopy(args),'alias_edges':[]}
  self.assertEqual(compare(875,args,want,row,'python'),(True,None))
  for key,value in [('result',True),('result_type','bool'),('args_after',[[1,3],2]),('alias_edges',[['result','args.0']])]:
   wrong=copy.deepcopy(row);wrong[key]=value;self.assertFalse(compare(875,args,want,wrong,'python')[0])
 def test_regeneration_and_batches(self):
  from qualify import batches,encoded
  data=build()
  self.assertEqual(set(data),{802,871,875,1438,1547,2246,2406,2416})
  for cases in data.values():
   flattened=[]
   for offset,batch in batches(cases):
    self.assertEqual(offset,len(flattened));self.assertLessEqual(len(batch),32)
    self.assertTrue(len(batch)==1 or sum(len(encoded({'args':c['args']}))for c in batch)<=1100000)
    flattened.extend(batch)
   self.assertEqual(flattened,cases)
if __name__=='__main__':unittest.main()
