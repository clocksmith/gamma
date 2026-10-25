import signal,sys,tempfile,threading,time,unittest
from pathlib import Path
from supervise import supervise,snapshot
class CleanupTests(unittest.TestCase):
 def run_tree(self,trigger):
  # Independently authored public Python control, never JS/candidate execution.
  code="import subprocess,sys,time; subprocess.Popen([sys.executable,'-c','import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(30)'],start_new_session=True); time.sleep(30)"
  with tempfile.TemporaryDirectory() as tmp:
   state={'signals':[]};deadline=time.monotonic()+(.35 if trigger=='deadline' else 30)
   timer=threading.Timer(.35,lambda:state['signals'].append(signal.SIGTERM)) if trigger=='signal' else None
   if timer:timer.start()
   result=supervise([sys.executable,'-c',code],Path(tmp)/'log',deadline,state,grace=.1)
   if timer:timer.join()
   self.assertTrue(result['no_executing_owned_processes_observed'],result)
   self.assertGreaterEqual(len({r['pgid']for r in result['owned_processes']}),2,result)
   self.assertTrue(any(r['signal']==signal.SIGKILL for r in result['cleanup_signals']),result)
   self.assertEqual(result['wall_timeout'],trigger=='deadline')
 def test_detached_descendant_deadline(self):self.run_tree('deadline')
 def test_detached_descendant_signal(self):self.run_tree('signal')
 def test_rapid_leader_exit_adopted_detached_child(self):
  code="import subprocess,sys,os; c=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'],start_new_session=True); print(c.pid,flush=True); os._exit(0)"
  with tempfile.TemporaryDirectory() as tmp:
   log=Path(tmp)/'log';result=supervise([sys.executable,'-c',code],log,time.monotonic()+5,{'signals':[]},grace=.1)
   pid=int(log.read_text().strip())
   self.assertIn(pid,[r['pid']for r in result['owned_processes']]);self.assertIn(pid,result['adopted_children_reaped'])
   self.assertTrue(result['no_executing_owned_processes_observed'],result)
   self.assertNotIn(pid,snapshot()[0])
 def test_nonfinite_deadline(self):
  with tempfile.TemporaryDirectory() as tmp:
   for n in [float('nan'),float('inf')]:
    with self.assertRaises(ValueError):supervise([sys.executable,'-c','pass'],Path(tmp)/'log',n,{'signals':[]})
if __name__=='__main__':unittest.main()
