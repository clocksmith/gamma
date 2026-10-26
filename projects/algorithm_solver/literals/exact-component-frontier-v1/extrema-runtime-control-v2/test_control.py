"""Host-only public transport/oracle negatives; no JavaScript execution."""
import copy,json,unittest
import control as c
class ControlTests(unittest.TestCase):
 def raw(self,change=None):
  records=[dict(c.expected_observed(),i=i)for i in range(3)]
  if change:change(records)
  return b''.join(c.q.b.encoded(x)for x in records+[{'done':3}])
 def snapshot_contract(self):
  source=c.HERE/'public-control.js';paths=[source]+[c.q.LIT/'admission500-v1'/n for n in c.HARNESSES];return {'public_fixture_sha256':c.q.b.sha(source.read_bytes()),'code_sha256':{str(p):c.q.b.sha(p.read_bytes())for p in paths}}
 def test_checked_snapshot(self):
  source,harnesses=c.checked_payloads(self.snapshot_contract());self.assertEqual(len(harnesses),2);self.assertIn(b'function solve()',source)
 def test_actual_buffer_drift(self):
  freeze=self.snapshot_contract();freeze['public_fixture_sha256']='0'*64
  with self.assertRaises(ValueError):c.checked_payloads(freeze)
 def test_good(self):self.assertEqual(c.inspect(self.raw()),3)
 def test_flag_false(self):
  with self.assertRaises(ValueError):c.inspect(self.raw(lambda rows:rows[1]['result'].update(signed_zero=False)))
 def test_effect_mismatch(self):
  with self.assertRaises(ValueError):c.inspect(self.raw(lambda rows:rows[0].update(args_after=[1])))
 def test_alias_mismatch(self):
  with self.assertRaises(ValueError):c.inspect(self.raw(lambda rows:rows[2].update(alias_edges=[['x','y']])))
 def test_terminal_missing(self):
  with self.assertRaises(Exception):c.inspect(self.raw().rsplit(b'\n',2)[0]+b'\n')
if __name__=='__main__':unittest.main()
