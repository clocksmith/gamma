"""Invented six-view pipeline; tests access barriers without private corpus reads."""
import copy
import os
from pathlib import Path
import platform
import tempfile
import time
import signal
import subprocess
import json
import parser_adapter
import unittest
from unittest.mock import patch
import common as c
import engine
import run


def fixture(root):
    work=root/'work';out=root/'run'
    texts={str(i):f'function solve(a){{return a+a+{i}}}' for i in range(3)}
    fit={p:t for p,t in texts.items() if int(p)<2};vocab=list(reversed(c.p.ALPHABET))+['aa']
    c.write(work/'fit.json',fit);c.write(work/'all.json',texts)
    dictionaries={}
    for anchor in c.ANCHORS:
        path=anchor+'/dictionary.json';c.write(work/path,vocab)
        dictionaries[anchor]={'path':path,'sha256':c.hashfile(work/path),'binary_sha256':c.sha(c.analyze.dictionary_bytes(vocab)),
                             'entries':len(vocab),'character_entries':96,'parent_seal':anchor+'/fit-seal.json'}
        c.write(work/dictionaries[anchor]['parent_seal'],{'dictionary_sha256':dictionaries[anchor]['sha256'],'validation_loaded':False})
    known={}
    for pid,text in texts.items():
        for source in (text,text.replace('(a)','(aa)').replace('a+a','aa+aa')):
            known[f'{pid}:{c.sha(source.encode())}']={'passed':True,'reused':True,'receipt':{'passed':True},'source_arm':'invented','source_policy':'shortest_min_char'}
    c.write(work/'population500/manifest.json',{'rows':[{'id':int(p)} for p in texts]})
    config={'active':True,'source_bound':True,'work':str(work),'python_bin':os.sys.executable,'python_version':platform.python_version(),
            'partition':{'dev_fit':[0,1],'dev_val':[2]},'sources':{k:{'path':p,'sha256':c.hashfile(work/p)} for k,p in [('fit','fit.json'),('all','all.json')]},
            'dictionaries':dictionaries,'source_qualification':{p:{'source_sha256':c.sha(t.encode()),'passed':True} for p,t in texts.items()},
            'known_receipts':known,'manifest_sha256':c.hashfile(work/'population500/manifest.json'),
            'qualification':[{'id':int(p),'files':{}} for p in texts],'code_hashes':{},'runtime_files':{},
            'all_cores':[0,1,2,3],'arm_cores':{'24':[0],'43N':[1],'43W':[2]},'proposal_cap':153600,
            'limits':{'overall_seconds':3600,'worker_seconds':1800,'qualification_seconds':900,'address_space_bytes':8*1024**3},
            'decoder_dependency_bytes':13010}
    config['parser']={'implementation_sha256':parser_adapter.implementation(),'limits':parser_adapter.LIMITS}
    return work,out,config


