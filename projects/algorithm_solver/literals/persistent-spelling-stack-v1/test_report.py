"""Invented failure-publication checks; no corpus or acceptance run."""
from pathlib import Path
import signal
import tempfile
import time
import unittest
from unittest.mock import patch
import report as r

class ForeignDeadline(BaseException):pass

class PublicationTests(unittest.TestCase):
    def setUp(self):self.handler=signal.getsignal(signal.SIGALRM)
    def tearDown(self):
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,self.handler)
    def test_foreign_deadline_stops_first_failure_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)
            for name in ('results.json','REPORT.md'):(out/name).write_text('old success')
            calls=[]
            def slow(path,*args,**kwargs):
                calls.append(path.name)
                self.assertFalse((out/'results.json').exists())
                self.assertFalse((out/'REPORT.md').exists())
                time.sleep(.3)
            def expired(*_):raise ForeignDeadline()
            signal.signal(signal.SIGALRM,expired)
            signal.setitimer(signal.ITIMER_REAL,.03)
            with patch.object(Path,'write_text',slow):
                with self.assertRaises(ForeignDeadline):r.withdraw(out,ValueError())
            self.assertEqual(calls,['REPORT.md.withdraw.tmp'])
    def test_expired_absolute_budget_starts_no_write(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(Path,'write_text') as write:
            with self.assertRaises(r.c.HardDeadline):r.withdraw(Path(tmp),ValueError(),time.monotonic()-1)
            write.assert_not_called()
    def test_publication_failure_removes_success_without_new_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)
            for name in ('results.json','REPORT.md'):(out/name).write_text('old success')
            with patch.object(r,'replay',side_effect=ForeignDeadline()),patch.object(Path,'write_text') as write:
                with self.assertRaises(ForeignDeadline):r.publish(out/'input',{'limits':{'report_seconds':10}},out)
                write.assert_not_called()
            self.assertFalse((out/'results.json').exists())
            self.assertFalse((out/'REPORT.md').exists())
    def test_unlink_after_phase_deadline_has_one_bounded_emergency(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);calls=[]
            original=Path.unlink
            def expired(*_):raise ForeignDeadline()
            def slow(path,*args,**kwargs):
                calls.append(path.name)
                time.sleep(.3)
            signal.signal(signal.SIGALRM,expired)
            try:
                with patch.object(r,'replay',side_effect=ForeignDeadline()),patch.object(Path,'unlink',slow):
                    with self.assertRaises(ForeignDeadline) as got:
                        r.publish(out/'input',{'limits':{'report_seconds':1}},out,started=time.monotonic()-10.97)
                self.assertEqual(calls,['results.json'])
                self.assertLessEqual(got.exception._gamma_failure_deadline,time.monotonic()+.01)
            finally:signal.setitimer(signal.ITIMER_REAL,0)
    def test_ordinary_first_failure_write_error_cannot_preserve_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)
            for name in ('results.json','REPORT.md'):(out/name).write_text('old success')
            original=Path.write_text
            def fail_first(path,*args,**kwargs):
                if path.name=='REPORT.md.withdraw.tmp':raise OSError('injected')
                return original(path,*args,**kwargs)
            with patch.object(Path,'write_text',fail_first):r.withdraw(out,ValueError())
            self.assertFalse((out/'REPORT.md').exists())
            self.assertFalse(r.c.read(out/'results.json')['complete'])

if __name__=='__main__':unittest.main()
