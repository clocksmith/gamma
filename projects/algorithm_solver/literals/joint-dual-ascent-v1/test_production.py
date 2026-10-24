"""Finite search controls, independent targets and fail-closed supervision."""
import copy
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import common as c
import production
import report
import run
import supervise
import make_contract


def result(value,gradient):
    return {'joint_family_feasible':True,'numerator':value,'denominator':1000000,
            'joint_path_numerator':value,'top_capacity_numerator':0,'selected_a':2,'assignments':[],
            'gradient':gradient,'endpoint_peak_bytes':32,'phase_seconds':{
              'cardinality_and_unrestricted':0,'all_assignments':0,'dictionary_weights_and_multiplicity':0,'path_recovery_and_gradient':0}}


class ProductionTests(unittest.TestCase):
    def test_fixed_step_zero_retention_and_registered_stops(self):
        self.assertEqual([production.step(1000000,t) for t in range(5)],[250000,125000,125000,125000,83333])
        index=c.p.dual.Index({'0':'abc'},{'abc'});q=c.p.zeros(index.texts);positive=copy.deepcopy(q);positive['0'][0][0]=1
        contract={'denominator':1000000,'search':{'points':3},'limits':{'endpoint_bytes':64*1024**2}}
        saves={}
        def save(name,q,proof):saves[name]=(copy.deepcopy(q),copy.deepcopy(proof))
        with patch.object(c.p,'oracle',side_effect=[result(10,positive),result(8,positive),result(10,positive)]):
            got=production.search(index,contract,10,save)
        self.assertEqual(got['stop'],'point_limit');self.assertEqual(got['best']['iteration'],0)
        self.assertEqual(saves['zero'],saves['best']);self.assertEqual(len(got['trajectory_search_diagnostics']),3)
        arm={**got,'seconds':1};report.verify_trajectory(arm,contract)
        bad=copy.deepcopy(arm);bad['trajectory_search_diagnostics'].pop()
        with self.assertRaises(AssertionError):report.verify_trajectory(bad,contract)
        bad=copy.deepcopy(arm);bad['best']['iteration']=2
        with self.assertRaises(AssertionError):report.verify_trajectory(bad,contract)
        with patch.object(c.p,'oracle',return_value=result(10,q)):
            zero=production.search(index,contract,10,save)
        self.assertEqual(zero['stop'],'zero_supergradient');report.verify_trajectory({**zero,'seconds':1},contract)
        negative=copy.deepcopy(q);negative['0'][0][0]=-1
        with patch.object(c.p,'oracle',return_value=result(10,negative)):
            stopped=production.search(index,contract,10,save)
        self.assertEqual(stopped['stop'],'unchanged_projection');report.verify_trajectory({**stopped,'seconds':1},contract)

    def test_independent_retained_certificate_and_corruptions(self):
        texts={str(i):'abc' for i in range(300)};index=c.p.dual.Index(texts,{'abc'});q=c.p.zeros(texts)
        got=c.p.oracle(index,q,256,1000000);proof=production.proof(got)
        with patch.object(c.p,'oracle',side_effect=AssertionError('No gradient search in report')),patch.object(c.p.assignment,'assignment_proof',side_effect=AssertionError('No assignment solver in report')):
            replay=report.replay_point(index,q,proof,{'denominator':1000000})
            self.assertEqual(replay['numerator'],got['numerator']);self.assertTrue(replay['full_pool_cardinality_and_assignment_replay'])
            for mutate in (
                lambda r:r.__setitem__('numerator',r['numerator']+1),
                lambda r:r.__setitem__('selected_a',32),
                lambda r:r['assignments'].pop(),
                lambda r:r['assignments'][1]['row_potentials'].__setitem__(0,1),
            ):
                bad=copy.deepcopy(proof);mutate(bad)
                with self.assertRaises(AssertionError):report.replay_point(index,q,bad,{'denominator':1000000})

    def test_worker_preflight_clamps_timer_and_withdraws_stale_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);c.write(root/'R.json',{'complete':True});callbacks=[];timers=[]
            def failed_read(path):
                self.assertEqual(timers[0],1200);callbacks[0](None,None)
            with patch.object(c,'read',side_effect=failed_read),patch.object(report.signal,'signal',side_effect=lambda sig,fn:callbacks.append(fn)),patch.object(report.signal,'setitimer',side_effect=lambda kind,value:timers.append(value)):
                with self.assertRaises(c.HardDeadline):report.replay_arm('R',root,root,root,time.monotonic()+999999)
            self.assertFalse((root/'R.json').exists());self.assertTrue((root/'R-failure.json').exists())

    def test_report_publication_and_failure_receipt_io_withdraw(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);c.write(root/'results.json',{'complete':True});(root/'REPORT.md').write_text('stale success')
            # Existing output is refused; even a failed failure.json write must
            # not prevent stale public-success withdrawal.
            with patch.object(c,'write',side_effect=OSError('invented receipt disk failure')):
                with self.assertRaises(OSError):supervise.main('report',root,root,root)
            self.assertFalse(c.read(root/'results.json')['complete']);self.assertIn('No verdict',(root/'REPORT.md').read_text())
            c.write(root/'results.json',{'complete':True});(root/'REPORT.md').write_text('stale success')
            minimal={'complete':True,'arms':[],'predictions':{}}
            with patch.object(c,'write',side_effect=OSError('invented staged serialization failure')):
                with self.assertRaises(OSError):report.publish(minimal,root)
            self.assertFalse(c.read(root/'results.json')['complete']);self.assertIn('No verdict',(root/'REPORT.md').read_text())

    def test_group_cleanup_and_pending_activation(self):
        child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],start_new_session=True)
        try:
            elapsed=supervise.cleanup([child],2);self.assertLess(elapsed,2);self.assertIsNotNone(child.returncode)
        finally:
            if child.poll() is None:child.kill();child.wait()
        pending={'active':False,'code_hashes':{},'runtime_files':{}}
        self.assertEqual(make_contract.activate(pending,copy.deepcopy(pending)),{**pending,'active':True})
        with self.assertRaises(AssertionError):make_contract.activate({**pending,'changed':True},pending)
        with self.assertRaises(AssertionError):c.check({'active':False})


if __name__=='__main__':unittest.main()
