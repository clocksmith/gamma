"""Invented workers and injected finalization faults; no private inputs."""
from contextlib import ExitStack
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

import common as c
import report
import supervise


class PublicationGuardTests(unittest.TestCase):
    def exercise(self, phase='report', fault=None):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);output=root/'out';run=root/'run';run.mkdir()
            c.write(run/'results.json',{'complete':True})
            seconds=.15 if fault=='publication_timeout' else 5
            cleanup_seconds=.05 if fault=='cleanup_timeout' else 1
            c.write(root/'contract.json',{'limits':{'production_seconds':seconds,'report_seconds':seconds,
                'cleanup_seconds':cleanup_seconds,'address_space_bytes':8*1024**3,'arm_cores':{'R':[4],'naming':[5]}}})
            original_write=c.write;original_open=Path.open;closed=[];publications=[];handles=[]
            class Log:
                def __init__(self,handle,name):self.handle=handle;self.name=name
                def close(self):
                    self.handle.close();closed.append(self.name)
                    if fault=='cleanup_timeout':time.sleep(1)
                    if fault=='log_close' and self.name=='R.log':raise OSError('invented close fault')
            def open_log(path,*args,**kwargs):
                handle=original_open(path,*args,**kwargs)
                if path.suffix=='.log':handles.append(handle)
                return Log(handle,path.name) if path.suffix=='.log' else handle
            class Process:
                pid=99999999;returncode=0
                def poll(self):return 0
            def spawn(command,**kwargs):
                cohort=command[command.index('--cohort')+1]
                target=output/cohort/'results.json' if phase=='production' else output/(cohort+'.json')
                target.parent.mkdir(parents=True,exist_ok=True)
                original_write(target,{'complete':True,'validation_loaded':False})
                return Process()
            def write(path,value):
                if fault=='receipt' and path.name=='supervisor.json':raise OSError('invented receipt fault')
                if fault=='failure_receipt' and path.name in ('failure.json','supervisor.json'):raise OSError('invented receipt fault')
                original_write(path,value)
            def publish(value,path):
                publications.append(value['complete'])
                original_write(path/'results.json',value)
                (path/'REPORT.md').write_text('success' if value['complete'] else 'no verdict')
                if value['complete'] and fault in ('publication','failure_receipt','failure_publisher'):
                    raise OSError('invented publication fault')
                if not value['complete'] and fault=='failure_publisher':raise OSError('invented failure publisher fault')
                if value['complete'] and fault=='publication_timeout':time.sleep(1)
            def cleanup(*args):
                if fault=='cleanup':raise OSError('invented cleanup fault')
                return 0
            with ExitStack() as stack:
                for target,name,value in [(c,'HERE',root),(c,'check_contract',lambda *_:None),
                        (supervise,'PHASE_SECONDS',seconds),(supervise,'CLEANUP_SECONDS',cleanup_seconds),
                        (supervise.subprocess,'Popen',spawn),(supervise,'stop',cleanup),
                        (c,'write',write),(Path,'open',open_log),
                        (report,'combine',lambda *args:{'complete':True}), (report,'publish',publish)]:
                    stack.enter_context(patch.object(target,name,value))
                if fault:
                    with self.assertRaisesRegex(RuntimeError,'phase incomplete'):
                        supervise.main(phase,root,output,run)
                else:supervise.main(phase,root,output,run)
            # Test-owned handles may remain unflushed after an exhausted cap;
            # close them outside the measured supervisor, using raw handles.
            for handle in handles:handle.close()
            self.assertEqual(closed,['R.log'] if fault=='cleanup_timeout' else ['R.log','naming.log'])
            if fault:
                for name in ('results.json','supervisor.json'):
                    if (output/name).exists():self.assertFalse(json.loads((output/name).read_text())['complete'])
                if (output/'REPORT.md').exists():self.assertIn('no verdict',(output/'REPORT.md').read_text())
                if fault in ('log_close','cleanup','cleanup_timeout','receipt'):self.assertNotIn(True,publications)
            else:
                self.assertTrue(json.loads((output/'results.json').read_text())['complete'])
                self.assertTrue(json.loads((output/'supervisor.json').read_text())['complete'])

    def test_log_close_failure_still_closes_second_log_and_never_publishes_success(self):self.exercise(fault='log_close')
    def test_cleanup_failure_never_publishes_success(self):self.exercise(fault='cleanup')
    def test_cleanup_timeout_does_not_start_another_unguarded_close(self):self.exercise(fault='cleanup_timeout')
    def test_receipt_failure_withdraws_report(self):self.exercise(fault='receipt')
    def test_failure_receipt_error_cannot_bypass_withdrawal(self):self.exercise(fault='failure_receipt')
    def test_partial_publication_is_withdrawn(self):self.exercise(fault='publication')
    def test_broken_failure_publisher_removes_stale_success(self):self.exercise(fault='failure_publisher')
    def test_publication_remains_inside_whole_job_deadline(self):self.exercise(fault='publication_timeout')
    def test_production_receipt_failure_leaves_no_accepted_result(self):self.exercise(phase='production',fault='receipt')
    def test_success(self):self.exercise()

    def test_cleanup_attempts_all_groups_and_waits_after_an_error(self):
        calls=[]
        class Process:
            def __init__(self,pid):self.pid=pid
            def wait(self,timeout):calls.append(('wait',self.pid))
        def kill(pid,sig):
            calls.append(('kill',pid))
            if pid==1:raise OSError('invented group fault')
        with patch.object(supervise.os,'killpg',kill):
            with self.assertRaises(OSError):supervise.stop([Process(1),Process(2)],1)
        self.assertEqual(calls,[('kill',1),('kill',2),('wait',1),('wait',2)])


if __name__=='__main__':unittest.main()
