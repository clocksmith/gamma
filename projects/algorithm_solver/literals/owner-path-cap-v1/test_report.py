"""Invented public authorities and exact reporter corruption checks only."""
import copy
import importlib.util
import json
from pathlib import Path
import signal
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import caps
import independent
import report

LIT=Path(__file__).resolve().parent.parent


def fixture(root):
    # Reuse invented fixture construction, not historical corpus artifacts.
    with patch.dict(sys.modules,{'report':report.prior,'tighten':caps.parent,'independent':independent}):
        spec=importlib.util.spec_from_file_location('fixture53_for57',LIT/'potential-tightening-v1/test_report.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        f=module.fixture(root)
    i=f.inputs
    proof=report.shaped(caps.check(i['texts'],i['banned'],i['pool'],i['q'],i['seed'],i['alphabet'],i['denominator'],
        expected_source_hashes=i['source_hashes'],expected_old_banned=i['banned'],expected_old_certificate=i['parent_certificate']))
    checked=report.shaped(independent.check(i['texts'],i['banned'],i['pool'],i['q'],i['seed'],i['alphabet'],i['denominator'],
        expected_source_hashes=i['source_hashes'],expected_old_banned=i['banned'],expected_old_certificate=i['parent_certificate'],
        expected_prefix_schedule=proof['owner_prefix_schedule']))
    report.write(root/'parent53-contract.json',{'invented':True});parent_hash=report.sha(root/'parent53-contract.json')
    arms=[]
    for old in f.production['arms']:
        a=report.prior.sanitize(old['cohort'],i,old,checked['base'],i['geometry'])
        a['contract_sha256']=parent_hash;arms.append(a)
    r={'schema':'gamma.potential-tightening.report.v1','complete':True,'contract_sha256':parent_hash,
       'validation_loaded':False,'validation_or_cases_opened':False,'predictions':{'P1':True},'arms':arms}
    report.write(root/'parent53.json',r)
    report.write(root/'feasibility59.json',{'complete':True,'capacity':256,'fit_id_set_sha256':report.digest(list(range(300))),
        'public_files':{},'arms':[{'cohort':a['cohort'],'minimum_feasible_one_owner_budget':3,
        'nonempty_at_most_budget_range':[3,256],'source_identity_sha256':a['source_identity_sha256']} for a in arms]})
    f.config.update(parent53_arms={a['cohort']:a for a in arms},
        parent53_contract={'path':root.name+'/parent53-contract.json','sha256':parent_hash},
        parent53_evidence={'path':root.name+'/parent53.json','sha256':report.sha(root/'parent53.json')},
        feasibility59={'path':root.name+'/feasibility59.json','sha256':report.sha(root/'feasibility59.json')})
    report.write(root/'contract.json',f.config);f.contract_hash=report.sha(root/'contract.json')
    for a in f.production['arms']:
        a.update(schema='gamma.owner-path-cap.arm.v1',proof=copy.deepcopy(proof),contract_sha256=f.contract_hash)
        report.write(f.run/a['cohort']/'results.json',a)
    for obj,name in [(f.production,'results.json'),(f.supervisor,'supervisor.json')]:
        obj['contract_sha256']=f.contract_hash;report.write(f.run/name,obj)
    return f


class ReporterTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.f=fixture(self.root)
        self.loads=[]
        binding=SimpleNamespace(check_contract=lambda c:None,load_inputs=self.load)
        self.patches=[patch.object(report,'HERE',self.root),patch.object(report,'module',side_effect=lambda n,p:binding if p.name=='binding.py' else independent),
            patch.object(report.resource,'setrlimit'),patch.object(report.os,'sched_setaffinity')]
        for p in self.patches:p.start()
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()
    def load(self,c,w,cohort,deadline):self.loads.append(cohort);return copy.deepcopy(self.f.inputs)
    def worker(self,cohort):return report.worker(cohort,self.root/'no-private',self.f.run,self.f.output,time.monotonic()+60)
    def test_complete_replay_combine_and_sanitization(self):
        for cohort in report.COHORTS:self.worker(cohort)
        result=report.combine(self.f.run,self.f.output,self.f.config,20.,[0,0]);report.publish(self.f.output,result)
        self.assertTrue(result['predictions']['P1']);self.assertEqual(self.loads,['R','naming'])
        for a in result['arms']:
            self.assertEqual(set(a),report.ARM_FIELDS);self.assertEqual(len(a['rows']),257)
            self.assertEqual(a['report_work']['production_forward_positions_checked'],900)
        for field in ('"owner_caps"','"owner_top_entries"','"owner_prefix_schedule"','"owner_suffix_schedule"','"path_numerators"','"aaa"','"q"'):
            self.assertNotIn(field,json.dumps(result))
        saved=report.read(self.f.output/'R.json')
        for field,value in [('owner_caps_sha256','0'*64),('report_peak_rss_kib',0),('report_worker_seconds',float('nan')),
                            ('minimum_feasible_one_owner_budget',2),('source_text','bad'),('baseline53_proof_sha256','0'*64)]:
            bad=copy.deepcopy(saved);bad[field]=value
            if field=='report_worker_seconds':
                (self.f.output/'R.json').write_text(json.dumps(bad))
            else:report.write(self.f.output/'R.json',bad)
            with self.assertRaises((AssertionError,ValueError)):report.combine(self.f.run,self.f.output,self.f.config,20.,[0,0])
            report.write(self.f.output/'R.json',saved)
    def test_forward_intermediate_recurrence_corruption_even_with_rehashed_commitment(self):
        raw=copy.deepcopy(self.f.production['arms'][0]);p=raw['proof'];pid='299'
        p['owner_prefix_schedule'][pid][1]+=1
        p['digests']['owner_prefix_schedule_sha256']=report.digest(p['owner_prefix_schedule'])
        with self.assertRaises(AssertionError):
            report.replay('R',self.f.inputs,raw,independent,self.f.config['old_arms']['R'],self.f.config['parent50_arms']['R'],
                          self.f.config['parent53_arms']['R'],self.f.output/'bad.json')
    def test_proof_top_allocation_parent_and_receipt_corruption(self):
        raw=self.f.production['arms'][0]
        mutations=[lambda p:p['owner_caps'].__setitem__('299',False),lambda p:p['base']['tightened']['rows'][0].update(charge=p['base']['tightened']['rows'][0]['charge']+1),
                   lambda p:p['rows'][0].update(integer_lower_bound=999),lambda p:p['deltas_vs53'][0].update(charge_reduction=7),
                   lambda p:p['owner_top_entries']['299'][0].__setitem__(0,999)]
        for mutate in mutations:
            bad=copy.deepcopy(raw);mutate(bad['proof'])
            with self.assertRaises(AssertionError):report.owner_shape(bad['proof'],bad['full_shape'])
        self.f.config['parent53_arms']['R']['paired_digests']['tightened_top_entries_sha256']='0'*64
        with self.assertRaises(AssertionError):report.parents(self.f.config)
    def test_failed_production_before_any_original_input(self):
        self.f.supervisor['returncodes']=[False,0];report.write(self.f.run/'supervisor.json',self.f.supervisor)
        with self.assertRaises(AssertionError):self.worker('R')
        self.assertEqual(self.loads,[]);self.assertFalse((self.f.output/'R.json').exists())
    def test_private_checked_receipt_dominates_public_success(self):
        for cohort in report.COHORTS:self.worker(cohort)
        p=self.f.output/'R-proof.json';value=report.read(p);value['owner_suffix_schedule']['299'][0]+=1;report.write(p,value)
        with self.assertRaises(AssertionError):report.combine(self.f.run,self.f.output,self.f.config,20.,[0,0])
    def test_publication_failure_and_expired_deadline(self):
        folder=self.f.output;report.write(folder/'results.json',{'complete':True})
        (folder/'REPORT.md').write_text('stale')
        with patch.object(report,'markdown',side_effect=OSError('serialize')):
            with self.assertRaises(OSError):report.publish(folder,{'complete':True})
        self.assertFalse((folder/'results.json').exists());self.assertFalse((folder/'REPORT.md').exists())
        with patch.object(Path,'unlink') as unlink:
            with self.assertRaises(report.HardDeadline):report.withdraw(folder,'bad',deadline=time.monotonic()-1)
            unlink.assert_not_called()

if __name__=='__main__':unittest.main()
