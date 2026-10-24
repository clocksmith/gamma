"""Invented-only policy, full charging, acceptance-gate and failure checks."""
import copy,importlib.util,random,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import canonical_shadow as c

def module(name,path):
    before=list(sys.path)
    try:
        spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    finally:sys.path[:]=before

def paths(text,vocab):
    if not text:return [()]
    return [(i,)+tail for i,w in enumerate(vocab) if text.startswith(w) for tail in paths(text[len(w):],vocab)]

def fixture(root):
    backend=module('shadow_test_backend',c.LIT/'fraction-primal-repair-v1/backend.py')
    lit=root/'lit';primary=lit/'direct-fraction-exchange-v1';work=root/'work';run=root/'run';accepted=root/'accepted'
    for folder in (primary,work,run,accepted):folder.mkdir(parents=True)
    texts={str(i):'aaaaaa' for i in range(300)};seed=['a','aaaaa'];final=['a','aa','aaaaa'];oldarms=[];arms=[];qualification=[]
    config={'active':True,'population':'fixed300_fit_only','python_bin':str(Path(sys.executable).absolute()),'fit_ids':list(range(300)),
      'code_hashes':{},'runtime_files':{},'decoder_source_files':{},'private_files':{},'parent_contract':'parent.json'}
    for rel,content in (('literals.py',b'codec'),('pass2/working/bitpack.py',b'bitcodec')):
        path=lit/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content)
        config['decoder_source_files'][rel]={'sha256':c.sha(path),'bytes':len(content)}
    config['decoder_dependency_bytes']=13
    c.write(lit/'parent.json',{'cohorts':{'R':'R','naming':'naming'}});config['parent_contract_sha256']=c.sha(lit/'parent.json')
    for cohort in ('R','naming'):
        folder=run/cohort;folder.mkdir();(folder/'incumbents').mkdir();c.write(work/cohort/'fit-sources.json',texts)
        sh=c.sha(work/cohort/'fit-sources.json');config['private_files'][cohort+'/fit-sources.json']=sh;rows=[]
        for i,v in enumerate((seed,final)):
            w=backend.measure(texts,v,folder/'incumbents'/f'{i:03d}',13);rows.append({'index':i,'witness':w});c.write(folder/'retained-dictionaries'/f'{i:03d}.json',v)
        old={'cohort':cohort,'incumbents':rows,'final_incumbent':1,'bindings':{'source_sha256':sh}};c.write(folder/'results.json',old);oldarms.append(old)
        arms.append({'cohort':cohort,'complete':True,'validation_loaded':False,'bindings':old['bindings'],'final_incumbent':1,
          'private_arm_result_sha256':c.sha(folder/'results.json'),'references':{'seed':{'original_parent_dictionary_sha256':rows[0]['witness']['dictionary_sha256']}}})
        qualification.append({'width':8,'arm':'control' if cohort=='R' else 'scope_joint','qualification':{pid:{'passed':True} for pid in texts},
          'per_problem':{pid:{'source_sha256':c.hashbytes(text.encode())} for pid,text in texts.items()}})
    c.write(lit/'binding-descent-v1/evidence/results.json',{'arms':qualification});c.write(primary/'contract.json',config);ch=c.sha(primary/'contract.json')
    for a in arms:a['contract_sha256']=ch
    c.write(run/'results.json',{'complete':True,'validation_loaded':False,'contract_sha256':ch,'arms':oldarms})
    c.write(run/'supervisor.json',{'complete':True,'phase':'production','contract_sha256':ch})
    c.write(accepted/'results.json',{'complete':True,'validation_loaded':False,'population':'fixed300_fit_only','m1_qualification':False,
      'contract_sha256':ch,'private_results_sha256':c.sha(run/'results.json'),'production_supervisor_sha256':c.sha(run/'supervisor.json'),'arms':arms})
    c.write(accepted/'supervisor.json',{'complete':True,'phase':'report','contract_sha256':ch,'returncodes':[0,0],'elapsed':1,'cleanup_seconds':0})
    return lit,primary,work,run,accepted,config

