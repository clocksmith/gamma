import hashlib,unittest
from search import Builder
class PrimitiveTests(unittest.TestCase):
 def make(self):
  helper='function pair(a,b){return [a,b];}'
  texts={'a':helper+'function solve(a){return pair(a,1).reverse();}','b':helper+'function solve(a){return pair(a,2).join();}'}
  row={'text':helper,'sha256':hashlib.sha256(helper.encode()).hexdigest(),'bytes':len(helper)}
  return Builder(texts,{'a':'1','b':'2'},{'1':'a','2':'b'},{'1':'x','2':'x'},capacity=128,audited_helpers=[row]),helper
 def test_audited_full_primitive_allowed(self):
  b,h=self.make();self.assertTrue(b.legal(h));self.assertIn((h,()),b.compositions(b.score(['1','2'],[])))
 def test_unreviewed_whole_helper_stays_blocked(self):
  b,h=self.make();self.assertFalse(b.legal('return [a,b];'))
 def test_no_raw_text_hash_override(self):
  b,h=self.make()
  with self.assertRaises(ValueError):Builder(b.texts,b.owners,b.references,b.families,capacity=128,audited_helpers=[{'text':h,'sha256':'0'*64,'bytes':len(h)}])
 def test_whole_solution_guard_overrides_allowlist(self):
  h='function F(a){return a+1;}'
  texts={'a':h+'function solve(a){return a+1;}','b':h+'function solve(a){return F(a)+2;}'}
  row={'text':h,'sha256':hashlib.sha256(h.encode()).hexdigest(),'bytes':len(h)}
  with self.assertRaises(ValueError):Builder(texts,{'a':'1','b':'2'},{'1':'a','2':'b'},{'1':'x','2':'x'},capacity=128,audited_helpers=[row])
if __name__=='__main__':unittest.main()
