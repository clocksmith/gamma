"""Public source-as-data synthetic controls; no solver/candidate execution."""
import unittest
from addition_policy import make_additions,sha,storage
class PolicyTests(unittest.TestCase):
 def test_new_identity_and_tie(self):
  a,d=make_additions({'1:original':'PUBLIC_A'},{'1':['1:original']},[('role','1','PUBLIC_B',sha('PUBLIC_B'))]);self.assertFalse(d);self.assertGreater(a['role']['1']['key'],'1:original')
 def test_same_owner_duplicate(self):
  a,d=make_additions({'1:original':'PUBLIC_A'},{'1':['1:original']},[('format','1','PUBLIC_A',sha('PUBLIC_A'))]);self.assertFalse(a['format']);self.assertEqual(len(d),1)
 def test_other_owner_not_silently_admitted(self):
  a,d=make_additions({'1:original':'PUBLIC_A','2:original':'PUBLIC_B'},{'1':['1:original'],'2':['2:original']},[('format','1','PUBLIC_B',sha('PUBLIC_B'))]);self.assertEqual(len(a['format']),1);self.assertFalse(d)
 def test_bad_hash(self):
  with self.assertRaises(ValueError):make_additions({'1:original':'PUBLIC_A'},{'1':['1:original']},[('format','1','PUBLIC_B','0'*64)])
 def test_duplicate_owner_arm_rejected(self):
  r=('format','1','PUBLIC_A',sha('PUBLIC_A'))
  with self.assertRaises(ValueError):make_additions({'1:original':'PUBLIC_A'},{'1':['1:original']},[r,r])
 def test_storage_unique_separate(self):
  texts={'1:original':'A'};groups={'1':['1:original']};additions,_=make_additions(texts,groups,[('format','1','BB',sha('BB')),('role','1','BB',sha('BB'))]);s=storage(texts,groups,additions);self.assertEqual(s['plus_both']['registry_utf8_bytes'],5);self.assertEqual(s['plus_both']['unique_content_utf8_bytes'],3);self.assertEqual(s['original_pool']['registry_source_entries'],1)
if __name__=='__main__':unittest.main()
