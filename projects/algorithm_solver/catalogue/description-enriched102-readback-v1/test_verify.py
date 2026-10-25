import unittest,copy
from verify import check_metrics,check_cleanup
class Tests(unittest.TestCase):
 def test_metrics(self):check_metrics(dict(positive_count=40,control_count=12,correct_accepts=9,wrong_positive_accepts=0,control_accepts=0,abstentions=43))
 def test_bad_total(self):
  with self.assertRaises(AssertionError):check_metrics(dict(positive_count=40,control_count=12,correct_accepts=9,wrong_positive_accepts=0,control_accepts=0,abstentions=42))
 def test_negative(self):
  with self.assertRaises(AssertionError):check_metrics(dict(positive_count=40,control_count=12,correct_accepts=9,wrong_positive_accepts=-1,control_accepts=0,abstentions=44))
 def test_cleanup(self):
  s=dict(status='completed',exit_code=0,wall_timeout=False,error_type=None,owned_group_cleanup=dict(leader_reaped=True,no_executing_group_members_observed=True,live_members=[],inspection_unreadable_pids=[]));check_cleanup(s)
  for key in ('live_members','inspection_unreadable_pids'):
   bad=copy.deepcopy(s);bad['owned_group_cleanup'][key]=[123]
   with self.assertRaises(AssertionError):check_cleanup(bad)
if __name__=='__main__':unittest.main()
