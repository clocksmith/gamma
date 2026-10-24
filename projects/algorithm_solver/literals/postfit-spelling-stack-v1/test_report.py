"""Independent replay tests; invented sources and cases only."""
import copy
from pathlib import Path
import tempfile
import unittest
import common as c
import engine
import report as r
TEXT='function solve(a){return a+a}'
MENU={'names':['aa'],'contexts':[{'pattern':['return ',None,'+',None,'']}]}

class ReportTests(unittest.TestCase):
    def test_actual_parent_order_full_id_ties_and_menu_derivation(self):
        vocab=['abc','dxx','ab','cdxx'];self.assertEqual(r.state({'0':'abcdxx'},vocab)['plans']['0'],['abc','dxx'])
        for policy in r.POLICIES:self.assertEqual(r.encode('abcdxx',vocab,policy),[0,1])
        self.assertNotEqual(r.state({'0':'abcdxx'},vocab)['plans'],c.p.evaluate({'0':'abcdxx'},vocab)['plans'])
        texts={'0':TEXT,'1':TEXT.replace('(a)','(b)').replace('a+a','b+b')};words=list(reversed(c.p.ALPHABET))+['aa']
        self.assertEqual(r.derive_menu(texts,words),engine.menu(texts,words))

    def test_every_local_proposal_replay_and_corrupt_geometry_cost_and_omission(self):
        texts={'0':TEXT};vocab=list(reversed(c.p.ALPHABET))+['aa'];dictionaries={'24':vocab}
        got=engine.apply(texts,vocab,MENU,dictionaries=dictionaries);selected,ledger,summary=r.replay_apply(got,texts,vocab,MENU,dictionaries)
        self.assertEqual(summary['accepted_passes'],1);self.assertEqual(summary['source_byte_delta'],3)
        self.assertEqual(r.state(selected,vocab)['N'],r.state(texts,vocab)['N']);self.assertLess(r.state(selected,vocab)['C'],r.state(texts,vocab)['C'])
        for mutate in (lambda x:x['trace'][0]['trials'][0]['score'].__setitem__(0,0),lambda x:x['trace'][0]['trials'][0]['group']['geometry'][0]['spans'].pop(),lambda x:x['trace'][0]['trials'].pop(),lambda x:x['ledger']['banned'].pop()):
            bad=copy.deepcopy(got);mutate(bad)
            with self.assertRaises(AssertionError):r.replay_apply(bad,texts,vocab,MENU,dictionaries)
        union=r.global_union([('24',ledger.receipt())],dictionaries);self.assertEqual(union,c.global_ledger([('24',ledger.receipt())],dictionaries));self.assertTrue(union['legal'])

    def test_uncovered_proposals_and_starting_failures_remain_in_denominator(self):
        vocab=[w for w in c.p.ALPHABET if w!='z'];menu={'names':['zz'],'contexts':MENU['contexts']};texts={'0':TEXT}
        got=engine.apply(texts,vocab,menu);selected,ledger,summary=r.replay_apply(got,texts,vocab,menu,{'24':vocab})
        self.assertEqual(selected,texts);self.assertEqual(summary['coverage_failed_proposals'],1);self.assertEqual(len(ledger.variants),2)
        no_a=[w for w in c.p.ALPHABET if w!='a']+['aa'];got=engine.apply(texts,no_a,MENU);selected,ledger,summary=r.replay_apply(got,texts,no_a,MENU,{'24':no_a})
        self.assertEqual(summary['initial_coverage_failures'],['0']);self.assertEqual(summary['proposals'],0)
        rows={'0':{'encodable':False,'qualified_source':False,'source_bytes':len(TEXT)}};a=r.aggregate(rows,['0'],10,13010)
        self.assertFalse(a['coverage_complete']);self.assertIsNone(a['selections']);self.assertEqual(a['problems'],1);self.assertEqual(a['covered'],0)

    def test_cross_dictionary_bans_retain_rejected_variants(self):
        vocab=c.p.ALPHABET;texts={'0':TEXT};got=engine.apply(texts,vocab,MENU);variant=TEXT.replace('(a)','(aa)').replace('a+a','aa+aa')
        self.assertEqual(got['accepted'],0);self.assertIn(variant,got['ledger']['variants'].values())
        with self.assertRaises(AssertionError):r.replay_apply(got,texts,vocab,MENU,{'24':vocab,'43N':vocab+[variant]})

    def test_both_policy_packets_and_full_charges_under_unsorted_ids(self):
        texts={'0':TEXT,'1':TEXT};vocab=list(reversed(c.p.ALPHABET))+['aa'];selected=engine.apply(texts,vocab,MENU)['selected']
        receipts={f'{pid}:{c.sha(text.encode())}':{'passed':True,'reused':True} for pid,text in selected.items()};config={'decoder_dependency_bytes':13010,'partition':{'dev_fit':[0],'dev_val':[1]}}
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);raw=c.prior('run').measure('24-S',selected,vocab,set(),out,config,texts);folder=out/'artifacts/24-S'
            for old,policy in zip(raw,r.POLICIES):
                rebuilt=r.measured(folder,'24-S',policy,selected,vocab,set(),config,texts,receipts)
                self.assertEqual(rebuilt['dictionary_binary_sha256'],c.sha(c.analyze.dictionary_bytes(vocab)))
                self.assertEqual(rebuilt['validation']['package_with_decoder_dependencies']-rebuilt['validation']['package_bytes'],13010)
                for pid,row in old['per_problem'].items():self.assertEqual({k:v for k,v in rebuilt['per_problem'][pid].items() if k!='qualified_source'},row)
            packet=folder/'canonical/0.bin';packet.write_bytes(packet.read_bytes()[:-1]+b'\x00')
            with self.assertRaises(AssertionError):r.measured(folder,'24-S','canonical',selected,vocab,set(),config,texts,receipts)


