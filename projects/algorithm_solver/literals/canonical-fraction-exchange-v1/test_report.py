"""Invented-only independent canonical packet, cap, trace and failure tests."""
import copy
from pathlib import Path
import random
import struct
import tempfile
import time
import unittest
from unittest.mock import patch
import codec
import common as c
import report as r
import search


def paths(text,vocab):
    if not text:return [()]
    return [(i,)+tail for i,word in enumerate(vocab) if text.startswith(word) for tail in paths(text[len(word):],vocab)]


def trace_fixture(root,evaluations=100,clock=None,emitter=None):
    texts={'x':'abx','y':'ccccx'};pool=['a','ab','b','c','cc','x'];seed=['a','ab','b','c','x'];capacity=5
    graph=search.CheckedGraph(texts,pool,seed,capacity=capacity,decoder_bytes=13010)
    limits={'seconds':600,'evaluations':evaluations,'epochs':2,'shortlist':4,'expected_free_slots':0}
    states={};events=[];caps={pid:{'source_sha256':r.rawsha(t.encode()),'N':graph.caps[pid]} for pid,t in texts.items()}
    def retain(state,index):
        folder=root/str(index);raw=codec.measure(graph,state['active'],folder,13010)
        w,v,p=r.witness(folder,raw,texts,set(),{'pool':{'capacity':capacity},'decoder_dependency_bytes':13010},caps)
        identity={'index':index,'dictionary_sha256':w['dictionary_sha256']}
        states[index]={'witness':w,'vocab':v,'plans':p,'identity':identity};return identity
    def emit(row):
        events.append(row)
        if emitter:emitter(row,graph)
    _,result=search.execute(graph,seed,limits,emit,retain,**({} if clock is None else {'clock':clock}))
    return events,result,texts,pool,states,limits,capacity,13010,caps


class ExactTests(unittest.TestCase):
    def test_full_id_canonical_dp_and_exact_ratio(self):
        rng=random.Random(47)
        for _ in range(50):
            text=''.join(rng.choice('ab') for _ in range(rng.randint(1,9)))
            vocab=sorted(set(['a','b']+[''.join(rng.choice('ab') for _ in range(rng.randint(2,4))) for _ in range(5)]))
            expected=min((len(ids),ids) for ids in paths(text,vocab));got=r.exact(text,vocab)
            self.assertEqual((got['N'],tuple(got['sequence'])),expected)
        self.assertEqual(r.exact('abcd',['a','ab','bcd','cd'])['words'],('a','bcd'))
        self.assertEqual(r.exact('abcd',['a','ab','bcd','cd'])['C'],1)
        n=10**30;self.assertLess(r.score_tuple([n-2,n,10]),r.score_tuple([n-1,n,10]))
        self.assertLess(r.score_tuple([1,2,100]),r.score_tuple([2,4,1]))
        with self.assertRaises(ValueError):r.exact('abc',['a','b'])

    def test_packet_cap_cost_and_same_length_wrong_canonical_tie(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);texts={'p':'abcd'};vocab=['a','ab','bcd','cd']
            graph=search.CheckedGraph(texts,vocab,vocab,capacity=4,decoder_bytes=13010)
            raw=codec.measure(graph,vocab,root/'w',13010);caps={'p':{'source_sha256':r.rawsha(b'abcd'),'N':2}}
            config={'pool':{'capacity':4},'decoder_dependency_bytes':13010}
            checked,_,_=r.witness(root/'w',raw,texts,set(),config,caps)
            self.assertEqual(checked['package_with_decoder_sources']-checked['package_bytes'],13010)
            for change in ('cost','cap','ban'):
                bad=copy.deepcopy(raw);cap=copy.deepcopy(caps);bans=set()
                if change=='cost':bad['per_problem']['p']['one_program_with_decoder']-=1
                elif change=='cap':cap['p']['N']=1
                else:bans={'ab'}
                with self.assertRaises(AssertionError):r.witness(root/'w',bad,texts,bans,config,cap)
            path=root/'w/packets/p.bin';blob=path.read_bytes();wrong=blob[:41]+bytes([1,3]);path.write_bytes(wrong)
            bad=copy.deepcopy(raw);bad['per_problem']['p']['packet_sha256']=r.rawsha(wrong)
            # ['ab','cd'] has same N and lower C, but is NOT canonical by full IDs.
            with self.assertRaises(AssertionError):r.witness(root/'w',bad,texts,set(),config,caps)


