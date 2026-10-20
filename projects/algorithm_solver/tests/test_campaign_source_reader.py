import hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from algsolve import corpus_campaign as c
class ReaderTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'corpus.jsonl';self.code='def answer(): return 7\n';self.row={'key':'lc:allowed','references':[{'uid':'lcd:7','code':self.code,'validated':True}]};self.ref={'kind':'corpus-reference','path':str(self.path),'key':'lc:allowed','uid':'lcd:7','sha256':hashlib.sha256(self.code.encode()).hexdigest()}
 def tearDown(self):self.tmp.cleanup()
 def write(self,*lines):self.path.write_text('\n'.join(lines)+'\n')
 def test_poison_and_nested_claimed_identity_never_decoded(self):
  selected=json.dumps(self.row);self.write('{"key":"lc:forbidden", BROKEN, "key":"lc:allowed"}',selected,'{"uid":"forbidden", "nested":{"key":"lc:allowed"}, BROKEN}')
  original=json.loads;seen=[]
  def observe(raw,*a,**kw):seen.append(raw);return original(raw,*a,**kw)
  with patch.object(c.json,'loads',side_effect=observe):c.verify_source(self.ref)
  self.assertEqual(seen,[(selected+'\n').encode()])
 def test_missing_identity_does_not_decode(self):
  self.write('{"key":"lc:forbidden",BROKEN}')
  with patch.object(c.json,'loads',side_effect=AssertionError('Forbidden decode')):
   with self.assertRaisesRegex(ValueError,'missing'):c.verify_source(self.ref)
 def test_duplicate_identity_rejected(self):
  self.write(json.dumps(self.row),json.dumps(self.row))
  with self.assertRaisesRegex(ValueError,'Duplicate'):c.verify_source(self.ref)
 def test_nonfirst_key_layout_fails_closed(self):
  self.write(json.dumps({'references':self.row['references'],'key':'lc:allowed'}))
  with patch.object(c.json,'loads',side_effect=AssertionError('Unsupported decode')):
   with self.assertRaisesRegex(ValueError,'missing'):c.verify_source(self.ref)
 def test_uid_and_code_hash_enforced(self):
  self.write(json.dumps(self.row))
  for changed in [{'uid':'lcd:8'},{'sha256':'0'*64}]:
   with self.subTest(changed=changed),self.assertRaisesRegex(ValueError,'changed'):c.verify_source(dict(self.ref,**changed))
 def test_duplicate_json_key_cannot_redirect(self):
  self.write('{"key":"lc:allowed","key":"lc:forbidden","references":[]}')
  with self.assertRaisesRegex(ValueError,'Duplicate JSON field'):c.verify_source(self.ref)
 def test_same_value_duplicate_json_field_rejected(self):
  row=json.dumps(self.row);self.write(row.replace('"key": "lc:allowed"','"key": "lc:allowed", "key": "lc:allowed"'))
  with self.assertRaisesRegex(ValueError,'Duplicate JSON field'):c.verify_source(self.ref)
 def test_existing_validated_reference_selection_preserved(self):
  self.row['references'].insert(0,{'uid':'lcd:other','code':'wrong'});self.write(json.dumps(self.row));c.verify_source(self.ref)
 def test_file_and_none_source_paths_preserved(self):
  c.verify_source(None);self.path.write_text('literal');c.verify_source({'kind':'file','path':str(self.path),'sha256':hashlib.sha256(b'literal').hexdigest()})
if __name__=='__main__':unittest.main(verbosity=2)
