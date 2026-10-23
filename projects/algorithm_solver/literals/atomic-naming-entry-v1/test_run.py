"""Only invented sources and metadata. Never imports or opens private corpus input."""
import copy
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import core as c
import engine
import proof
import run
import make_contract


def fixture(root):
    source=root/'parent';work=root/'work';out=root/'run';texts,_,vocab,_=proof.fixture()
    fit={pid:text for pid,text in texts.items() if int(pid)<6}
    c.write(source/'fit/D11/fit-sources.json',fit);c.write(source/'artifacts/D11/sources.json',texts)
    c.write(source/'artifacts/D10/dictionary.json',vocab);c.write(source/'artifacts/D11/dictionary.json',vocab)
    c.write(source/'fit/D11/dictionary.json',vocab);c.write(source/'results.json',{'synthetic':True})
    c.write(source/'supervisor-receipt.json',{'complete':True})
    c.write(work/'population500/manifest.json',{'rows':[{'id':int(pid)} for pid in texts]})
    known={f'{pid}:{c.sha(text.encode())}':{'passed':True,'reused':True,'receipt':{'passed':True},'source_arm':'invented','source_policy':'shortest_min_char'} for pid,text in texts.items()}
    cfg={'active':True,'source_run':str(source),'work':str(work),'python_bin':sys.executable,'python_version':platform.python_version(),
         'partition':{'dev_fit':list(range(6)),'dev_val':[6,7]},
         'source_qualification':{pid:{'source_sha256':c.sha(text.encode()),'passed':True} for pid,text in texts.items()},
         'initial_dictionary':{'path':'artifacts/D10/dictionary.json','sha256':run.hashfile(source/'artifacts/D10/dictionary.json'),
                               'binary_sha256':c.sha(c.analyze.dictionary_bytes(vocab)),'entries':256,'character_entries':96},
         'source_carrier':{'private_files':{str(path.relative_to(source)):run.hashfile(path) for path in source.rglob('*.json') if 'D10' not in str(path)}},
         'code_hashes':{},'runtime_files':{},'cores':[[next(iter(os.sched_getaffinity(0)))]]*4,
         'limits':{'address_space_bytes':8589934592,'worker_seconds':20},'search':{'trials':1,'seconds':10},
         'known_receipts':known,'qualification':[{'id':int(pid),'files':{}} for pid in texts],
         'manifest_sha256':run.hashfile(work/'population500/manifest.json'),'decoder_dependency_bytes':13010}
    return source,work,out,cfg


