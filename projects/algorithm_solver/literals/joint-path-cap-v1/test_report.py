"""Invented full-baseline reporting, corruption and private-read gates."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import caps
import independent
import report
import binding as b


def fixture(root):
    # Tests alone create invented predecessor evidence. No saved corpus artifacts.
    with patch.dict(sys.modules,{'report':report.prior,'caps':caps.prior,'independent':independent.parent}):
        module=report.module('joint60_test57',b.LIT/'owner-path-cap-v1/test_report.py')
        f=module.fixture(root)
    i=f.inputs;args=(i['texts'],i['banned'],i['pool'],i['q'],i['seed'],i['alphabet'],i['denominator'])
    kwargs={'expected_source_hashes':i['source_hashes'],'expected_old_banned':i['banned'],'expected_old_certificate':i['parent_certificate']}
    p=report.shaped(caps.check(*args,**kwargs));checked=report.shaped(independent.check(*args,**kwargs,
        expected_base57_prefix_schedule=p['base57']['owner_prefix_schedule'],expected_prefix_schedule=p['all_prefix_schedule']))
    parents=[]
    for raw in f.production['arms']:
        a=report.prior.public_arm(raw['cohort'],raw,checked['base57'],f.config['parent53_arms'][raw['cohort']]);parents.append(a)
    b.write(root/'parent57.json',{'complete':True,'arms':parents});b.write(root/'parent57-contract.json',{'invented':True})
    f.config.update(full_shape={cohort:i['geometry'] for cohort in ('R','naming')},parent57_arms={a['cohort']:a for a in parents},parent57_evidence={'path':str(root/'parent57.json'),'sha256':b.sha(root/'parent57.json')},
        parent57_contract={'path':str(root/'parent57-contract.json'),'sha256':b.sha(root/'parent57-contract.json')})
    b.write(root/'contract.json',f.config);f.contract_hash=b.sha(root/'contract.json')
    for raw in f.production['arms']:
        raw.update(schema='gamma.joint-path-cap.arm.v1',proof=copy.deepcopy(p),contract_sha256=f.contract_hash)
        b.write(f.run/raw['cohort']/'results.json',raw)
    for value,name in ((f.production,'results.json'),(f.supervisor,'supervisor.json')):
        value['contract_sha256']=f.contract_hash;b.write(f.run/name,value)
    return f


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.f=fixture(self.root);self.loads=[]
        def load(*args):self.loads.append(args[2]);return copy.deepcopy(self.f.inputs)
        self.patches=[patch.object(report,'HERE',self.root),patch.object(b,'check_contract'),patch.object(b,'load_inputs',side_effect=load),
            patch.object(report,'module',return_value=independent),patch.object(report.resource,'setrlimit'),patch.object(report.os,'sched_setaffinity')]
        self.patches += [patch.object(b,key) for key in ('verify_parent50','verify_parent53','verify_parent57','verify_feasibility')]
        for p in self.patches:p.start()
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.tmp.cleanup()
    def worker(self,cohort):return report.worker(cohort,self.root/'invented',self.f.run,self.f.output,time.monotonic()+30)

    def test_complete_replay_combine_sanitizer_and_corruptions(self):
        for cohort in report.COHORTS:self.worker(cohort)
        result=report.combine(self.f.run,self.f.output,self.f.config,20,[0,0]);report.publish(self.f.output,result)
        self.assertTrue(result['predictions']['P1']);self.assertEqual(self.loads,['R','naming'])
        for a in result['arms']:
            self.assertEqual(set(a),report.ARM_FIELDS);self.assertEqual(len(a['rows']),257)
            self.assertEqual(a['report_work']['production_forward_positions_checked'],900)
            self.assertEqual(a['baseline57_report_work']['production_forward_positions_checked'],900)
        for field in ('"local_shared_top_entries"','"all_prefix_schedule"','"owner_caps"','"path_numerators"','"aaa"','"q"'):
            self.assertNotIn(field,json.dumps(result))
        saved=b.read(self.f.output/'R.json')
        for key,val in [('minimum_feasible_one_owner_budget',2),('source_text','not allowed'),('report_peak_rss_kib',0)]:
            bad=copy.deepcopy(saved);bad[key]=val;b.write(self.f.output/'R.json',bad)
            with self.assertRaises(AssertionError):report.combine(self.f.run,self.f.output,self.f.config,20,[0,0])
            b.write(self.f.output/'R.json',saved)

    def test_rehashed_forward_recurrence_and_local_weights(self):
        original=self.f.production['arms'][0]
        for which in ('all','owner'):
            raw=copy.deepcopy(original);p=raw['proof'] if which=='all' else raw['proof']['base57']
            key='all_prefix_schedule' if which=='all' else 'owner_prefix_schedule'
            p[key]['299'][1]+=1;p['digests'][key+'_sha256']=report.digest(p[key])
            with self.assertRaises(AssertionError):report.replay('R',self.f.inputs,raw,independent,self.f.config)
        raw=copy.deepcopy(original);raw['proof']['local_shared_top_entries']['0'][0][0]+=1
        with self.assertRaises(AssertionError):report.shape(raw['proof'],raw['full_shape'])

    def test_failed_production_before_read_and_fresh_output(self):
        self.f.supervisor['returncodes']=[False,0];b.write(self.f.run/'supervisor.json',self.f.supervisor)
        with self.assertRaises(AssertionError):self.worker('R')
        self.assertEqual(self.loads,[])
        target=self.f.output/'naming-proof.json';target.write_text('existing authority')
        with self.assertRaises(AssertionError):self.worker('naming')
        self.assertEqual(target.read_text(),'existing authority')

    def test_checked_private_receipt_failure_dominates_public(self):
        for cohort in report.COHORTS:self.worker(cohort)
        path=self.f.output/'R-proof.json';value=b.read(path);value['all_suffix_schedule']['299'][0]+=1;b.write(path,value)
        with self.assertRaises(AssertionError):report.combine(self.f.run,self.f.output,self.f.config,20,[0,0])

    def test_publication_deadline_and_failure(self):
        b.write(self.f.output/'results.json',{'complete':True});(self.f.output/'REPORT.md').write_text('stale')
        with patch.object(report,'markdown',side_effect=OSError('write')):
            with self.assertRaises(OSError):report.publish(self.f.output,{'complete':True})
        self.assertFalse((self.f.output/'results.json').exists())
        with patch.object(Path,'unlink') as unlink:
            with self.assertRaises(report.HardDeadline):report.withdraw(self.f.output,ValueError(),time.monotonic()-1)
            unlink.assert_not_called()


if __name__=='__main__':unittest.main()