class TraceTests(unittest.TestCase):
    def test_full_partial_failure_witnesses_and_corruptions(self):
        for budget in (1,2,3,100):
            with self.subTest(budget=budget),tempfile.TemporaryDirectory() as tmp:
                args=trace_fixture(Path(tmp),budget);got=r.audit_trace(*args)
                self.assertEqual(got['attempted'],args[1]['attempted'])
                if budget==100:
                    self.assertGreater(sum(v['cap_failures'] for v in got['counters'].values()),0)
                    self.assertGreater(sum(v['coverage_failures'] for v in got['counters'].values()),0)
                modes=['count','price','opportunities','start','identity']+(['cap'] if budget==100 else [])
                for mode in modes:
                    events,result,*tail=copy.deepcopy(args)
                    if mode=='count':result['attempted']+=1
                    elif mode=='price':next(e for e in events if e['event']=='evaluation' and 'score' in e)['score'][2]-=13010
                    elif mode=='opportunities':next(e for e in events if e['event']=='sweep_start')['opportunity_sha256']='bad'
                    elif mode=='start':next(e for e in events if e['event']=='evaluation')['started_seconds']=600
                    elif mode=='identity':events[0]['seed']={**events[0]['seed'],'dictionary_sha256':'bad'}
                    else:next(e for e in events if e['event']=='evaluation' and e['outcome']=='cap_failure')['cap_failure_witness']['N']-=1
                    with self.subTest(mode=mode),self.assertRaises(AssertionError):r.audit_trace(events,result,*tail)

    def test_interrupt_new_best_rescore_preserves_earlier_incumbent(self):
        now=[0];armed=[False]
        def emit(row,graph):
            if row['event']=='evaluation' and row['kind']=='remove' and row['outcome']=='feasible' and not armed[0]:
                original=graph.path;armed[0]=True
                def path(pid,active):
                    value=original(pid,active);now[0]=601;return value
                graph.path=path
        with tempfile.TemporaryDirectory() as tmp:
            args=trace_fixture(Path(tmp),clock=lambda:now[0],emitter=emit);got=r.audit_trace(*args)
            self.assertEqual(got['interrupted_probes'],1);self.assertEqual(got['stop'],'time_limit')
            self.assertEqual(args[1]['final_incumbent'],0)


