"""Focused invented supervision and real process-group cleanup checks."""
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch
import binding as b
import supervise as s


class Process:
    pid = 999999999
    returncode = 0
    def poll(self): return self.returncode


class SupervisorTests(unittest.TestCase):
    def test_existing_accepted_report_is_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);out=root/'out';out.mkdir()
            sentinels={'results.json':'{"complete":true}', 'REPORT.md':'accepted prior report', 'supervisor.json':'accepted receipt'}
            for name,text in sentinels.items():(out/name).write_text(text)
            with patch.object(s.os,'sched_setaffinity'),patch.object(s.resource,'setrlimit'):
                with self.assertRaises(RuntimeError):s.main('report',root,out,root/'parent')
            self.assertEqual({p.name:p.read_text() for p in out.iterdir()},sentinels)

    def test_actual_worker_child_grandchild_group_cleanup(self):
        child = ('import subprocess,sys,time; '
                 'p=subprocess.Popen([sys.executable,"-c","import time;time.sleep(60)"]); '
                 'print(p.pid,flush=True);time.sleep(60)')
        parent = ('import subprocess,sys,time; p=subprocess.Popen([sys.executable,"-c",'+repr(child)+']); '
                  'print(p.pid,flush=True);time.sleep(60)')
        proc = subprocess.Popen([sys.executable, '-c', parent], stdout=subprocess.PIPE,
                                text=True, start_new_session=True)
        descendants = []
        try:
            for _ in range(2):
                self.assertTrue(select.select([proc.stdout], [], [], 3)[0])
                descendants.append(int(proc.stdout.readline()))
            signal.signal(signal.SIGALRM, s.expired)
            elapsed = s.stop([proc], 3)
            signal.setitimer(signal.ITIMER_REAL, 0)
            self.assertLess(elapsed, 3); self.assertIsNotNone(proc.returncode)
            for pid in descendants:
                stat = Path(f'/proc/{pid}/stat')
                if stat.exists(): self.assertIn(stat.read_text().split()[2], ('Z', 'X'))
        finally:
            try: os.killpg(proc.pid, 9)
            except ProcessLookupError: pass
            proc.wait(timeout=3); proc.stdout.close()

    def invoke(self, root, phase='production', failure=None):
        out = root/'out'; (root/'contract.json').write_text('{}')
        original = b.write
        def spawn(command, **kwargs):
            self.assertIs(kwargs['start_new_session'], True)
            cohort = command[command.index('--cohort')+1]
            if phase == 'production':
                folder = out/cohort; folder.mkdir()
                original(folder/'results.json', {'cohort': cohort, 'complete': True, 'validation_loaded': False,
                       'contract_sha256': b.sha(root/'contract.json'), 'seconds': 0, 'peak_rss_kib': 1})
            return Process()
        def write(path, value):
            if failure == 'receipt' and path.name == 'failure.json': raise OSError('failure receipt rejected')
            original(path, value)
            if failure in ('publication', 'receipt') and path == out/'results.json':
                raise OSError('post-publication failure')
        with patch.object(b, 'HERE', root), patch.object(b, 'check_contract'), patch.object(b, 'write', side_effect=write), \
             patch.object(s.os, 'sched_setaffinity'), patch.object(s.resource, 'setrlimit'), \
             patch.object(s.subprocess, 'Popen', side_effect=spawn), patch.object(s, 'stop', return_value=0):
            s.main(phase, root, out, root/'parent')
        return out

    def test_success_after_cleanup_integer_exit_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            out = self.invoke(Path(d))
            receipt = json.loads((out/'supervisor.json').read_text())
            self.assertEqual(receipt['returncodes'], [0, 0]); self.assertTrue(receipt['complete'])

    def test_post_publication_and_failure_receipt_errors_withdraw_success(self):
        for failure in ('publication', 'receipt'):
            with tempfile.TemporaryDirectory() as d:
                root = Path(d)
                with self.assertRaises(RuntimeError): self.invoke(root, failure=failure)
                self.assertFalse((root/'out/results.json').exists())
                self.assertFalse(json.loads((root/'out/supervisor.json').read_text())['complete'])

    def test_withdraw_survives_broken_report_withdrawal(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)
            for name in ('results.json', 'REPORT.md'): (path/name).write_text('stale success')
            module = types.SimpleNamespace(withdraw=lambda *args, **kwargs: (_ for _ in ()).throw(OSError()))
            signal.signal(signal.SIGALRM, s.expired)
            try: s.withdraw(path, 'report', 'error', module, deadline=time.monotonic()+1)
            finally: signal.setitimer(signal.ITIMER_REAL, 0)
            self.assertFalse((path/'results.json').exists()); self.assertFalse((path/'REPORT.md').exists())

    def test_report_withdraw_receives_same_absolute_deadline_and_propagates(self):
        with tempfile.TemporaryDirectory() as d:
            deadline=time.monotonic()+1
            callback=unittest.mock.Mock(side_effect=s.HardDeadline('report failure write'))
            module=types.SimpleNamespace(withdraw=callback)
            signal.signal(signal.SIGALRM,s.expired)
            try:
                with patch.object(b,'write') as write:
                    with self.assertRaises(s.HardDeadline):
                        s.publish_failure(Path(d),'report',{}, {},module,deadline)
                    callback.assert_called_once_with(Path(d),'supervisor_failure',deadline=deadline)
                    write.assert_not_called()
            finally:signal.setitimer(signal.ITIMER_REAL,0)

    def test_slow_failure_write_deadline_stops_later_writes(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d)
            for name in ('results.json', 'REPORT.md', 'supervisor.json'):
                (output/name).write_text('stale success')
            begun = []
            def slow_write(path, value):
                begun.append(path.name)
                time.sleep(.3)
            signal.signal(signal.SIGALRM, s.expired)
            try:
                with patch.object(b, 'write', side_effect=slow_write):
                    with self.assertRaises(s.HardDeadline):
                        s.publish_failure(output, 'production', {}, {}, None, time.monotonic()+.03)
                self.assertEqual(begun, ['failure.json'])
                self.assertTrue(all(not (output/name).exists() for name in
                                    ('results.json', 'REPORT.md', 'supervisor.json')))
            finally: signal.setitimer(signal.ITIMER_REAL, 0)

    def test_stop_hard_deadline_propagates_without_next_operation(self):
        for during in ('kill', 'wait'):
            first, second = unittest.mock.Mock(pid=123), unittest.mock.Mock(pid=456)
            signal.signal(signal.SIGALRM, s.expired)
            try:
                with patch.object(s.os, 'killpg') as kill:
                    if during == 'kill': kill.side_effect = s.HardDeadline()
                    else: first.wait.side_effect = s.HardDeadline()
                    with self.assertRaises(s.HardDeadline): s.stop([first, second], .5)
                    if during == 'kill':
                        self.assertEqual(kill.call_count, 1); first.wait.assert_not_called()
                    second.wait.assert_not_called()
            finally: signal.setitimer(signal.ITIMER_REAL, 0)

    def test_expired_cleanup_budget_cannot_be_rearmed(self):
        with patch.object(s.signal, 'setitimer') as timer:
            with self.assertRaises(s.HardDeadline): s.arm(time.monotonic()-.01)
            timer.assert_not_called()

    def test_cleanup_exception_blocks_publication(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root/'contract.json').write_text('{}')
            with patch.object(b, 'HERE', root), patch.object(b, 'check_contract', side_effect=ValueError()), \
                 patch.object(s.os, 'sched_setaffinity'), patch.object(s.resource, 'setrlimit'), \
                 patch.object(s, 'stop', side_effect=OSError('cleanup')):
                with self.assertRaises(RuntimeError): s.main('production', root, root/'out')
            self.assertFalse((root/'out/results.json').exists())
            self.assertEqual(json.loads((root/'out/failure.json').read_text())['phase'], 'cleanup')


if __name__ == '__main__': unittest.main()