class RunTests(unittest.TestCase):
    def test_activation_only_changes_flag_and_rejects_drift(self):
        pending={'active':False,'source':'opaque','budget':10,'code_hashes':{'script':'digest'}}
        active=make_contract.activate(copy.deepcopy(pending),pending)
        self.assertTrue(active.pop('active'));self.assertEqual(active,{k:v for k,v in pending.items() if k!='active'})
        self.assertFalse(pending['active'])
        for field,value in (('source','different'),('budget',11),('code_hashes',{'script':'changed'})):
            current=copy.deepcopy(pending);current[field]=value
            with self.assertRaises(AssertionError):make_contract.activate(current,pending)

    def test_inactive_runner_never_hashes_private_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'unused'
            with patch.object(c,'read',return_value={'active':False}),patch.object(run,'hashfile') as hasher:
                with self.assertRaisesRegex(AssertionError,'Inactive'):run.main(Path(tmp),out)
            hasher.assert_not_called();self.assertFalse(out.exists())

    def test_full_synthetic_pipeline_seals_before_validation_and_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            source,work,out,cfg=fixture(Path(tmp));realread=c.read;realhash=run.hashfile;seen=[]
            def read(path):
                path=Path(path)
                if path==run.HERE/'contract.json':return copy.deepcopy(cfg)
                if path==source/'artifacts/D11/sources.json':
                    self.assertTrue((out/'all-fit-sealed.json').exists());seen.append('validation')
                if path==work/'population500/manifest.json':
                    self.assertTrue((out/'all-validation-sealed.json').exists());seen.append('cases')
                return realread(path)
            def hashfile(path):
                path=Path(path)
                if path==run.HERE/'contract.json':return 'synthetic-contract'
                if path==source/'artifacts/D11/sources.json':self.assertTrue((out/'all-fit-sealed.json').exists())
                if path==work/'population500/manifest.json':self.assertTrue((out/'all-validation-sealed.json').exists())
                return realhash(path)
            with patch.object(c,'names',return_value=['aa']),patch.object(c,'read',side_effect=read),patch.object(run,'hashfile',side_effect=hashfile),patch.object(run,'limit'),patch.object(run.resource,'setrlimit'),patch.object(run,'parallel',side_effect=lambda fn,jobs:[fn(j) for j in jobs]),patch.dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'):
                run.main(source,out)
            self.assertIn('validation',seen);self.assertIn('cases',seen)
            self.assertTrue(realread(out/'status.json')['complete'])
            result=realread(out/'results.json');self.assertEqual(result['decoded_packets'],80)
            self.assertEqual(len(result['arms']),10);self.assertEqual(result['fresh_qualification_summary']['distinct_new_sources'],0)
            for arm in result['arms']:
                self.assertEqual(arm['fit']['qualified'],6);self.assertEqual(arm['validation']['qualified'],2)
                for row in arm['per_problem'].values():self.assertEqual(row['one_program_package_with_decoder_dependencies']-row['one_program_package_bytes'],13010)
            for arm in engine.ARMS:
                run.verify_seal(out/'fit'/arm,'fit-seal.json');run.verify_seal(out/'fit'/arm,'validation-seal.json')

    def test_worker_failure_keeps_partial_and_failure_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            source,work,out,cfg=fixture(Path(tmp));out.mkdir()
            def broken(*args,**kwargs):
                args[-1]({'complete':False,'trace':[{'trial':1}],'ledger':{'variants':{'invented':'text'}}})
                raise c.HardDeadline('invented worker deadline')
            with patch.object(run,'limit'),patch.object(engine,'optimize',side_effect=broken):
                with self.assertRaises(c.HardDeadline):run.fit_job(('J',str(out),cfg,cfg['cores'][0]))
            folder=out/'fit/J';self.assertFalse(c.read(folder/'failure.json')['promotion_allowed'])
            self.assertEqual(c.read(folder/'partial.json')['trace'],[{'trial':1}]);self.assertFalse((folder/'fit-seal.json').exists())

    def test_validation_parser_failure_keeps_new_encounter(self):
        texts={'0':'function solve(a){return a+1;}'};ledger=c.BanLedger();ledger.encounter(texts,'fit:initial')
        snapshots=[]
        altered={'0':'function solve(a){return a+2;}'}
        with patch.object(c,'banned',side_effect=RuntimeError('invented parser failure')):
            with self.assertRaises(RuntimeError):engine.validation(altered,c.ALPHABET,['aa'],[],ledger.receipt(),'S',snapshots.append)
        self.assertFalse(snapshots[-1]['complete'])
        self.assertIn('0:'+c.sha(altered['0'].encode()),snapshots[-1]['ledger']['variants'])

    def test_worker_alarm_covers_setup_and_finalization(self):
        script="import run,time,os;run.limit({'active':True,'limits':{'address_space_bytes':8589934592,'worker_seconds':1}},list(os.sched_getaffinity(0)))\ntry: time.sleep(3)\nexcept Exception: print('deadline swallowed')"
        got=subprocess.run([sys.executable,'-B','-c',script],cwd=run.HERE,capture_output=True,text=True,timeout=8)
        self.assertNotEqual(got.returncode,0);self.assertIn('Hard worker deadline',got.stderr);self.assertNotIn('deadline swallowed',got.stdout)

    def test_reject_optimized_python(self):
        got=subprocess.run([sys.executable,'-O','-B','-c','import core'],cwd=run.HERE,capture_output=True,text=True,timeout=8)
        self.assertNotEqual(got.returncode,0);self.assertIn('assertions required',got.stderr)
        got=subprocess.run([sys.executable,'-O','-B','make_contract.py','--activate'],cwd=run.HERE,capture_output=True,text=True,timeout=8)
        self.assertNotEqual(got.returncode,0);self.assertIn('assertions required for activation',got.stderr)

if __name__=='__main__':unittest.main()
