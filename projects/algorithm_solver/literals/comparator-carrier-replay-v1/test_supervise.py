"""Actual invented child groups and bounded I/O failures; no private inputs."""
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch
import common as c
import run
import supervise

STUB='''import argparse,json,subprocess,sys,time,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output');a=p.parse_args();out=Path(a.output);out.mkdir()
child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])
(out.parent/'child.pid').write_text(str(child.pid))
contract=Path(__file__).with_name('contract.json')
v={'complete':True,'historical_only':True,'promotion_allowed':False,'contract_sha256':hashlib.sha256(contract.read_bytes()).hexdigest(),'worker_seconds':.001}
(out/'results.json').write_text(json.dumps(v));(out/'REPORT.md').write_text('invented report')
MODE
'''

def running(pid):
    try:return (Path('/proc')/str(pid)/'stat').read_text().split()[2]!='Z'
    except FileNotFoundError:return False

class SupervisorTests(unittest.TestCase):
    def tearDown(self):signal.setitimer(signal.ITIMER_REAL,0)
    def invoke(self,root,mode,cap=.5,fault=None):
        (root/'run.py').write_text(STUB.replace('MODE',mode));c.write(root/'contract.json',{'python_bin':os.sys.executable})
        out=root/'out'
        with patch.object(c,'HERE',root),patch.object(c,'verify'),patch.object(run,'validate_output',side_effect=lambda v: v if v.get('complete') is True else (_ for _ in ()).throw(AssertionError())),patch.object(c,'WHOLE_SECONDS',cap),patch.object(c,'CLEANUP',.08),patch.object(supervise,'STARTED',time.monotonic()),patch.object(supervise.resource,'setrlimit'),patch.object(supervise.os,'sched_setaffinity'):
            if fault is None:
                try:supervise.main(out)
                except RuntimeError:pass
            else:
                with fault:
                    try:supervise.main(out)
                    except RuntimeError:pass
        pid=int((out/'child.pid').read_text());time.sleep(.03);self.assertFalse(running(pid),'child group survives supervisor')
        return out
    def test_bootstrap_alarm_interrupts_blocked_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'common.py').write_text('import time;time.sleep(60)\n')
            for name,cap in [('run.py',600),('supervise.py',1200)]:
                source=(c.HERE/name).read_text().replace('STARTED+'+str(cap)+'-time.monotonic()', 'STARTED+.08-time.monotonic()')
                target=root/name;target.write_text(source);start=time.monotonic()
                result=subprocess.run([os.sys.executable,'-B',str(target)],capture_output=True,text=True,timeout=1)
                self.assertNotEqual(result.returncode,0);self.assertIn('BootstrapDeadline',result.stderr)
                self.assertLess(time.monotonic()-start,.7)

    def test_success_group_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=self.invoke(Path(tmp),'pass',2)
            self.assertTrue(c.read(out/'supervisor.json')['complete']);self.assertTrue(c.read(out/'results.json')['complete'])
    def test_timeout_and_nonzero_failure_no_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name,mode in [('timeout','time.sleep(60)'),('failed','sys.exit(7)')]:
                root=Path(tmp)/name;root.mkdir();out=self.invoke(root,mode)
                self.assertFalse(c.read(out/'results.json')['complete']);self.assertFalse((out/'supervisor.json').exists())
    def test_final_write_timeout_withdraws_complete_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            original=c.write
            def write(path,value):
                original(path,value)
                if Path(path).name=='results.json' and value['complete']:time.sleep(2)
            out=self.invoke(Path(tmp),'pass',.3,patch.object(c,'write',side_effect=write))
            self.assertFalse(c.read(out/'results.json')['complete']);self.assertFalse((out/'supervisor.json').exists())
    def test_group_killed_before_blocking_unlink_no_budget_refresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls=[]
            def blocked(*args):calls.append(time.monotonic());time.sleep(2)
            start=time.monotonic();out=self.invoke(Path(tmp),'pass',2,patch.object(run,'remove_success',side_effect=blocked))
            self.assertLess(time.monotonic()-start,.5);self.assertEqual(len(calls),1)
            self.assertFalse((out/'supervisor.json').exists());self.assertFalse((out/'results.json').exists())
    def test_partial_worker_result_never_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=self.invoke(Path(tmp),"(out/'results.json').write_text('{\\\"complete\\\":false}')",2)
            self.assertFalse(c.read(out/'results.json')['complete']);self.assertFalse((out/'supervisor.json').exists())
if __name__=='__main__':unittest.main()
