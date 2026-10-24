"""Invented-only two-file loading, authority, recurrence and pipeline checks."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch
import binding as b
import coverage as kernel
import production
import report
import run
import make_contract

LIT=Path(__file__).resolve().parent.parent


def fixture(root):
    public=root/'public';here=public/'support-coverage-floor-v1';here.mkdir(parents=True)
    work=root/'invented';work.mkdir();out=root/'out';out.mkdir();replay=root/'replay';replay.mkdir()
    ids=list(range(300));cohorts={};private={};sourcehashes={};arms={};old={};inputs={}
    alphabet=[chr(i) for i in range(32,127)]+['\n'];pool=sorted(alphabet)
    for cohort in ('R','naming'):
        texts={str(i):'aa' if i<297 else 'a'+'bcd'[i-297] for i in ids}
        banned=set(texts.values());paths={'sources':cohort+'/fit-sources.json','pool':cohort+'/pool.json'}
        (work/cohort).mkdir()
        for key,value in (('sources',texts),('pool',pool)):
            b.write(work/paths[key],value);private[paths[key]]=b.sha(work/paths[key])
        sourcehashes[cohort]={pid:hashlib.sha256(t.encode()).hexdigest() for pid,t in texts.items()}
        proof=kernel.production(texts,pool,banned);cohorts[cohort]=paths
        rows=[]
        for k in range(257):
            num=100-40*k
            rows.append({'k':k,'charge':40*k,'numerator':num,'integer_lower_bound':-(-num//10),
                         'one_owner_slots':min(k,3),'shared_slots':min(256-min(k,3),1)})
        arms[cohort]={'cohort':cohort,'complete':True,'validation_loaded':False,
            'fit_problems':300,'old_pool_entries':len(pool),'old_occurrences':proof['occurrences'],
            'source_identity_sha256':b.digest(sourcehashes[cohort]),'banned_set_sha256':b.digest(sorted(banned)),
            'old_occurrence_order_sha256':proof['occurrence_sha256'],'class_counts':{'1':3,'2':1},
            'geometry':{'source_characters':600},'path_numerator':100,'denominator':10,'rows':rows,'largest_positive_k':2,
            'all257_independently_replayed':True,'old_certificate_independently_replayed':True,'suffix_potential_proof_checked':True}
        old[cohort]={'pool_entries':len(pool),'occurrences':proof['occurrences']}
        inputs[cohort]={'texts':texts,'pool':pool,'banned':banned,'source_hashes':sourcehashes[cohort]}
    parent={'active':True,'population':'fixed300_fit_only','fit_ids':ids,'old_arms':old,'cohorts':cohorts,
            'source_hashes':sourcehashes,'private_files':private}
    folder=public/'recorded50';folder.mkdir();b.write(folder/'contract.json',parent);ph=b.sha(folder/'contract.json')
    for a in arms.values():a['contract_sha256']=ph
    evidence={'schema':'gamma.potential-lift.report.v1','complete':True,'contract_sha256':ph,'validation_loaded':False,
              'validation_or_cases_opened':False,'verdicts':{'all257_replayed':True,'k0_preserves_old_bound':True},'arms':list(arms.values())}
    b.write(folder/'results.json',evidence)
    c={'schema':'gamma.support-coverage-floor.contract.v1','active':True,'population':'fixed300_fit_only',
       'fit_ids':ids,'limits':copy.deepcopy(b.LIMITS),'cohorts':cohorts,'private_files':private,'source_hashes':sourcehashes,
       'parent50_contract':{'path':'recorded50/contract.json','sha256':ph},
       'parent50_evidence':{'path':'recorded50/results.json','sha256':b.sha(folder/'results.json')},'parent50_arms':arms,
       'python_bin':str(Path(sys.executable).absolute()),'python_version':b.platform.python_version(),
       'code_hashes':{},'runtime_files':{}}
    for cohort,data in inputs.items():
        paths=cohorts[cohort];data['bindings']={'source_sha256':private[paths['sources']],'pool_sha256':private[paths['pool']],
            'source_identity_sha256':b.digest(data['source_hashes']),'banned_set_sha256':b.digest(sorted(data['banned'])),
            'banned_entries':len(data['banned']),'parent50_evidence_sha256':c['parent50_evidence']['sha256']}
    b.write(here/'contract.json',c)
    return types.SimpleNamespace(here=here,public=public,work=work,out=out,replay=replay,c=c,inputs=inputs)


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.f=fixture(self.root)
        self.patches=[patch.object(b,'HERE',self.f.here),patch.object(b,'LIT',self.f.public),patch.object(report,'HERE',self.f.here),
          patch.dict(os.environ,{'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}),
          patch.object(run.resource,'setrlimit'),patch.object(run.os,'sched_setaffinity')]
        for p in self.patches:p.start()
        self.original_module=report.module
        self.modules=patch.object(report,'module',side_effect=self.loadmodule);self.modules.start()
    def tearDown(self):
        self.modules.stop()
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()
    def loadmodule(self,name,path):
        if path.name=='binding.py':return b
        if path.name=='coverage.py':return kernel
        return self.original_module(name,LIT/'potential-lift-certificate-v1/independent.py')
    def parse(self,texts,deadline):return set(texts.values())
    def production(self):
        with patch.object(b,'parse_bans',side_effect=self.parse):
            for cohort in b.COHORTS:run.arm(cohort,self.f.work,self.f.out,time.monotonic()+30)
        ch=b.sha(self.f.here/'contract.json');arms=[b.read(self.f.out/a/'results.json') for a in b.COHORTS]
        b.write(self.f.out/'results.json',{'complete':True,'validation_loaded':False,'contract_sha256':ch,'seconds':1.,'arms':arms})
        b.write(self.f.out/'supervisor.json',{'complete':True,'phase':'production','contract_sha256':ch,'elapsed':1.1,
                                          'cleanup_seconds':.01,'returncodes':[0,0]})
    def report(self):
        with patch.object(b,'parse_bans',side_effect=self.parse):
            for cohort in b.COHORTS:report.worker(cohort,self.f.work,self.f.out,self.f.replay,time.monotonic()+30)
        return report.combine(self.f.out,self.f.replay,self.f.c,10.,[0,0])

    def test_exact_two_files_per_cohort_and_no_other_private_read(self):
        original=b.checked_bytes
        for cohort in b.COHORTS:
            with patch.object(b,'checked_bytes',wraps=original) as opened,patch.object(b,'parse_bans',side_effect=self.parse):
                loaded=b.load_inputs(self.f.c,self.f.work,cohort,time.monotonic()+10)
            self.assertEqual(opened.call_count,2)
            self.assertEqual({c.args[2] for c in opened.call_args_list},set(self.f.c['cohorts'][cohort].values()))
            self.assertEqual(set(loaded),{'texts','pool','banned','source_hashes','bindings'})
            self.assertEqual(loaded,self.f.inputs[cohort])

    def test_inactive_parent_drift_source_pool_and_bans_rejected(self):
        c=copy.deepcopy(self.f.c);c['active']=False
        with patch.object(b,'checked_bytes') as opened:
            with self.assertRaises(AssertionError):b.load_inputs(c,self.f.work,'R',time.monotonic()+10)
            opened.assert_not_called()
        for relative in self.f.c['cohorts']['R'].values():
            path=self.f.work/relative;saved=path.read_bytes();path.write_bytes(b'corrupt')
            with self.assertRaises(AssertionError):b.load_inputs(self.f.c,self.f.work,'R',time.monotonic()+10)
            path.write_bytes(saved)
        with patch.object(b,'parse_bans',return_value={'wrong'}):
            with self.assertRaises(AssertionError):b.load_inputs(self.f.c,self.f.work,'R',time.monotonic()+10)
        (self.f.public/'recorded50/results.json').write_text('{}')
        with patch.object(b,'checked_bytes') as opened:
            with self.assertRaises(AssertionError):b.load_inputs(self.f.c,self.f.work,'R',time.monotonic()+10)
            opened.assert_not_called()

    def test_activation_exactness_and_no_free_input_authority(self):
        c=copy.deepcopy(self.f.c);c['active']=False
        activated=make_contract.activate(c,copy.deepcopy(c));self.assertTrue(activated['active'])
        d=copy.deepcopy(c);d['private_files']['q.npy']='0'*64
        with self.assertRaises(AssertionError):make_contract.activate(c,d)
        with self.assertRaises(AssertionError):b.accepted_parent(d)

    def test_actual_workers_complete_report_sanitization_and_predictions(self):
        self.production();result=self.report();report.publish(self.f.replay,result)
        self.assertEqual(result['predictions'],{'P1':True,'P2':True})
        for a in result['arms']:
            self.assertEqual(set(a),report.ARM_FIELDS)
            self.assertEqual(a['coverage_floor'],3);self.assertEqual(a['private_character_floor'],3)
            self.assertEqual(a['coverable_sources'],297)
            self.assertEqual(a['positive_budgets_below_floor'],[0,1,2]);self.assertEqual(a['positive_budgets_not_ruled_out'],[])
        encoded=json.dumps(result)
        for token in ('"texts"','"pool"','"source_success"','"shared_entry_ids"','"prefix_reachable"','"aa"','"ab"'):
            self.assertNotIn(token,encoded)
        saved=b.read(self.f.replay/'R.json')
        for key,value in [('coverage_floor',False),('coverage_floor',2),('shared_entries',99),
                          ('independent_suffix_sha256','0'*64),('report_peak_rss_kib',0),('source_text','secret')]:
            corrupt=copy.deepcopy(saved);corrupt[key]=value;b.write(self.f.replay/'R.json',corrupt)
            with self.assertRaises(AssertionError):report.combine(self.f.out,self.f.replay,self.f.c,10.,[0,0])
        b.write(self.f.replay/'R.json',saved)
        checked=b.read(self.f.replay/'R-proof.json');checked['suffix_reachable']['0'][1]=False
        b.write(self.f.replay/'R-proof.json',checked)
        with self.assertRaises(AssertionError):report.combine(self.f.out,self.f.replay,self.f.c,10.,[0,0])

    def test_failed_production_precedes_any_private_input(self):
        self.production();sup=b.read(self.f.out/'supervisor.json');sup['returncodes']=[False,0];b.write(self.f.out/'supervisor.json',sup)
        with patch.object(b,'load_inputs') as opened:
            with self.assertRaises(AssertionError):report.worker('R',self.f.work,self.f.out,self.f.replay,time.monotonic()+20)
            opened.assert_not_called()
        self.assertFalse((self.f.replay/'R.json').exists())

    def test_owner_order_source_flags_and_intermediate_vectors_corruptions(self):
        self.production();raw=b.read(self.f.out/'R/results.json');inputs=self.f.inputs['R'];expected=self.f.c['parent50_arms']['R']
        for mutate in (lambda p:p['owner_classes'].__setitem__(0,2),lambda p:p.update(occurrence_sha256='0'*64),
                       lambda p:p['source_success'].update({'0':False}),lambda p:p['prefix_reachable']['0'].__setitem__(1,False),
                       lambda p:p['private_character_source_ids'].pop()):
            changed=copy.deepcopy(raw);mutate(changed['proof'])
            with self.assertRaises(AssertionError):report.replay('R',inputs,changed,kernel,expected)
        good=kernel.replay(inputs['texts'],inputs['pool'],inputs['banned'])
        bad=copy.deepcopy(good);bad['suffix_reachable']['0'][1]=False
        checker=types.SimpleNamespace(replay=lambda *a:bad)
        with self.assertRaises(AssertionError):report.replay('R',inputs,raw,checker,expected)
        missing=copy.deepcopy(inputs);missing['pool'].remove(' ')
        with self.assertRaises(AssertionError):report.replay('R',missing,raw,kernel,expected)
        with self.assertRaises(AssertionError):production.execute(missing,expected)

    def test_floor_zero_does_not_claim_feasibility(self):
        texts={'0':'ab','1':'ba'};pool=['a','b'];proof=kernel.production(texts,pool,{'ab','ba'})
        expected=copy.deepcopy(self.f.c['parent50_arms']['R']);expected['geometry']['source_characters']=4
        result=report.summary(proof,expected)
        self.assertEqual(result['coverage_floor'],0);self.assertEqual(result['positive_budgets_not_ruled_out'],[0,1,2])
        self.assertTrue(result['positive_bound_remaining'])

    def test_bounded_failure_unlink_and_expired_owner_alarm(self):
        previous=signal.signal(signal.SIGALRM,run.expired)
        try:
            with patch.object(Path,'unlink',side_effect=lambda **k:time.sleep(.2)),patch.object(b,'write') as write:
                with self.assertRaises(run.HardDeadline):run.withdraw_worker(self.f.out,{},time.monotonic()+.02)
                write.assert_not_called()
        finally:signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,previous)
        class Foreign(BaseException):pass
        previous=signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(Foreign()))
        try:
            with patch.object(report,'markdown',side_effect=lambda *a:time.sleep(.2)),patch.object(Path,'unlink') as unlink:
                signal.setitimer(signal.ITIMER_REAL,.02)
                with self.assertRaises(Foreign):report.publish(self.f.replay,{'complete':True})
                unlink.assert_not_called()
            with patch.object(Path,'write_text') as write,patch.object(Path,'unlink') as unlink:
                with self.assertRaises(report.HardDeadline):report.withdraw(self.f.replay,RuntimeError(),deadline=time.monotonic()-.01)
                write.assert_not_called();unlink.assert_not_called()
        finally:signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,previous)


if __name__=='__main__':unittest.main()