class ShadowTests(unittest.TestCase):
    def test_both_policies_against_exhaustive_paths_and_legacy_canonical(self):
        codec=module('shadow_legacy_codec',c.LIT/'literals.py');rng=random.Random(4401)
        for _ in range(60):
            text=''.join(rng.choice('ab') for _ in range(rng.randint(1,8)))
            vocab=sorted(set(['a','b']+[''.join(rng.choice('ab') for _ in range(rng.randint(2,5))) for _ in range(5)]));options=paths(text,vocab)
            for policy in c.POLICIES:
                key=(lambda ids:(sum(9 if len(vocab[i])==1 else -1 for i in ids),len(ids),ids)) if policy=='min_F' else (lambda ids:(len(ids),ids))
                self.assertEqual(c.encode(text,vocab,policy)['ids'],min(options,key=key))
            self.assertEqual(c.encode(text,vocab,'canonical_min_N')['ids'],tuple(codec.shortest_encode(text,vocab)))
        got=c.encode('aaaa',['a','aa','aaa'],'canonical_min_N');self.assertEqual(got['ids'],(0,2));self.assertEqual(got['C'],1)
        self.assertEqual(c.encode('aaaa',['a','aa','aaa'],'min_F')['ids'],(1,1))

    def test_full_replay_exposes_policy_tradeoff_and_exact_charges(self):
        with tempfile.TemporaryDirectory() as tmp:
            lit,primary,work,run,accepted,config=fixture(Path(tmp))
            with patch.object(c,'LIT',lit),patch.object(c,'PRIMARY',primary):got=c.replay(work,run,accepted,config)
            self.assertTrue(got['complete']);self.assertFalse(got['optimization_performed'])
            for arm in got['arms']:
                final=arm['witnesses']['final'];f=final['min_F'];n=final['canonical_min_N']
                self.assertEqual((f['F'],f['C'],f['N']),(-900,0,900));self.assertEqual((n['F'],n['C'],n['N']),(2400,300,600))
                self.assertEqual(n['character_fraction'],.5);self.assertEqual(f['character_fraction'],0)
                self.assertEqual(arm['final_minus_seed']['canonical_min_N']['character_fraction'],0)
                self.assertEqual(n['package_with_decoder_sources']-n['package_bytes'],13);self.assertEqual(n['actions'],n['N']+300)
                self.assertEqual(n['framing_bytes'],41*300);self.assertEqual(n['per_problem']['0']['one_program_package_with_decoder'],n['dictionary_bytes']+43+13)
            public=Path(tmp)/'publication';public.mkdir();c.publish(got,public)
            self.assertIn('canonical_min_N',(public/'REPORT.md').read_text());self.assertNotIn('aaaaaa',(public/'results.json').read_text())
            damaged=run/'R/incumbents/001/packets/0.bin';damaged.write_bytes(damaged.read_bytes()[:-1]+b'\x00')
            with patch.object(c,'LIT',lit),patch.object(c,'PRIMARY',primary),self.assertRaises(AssertionError):c.replay(work,run,accepted,config)

    def test_accepted_primary_gate_precedes_all_private_access(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);primary=root/'primary';primary.mkdir();c.write(primary/'contract.json',{})
            directory=root/'unaccepted';directory.mkdir();c.write(directory/'results.json',{'complete':False});c.write(directory/'supervisor.json',{'complete':False})
            with patch.object(c,'PRIMARY',primary),patch.object(c,'runtime',side_effect=AssertionError('Runtime/private gate crossed')) as runtime:
                with self.assertRaises(AssertionError):c.replay(root/'missing-work',root/'missing-run',directory,{})
                runtime.assert_not_called()
            with self.assertRaises(FileNotFoundError):c.accepted_primary(root/'missing','x')

    def test_failure_receipt_and_postreplacement_errors_withdraw_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'out';c.write(root/'results.json',{'complete':True});(root/'REPORT.md').write_text('stale')
            with patch.object(c.resource,'setrlimit'),patch.object(c.os,'sched_setaffinity'),patch.object(c,'write',side_effect=OSError('invented receipt failure')):
                with self.assertRaises(OSError):c.main(Path(tmp)/'work',Path(tmp)/'run',Path(tmp)/'accepted',root)
            self.assertFalse(c.read(root/'results.json')['complete']);self.assertIn('No verdict',(root/'REPORT.md').read_text())
            original=Path.replace
            def broken(path,target):
                if path.name=='results.json.staged':raise c.HardDeadline()
                return original(path,target)
            minimal={'complete':True,'interpretation':'test','policy_scope':'test','arms':[]}
            with patch.object(Path,'replace',broken),self.assertRaises(c.HardDeadline):c.publish(minimal,root)
            self.assertFalse(c.read(root/'results.json')['complete']);self.assertIn('No verdict',(root/'REPORT.md').read_text())

    def test_overlapping_output_cannot_withdraw_primary_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);run=root/'run';c.write(run/'results.json',{'complete':True});before=(run/'results.json').read_bytes()
            with patch.object(c.resource,'setrlimit'),patch.object(c.os,'sched_setaffinity'):
                with self.assertRaises(ValueError):c.main(root/'work',run,root/'accepted',run)
            self.assertEqual((run/'results.json').read_bytes(),before);self.assertFalse((run/'failure.json').exists())

    def test_timer_is_live_before_contract_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'out'
            def failed(path):
                self.assertGreater(c.signal.getitimer(c.signal.ITIMER_REAL)[0],0);raise c.HardDeadline()
            with patch.object(c.resource,'setrlimit'),patch.object(c.os,'sched_setaffinity'),patch.object(c,'read',side_effect=failed):
                with self.assertRaises(c.HardDeadline):c.main(Path(tmp)/'work',Path(tmp)/'run',Path(tmp)/'accepted',root)
            self.assertFalse(c.read(root/'results.json')['complete'])

if __name__=='__main__':unittest.main()