class PipelineTests(unittest.TestCase):
    def test_real_runner_replay_caps_parent_identity_and_failure(self):
        import run
        import test_run
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);config,inputs=test_run.fixture(root)
            config['fit_ids']=list(map(int,inputs['texts']));config['pool']['entries']=2048
            config['construction']={'max_arcs':1000000,'max_transitions':20000000,'max_pool_characters':2000000}
            config['limits'].update(report_seconds=1200,cleanup_seconds=10);config['offline_encoder_bytes']=0
            config['canonical_seed_caps']['naming']=copy.deepcopy(config['canonical_seed_caps']['R'])
            parent=r.read(root/'parent-seed/dictionary.json');seedraw=r.read(root/'shadow.json')['arms'][0]['witnesses']['seed']['canonical_min_N']
            graph=search.CheckedGraph(inputs['texts'],inputs['candidates'],inputs['seed'],capacity=6,decoder_bytes=13010)
            measured=codec.measure(graph,inputs['seed'],root/'measured-seed',13010)
            seedraw.update(C=measured['characters'],selections=measured['selections'],action_distribution=measured['actions'],dictionary_bytes=measured['dictionary_bytes'],
                package_bytes=measured['package_bytes'],package_with_decoder_sources=measured['package_with_decoder_sources'])
            prior=root/'direct-fraction-exchange-v1';r.write(prior/'contract.json',{'invented':True});oldhash=r.sha(prior/'contract.json')
            primary={'complete':True,'validation_loaded':False,'contract_sha256':oldhash};r.write(prior/'evidence/results.json',primary)
            shadow={'complete':True,'validation_loaded':False,'contract_sha256':oldhash,'accepted_primary_report_sha256':r.sha(prior/'evidence/results.json'),
              'arms':[{'cohort':cohort,'source_sha256':inputs['bindings']['source_sha256'],'original_parent_seed_dictionary_sha256':inputs['original_reference_hashes']['seed'],
                'witnesses':{'seed':{'canonical_min_N':seedraw,'sorted_dictionary_sha256':measured['dictionary_sha256']}}} for cohort in ('R','naming')]}
            r.write(root/'shadow.json',shadow);config['code_hashes']={rel:r.sha(root/rel) for rel in ('shadow.json','direct-fraction-exchange-v1/evidence/results.json')}
            r.write(root/'contract.json',config);ch=r.sha(root/'contract.json');out=root/'run';out.mkdir();inputs['certificate']={'integer_lower_bound':-100}
            with patch.object(c,'HERE',root),patch.object(c,'LIT',root),patch.object(c,'check_contract'),patch.object(c,'load_cohort',return_value=inputs),\
                 patch.object(run.resource,'setrlimit'),patch.object(run.os,'sched_setaffinity'):
                for cohort in ('R','naming'):run.arm(cohort,root,out,time.monotonic()+30)
            raws=[r.read(out/cohort/'results.json') for cohort in ('R','naming')]
            with patch.object(r,'LIT',root):arms=[r.replay_arm(raw,out,inputs,config,ch) for raw in raws]
            for arm in arms:arm.update(report_worker_seconds=.001,report_peak_rss_kib=1000)
            self.assertTrue(all(a['final']['relative_to_seed']['worse']==0 for a in arms));self.assertGreater(arms[0]['final_incumbent'],0)
            elapsed=max(raw['seconds'] for raw in raws)+.01
            production={'complete':True,'validation_loaded':False,'contract_sha256':ch,'seconds':elapsed,'arms':raws};r.write(out/'results.json',production)
            r.write(out/'supervisor.json',{'complete':True,'phase':'production','contract_sha256':ch,'returncodes':[0,0],'cleanup_seconds':0,'elapsed':elapsed})
            with patch.object(r,'HERE',root):result=r.combine(arms,production,config,.1,out)
            r.publish(result,root/'report');self.assertTrue(result['complete']);self.assertFalse(result['m1_qualification'])
            for field,bad in [('report_worker_seconds',float('nan')),('report_worker_seconds',1),('report_peak_rss_kib',0),('report_peak_rss_kib',9*1024**2)]:
                altered=copy.deepcopy(arms);altered[0][field]=bad
                with patch.object(r,'HERE',root),self.assertRaises(AssertionError):r.combine(altered,production,config,.1,out)
            supervisor=r.read(out/'supervisor.json');wrong=copy.deepcopy(supervisor);wrong['returncodes']=[False,0];r.write(out/'supervisor.json',wrong)
            with patch.object(r,'HERE',root),self.assertRaises(AssertionError):r.combine(arms,production,config,.1,out)
            r.write(out/'supervisor.json',supervisor)
            broken=copy.deepcopy(raws[0]);broken['incumbents'][-1]['witness']['package_bytes']-=1;r.write(out/'R/results.json',broken)
            with patch.object(r,'LIT',root),self.assertRaises(AssertionError):r.replay_arm(broken,out,inputs,config,ch)
            r.write(out/'R/results.json',raws[0]);r.write(out/'failure.json',{'complete':False})
            with patch.object(r,'HERE',root),self.assertRaises(AssertionError):r.combine(arms,production,config,.1,out)
            r.publish(r.failure_result('execution_failed'),root/'report');self.assertFalse(r.read(root/'report/results.json')['complete'])

    def test_setup_deadline_and_publication_failure_withdraw(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);r.write(root/'R.json',{'complete':True})
            def fail(_):
                self.assertGreater(r.signal.getitimer(r.signal.ITIMER_REAL)[0],0);raise r.HardDeadline()
            with patch.object(r,'read',side_effect=fail),patch.object(r.resource,'setrlimit'),patch.object(r.os,'sched_setaffinity'),self.assertRaises(r.HardDeadline):
                r.main('R',root,root,root,time.monotonic()+30)
            self.assertFalse((root/'R.json').exists());self.assertFalse(r.read(root/'R-failure.json')['complete'])
            r.publish(r.failure_result('initial'),root);r.write(root/'results.json',{'complete':True});(root/'REPORT.md').write_text('stale success')
            with patch.object(r,'markdown',side_effect=[r.HardDeadline(),'# no verdict\n']),self.assertRaises(r.HardDeadline):r.publish({'complete':True},root)
            self.assertFalse(r.read(root/'results.json')['complete']);self.assertIn('no verdict',(root/'REPORT.md').read_text())


