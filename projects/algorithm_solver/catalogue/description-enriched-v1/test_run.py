import importlib.util,unittest,hashlib,tempfile,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('enriched',Path(__file__).with_name('run.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
 def rows(self):
  old=[{'problem_id':f'leetcode:{i}','text':f'title{i}'}for i in range(4081)]
  new=[dict(r,text=r['text']+(' enriched'if i<54 else''))for i,r in enumerate(old)]
  for a,b in zip(old,new):
   b['document_sha256']=hashlib.sha256(b['text'].encode()).hexdigest();b['baseline_document_sha256']=hashlib.sha256(a['text'].encode()).hexdigest()
  return old,new
 def test_full(self):self.assertEqual(m.alignment(*self.rows()),list(range(54)))
 def test_dropped(self):
  a,b=self.rows()
  with self.assertRaises(ValueError):m.alignment(a,b[:-1])
 def test_reorder(self):
  a,b=self.rows();b[1],b[2]=b[2],b[1]
  with self.assertRaises(ValueError):m.alignment(a,b)
 def test_bad_text(self):
  a,b=self.rows();b[80]['text']='changed'
  with self.assertRaises(ValueError):m.alignment(a,b)
 def test_pin(self):
  with tempfile.TemporaryDirectory()as td:
   p=Path(td)/'x';p.write_text('{}')
   with self.assertRaises(ValueError):m.read({'path':str(p),'sha256':'0'*64})
 def test_no_confirmation_cli(self):
  source=Path(m.__file__).read_text();self.assertNotIn("'--stage'",source);self.assertNotIn("confirmation_sha256",source)
if __name__=='__main__':unittest.main()
