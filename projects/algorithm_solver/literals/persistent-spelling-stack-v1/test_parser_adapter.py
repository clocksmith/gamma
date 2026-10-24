"""Invented requests, unchanged46 traces, deadline and receipt failure checks."""
import copy
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch
import common as c
import engine
import parser_adapter as a

TEXT='function solve(a){return a+a}'
MENU={'names':['aa','ab'],'contexts':[{'pattern':['return ',None,'+',None,'']}, {'pattern':['return ',None,'+',None,'']}]}
def untimed(value):
    value=copy.deepcopy(value);value.pop('seconds',None);return value

class AdapterTests(unittest.TestCase):
    def config(self):return {'parser':{'implementation_sha256':a.implementation(),'limits':dict(a.LIMITS)}}
    def session(self,path,deadline=None):return a.Session('fit',deadline or time.monotonic()+30,path,self.config())
    def test_scalar_order_duplicate_failure_and_restoration(self):
        original=c.p.banned
        texts={'10':TEXT,'2':TEXT,'2:'+('a'*64):'const solve=(a)=>a+1;'}
        expected=original(texts)
        with tempfile.TemporaryDirectory() as folder,patch.object(a.resource,'getrlimit',return_value=(8*1024**3,)*2):
            path=Path(folder)/'receipt.json'
            with self.session(path) as service:
                pid=service.client.process.pid
                self.assertEqual(c.p.banned(texts),expected)
                self.assertEqual(c.p.banned(texts),expected)
                self.assertEqual(service.client.process.pid,pid)
            self.assertIs(c.p.banned,original)
            r=c.read(path);self.assertTrue(r['complete']);self.assertEqual(r['requests_completed'],2)
            self.assertEqual(r['worker_process_group'],r['service_process_group'])
            self.assertEqual(r['worker_core_affinity'],r['service_core_affinity'])
            self.assertGreater(r['service_peak_rss_kib_observed'],0)
            self.assertGreater(r['response_bytes_total'],0);self.assertIsNotNone(r['returncode'])
            for text in ['function solve(',TEXT+'/*é*/','function solve(){}']:
                with self.assertRaises(subprocess.CalledProcessError):original({'0':text})
                with self.assertRaises(subprocess.CalledProcessError):
                    with self.session(path) as service:c.p.banned({'0':text})
                self.assertIs(c.p.banned,original);r=c.read(path)
                self.assertFalse(r['complete']);self.assertTrue(r['closed'])
                self.assertEqual(r['failed_requests'],1);self.assertEqual(r['error_type'],'CalledProcessError')
    def test_complete_trace_and_pending_collision_match_old_helpers(self):
        sources={'10':TEXT,'2':TEXT};vocab=list(reversed(c.p.ALPHABET))+['aa']
        old_menu=engine.menu(sources,vocab);old=engine.apply(sources,vocab,MENU)
        oldpartial=[]
        with self.assertRaises(c.LegalityFailure):engine.apply(sources,vocab+['return aa+aa'],MENU,checkpoint=oldpartial.append)
        original=c.p.banned
        with tempfile.TemporaryDirectory() as folder,patch.object(a.resource,'getrlimit',return_value=(8*1024**3,)*2):
            path=Path(folder)/'receipt.json'
            with self.session(path):
                self.assertEqual(engine.menu(sources,vocab),old_menu)
                self.assertEqual(untimed(engine.apply(sources,vocab,MENU)),untimed(old))
            newpartial=[]
            with self.assertRaises(c.LegalityFailure):
                with self.session(path):engine.apply(sources,vocab+['return aa+aa'],MENU,checkpoint=newpartial.append)
            self.assertEqual([untimed(v) for v in newpartial],[untimed(v) for v in oldpartial])
            self.assertFalse(c.read(path)['complete']);self.assertIs(c.p.banned,original)
    def test_expired_never_spawns_or_changes_authority(self):
        original=c.p.banned
        with tempfile.TemporaryDirectory() as folder,patch.object(a.prior,'Client') as client:
            with self.assertRaises(c.HardDeadline):
                with self.session(Path(folder)/'r.json',time.monotonic()-1):pass
            client.assert_not_called();self.assertIs(c.p.banned,original)
    def test_new_envelope_failure_never_restarts(self):
        original=c.p.banned
        with tempfile.TemporaryDirectory() as folder,patch.object(a.resource,'getrlimit',return_value=(8*1024**3,)*2):
            path=Path(folder)/'r.json'
            with self.assertRaises(subprocess.CalledProcessError):
                with self.session(path) as service:service.client.request({'x'*a.LIMITS['request_bytes']:TEXT})
            self.assertIs(c.p.banned,original);r=c.read(path)
            self.assertFalse(r['complete']);self.assertTrue(r['closed']);self.assertEqual(r['requests_attempted'],1)
    def test_receipt_write_failure_restores_and_closes(self):
        original=c.p.banned
        with tempfile.TemporaryDirectory() as folder,patch.object(a.resource,'getrlimit',return_value=(8*1024**3,)*2):
            with self.assertRaises(OSError):
                with patch.object(c,'write',side_effect=OSError('invented')):
                    with self.session(Path(folder)/'r.json') as service:c.p.banned({'0':TEXT})
            self.assertIs(c.p.banned,original);self.assertTrue(service.client.closed)
    def test_slow_failure_receipt_stops_and_propagates_same_budget(self):
        original=c.p.banned
        with tempfile.TemporaryDirectory() as folder,patch.object(a.resource,'getrlimit',return_value=(8*1024**3,)*2):
            path=Path(folder)/'r.json';error=ValueError('invented')
            bound=time.monotonic()+.1;error._gamma54_failure_deadline=bound
            with patch.object(c,'write',side_effect=lambda *_:time.sleep(1)) as write:
                with self.assertRaises(c.HardDeadline) as raised:
                    with self.session(path) as service:raise error
                self.assertEqual(write.call_count,1)
                self.assertEqual(raised.exception._gamma54_failure_deadline,bound)
                self.assertEqual(c.failure_deadline(raised.exception,time.monotonic()+1800),bound)
            self.assertTrue(service.client.closed);self.assertIsNotNone(service.client.process.returncode)
            self.assertIs(c.p.banned,original);self.assertFalse(path.exists())

    def test_request_absolute_deadline_has_no_refresh(self):
        original=c.p.banned
        with tempfile.TemporaryDirectory() as folder,patch.object(a.resource,'getrlimit',return_value=(8*1024**3,)*2):
            path=Path(folder)/'r.json'
            with self.assertRaises(c.HardDeadline):
                with self.session(path) as service:
                    service.deadline=time.monotonic()-1;c.p.banned({'0':TEXT})
            self.assertIs(c.p.banned,original);r=c.read(path)
            self.assertFalse(r['complete']);self.assertTrue(r['closed']);self.assertEqual(r['failed_requests'],1)

if __name__=='__main__':unittest.main()
