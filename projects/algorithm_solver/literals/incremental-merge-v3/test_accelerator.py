import hashlib,importlib.util,os,random,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
CORE=Path(os.environ.get('GAMMA_INCREMENTAL_CORE',str(HERE)))
MODULE=Path(os.environ.get('GAMMA_TRIE_MODULE',str(HERE/'accelerator.py')))
SOURCE=Path(os.environ.get('GAMMA_TRIE_SOURCE',str(HERE/'score_kernel.c')))
sys.path.insert(0,str(CORE))
def load():
 s=importlib.util.spec_from_file_location('trie_unit_module',MODULE);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class TrieTests(unittest.TestCase):
 def test_import_and_mismatch_never_load(self):
  with patch('ctypes.CDLL',side_effect=AssertionError('must not load')) as called:
   m=load();called.assert_not_called()
   with tempfile.TemporaryDirectory() as d:
    p=Path(d)/'bad.so';p.write_bytes(b'synthetic')
    with self.assertRaises(ValueError):m.configure('0'*64,p)
    called.assert_not_called()
 def test_compiled_random_exactness_and_incremental_cache(self):
  cc=shutil.which('cc')
  if cc is None:self.skipTest('compiler unavailable')
  m=load()
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'kernel.so';subprocess.run([cc,'-O2','-std=c11','-Wall','-Wextra','-Werror','-shared','-fPIC',str(SOURCE),'-o',str(p)],check=True,timeout=20,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   m.configure(hashlib.sha256(p.read_bytes()).hexdigest(),p);r=random.Random(20261025)
   for _ in range(200):
    text=''.join(r.choice('abca(){}; \n') for _ in range(r.randrange(1,220)));words=set()
    for _ in range(100):
     at=r.randrange(len(text));piece=text[at:at+r.randrange(2,20)]
     if len(piece)>1:words.add(piece)
    vocab=m.search.ALPHABET+sorted(words)[:160];texts={'a':text,'b':text[::-1]};fast=m.TrieGraph(texts);slow=m.OriginalGraph(texts)
    prior=fast.score(vocab);expected=slow.score(vocab);self.assertEqual(prior,expected)
    if len(vocab)>96:
     piece=vocab[-1];next_vocab=vocab[:-1]
     self.assertEqual(fast.score(next_vocab,prior,[piece]),slow.score(next_vocab,expected,[piece]))
   for words in [['aa','aaa'],['ab','abc','bc'],['ab','ba','aba','bab'],['\n\n','\n\na']]:
    vocab=m.search.ALPHABET+sorted(words)
    for text in ['aaaaaa','abcabc','abababab','\n\na\n\n','']:
     self.assertEqual(m.TrieGraph({'x':text}).score(vocab),m.OriginalGraph({'x':text}).score(vocab))
 def test_configuration_required(self):
  m=load()
  with self.assertRaises(RuntimeError):m.TrieGraph({'x':'x'}).score(m.search.ALPHABET)
if __name__=='__main__':unittest.main()
