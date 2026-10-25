"""Bounded synthetic child-only allocation, escaped descendant, and signal controls."""
import json,os,pathlib,subprocess,sys,tempfile,unittest
HERE=pathlib.Path(__file__).resolve().parent
class SupervisorTests(unittest.TestCase):
 def check(self,child,limit,terminate=False):
  with tempfile.TemporaryDirectory()as td:
   code="""import sys,json,time,signal,threading,os
from pathlib import Path
from owned_supervisor import supervise
state={'signals':[]}
for sig in (signal.SIGTERM,signal.SIGHUP,signal.SIGINT):signal.signal(sig,lambda n,f:state['signals'].append(n))
if sys.argv[4]=='True':threading.Timer(.3,lambda:os.kill(os.getpid(),signal.SIGTERM)).start()
r=supervise([sys.executable,'-c',sys.argv[1]],Path(sys.argv[2]),time.monotonic()+8,state,grace=.1,rss_limit_bytes=int(sys.argv[3]))
print(json.dumps(r))
"""
   env=dict(os.environ,PYTHONPATH=str(HERE),PYTHONDONTWRITEBYTECODE='1')
   r=subprocess.run([sys.executable,'-c',code,child,td+'/child.log',str(limit),str(terminate)],env=env,text=True,capture_output=True,timeout=12);self.assertEqual(r.returncode,0,r.stderr);v=json.loads(r.stdout);self.assertTrue(v['no_executing_owned_processes_observed'],v);self.assertFalse(v['remaining_live_owned']);return v
 def test_allocation_limit(self):
  v=self.check('import time;x=bytearray(64*1024**2);time.sleep(10)',32*1024**2);self.assertTrue(v['rss_limit_exceeded']);self.assertGreater(v['peak_summed_owned_rss_bytes'],32*1024**2)
 def test_escaped_descendant_limit(self):
  v=self.check("import subprocess,sys,time;subprocess.Popen([sys.executable,'-c','import time;x=bytearray(64*1024**2);time.sleep(10)'],start_new_session=True);time.sleep(10)",48*1024**2);self.assertTrue(v['rss_limit_exceeded']);self.assertGreaterEqual(len(v['owned_processes']),2)
 def test_no_term_allocation_grace(self):
  child="import signal,time;signal.signal(signal.SIGTERM,lambda n,f: bytearray(64*1024**2));time.sleep(10)"
  v=self.check(child,48*1024**2,True);self.assertTrue(v['termination_signals']);self.assertEqual(v['termination_grace_seconds'],0);self.assertTrue(v['cleanup_signals']);self.assertTrue(all(r['signal']==9 for r in v['cleanup_signals']))
 def test_handled_termination_cleans_tree(self):
  v=self.check("import subprocess,sys,time;subprocess.Popen([sys.executable,'-c','import time;time.sleep(10)'],start_new_session=True);time.sleep(10)",128*1024**2,True);self.assertTrue(v['termination_signals']);self.assertGreaterEqual(len(v['owned_processes']),2)
if __name__=='__main__':unittest.main()
