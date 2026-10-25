import importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('role_qualify',HERE/'qualify.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
class SourceTests(unittest.TestCase):
 def test_exact_outputs_fallback_and_population(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);source=root/'source.js';source.write_text('function solve(x){return x;}')
   pilot={'ids':q.IDS,'references':{str(i):{'path':str(source),'sha256':q.sha(source.read_bytes())} for i in q.IDS}}
   original=q.encoded(pilot);pilot_path=root/'inputs.json';pilot_path.write_bytes(original)
   rows={str(i):{'ok':True,'mode':'role','ast_verified':True,'candidate_executions':0,'source':'function solve(p0){return p0;}'} for i in q.IDS}
   rows[str(q.IDS[0])]={'ok':False,'error':'unsupported'}
   output=root/'output.json';output.write_bytes(q.encoded(rows));real=Path.read_bytes
   def read(path):
    if str(path)=='/workspace/shared/gamma-role-canonical-pilot-20261025/inputs.json':return original
    return real(path)
   with patch.object(q,'INPUTS_SHA256',q.sha(original)),patch.object(Path,'read_bytes',read):
    _,_,sources=q.load_sources(pilot_path,output,'role');self.assertEqual(len(sources),32);self.assertEqual(sources[q.IDS[0]],source.read_bytes())
    self.assertIn(b'p0',sources[q.IDS[1]])
    rows[str(q.IDS[1])]['mode']='format';output.write_bytes(q.encoded(rows))
    with self.assertRaises(ValueError):q.load_sources(pilot_path,output,'role')
    del rows[str(q.IDS[1])];output.write_bytes(q.encoded(rows))
    with self.assertRaises(ValueError):q.load_sources(pilot_path,output,'role')
 def test_exact_integer_bool_transport(self):
  self.assertIs(q.tag(True),True)
  self.assertEqual(q.tag(2**53),{'__gamma_bigint_v1__':str(2**53)})
if __name__=='__main__':unittest.main()
