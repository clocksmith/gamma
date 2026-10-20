"""Protocol checks; optional real isolated replay is run separately."""
import json,unittest
from algsolve.literal_editor import decode,ROOT,DICTIONARY_SHA,check
class ProtocolTests(unittest.TestCase):
 def test_twenty_pinned_programs(self):
  m=json.loads((ROOT/'pass2/working/packages/shared7/manifest.json').read_text())
  for key,row in m['programs'].items():
   bits=''.join(f'{i:07b}' for i in row['sequence'])+'1111111';d=decode(bits)
   self.assertEqual(d['source_sha256'],row['source_sha256']);self.assertEqual(d['selections'],row['sequence']);self.assertEqual(d['cost']['control_bits'],7)
 def test_controls_and_errors(self):
  d=decode('0000000'+'1111101'+'0000001'+'1111110'+'0000010'+'1111111')
  self.assertEqual(d['selections'],[2]);self.assertEqual(d['cost'],{'literal_bits':21,'control_bits':21,'total_bits':42,'source_only_bits':7})
  for bits in ['', '1','x','1001111','1111111','0000000'+'1111111'+'0000000','0'*8197]:
   with self.assertRaises(ValueError):decode(bits)
 def test_identity_fails_before_execution(self):
  with self.assertRaises(ValueError):check({'operation':'literal_check','profile':'wrong','dictionary_sha256':DICTIONARY_SHA,'bits':'','problem_id':'0242'})
if __name__=='__main__':unittest.main()
