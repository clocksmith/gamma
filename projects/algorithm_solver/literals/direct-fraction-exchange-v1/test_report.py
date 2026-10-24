"""Invented inputs only; exact decoding, receipt and publication corruption tests."""
import copy
from pathlib import Path
import random
import struct
import tempfile
import unittest
from unittest.mock import patch
import report as r


def paths(text,vocab):
    if not text:return [()]
    return [(i,)+tail for i,w in enumerate(vocab) if text.startswith(w) for tail in paths(text[len(w):],vocab)]


def fixture(root):
    backend=r.module('exchange_report_test_codec',r.LIT/'fraction-primal-repair-v1/backend.py')
    texts={'0':'ababa','1':'abaab'};vocab=['a','ab','aba','b','ba'];folder=root/'witness'
    raw=backend.measure(texts,vocab,folder,13010)
    return texts,vocab,folder,raw,{'pool':{'capacity':256},'decoder_dependency_bytes':13010}


class ReportTests(unittest.TestCase):
    def test_complete_id_tie_and_negative_dag_scores_against_path_enumeration(self):
        rng=random.Random(4404)
        for _ in range(45):
            text=''.join(rng.choice('ab') for _ in range(rng.randint(1,8)))
            vocab=sorted(set(['a','b']+[''.join(rng.choice('ab') for _ in range(rng.randint(2,4))) for _ in range(5)]))
            options=paths(text,vocab)
            expected=min((sum(9 if len(vocab[i])==1 else -1 for i in ids),len(ids),ids) for ids in options)
            got=r.exact(text,vocab)
            self.assertEqual((got['F'],got['N'],tuple(got['sequence'])),expected)
        with self.assertRaises(ValueError):r.exact('abc',['a','b'])

    def test_retained_witness_costs_descriptions_and_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            texts,vocab,folder,raw,c=fixture(Path(tmp))
            checked,words,plans=r.witness(folder,raw,texts,set(),c,-999,vocab)
            self.assertEqual(words,vocab);self.assertTrue(checked['exact_packet_ids_and_costs_rechecked'])
            self.assertEqual(r.summary(checked)['N'],sum(p['N'] for p in plans.values()))
            self.assertEqual(checked['package_with_decoder_sources']-checked['package_bytes'],13010)
            changed=copy.deepcopy(raw);changed['per_problem']['0']['one_program_package_bytes']-=1
            with self.assertRaises(AssertionError):r.witness(folder,changed,texts,set(),c,-999)
            with self.assertRaises(AssertionError):r.witness(folder,raw,texts,{'aba'},c,-999)
            changed=copy.deepcopy(raw);changed['objective']-=1
            with self.assertRaises(AssertionError):r.witness(folder,changed,texts,set(),c,-999)
            packet=folder/'packets/0.bin';original=packet.read_bytes()
            alternate=original[:37]+struct.pack('>I',2)+bytes([vocab.index('aba'),vocab.index('ba')])
            packet.write_bytes(alternate);changed=copy.deepcopy(raw);changed['per_problem']['0']['packet_sha256']=r.rawsha(alternate)
            with self.assertRaises(AssertionError):r.witness(folder,changed,texts,set(),c,-999)



def trace_fixture(root,evaluations=100,clock=None):
    import search
    backend=r.module('exchange_trace_codec',r.LIT/'fraction-primal-repair-v1/backend.py')
    texts={'0':'ababa','1':'abaab'};pool=['a','ab','aba','b','ba'];seed=['a','b'];capacity=3
    graph=search.CheckedGraph(texts,pool,capacity,decoder_bytes=13010)
    limits={'seconds':600,'evaluations':evaluations,'epochs':3,'shortlist':4,'expected_free_slots':1}
    states={};events=[]
    def retain(state,index):
        folder=root/str(index);v=sorted(state['active']);raw=backend.measure(texts,v,folder,13010)
        w,v,p=r.witness(folder,raw,texts,set(),{'pool':{'capacity':capacity},'decoder_dependency_bytes':13010},-999)
        identity={'index':index,'dictionary_sha256':w['dictionary_sha256']}
        states[index]={'witness':w,'vocab':v,'plans':p,'identity':identity};return identity
    _,result=search.execute(graph,seed,limits,events.append,retain,**({} if clock is None else {'clock':clock}))
    return events,result,texts,pool,states,limits,capacity


class ReceiptTests(unittest.TestCase):
    def test_complete_partial_and_interrupted_receipts(self):
        for cap in (1,2,100):
            with self.subTest(cap=cap),tempfile.TemporaryDirectory() as tmp:
                args=trace_fixture(Path(tmp),cap)
                got=r.audit_trace(*args)
                self.assertEqual(got['attempted'],args[1]['attempted'])
                for alter in ('count','price','identity','enumeration'):
                    events,result,*tail=copy.deepcopy(args)
                    if alter=='count':result['attempted']+=1
                    elif alter=='price':
                        event=next(e for e in events if e['event']=='evaluation' and 'objective' in e)
                        event['objective'][2]-=13010
                    elif alter=='identity':events[0]['seed']={**events[0]['seed'],'dictionary_sha256':'bad'}
                    else:next(e for e in events if e['event']=='sweep_start')['opportunities']+=1
                    with self.subTest(alter=alter),self.assertRaises(AssertionError):r.audit_trace(events,result,*tail)
        calls=0
        def clock():
            nonlocal calls
            calls+=1;return 0 if calls<5 else 601
        with tempfile.TemporaryDirectory() as tmp:
            args=trace_fixture(Path(tmp),clock=clock);got=r.audit_trace(*args)
            self.assertEqual(got['interrupted_probes'],1);self.assertEqual(got['soft_overrun_seconds'],1)

    def test_publication_withdraws_stale_success_after_baseexception(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);r.publish(r.failure_result('initial'),root)
            (root/'results.json').write_text('{"complete":true}')
            (root/'REPORT.md').write_text('stale success')
            with patch.object(r,'markdown',side_effect=[r.HardDeadline(), '# no verdict\n']):
                with self.assertRaises(r.HardDeadline):r.publish({'complete':True},root)
            self.assertFalse(r.read(root/'results.json')['complete'])
            self.assertIn('no verdict',(root/'REPORT.md').read_text())


