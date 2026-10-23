"""Invented-only independent replay and fail-closed corruption checks."""
import copy
import json
import os
from pathlib import Path
import random
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import core as c
import engine
import metrics
import proof
import qualification
import report
import run
import test_run
import test_qualification


class ReportTests(unittest.TestCase):
    def test_independent_dp_and_scalar_accounting(self):
        rng=random.Random(41)
        for _ in range(60):
            vocab=c.order(['a','b']+[''.join(rng.choice('ab') for _ in range(rng.randint(2,5))) for _ in range(7)])
            text=''.join(rng.choice('ab') for _ in range(rng.randint(1,18)))
            for policy in report.POLICIES:self.assertEqual(report.encode(text,vocab,policy),c.segment.encode(text,vocab,policy))
        with self.assertRaises(ValueError):report.encode('abc',['a','b'])
        self.assertEqual(report.distribution([1,4,6,8]),c.analyze.distribution([1,4,6,8]))
        rows={'0':{'encodable':True,'selections':4,'actions':5,'single_characters':2,'source_bytes':7,'packet_bytes':45,'qualified_source':True},
              '1':{'encodable':False,'source_bytes':8,'qualified_source':True}}
        got=report.aggregate(rows,[0,1],100,13010)
        self.assertEqual(got,metrics.aggregate(rows,[0,1],100,13010))
        self.assertFalse(got['coverage_complete']);self.assertIn('covered programs only',got['distribution_scope'])
        arm={'fit':got,'validation':got,'per_problem':rows,'entries':2,'illegal_entry_sha256':[]}
        self.assertFalse(report.gates(arm,arm,{'partition':{'dev_fit':[0,1],'dev_val':[0,1]}})['passed'])

    def test_accepted_fit_and_validation_replay_and_corruption(self):
        texts,_,vocab,_=proof.fixture();limits={'trials':180,'seconds':20}
        with patch.object(c,'names',return_value=['aa']):
            fit=engine.optimize(texts,vocab,['aa'],'J',limits)
            current,ledger,moves=report.replay_fit(fit,texts,vocab,limits)
            self.assertTrue(moves)
            valtexts={'99':'function solve(c){let z=4;return c+c+z;}'}
            val=engine.validation(valtexts,current['vocab'],fit['names'],fit['final_contexts'],fit['ledger'],'J')
            report.replay_validation(val,valtexts,current['vocab'],fit,ledger)
            bad=copy.deepcopy(fit);bad['state']['C']+=1
            with self.assertRaises(AssertionError):report.replay_fit(bad,texts,vocab,limits)
            bad=copy.deepcopy(fit);bad['ledger']['banned'].append('invented missing ban')
            with self.assertRaises(AssertionError):report.replay_fit(bad,texts,vocab,limits)
            bad=copy.deepcopy(fit);bad['round_menus'][0]['groups'][0]['geometry'][0]['spans'][0][0]+=1
            with self.assertRaises(AssertionError):report.replay_fit(bad,texts,vocab,limits)
            bad=copy.deepcopy(fit);bad['seconds']=float('nan')
            with self.assertRaises(AssertionError):report.replay_fit(bad,texts,vocab,limits)

    def test_raw_strict_qualification_rejudge_and_corruption(self):
        c.module('atomic_report_test_raw',c.LIT/'minify-control-v1/minify.py')
        from algsolve.judge import sandbox
        for mode in ('pass','mismatch','timeout'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);source,record,spec=test_qualification.fixture(root)
                c.write(root/'population500/manifest.json',{'rows':[spec]})
                pins={rel:report.hashfile(root/rel) for rel in ('population500/1-tests.json','population500-baseline/qualification/baselines/1.json')}
                cfg={'work':str(root),'manifest_sha256':report.hashfile(root/'population500/manifest.json'),
                     'qualification':[{'id':1,'files':pins}],'limits':{'worker_seconds':20}}
                if mode=='mismatch':record['args_after']=[9]
                stdout=(json.dumps(record)+'\n'+json.dumps({'done':1})+'\n').encode()
                injected=sandbox.SandboxResult(0,None,stdout,b'',.001) if mode!='timeout' else sandbox.SandboxResult(None,None,b'',b'timeout',1.0,timed_out=True)
                rel=Path('raw-qualification')/('1-'+c.sha(source.encode()))/'receipt.json'
                with patch.object(sandbox,'run',return_value=injected):
                    passed,ok,n,bad,digest=qualification.execute(root,1,source,spec,(root/rel).parent)
                fresh={'passed':passed,'checks_passed':ok,'cases':n,'reused':False,'raw_receipt':str(rel),'raw_receipt_sha256':digest}
                with patch.object(sandbox,'run',side_effect=AssertionError('report must never execute sandbox')):
                    self.assertEqual(report.replay_qualification(root,cfg,'1',source,fresh),(fresh,bad))
                wrong=copy.deepcopy(cfg);wrong['qualification'][0]['files']['population500/1-tests.json']='0'*64
                with self.assertRaises(AssertionError):report.replay_qualification(root,wrong,'1',source,fresh)
                path=(root/rel).parent/'0.stdout';path.write_bytes(path.read_bytes()+b'corrupt')
                with self.assertRaises(AssertionError):report.replay_qualification(root,cfg,'1',source,fresh)

    def test_complete_pipeline_packets_gates_and_failure_dominance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source,work,out,cfg=test_run.fixture(root)
            cfg['limits']['overall_seconds']=60
            cfg['limits']['report_seconds']=60
            texts=c.read(source/'artifacts/D11/sources.json');vocab=c.read(source/'artifacts/D10/dictionary.json')
            parentarms=[]
            for name in ('R','seed13','best24','N','NCP'):
                rows=run.measure(name,texts,vocab,c.banned(texts),root/'reference',cfg,texts)
                for arm in rows:
                    arm['qualification']={p:{'passed':True} for p in texts}
                    for r in arm['per_problem'].values():r['qualified_source']=True
                    for split,key in (('fit','dev_fit'),('validation','dev_val')):
                        arm[split]=metrics.aggregate(arm['per_problem'],cfg['partition'][key],arm['dictionary_bytes'],13010)
                parentarms+=rows
            parent={'arms':parentarms,'private_results_sha256':'invented'};parentpath=root/'parent-public.json';c.write(parentpath,parent)
            cfg['parent_evidence']={'path':str(parentpath),'sha256':report.hashfile(parentpath),'private_results_sha256':'invented'}
            cfg['known_receipts']=report.known_receipts(parent)
            contract=root/'contract.json';c.write(contract,cfg);digest=report.hashfile(contract)
            realread=c.read;realhash=run.hashfile
            def read(path):return copy.deepcopy(cfg) if Path(path)==c.HERE/'contract.json' else realread(path)
            def hashed(path):return digest if Path(path)==c.HERE/'contract.json' else realhash(path)
            with patch.object(c,'names',return_value=['aa']),patch.object(c,'read',side_effect=read),patch.object(run,'hashfile',side_effect=hashed),patch.object(report,'hashfile',side_effect=hashed),patch.object(run,'limit'),patch.object(run.resource,'setrlimit'),patch.object(run,'parallel',side_effect=lambda fn,jobs:[fn(j) for j in jobs]),patch.dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'):
                run.main(source,out)
                c.write(out/'supervisor-receipt.json',{'complete':True,'exit_code':0,'outer_timeout':False,'elapsed':30,'promotion_allowed':True,'log':'invented'})
                evidence=root/'evidence';got=report.publish(out,cfg,evidence)
                self.assertEqual(got['decoded_packets'],80);self.assertTrue(got['independent_replay']);self.assertFalse(got['verdicts']['shortest_min_char']['ready'])
                for text in texts.values():self.assertNotIn(text,(evidence/'results.json').read_text())
                packet=next((out/'artifacts/J/shortest_min_char').glob('*.bin'));raw=packet.read_bytes();packet.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
                with self.assertRaises(AssertionError):report.publish(out,cfg,evidence)
                self.assertFalse(c.read(evidence/'results.json')['complete']);self.assertIn('No verdict',(evidence/'README.md').read_text())
                packet.write_bytes(raw)
                c.write(out/'failure.json',{'complete':False})
                with self.assertRaises(AssertionError):report.publish(out,cfg,evidence)
                self.assertIsNone(c.read(evidence/'results.json')['verdicts'])
                inactive=copy.deepcopy(cfg);inactive['active']=False
                with self.assertRaises(AssertionError):report.publish(out,inactive,evidence)

    def test_post_replay_write_deadline_and_preflight_withdraw_success(self):
        success={'complete':True,'independent_replay':True,'scope':'invented','arms':[],
                 'verdicts':{'shortest_min_char':{'ready':True,'comparisons':{}}},'predictions':{},'replay_scope':'invented'}
        for mode in ('serialization','replacement_deadline','elapsed_deadline','preflight','preflight_deadline'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)/'run';folder.mkdir();output=Path(tmp)/'evidence';output.mkdir()
                c.write(output/'results.json',success);(output/'README.md').write_text('stale successful verdict')
                cfg={'limits':{'report_seconds':1}}
                realwrite=c.write;realreplace=Path.replace;injected=[]
                def write(path,value):
                    if mode=='serialization' and Path(path).parent.name.startswith('.report-stage-') and not injected:
                        injected.append(True);raise OSError('invented post-replay write failure')
                    return realwrite(path,value)
                def replace(path,target):
                    if mode=='replacement_deadline' and path.parent.name.startswith('.report-stage-') and path.name=='results.json' and not injected:
                        self.assertNotIn('stale successful',(output/'README.md').read_text())
                        injected.append(True);raise c.HardDeadline('invented publication deadline')
                    return realreplace(path,target)
                if mode in ('preflight','preflight_deadline'):
                    callbacks=[];timers=[]
                    def read_config(path):
                        self.assertEqual(timers,[900]);self.assertEqual(len(callbacks),1)
                        if mode=='preflight_deadline':callbacks[0](None,None)
                        raise PermissionError('invented contract read failure')
                    with patch.object(c,'read',side_effect=read_config),patch.object(report.signal,'signal',side_effect=lambda sig,fn:callbacks.append(fn)),patch.object(report.signal,'setitimer',side_effect=lambda kind,n:timers.append(n)):
                        with self.assertRaises(c.HardDeadline if mode=='preflight_deadline' else PermissionError):report.main(SimpleNamespace(run=folder,output=output))
                else:
                    with patch.object(report,'replay',return_value=copy.deepcopy(success)),patch.object(c,'write',side_effect=write),patch.object(Path,'replace',replace):
                        if mode=='elapsed_deadline':
                            with patch.object(report.time,'monotonic',side_effect=[0,0,2]):
                                with self.assertRaises(AssertionError):report.publish(folder,cfg,output)
                        else:
                            with self.assertRaises(OSError if mode=='serialization' else c.HardDeadline):report.publish(folder,cfg,output)
                self.assertFalse(c.read(output/'results.json')['complete'])
                self.assertIsNone(c.read(output/'results.json')['verdicts'])
                self.assertIn('No verdict',(output/'README.md').read_text())
                self.assertNotIn('stale successful',(output/'README.md').read_text())
                self.assertFalse(c.read(folder/'report-failure.json')['promotion_allowed'])


if __name__=='__main__':unittest.main()
