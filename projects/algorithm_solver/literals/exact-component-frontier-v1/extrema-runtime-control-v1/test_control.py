"""Host-only public transport/oracle negatives; no JavaScript execution."""
import copy,json,unittest
import control as c
class ControlTests(unittest.TestCase):
 def raw(self,change=None):
  records=[dict(c.expected_observed(),i=i)for i in range(3)]
  if change:change(records)
  return b''.join(c.q.b.encoded(x)for x in records+[{'done':3}])
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