class PipelineTests(unittest.TestCase):
    def test_full_six_view_replay_ordered_packets_seals_and_failure_dominance(self):
        import os
        from unittest.mock import patch
        import run
        import test_run
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);work,out,config=test_run.fixture(root)
            config['limits'].update(report_seconds=1800,cleanup_seconds=10)
            config['decoder_dependencies']=[str(c.LIT/'literals.py'),str(c.LIT/'pass2/working/bitpack.py')]
            config['parent_evidence']={a:{'path':'invented','sha256':'invented','arm':a} for a in c.ANCHORS}
            config['standing_reference_evidence']={'path':'invented','sha256':'invented'}
            read=c.read;hashfile=c.hashfile
            def reading(path):return copy.deepcopy(config) if Path(path)==c.HERE/'contract.json' else read(path)
            def hashing(path):return 'invented-contract' if Path(path)==c.HERE/'contract.json' else hashfile(path)
            with patch.object(c,'read',side_effect=reading),patch.object(c,'hashfile',side_effect=hashing),patch.object(run,'limit'),\
                 patch.object(run.resource,'setrlimit'),patch.object(run.os,'sched_setaffinity'),\
                 patch.object(run,'parallel',side_effect=lambda jobs:[run.worker(j) for j in jobs]),\
                 patch.dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'):
                got=run.main(out)
                c.write(out/'supervisor-receipt.json',{'complete':True,'outer_timeout':False,'exit_code':0,'elapsed':got['seconds']+.01})
                refs={(name,policy):next(a for a in got['arms'] if a['arm']=='24-U' and a['policy']==policy)
                      for name in ('R','seed13','best24','N','NCP') for policy in r.POLICIES}
                verified=[];actual_check=r.check_seal
                def seals(folder,name,files,flag):
                    actual_check(folder,name,files,flag);verified.append((Path(folder).name,name))
                def checked_read(base,binding):
                    if binding==config['sources']['all']:
                        self.assertTrue(all((a,'fit-seal.json') in verified for a in r.ANCHORS))
                    path=Path(base)/binding['path'];self.assertEqual(hashing(path),binding['sha256']);return reading(path)
                evidence=root/'evidence'
                with patch.object(r,'public_inputs',return_value=(config['known_receipts'],refs,{})),patch.object(r,'check_seal',side_effect=seals),patch.object(c,'checked_read',side_effect=checked_read):
                    result=r.publish(out,config,evidence)
                    self.assertTrue(result['complete']);self.assertEqual(result['decoded_packets'],36)
                    self.assertIsNone(result['predictions']['P4']);self.assertIsNone(result['selected_successor'])
                    self.assertEqual(set(result['verdicts']),{'24-S','43N-S','43W-S'})
                    for text in read(work/'all.json').values():self.assertNotIn(text,(evidence/'results.json').read_text())
                    self.assertGreater(result['search']['24']['fit']['accepted_passes'],0)
                    self.assertTrue(all((a,'validation-seal.json') in verified for a in r.ANCHORS))
                    packet=out/'artifacts/43N-S/canonical/2.bin';blob=packet.read_bytes();packet.write_bytes(blob[:-1]+bytes([blob[-1]^1]))
                    with self.assertRaises(AssertionError):r.publish(out,config,evidence)
                    self.assertFalse(read(evidence/'results.json')['complete']);self.assertIn('No verdict',(evidence/'REPORT.md').read_text());packet.write_bytes(blob)
                    seal=out/'fit/24/fit-seal.json';prior=seal.read_bytes();bad=read(seal);bad['files']['fit.json']='0'*64;c.write(seal,bad)
                    with self.assertRaises(AssertionError):r.replay(out,config)
                    seal.write_bytes(prior)
                    c.write(out/'failure.json',{'complete':False})
                    with self.assertRaises(AssertionError):r.publish(out,config,evidence)
                    self.assertIsNone(read(evidence/'results.json')['verdicts'])

    def test_raw_qualification_rejudge_failure_and_hash_reuse(self):
        import json
        from unittest.mock import patch
        c.p.module('postfit_qualification_minify',c.LIT/'minify-control-v1/minify.py')
        from algsolve.judge import sandbox
        for mode in ('pass','mismatch','timeout'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp);text='function solve(a){return a+1;}'
                record={'result':2,'result_type':'number','args_before':[1],'args_after':[1],'alias_edges':[],'error':None};spec={'id':1,'transport':'standard'}
                c.write(folder/'population500/1-tests.json',[{'args':[1],'expected':2}])
                c.write(folder/'population500-baseline/qualification/baselines/1.json',[record])
                c.write(folder/'population500/manifest.json',{'rows':[spec]})
                files={rel:c.hashfile(folder/rel) for rel in ('population500/1-tests.json','population500-baseline/qualification/baselines/1.json')}
                config={'work':str(folder),'manifest_sha256':c.hashfile(folder/'population500/manifest.json'),
                        'qualification':[{'id':1,'files':files}],'limits':{'worker_seconds':1800}}
                if mode=='mismatch':record['args_after']=[9]
                stdout=(json.dumps(record)+'\n'+json.dumps({'done':1})+'\n').encode()
                observation=sandbox.SandboxResult(0,None,stdout,b'',.001) if mode!='timeout' else sandbox.SandboxResult(None,None,b'',b'timeout',1.0,timed_out=True)
                key='1:'+c.sha(text.encode());rel=Path('raw-qualification')/key.replace(':','-')/'receipt.json'
                with patch.object(sandbox,'run',return_value=observation):
                    passed,ok,total,bad,digest=c.prior('qualification').execute(folder,1,text,spec,(folder/rel).parent)
                fresh={'passed':passed,'checks_passed':ok,'cases':total,'reused':False,'raw_receipt':str(rel),'raw_receipt_sha256':digest}
                q={'complete':True,'expected_keys':[key],'receipts':{key:fresh},'failures':{} if passed else {key:bad or {'passed':False}}}
                c.write(folder/'qualification-private.json',q)
                summary={'distinct_new_sources':1,'passed':int(passed),'checks':total,'checks_passed':ok,'failed_sources':int(not passed)}
                with patch.object(sandbox,'run',side_effect=AssertionError('Reporter must not execute candidate')):
                    receipts,_=r.qualify_replay(folder,config,{'24-S':{'1':text}}, {},summary)
                self.assertEqual(receipts[key],fresh)
                if not passed:
                    wrong=copy.deepcopy(q);wrong['receipts'][key]['passed']=True;c.write(folder/'qualification-private.json',wrong)
                    with self.assertRaises(AssertionError):r.qualify_replay(folder,config,{'24-S':{'1':text}}, {},summary)
                    c.write(folder/'qualification-private.json',q)
                raw=(folder/rel).parent/'0.stdout';raw.write_bytes(raw.read_bytes()+b'corrupt')
                with self.assertRaises(AssertionError):r.qualify_replay(folder,config,{'24-S':{'1':text}}, {},summary)

    def test_publication_preflight_and_post_replay_failure_withdraw(self):
        from unittest.mock import patch
        success={'complete':True,'scope':'invented','arms':[],'verdicts':{},'selected_successor':None,'predictions':{},'replay_scope':'invented'}
        for mode in ('serialize','replace','elapsed','setup'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);run=root/'run';run.mkdir();output=root/'report';output.mkdir()
                c.write(output/'results.json',success);(output/'REPORT.md').write_text('stale success')
                cfg={'limits':{'report_seconds':1}};write=c.write;replace=Path.replace
                def writing(path,value):
                    if mode=='serialize' and Path(path).parent.name.startswith('.report-stage-'):raise OSError('serialization failed')
                    return write(path,value)
                def replacing(path,target):
                    if mode=='replace' and path.parent.name.startswith('.report-stage-') and path.name=='results.json':raise c.HardDeadline('deadline during publication')
                    return replace(path,target)
                if mode=='setup':
                    timers=[];callbacks=[]
                    def reading(path):
                        self.assertEqual(timers,[1800]);callbacks[0](None,None)
                    with patch.object(r.signal,'signal',side_effect=lambda sig,fn:callbacks.append(fn)),patch.object(r.signal,'setitimer',side_effect=lambda kind,n:timers.append(n)),\
                         patch.object(c,'read',side_effect=reading),patch.object(r.resource,'setrlimit'),patch.object(r.os,'sched_setaffinity'):
                        with self.assertRaises(c.HardDeadline):r.main(run,output)
                else:
                    with patch.object(r,'replay',return_value=copy.deepcopy(success)),patch.object(c,'write',side_effect=writing),patch.object(Path,'replace',replacing):
                        if mode=='elapsed':
                            with patch.object(r.time,'monotonic',side_effect=[0,0,2]):
                                with self.assertRaises(AssertionError):r.publish(run,cfg,output)
                        else:
                            with self.assertRaises(OSError if mode=='serialize' else c.HardDeadline):r.publish(run,cfg,output)
                self.assertFalse(c.read(output/'results.json')['complete']);self.assertIsNone(c.read(output/'results.json')['verdicts'])
                self.assertIn('No verdict',(output/'REPORT.md').read_text())


