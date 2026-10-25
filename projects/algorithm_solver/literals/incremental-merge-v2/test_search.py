import unittest
from search import Builder,ALPHABET
class CompositionTests(unittest.TestCase):
 def make(self):
  texts={'a':'function solve(a){return a+1;}','b':'function solve(a){return a+2;}'}
  return Builder(texts,{'a':'1','b':'2'},{'1':'a','2':'b'},{'1':'f','2':'f'},capacity=128,initial=['fu'])
 def test_parent_retirement_proposed(self):
  b=self.make();s=b.score(['1','2'],['fu']);self.assertIn(('fun',('fu',)),b.compositions(s))
 def test_alphabet_never_retired(self):
  b=self.make();s=b.score(['1','2'],['fu']);self.assertTrue(all(all(len(p)>1 for p in removed) for _,removed in b.compositions(s)))
 def test_exact_net_improvement(self):
  b=self.make();a=b.score(['1','2'],['fu']);z=b.score(['1','2'],['fun'],a['all_rows'],['fu','fun']);self.assertLess(z['metrics']['selections'],a['metrics']['selections']);self.assertEqual(z['metrics']['entries'],a['metrics']['entries'])
if __name__=='__main__':unittest.main()