class PipelineTests(unittest.TestCase):
    def test_real_synthetic_runner_packets_trace_and_public_failure_dominance(self):
        import run,search,time
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);runpath=root/'production';runpath.mkdir();out=root/'publication'
            texts={str(i):'ababab' for i in range(300)}
            pool=sorted({'a','b','ab','aba','abab','ababa','ababab','ba','bab','baba','babab'});seed=['a','b']
            config={'active':True,'fit_ids':list(range(300)),'pool':{'capacity':9,'entries':2048},
              'decoder_dependency_bytes':13010,'construction':{'max_arcs':1000000,'max_transitions':20000000,'max_pool_characters':2000000},
              'search':{'seconds':600,'evaluations':100,'epochs':3,'shortlist':4,'expected_free_slots':7},
              'limits':{'production_seconds':1200,'report_seconds':1200,'address_space_bytes':8*1024**3,
                        'arm_cores':{'R':[6],'naming':[7]},'cleanup_seconds':10}}
            r.write(root/'contract.json',config);ch=r.sha(root/'contract.json')
            arcs,trans=r.occurrence_counts(texts,pool,config['construction'])
            parent=run.c.backend.measure(texts,seed,root/'original',13010)
            inputs={'texts':texts,'candidates':pool,'seed':seed,'references':{k:seed for k in ('seed','warm','cold')},
              'bans':set(),'parent_arm':{'arcs':arcs,'transitions':trans,'witnesses':{k:parent for k in ('seed','warm','cold')}},
              'pool_counts':{'pool_entries':len(pool)},'original_reference_hashes':{k:parent['dictionary_sha256'] for k in ('seed','warm','cold')},
              'bindings':{'source_sha256':r.digest(texts),'parent_q_sha256':'q','pool_sha256':r.digest(pool),'parent_private_results_sha256':'p'},
              'certificate':{'integer_lower_bound':-1800}}
            with patch.object(run.c,'HERE',root),patch.object(run.c,'check_contract'),patch.object(run.c,'load_cohort',return_value=inputs),patch.object(run.resource,'setrlimit'),patch.object(run.os,'sched_setaffinity'):
                for cohort in ('R','naming'):run.arm(cohort,root,runpath,time.monotonic()+1200)
            rawarms=[r.read(runpath/cohort/'results.json') for cohort in ('R','naming')]
            arms=[r.replay_arm(a,runpath,inputs,config,ch) for a in rawarms]
            self.assertTrue(all(a['final']['F']<=a['references']['seed']['F'] for a in arms))
            elapsed=max(a['seconds'] for a in rawarms)+.1
            production={'complete':True,'validation_loaded':False,'contract_sha256':ch,'seconds':elapsed,'arms':rawarms}
            r.write(runpath/'results.json',production)
            r.write(runpath/'supervisor.json',{'complete':True,'phase':'production','contract_sha256':ch,'returncodes':[0,0],'cleanup_seconds':0,'elapsed':elapsed})
            with patch.object(r,'HERE',root):result=r.combine(arms,production,config,1,runpath)
            r.publish(result,out);self.assertTrue(r.read(out/'results.json')['complete'])
            self.assertFalse(result['m1_qualification']);self.assertEqual(len(arms[0]['retained']),rawarms[0]['final_incumbent']+1)
            damaged=copy.deepcopy(rawarms[0]);damaged['incumbents'][-1]['witness']['package_bytes']-=1
            r.write(runpath/'R/results.json',damaged)
            with self.assertRaises(AssertionError):r.replay_arm(damaged,runpath,inputs,config,ch)
            r.write(runpath/'R/results.json',rawarms[0]);r.write(runpath/'failure.json',{'complete':False})
            with patch.object(r,'HERE',root),self.assertRaises(AssertionError):r.combine(arms,production,config,1,runpath)
            r.publish(r.failure_result('execution_failed'),out)
            self.assertFalse(r.read(out/'results.json')['complete']);self.assertIn('no verdict',(out/'REPORT.md').read_text())

    def test_deadline_precedes_contract_read_and_withdraws_worker_output(self):
        import time
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);r.write(root/'R.json',{'complete':True})
            def fail(_):
                self.assertGreater(r.signal.getitimer(r.signal.ITIMER_REAL)[0],0)
                raise r.HardDeadline()
            with patch.object(r,'read',side_effect=fail),self.assertRaises(r.HardDeadline):
                r.main('R',root,root,root,time.monotonic()+30)
            self.assertFalse((root/'R.json').exists());self.assertFalse(r.read(root/'R-failure.json')['complete'])




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
            for name in ('seed','warm','cold'):
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
