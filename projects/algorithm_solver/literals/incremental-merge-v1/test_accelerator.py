import random,unittest
from accelerator import FastGraph,OriginalGraph
from search import ALPHABET
class KernelTests(unittest.TestCase):
 def test_exact_randomized_canonical(self):
  r=random.Random(193)
  for trial in range(100):
   texts={str(i):''.join(r.choice(' abcd\n{}') for _ in range(r.randrange(1,150))) for i in range(5)}
   pieces=set()
   for text in texts.values():
    for _ in range(20):
     start=r.randrange(len(text));piece=text[start:start+r.randrange(2,12)]
     if len(piece)>1:pieces.add(piece)
   vocab=ALPHABET+sorted(pieces)[:160]
   self.assertEqual(FastGraph(texts).score(vocab),OriginalGraph(texts).score(vocab))
 def test_incremental_affected_rows(self):
  texts={'a':'abcabc','b':'xxxxx'};a=FastGraph(texts);v=ALPHABET+['ab'];old=a.score(v)
  self.assertEqual(a.score(v+['abc'],old,['abc']),OriginalGraph(texts).score(v+['abc']))
 def test_invalid_ascii(self):
  with self.assertRaises(ValueError):FastGraph({'a':'\t'}).score(ALPHABET)
if __name__=='__main__':unittest.main()
