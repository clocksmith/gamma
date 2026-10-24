"""Supervisor fault tests with stub children only; not timing measurements."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import timing as t


def complete_fixture():
    return {'complete':True,'fixture_sha256':t.fixtures.digest(t.fixtures.specification()),
      'blocks':[{'complete':True,'block':b,'semantics':{'invented_test':True},'end_to_end_seconds':1.0}
                for b in t.fixtures.BLOCKS]}


class SupervisorTests(unittest.TestCase):
    def invoke(self,output,script,seconds=2,collector=None):
        command=lambda out,deadline:[sys.executable,'-c',script,str(out)]
        with patch.object(t.pin,'verify',return_value={'synthetic_only':True}),patch.object(t,'command',side_effect=command),patch.object(t,'SECONDS',seconds),patch.object(t,'STARTED',time.monotonic()):
            if collector is None:return t.main(output,'invented-pin')
            with patch.object(t,'collect',return_value=collector):return t.main(output,'invented-pin')

    def assert_failed(self,output):
        for name in ('results.json','supervisor.json'):
            path=output/name
            if path.exists():self.assertIs(json.loads(path.read_text())['complete'],False)
        report=output/'REPORT.md'
        if report.exists():self.assertIn('No accepted timing comparison',report.read_text())

    def assert_dead_child(self,output):
        pid=int((output/'grandchild.pid').read_text())
        with self.assertRaises(ProcessLookupError):os.kill(pid,0)

    def test_timeout_kills_and_reaps_actual_descendant_group(self):
        script='''import subprocess,sys,time,pathlib
p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])
pathlib.Path(sys.argv[1],'grandchild.pid').write_text(str(p.pid))
time.sleep(30)
'''
        with tempfile.TemporaryDirectory() as root:
            output=Path(root)/'out'
            with self.assertRaises(RuntimeError):self.invoke(output,script,seconds=.4)
            self.assert_failed(output);self.assert_dead_child(output)

    def test_worker_failure_kills_orphan_and_retains_failure(self):
        script='''import subprocess,sys,pathlib
p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])
pathlib.Path(sys.argv[1],'grandchild.pid').write_text(str(p.pid))
sys.exit(7)
'''
        with tempfile.TemporaryDirectory() as root:
            output=Path(root)/'out'
            with self.assertRaises(RuntimeError):self.invoke(output,script)
            self.assert_failed(output);self.assert_dead_child(output)

    def test_partial_output_cannot_become_accepted(self):
        script="import pathlib,sys;pathlib.Path(sys.argv[1],'coordinator.json').write_text('{\"complete\":false}')"
        with tempfile.TemporaryDirectory() as root:
            output=Path(root)/'out'
            with self.assertRaises(RuntimeError):self.invoke(output,script)
            self.assert_failed(output)

    def test_deadline_after_success_write_withdraws_both_markers(self):
        write=t.write
        def broken(path,value):
            write(path,value)
            if path.name=='results.json' and value.get('complete'):raise t.Deadline('invented post-write deadline')
        with tempfile.TemporaryDirectory() as root,patch.object(t,'write',side_effect=broken):
            output=Path(root)/'out'
            with self.assertRaises(RuntimeError):self.invoke(output,'pass',collector=complete_fixture())
            self.assert_failed(output)

    def test_failure_io_cannot_preserve_success_or_skip_child_kill(self):
        write=t.write
        def broken(path,value):
            if path.name=='results.json' and value.get('complete'):
                write(path,value);raise OSError('invented publication fault')
            if value.get('complete') is False:raise OSError('invented failure receipt fault')
            write(path,value)
        # Let the initial incomplete receipt succeed, then fail post-worker writes.
        calls=0
        def staged(path,value):
            nonlocal calls
            calls+=1
            if calls==1:return write(path,value)
            return broken(path,value)
        with tempfile.TemporaryDirectory() as root,patch.object(t,'write',side_effect=staged):
            output=Path(root)/'out'
            with self.assertRaises(RuntimeError):self.invoke(output,'pass',collector=complete_fixture())
            self.assert_failed(output)

    def test_failure_publication_deadline_stops_remaining_writes(self):
        write=t.write;attempts=[]
        def slow(path,value):
            attempts.append(path.name)
            if path.name=='failure.json':time.sleep(2)
            write(path,value)
        with tempfile.TemporaryDirectory() as root,patch.object(t,'write',side_effect=slow),patch.object(t,'FAILURE_CLEANUP',.1):
            output=Path(root)/'out';started=time.monotonic()
            with self.assertRaises(RuntimeError):self.invoke(output,'raise SystemExit(1)')
            self.assertLess(time.monotonic()-started,1)
            self.assert_failed(output)
            self.assertEqual(attempts[-1],'failure.json')

    def test_optimized_mode_rejected_without_output(self):
        with tempfile.TemporaryDirectory() as root:
            output=Path(root)/'out'
            result=subprocess.run([sys.executable,'-O',str(t.pin.HERE/'timing.py'),
                                   '--output',str(output),'--pin-sha256','invented'],capture_output=True,timeout=3)
            self.assertNotEqual(result.returncode,0);self.assertFalse(output.exists())


if __name__=='__main__':unittest.main()
