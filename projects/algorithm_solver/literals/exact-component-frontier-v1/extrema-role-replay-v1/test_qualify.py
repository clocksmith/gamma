"""Host-only scope/deadline/cap controls; no corpus opens or candidate execution."""
import math,time,unittest
import qualify as q
class ReplayControls(unittest.TestCase):
 def test_identical_per_child_limits(self):
  self.assertEqual(q.LIMITS,q.admission.original_owner.LIMITS)
  self.assertEqual(q.NODE_ARGS,q.admission.original_owner.NODE_ARGS)
 def test_exact_scope(self):self.assertEqual(q.IDS,[123,55,1014,1121,1375,1725,1732,2873])
 def test_past_deadline(self):
  with self.assertRaises(TimeoutError):q.check(time.monotonic()-1)
 def test_nonfinite_deadline(self):
  for d in(float('nan'),float('inf'),-float('inf')):
   with self.assertRaises(TimeoutError):q.check(d)
 def test_cancel_flag(self):
  q.STOP.append(15)
  try:
   with self.assertRaises(RuntimeError):q.check(time.monotonic()+100)
  finally:q.STOP.clear()
 def test_call_reserve(self):
  with self.assertRaises(TimeoutError):q.check(time.monotonic()+4,8)
if __name__=='__main__':unittest.main()