class ParentBindingTests(unittest.TestCase):
    def test_rebuilds_exact_pool_provenance_and_parent_hash_chain(self):
        backend=r.module('report_test_parent_backend',r.LIT/'fraction-primal-repair-v1/backend.py')
        builder=r.module('report_test_parent_pool',r.LIT/'fraction-primal-repair-v1/pool.py')
        texts={str(i):'ababa' for i in range(300)};seed=['a','b'];bans={'ababa'}
        q={pid:[[0]*11 for _ in text] for pid,text in texts.items()}
        index=builder.implicit.Index(texts,bans);cert=index.certificate(q,9,1000000)
        pool,info=builder.build(index,q,seed,1000000,9,2048)
        certificate={k:cert[k] for k in backend.CERT_KEYS};certificate['q_sha256']=r.digest(q)
        p35={'fit_source_sha256':r.digest(texts),'certificate':certificate}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);work=root/'work';work.mkdir()
            r.write(root/'parent-contract.json',{'synthetic_only':True});ch=r.sha(root/'parent-contract.json')
            r.write(work/'pool.json',pool);r.write(work/'pool-provenance.json',info)
            refs={};witnesses={};hashes={}
            for name in ('seed',):
                refs[name]=name+'.json';r.write(work/refs[name],seed)
                witnesses[name]={'dictionary_sha256':r.sha(work/refs[name])};hashes[refs[name]]=r.sha(work/refs[name])
            arm={'cohort':'R','fit_source_sha256':p35['fit_source_sha256'],'parent_q_sha256':certificate['q_sha256'],
               'parent_full_class_certificate':{k:certificate[k] for k in backend.CERT_KEYS},
               'pool_counts':{k:v for k,v in info.items() if k!='provenance'},'pool_sha256':r.sha(work/'pool.json'),
               'pool_provenance_sha256':r.sha(work/'pool-provenance.json'),'witnesses':witnesses}
            raw={'complete':True,'validation_loaded':False,'contract_sha256':ch,'arms':[arm]};r.write(work/'parent-results.json',raw)
            public=copy.deepcopy(raw);public['private_results_sha256']=r.sha(work/'parent-results.json')
            del public['arms'][0]['pool_provenance_sha256']
            r.write(root/'parent-evidence.json',public)
            config={'active':True,'fit_ids':list(range(300)),'parent_contract':'parent-contract.json','parent_contract_sha256':ch,
              'parent_evidence':'parent-evidence.json','parent_private_results':'parent-results.json',
              'private_files':{**hashes,'parent-results.json':r.sha(work/'parent-results.json'),'pool.json':r.sha(work/'pool.json')},
              'parent_pool':{'R':'pool.json'},'parent_references':{'R':refs},'pool':{'capacity':9,'denominator':1000000,'entries':2048},
              'expected_seed_entries':{'R':2},'search':{'expected_free_slots':7}}
            def mods(name,path):return backend if 'backend' in name else builder
            with patch.object(r,'LIT',root),patch.object(r,'module',side_effect=mods),patch.object(backend,'inputs',return_value=(texts,seed,q,p35)),patch.object(backend.dual.sel,'forbidden_strings',return_value=bans):
                got=r.independent_inputs(config,work,'R');self.assertEqual(got['candidates'],pool)
                broken=copy.deepcopy(info);broken['provenance'][pool[0]]=[]
                r.write(work/'pool-provenance.json',broken)
                with self.assertRaises(AssertionError):r.independent_inputs(config,work,'R')


if __name__=='__main__':unittest.main()
