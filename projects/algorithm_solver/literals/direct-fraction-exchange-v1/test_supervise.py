"""Actual process-group cleanup with invented workers; no corpus access."""
import json
import os
from pathlib import Path
import signal
import tempfile
import time
import unittest
from unittest.mock import patch

import common as c
import supervise


STUB='''import json,os,subprocess,sys,time
from pathlib import Path
args=sys.argv[1:]
cohort=args[args.index('--cohort')+1]
output=Path(args[args.index('--output')+1])
child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'])
(output/(cohort+'-processes.json')).write_text(json.dumps({'worker':os.getpid(),'group':os.getpgrp(),'child':child.pid}))
arm=output/cohort
arm.mkdir()
# Deliberately incomplete, despite a claimed complete flag: this partial
# worker artifact must never become an accepted whole-job certificate.
(arm/'results.json').write_text(json.dumps({'cohort':cohort,'complete':True,'validation_loaded':False,'points':[{'ordinal':0}]}))
mode=Path(__file__).with_name('stub-mode').read_text()
if mode=='failure' and cohort=='R':
    until=time.monotonic()+2
    while not (output/'naming-processes.json').exists() and time.monotonic()<until:time.sleep(.01)
    sys.exit(7)
time.sleep(60)
'''


def running(pid):
    try:state=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[0]
    except FileNotFoundError:return False
    # An orphaned zombie has terminated; reaping belongs to the init process.
    return state not in ('Z','X')


class SupervisorTests(unittest.TestCase):
    def test_contract_read_is_already_guarded_and_failure_publishes_no_verdict(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);output=root/'report-output';self.fixture(root,'timeout')
            original=Path.read_text
            def slow_contract(path,*args,**kwargs):
                if path==root/'contract.json':
                    self.assertGreater(signal.getitimer(signal.ITIMER_REAL)[0],0)
                    time.sleep(2)
                return original(path,*args,**kwargs)
            with patch.object(c,'HERE',root),patch.object(supervise,'PHASE_SECONDS',.05),patch.object(Path,'read_text',slow_contract):
                with self.assertRaisesRegex(RuntimeError,'phase incomplete'):
                    supervise.main('report',root,output,root)
            failure=json.loads((output/'failure.json').read_text())
            self.assertEqual(failure['phase'],'preflight');self.assertEqual(failure['exception'],'WholeJobTimeout')
            self.assertFalse(json.loads((output/'results.json').read_text())['complete'])
            self.assertIn('no verdict',(output/'REPORT.md').read_text())
            self.assertEqual(json.loads((output/'supervisor.json').read_text())['returncodes'],[])

    def test_existing_report_is_archived_then_replaced_by_no_verdict(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);output=root/'report-output';output.mkdir()
            c.write(output/'results.json',{'complete':True});(output/'REPORT.md').write_text('old successful report')
            with patch.object(c,'HERE',root):
                with self.assertRaisesRegex(RuntimeError,'phase incomplete'):
                    supervise.main('report',root,output,root)
            self.assertFalse(json.loads((output/'results.json').read_text())['complete'])
            self.assertIn('no verdict',(output/'REPORT.md').read_text())
            self.assertEqual(len(list(output.glob('previous-*/REPORT.md'))),1)

    def fixture(self,root,mode):
        contract={'limits':{'production_seconds':1,'report_seconds':1,'cleanup_seconds':2,
                  'address_space_bytes':8*1024**3,'arm_cores':{'R':[6],'naming':[7]}}}
        c.write(root/'contract.json',contract)
        (root/'run.py').write_text(STUB);(root/'report.py').write_text(STUB)
        (root/'stub-mode').write_text(mode)
        return contract

    def assert_groups_terminated(self,output):
        records=[json.loads((output/f'{cohort}-processes.json').read_text()) for cohort in ('R','naming')]
        self.assertEqual(len({r['group'] for r in records}),2)
        for r in records:self.assertEqual(r['group'],r['worker'])
        pids=[r[k] for r in records for k in ('worker','child')]
        until=time.monotonic()+1
        while any(running(pid) for pid in pids) and time.monotonic()<until:time.sleep(.01)
        self.assertFalse([pid for pid in pids if running(pid)])

    def emergency_cleanup(self,output):
        # A broken cleanup regression must not leave the invented sleepers live.
        for path in output.glob('*-processes.json'):
            try:os.killpg(json.loads(path.read_text())['group'],signal.SIGKILL)
            except ProcessLookupError:pass

    def test_report_timeout_kills_workers_and_descendants(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);output=root/'report-output';run=root/'invented-run';run.mkdir()
            self.fixture(root,'timeout')
            try:
                with patch.object(c,'HERE',root),patch.object(c,'check_contract'),patch.object(supervise,'PHASE_SECONDS',1),patch.object(supervise,'CLEANUP_SECONDS',2):
                    with self.assertRaisesRegex(RuntimeError,'phase incomplete'):
                        supervise.main('report',root,output,run)
                self.assert_groups_terminated(output)
                failure=json.loads((output/'failure.json').read_text())
                self.assertEqual(failure['exception'],'WholeJobTimeout')
                self.assertEqual(failure['phase'],'workers')
                self.assertFalse(failure['partial_witnesses_promoted'])
                receipt=json.loads((output/'supervisor.json').read_text())
                self.assertFalse(receipt['complete'])
                self.assertEqual(receipt['returncodes'],[-signal.SIGKILL,-signal.SIGKILL])
                self.assertFalse(json.loads((output/'results.json').read_text())['complete'])
                self.assertIn('no verdict',(output/'REPORT.md').read_text())
            finally:self.emergency_cleanup(output)

    def test_worker_failure_retains_partial_but_report_accepts_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);output=root/'production-output';replay=root/'report-output'
            self.fixture(root,'failure')
            try:
                with patch.object(c,'HERE',root),patch.object(c,'check_contract'),patch.object(supervise,'PHASE_SECONDS',1),patch.object(supervise,'CLEANUP_SECONDS',2):
                    with self.assertRaisesRegex(RuntimeError,'phase incomplete'):
                        supervise.main('production',root,output)
                    self.assert_groups_terminated(output)
                    self.assertTrue((output/'R/results.json').exists())
                    self.assertTrue((output/'naming/results.json').exists())
                    self.assertFalse((output/'results.json').exists())
                    failure=json.loads((output/'failure.json').read_text())
                    self.assertEqual(failure['exception'],'RuntimeError')
                    self.assertFalse(failure['partial_witnesses_promoted'])
                    receipt=json.loads((output/'supervisor.json').read_text())
                    self.assertEqual(receipt['returncodes'],[7,-signal.SIGKILL])
                    with self.assertRaisesRegex(RuntimeError,'phase incomplete'):
                        supervise.main('report',root,replay,output)
                self.assertFalse(json.loads((replay/'results.json').read_text())['complete'])
                self.assertIn('no verdict',(replay/'REPORT.md').read_text())
                self.assertEqual(json.loads((replay/'supervisor.json').read_text())['returncodes'],[])
            finally:self.emergency_cleanup(output)


if __name__=='__main__':unittest.main()
