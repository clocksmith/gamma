import importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('traversal_qualification_tests_module',HERE/'qualify.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
class FreezeTests(unittest.TestCase):
 def test_fixed_five_exact_byte_gate(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);raw=b'function solve(root){return root;}';policy=b'synthetic contract'
   sources={str(i):{'path':f'{i}.js','sha256':q.sha(raw),'bytes':len(raw)} for i in q.IDS}
   for i in q.IDS:(root/f'{i}.js').write_bytes(raw)
   c={'schema':'gamma.traversal-family.sources.v1','ids':q.IDS,'sources':sources,'code_sha256':{'synthetic':'hash'},'baseline_loader_sha256':q.sha(Path(q.b.__file__).read_bytes()),'source_policy_sha256':q.sha(policy),'protected_access':False,'m1_qualified':False}
   (root/'contract.json').write_bytes(q.encoded(c));real=Path.read_bytes
   def read(path):return policy if path==HERE/'CONTRACT.md' else real(path)
   with patch.object(q,'pins',return_value={'synthetic':'hash'}),patch.object(Path,'read_bytes',read):
    _,loaded=q.load_freeze(root);self.assertEqual(list(loaded),q.IDS)
    (root/'103.js').write_bytes(raw+b' ')
    with self.assertRaises(ValueError):q.load_freeze(root)
    (root/'103.js').write_bytes(raw);c['ids']=q.IDS[:-1];(root/'contract.json').write_bytes(q.encoded(c))
    with self.assertRaises(ValueError):q.load_freeze(root)
 def test_typed_protocol_needs_completion(self):
  with self.assertRaises(ValueError):q.parse(b'{"i":0,"result":1}\n',1)
if __name__=='__main__':unittest.main()
