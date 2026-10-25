import hashlib,importlib.util,sys,tempfile,unittest,os,random,shutil,subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
PATH=Path(os.environ.get('GAMMA_ACCELERATOR_MODULE',str(HERE/'accelerator.py')))
CORE=Path(os.environ.get('GAMMA_INCREMENTAL_CORE',str(PATH.parent)))
sys.path.insert(0,str(CORE))
def load():
 spec=importlib.util.spec_from_file_location('accelerator_v2_draft',PATH);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class LoaderTests(unittest.TestCase):
 def test_import_never_loads_elf(self):
  with patch('ctypes.CDLL',side_effect=AssertionError('must not load')) as called:
   m=load();self.assertIsNone(m.FN);called.assert_not_called()
 def test_mismatch_precedes_cdll(self):
  m=load()
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'owned.so';p.write_bytes(b'synthetic trusted artifact')
   with patch.object(m.ctypes,'CDLL',side_effect=AssertionError('must not load')) as called:
    with self.assertRaises(ValueError):m.configure('0'*64,p)
    called.assert_not_called()
 def test_explicit_identity_only_once_and_mutation_rejected(self):
  m=load()
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'owned.so';p.write_bytes(b'synthetic trusted artifact');h=hashlib.sha256(p.read_bytes()).hexdigest()
   lib=SimpleNamespace(gamma_score=SimpleNamespace())
   with patch.object(m.ctypes,'CDLL',return_value=lib) as called:
    self.assertIs(m.configure(h,p),lib);self.assertIs(m.configure(h,p),lib);self.assertEqual(called.call_count,1)
    p.write_bytes(b'changed')
    with self.assertRaises(ValueError):m.configure(h,p)
    self.assertEqual(called.call_count,1)
 def test_no_scoring_before_configure(self):
  m=load();g=m.FastGraph({'x':'synthetic'})
  with self.assertRaises(RuntimeError):g.score(m.search.ALPHABET)
 def test_temporary_compiled_kernel_matches_python(self):
  compiler=shutil.which('cc')
  if compiler is None:self.skipTest('C compiler unavailable')
  m=load()
  with tempfile.TemporaryDirectory() as d:
   binary=Path(d)/'score_kernel.so'
   subprocess.run([compiler,'-O2','-std=c11','-shared','-fPIC',str(CORE/'score_kernel.c'),'-o',str(binary)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20)
   m.configure(hashlib.sha256(binary.read_bytes()).hexdigest(),library_path=binary)
   rng=random.Random(20261025)
   for _ in range(100):
    text=''.join(rng.choice('abc(){}; \n') for _ in range(rng.randrange(1,100)))
    learned=set()
    for _ in range(40):
     at=rng.randrange(len(text));piece=text[at:at+rng.randrange(2,9)]
     if len(piece)>1:learned.add(piece)
    vocab=m.search.ALPHABET+sorted(learned)
    texts={'one':text,'two':text[::-1]}
    self.assertEqual(m.FastGraph(texts).score(vocab),m.OriginalGraph(texts).score(vocab))
if __name__=='__main__':unittest.main()
