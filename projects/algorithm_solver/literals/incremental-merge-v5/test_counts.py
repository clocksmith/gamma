"""Exact deferred-trace checks, including affected-source cache reuse."""
import hashlib,random,unittest
from pathlib import Path
import accelerator as a
from search import ALPHABET
KERNEL=Path('/workspace/shared/gamma-dot-diagnostics/score_trie_kernel.so')
PIN='d58b1cd860b9344db011377ff4b43353b21c90252aeccc27e4aeea3db7975222'
class Counts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):a.configure(PIN,KERNEL)
 def test_counts_and_cache(self):
  rng=random.Random(821)
  for _ in range(100):
   texts={str(i):''.join(rng.choice('abc ;\n') for _ in range(90)) for i in range(5)}
   g=a.TrieGraph(texts);v=ALPHABET+['ab','bc','abc'];counts=g.score(v);full=g.materialize(v,counts)
   self.assertTrue(all('used' not in r for r in counts.values()))
   for k in texts:self.assertEqual(''.join(full[k]['used']),texts[k])
   w=ALPHABET+['ab','abc','ca'];cached=g.score(w,full,['bc','ca']);fresh=g.score(w)
   self.assertEqual({k:(r['selections'],r['characters']) for k,r in cached.items()},{k:(r['selections'],r['characters']) for k,r in fresh.items()})
   g.materialize(w,cached)
 def test_mismatch_rejected(self):
  g=a.TrieGraph({'x':'abc'});rows=g.score(ALPHABET);rows['x']['characters']+=1
  with self.assertRaises(ValueError):g.materialize(ALPHABET,rows)
if __name__=='__main__':unittest.main()