class RunTests(unittest.TestCase):
    def setUp(self):
        run.STARTED=time.monotonic()

    def test_full_six_view_pipeline_orders_every_boundary(self):
        with tempfile.TemporaryDirectory() as folder:
            work,out,config=fixture(Path(folder));read=c.read;hashfile=c.hashfile;seen=[]
            def checked(path):
                path=Path(path)
                if path==work/'all.json':
                    self.assertTrue((out/'all-fit-sealed.json').exists());seen.append('validation')
                if path==work/'population500/manifest.json':
                    self.assertTrue((out/'all-validation-sealed.json').exists())
                    self.assertTrue(read(out/'global-ledger.json')['legal']);seen.append('cases')
            def reading(path):
                if Path(path)==c.HERE/'contract.json':return copy.deepcopy(config)
                checked(path);return read(path)
            def hashing(path):
                if Path(path)==c.HERE/'contract.json':return 'invented-contract'
                checked(path);return hashfile(path)
            with patch.object(c,'read',side_effect=reading),patch.object(c,'hashfile',side_effect=hashing),patch.object(run,'limit'),\
                 patch.object(run.resource,'setrlimit'),patch.object(run.os,'sched_setaffinity'),\
                 patch.object(parser_adapter.resource,'getrlimit',return_value=(8*1024**3,)*2),\
                 patch.object(run,'parallel',side_effect=lambda jobs:[run.worker(j) for j in jobs]),\
                 patch.dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'):
                got=run.main(out)
            self.assertIn('validation',seen);self.assertIn('cases',seen)
            self.assertTrue(got['complete']);self.assertEqual(got['decoded_packets'],36);self.assertEqual(len(got['arms']),12)
            self.assertEqual(got['fresh_qualification_summary']['distinct_new_sources'],0)
            for arm in got['arms']:
                self.assertEqual(arm['fit']['qualified'],2);self.assertEqual(arm['validation']['qualified'],1)
                self.assertEqual(read(out/'artifacts'/arm['arm']/'dictionary.json'),list(reversed(c.p.ALPHABET))+['aa'])
            for anchor in c.ANCHORS:
                fit=read(out/'fit'/anchor/'fit.json');val=read(out/'fit'/anchor/'validation.json')
                self.assertEqual(fit['menu']['contexts'],val['contexts']);self.assertGreater(fit['accepted'],0)
                self.assertLessEqual(fit['proposals']+val['proposals'],153600)
                for phase in ('fit','validation'):
                    receipt=read(out/'fit'/anchor/(phase+'-parser.json'))
                    self.assertTrue(receipt['complete']);self.assertTrue(receipt['closed'])
                    self.assertEqual(receipt['requests_attempted'],receipt['requests_completed'])
                    self.assertEqual(receipt['failed_requests'],0)
                    self.assertLess(receipt['finished_monotonic'],fit['anchor_deadline'])
                    self.assertIn(phase+'-parser.json',run.verify_seal(out/'fit'/anchor,phase+'-seal.json')['files'])

    def test_actual_worker_import_binds_service_to_anchor_core_and_group(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);work,out,config=fixture(root)
            c.write(root/'config.json',config)
            script="import json,sys,run;run.worker(('24','fit',sys.argv[2],json.load(open(sys.argv[1]))))"
            process=subprocess.Popen([os.sys.executable,'-B','-c',script,str(root/'config.json'),str(out)],
                cwd=c.HERE,start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            try:
                _,error=process.communicate(timeout=15)
                self.assertEqual(process.returncode,0,error.decode())
                r=c.read(out/'fit/24/fit-parser.json')
                self.assertTrue(r['complete']);self.assertEqual(r['worker_core_affinity'],[0])
                self.assertEqual(r['service_core_affinity'],[0]);self.assertEqual(r['service_process_group'],process.pid)
                self.assertTrue(r['closed']);self.assertIsNotNone(r['returncode'])
                self.assertIn('fit-parser.json',run.verify_seal(out/'fit/24','fit-seal.json')['files'])
            finally:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                process.wait(timeout=2)

    def test_inactive_never_opens_private_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(c,'read',return_value={'active':False}),patch.object(c,'hashfile') as hashing,\
                 patch.object(run.resource,'setrlimit'),patch.object(run.os,'sched_setaffinity'):
                with self.assertRaises(AssertionError):run.main(Path(folder)/'out')
            hashing.assert_not_called()

    def test_expired_validation_deadline_blocks_every_dictionary_read(self):
        with tempfile.TemporaryDirectory() as folder:
            work,out,config=fixture(Path(folder))
            with patch.object(c,'dictionary') as read_dictionary:
                with self.assertRaises(c.HardDeadline):run.worker(('24','validation',str(out),config,0))
            read_dictionary.assert_not_called();self.assertFalse(out.exists())

    def test_worker_slow_failure_write_inherits_parser_bound(self):
        with tempfile.TemporaryDirectory() as folder:
            work,out,config=fixture(Path(folder));write=c.write;bound=[]
            def broken(*args,**kwargs):
                error=ValueError('invented');error._gamma54_failure_deadline=time.monotonic()+.15
                bound.append(error._gamma54_failure_deadline);raise error
            def writing(path,value):
                if Path(path).name=='failure.json':time.sleep(1)
                else:write(path,value)
            with patch.object(engine,'menu',return_value={'names':[],'contexts':[]}),patch.object(engine,'apply',side_effect=broken),patch.object(c,'write',side_effect=writing):
                with self.assertRaises(c.HardDeadline) as raised:run.worker(('24','fit',str(out),config))
            self.assertEqual(raised.exception._gamma54_failure_deadline,bound[0])
            self.assertFalse((out/'fit/24/fit-seal.json').exists())
            self.assertFalse(c.read(out/'fit/24/fit-parser.json')['complete'])
            self.assertLess(time.monotonic()-bound[0],.2)

    def test_production_slow_failure_write_withdraws_result_first(self):
        with tempfile.TemporaryDirectory() as folder:
            work,out,config=fixture(Path(folder));read=c.read;write=c.write;bound=[]
            def reading(path):return copy.deepcopy(config) if Path(path)==c.HERE/'contract.json' else read(path)
            def broken(jobs):
                write(out/'results.json',{'complete':True})
                error=ValueError('invented');error._gamma54_failure_deadline=time.monotonic()+.06
                bound.append(error._gamma54_failure_deadline);raise error
            def writing(path,value):
                if Path(path).name=='failure.json':time.sleep(1)
                else:write(path,value)
            with patch.object(c,'read',side_effect=reading),patch.object(c,'write',side_effect=writing),patch.object(run,'parallel',side_effect=broken),patch.dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'):
                with self.assertRaises(c.HardDeadline) as raised:run.main(out)
            self.assertEqual(raised.exception._gamma54_failure_deadline,bound[0])
            self.assertFalse((out/'results.json').exists());self.assertFalse((out/'status.json').exists())

    def test_failure_receipt_is_bounded_and_cannot_refresh(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder);c.write(out/'results.json',{'complete':True});c.write(out/'status.json',{'complete':True})
            error=ValueError('invented');bound=time.monotonic()+.06;error._gamma54_failure_deadline=bound
            handler=signal.getsignal(signal.SIGALRM)
            try:
                with patch.object(c,'write',side_effect=lambda *_:time.sleep(1)) as write:
                    with self.assertRaises(c.HardDeadline) as raised:
                        run.failure(out,'fit',error,c.failure_deadline(error,time.monotonic()+1800),['results.json','status.json'])
                    self.assertEqual(raised.exception._gamma54_failure_deadline,bound)
                    self.assertEqual(write.call_count,1)
                    with self.assertRaises(c.HardDeadline):run.failure(out,'fit',error,c.failure_deadline(error,time.monotonic()+1800),['results.json'])
                    self.assertEqual(write.call_count,1)
                self.assertFalse((out/'results.json').exists());self.assertFalse((out/'status.json').exists())
            finally:signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,handler)

    def test_global_conflict_blocks_barrier(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)
            for anchor in c.ANCHORS:
                directory=out/'fit'/anchor
                c.write(directory/'fit.json',{'complete':True,'ledger':{'variants':{},'banned':['collision'],'encounters':[],'last_rendered_group':None}})
                run.seal(directory,'fit-seal.json',['fit.json'],validation_loaded=False)
            with self.assertRaises(c.LegalityFailure):run.merge(out,'fit',{'24':['x'],'43N':['collision'],'43W':['y']})
            self.assertFalse(c.read(out/'global-fit-ledger.json')['legal'])
            self.assertFalse((out/'all-fit-sealed.json').exists())

if __name__=='__main__':unittest.main()
