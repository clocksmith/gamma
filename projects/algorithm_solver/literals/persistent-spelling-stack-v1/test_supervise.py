"""Actual invented descendants and final I/O faults, under short test caps."""
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import common as c
import supervise as s

STUB='''import json,os,subprocess,sys,time
from pathlib import Path
out=Path(sys.argv[sys.argv.index('--output')+1]);out.mkdir(parents=True)
mode=Path(__file__).with_name('mode').read_text()
child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])
(out/'processes.json').write_text(json.dumps({'worker':os.getpid(),'child':child.pid,'group':os.getpgrp()}))
(out/'results.json').write_text(json.dumps({'complete':True}))
(out/'REPORT.md').write_text('invented success')
if mode=='failure':sys.exit(7)
if mode=='timeout':time.sleep(30)
'''

def alive(pid):
    try:return Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[0] not in ('Z','X')
    except (FileNotFoundError,ProcessLookupError):return False

class SupervisorTests(unittest.TestCase):
    def setUp(self):s.STARTED=time.monotonic()

    def exercise(self,mode,fault=None,phase='report'):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);out=root/'out';run=root/'parent';run.mkdir()
            c.write(run/'supervisor-receipt.json',{'complete':True})
            cap=.35 if mode=='timeout' or fault=='publication_timeout' else 3
            c.write(root/'contract.json',{'python_bin':sys.executable,'limits':{
                'overall_seconds':cap,'report_seconds':cap,'cleanup_seconds':.1,'address_space_bytes':8*1024**3}})
            (root/'run.py').write_text(STUB);(root/'report.py').write_text(STUB);(root/'mode').write_text(mode)
            actualwrite=c.write;actualopen=Path.open;actualtext=Path.write_text;actualunlink=Path.unlink;close_calls=[]
            class Log:
                def __init__(self,handle):self.handle=handle
                def fileno(self):return self.handle.fileno()
                def close(self):
                    close_calls.append(time.monotonic())
                    self.handle.close()
                    if fault=='log_close':raise OSError('injected')
                    if fault=='cleanup_timeout':time.sleep(1)
            def opening(path,*a,**kw):
                handle=actualopen(path,*a,**kw)
                return Log(handle) if path.name.endswith('-supervisor.log') else handle
            def writing(path,value):
                if fault=='failure_write_timeout' and value.get('complete') is False:
                    if path.name=='failure.json':time.sleep(1)
                    else:raise AssertionError('write attempted after emergency timeout')
                if fault=='receipt' and path.name in ('supervisor-receipt.json','failure.json'):raise OSError('injected')
                if fault=='publication_timeout' and path.name=='supervisor-receipt.json' and value['complete']:time.sleep(1)
                actualwrite(path,value)
                if fault=='result_publication' and path==out/'results.json' and value['complete']:raise OSError('injected')
            def text(path,*a,**kw):
                if fault=='publication' and path.name=='REPORT.md.pending':raise OSError('injected')
                return actualtext(path,*a,**kw)
            def unlink(path,*a,**kw):
                if fault=='unlink_timeout' and path==out/'results.json':time.sleep(1)
                return actualunlink(path,*a,**kw)
            try:
                with patch.object(c,'HERE',root),patch.object(c,'verify_public'),patch.object(s,'CAPS',{'production':cap,'report':cap}),\
                     patch.object(s,'CLEANUP',.1),patch.object(c,'write',side_effect=writing),\
                     patch.object(Path,'open',opening),patch.object(Path,'write_text',text),patch.object(Path,'unlink',unlink):
                    if mode!='success' or fault:
                        started=time.monotonic()
                        with self.assertRaisesRegex(RuntimeError,'no verdict'):s.main(phase,out,run)
                    else:s.main(phase,out,run)
                    if fault=='failure_write_timeout':self.assertLess(time.monotonic()-started,1)
                    if fault=='cleanup_timeout':
                        self.assertEqual(len(close_calls),1)
                        self.assertLess(time.monotonic()-close_calls[0],.18)
                records=out/('worker-report/processes.json' if phase=='report' else 'processes.json')
                info=json.loads(records.read_text());self.assertEqual(info['worker'],info['group'])
                until=time.monotonic()+1
                while any(alive(info[k]) for k in ('worker','child')) and time.monotonic()<until:time.sleep(.01)
                self.assertFalse(any(alive(info[k]) for k in ('worker','child')))
                if mode!='success' or fault:
                    for name in ('results.json','supervisor-receipt.json'):
                        if (out/name).exists():self.assertFalse(json.loads((out/name).read_text())['complete'])
                    if (out/'REPORT.md').exists():self.assertIn('No verdict',(out/'REPORT.md').read_text())
                else:self.assertTrue(c.read(out/'supervisor-receipt.json')['complete'])
            finally:
                for record in out.rglob('processes.json'):
                    try:os.killpg(json.loads(record.read_text())['group'],signal.SIGKILL)
                    except ProcessLookupError:pass

    def test_success_kills_remaining_descendant_before_promotion(self):self.exercise('success')
    def test_timeout_withdraws_partial_worker_success(self):self.exercise('timeout')
    def test_failure_write_timeout_stops_before_next_io(self):self.exercise('failure','failure_write_timeout')
    def test_worker_failure(self):self.exercise('failure',phase='production')
    def test_log_close_failure(self):self.exercise('success','log_close')
    def test_cleanup_deadline(self):self.exercise('success','cleanup_timeout')
    def test_group_killed_before_unlink_can_exhaust_cleanup(self):self.exercise('success','unlink_timeout')
    def test_receipt_failure_cannot_skip_withdrawal(self):self.exercise('success','receipt')
    def test_partial_publication(self):self.exercise('success','publication')
    def test_prose_then_result_failure_withdraws_both(self):self.exercise('success','result_publication')
    def test_publication_deadline(self):self.exercise('success','publication_timeout')
    def test_expired_import_clock_blocks_preflight(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(s,'STARTED',time.monotonic()-4000),patch.object(c,'read') as read:
            with self.assertRaisesRegex(RuntimeError,'no verdict'):s.main('production',Path(folder)/'out')
            read.assert_not_called()

    def test_refused_existing_production_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder);c.write(out/'results.json',{'complete':True})
            with self.assertRaises(RuntimeError):s.main('production',out)
            self.assertTrue(c.read(out/'results.json')['complete'])

if __name__=='__main__':unittest.main()