class DecisionTests(unittest.TestCase):
    def test_fraction_is_ratio_and_record_time_best_cannot_waive_actions(self):
        from unittest.mock import patch
        cfg={'decoder_dependency_bytes':13010,'partition':{'dev_fit':[0],'dev_val':[1]},'parent_evidence':{a:{'path':'invented.json','sha256':'hash'} for a in r.ANCHORS}}
        def arm(label,policy,n,chars):
            rows={str(i):{'encodable':True,'qualified_source':True,'selections':n,'actions':n+1,'single_characters':chars,'source_bytes':30,'packet_bytes':41+n} for i in (0,1)}
            return {'arm':label,'policy':policy,'dictionary_bytes':100,'entries':97,'illegal_entry_sha256':[],'dictionary_binary_sha256':'fixed',
                    'per_problem':rows,**{split:r.aggregate(rows,ids,100,13010) for split,ids in [('fit',[0]),('validation',[1])]}}
        u=arm('24-U','canonical',10,5);bad=arm('24-S','canonical',9,5)
        self.assertFalse(r.transfer(bad,u,cfg)['checks']['strict_fraction'])
        good=arm('24-S','canonical',10,4);self.assertTrue(r.transfer(good,u,cfg)['passed'])
        self.assertEqual(r.transfer(good,u,cfg)['paired_diagnostics']['validation']['character_codes_delta'],-1)
        arms=[arm(a+'-'+suffix,policy,10,5 if suffix=='U' else 4) for a in r.ANCHORS for suffix in ('U','S') for policy in r.POLICIES]
        refs={(label,policy):arm(label,policy,10,5) for label in ('R','seed13','best24','N','NCP') for policy in r.POLICIES}
        self.assertIsNone(r.decisions(arms,refs,cfg)['predictions']['P4'])
        binding={'recorded_commit':'1234567','recorded_label':'43N','evidence':{'path':'invented.json','sha256':'hash'},'comparison':{'kind':'anchor','anchor':'43N'}}
        with patch.object(c,'hashfile',return_value='hash'):result=r.decisions(arms,refs,cfg,binding)
        self.assertTrue(result['record_time_best']['resolved']);self.assertTrue(result['predictions']['P4'])
        self.assertFalse(result['verdicts']['43N-S']['policies']['canonical']['comparisons']['record_time_best']['checks']['actions'])
        self.assertTrue(result['verdicts']['43N-S']['transfer']);self.assertIsNone(result['selected_successor'])
        malformed=copy.deepcopy(binding);malformed['evidence']['sha256']='wrong'
        with self.assertRaises(AssertionError):r.current_best(malformed,cfg,{})

if __name__=='__main__':unittest.main()
