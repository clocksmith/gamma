"""Synthetic only: selected-entry MILP, width budgets, Python bans, receipt replay."""
import copy
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import common
engine=common.module("python_slots_test_engine",common.HERE/"engine.py")
report=common.module("python_slots_test_report",common.HERE/"report.py")
from common import ALPHABET,analyze,authority,banned,evaluate,ordered,repair,sha,write

class MechanismTests(unittest.TestCase):
    def test_actual_flow_matches_exhaustive_and_no_implicit_character(self):
        texts={'1':'abab','2':'abba'};fixed=['a','b'];candidates=['ab','ba','bb','aba']
        chosen,receipt=repair.solve(texts,fixed,candidates,1,5)
        optimum=min(repair.exact(texts,fixed+list(subset))[0] for n in (0,1) for subset in itertools.combinations(candidates,n))
        self.assertTrue(receipt['feasible']);self.assertEqual(repair.exact(texts,fixed+chosen)[0],optimum)
        self.assertEqual(receipt['objective'],optimum)
        chosen,receipt=repair.solve({'1':'ab'},['a'],['x'],1,5)
        self.assertFalse(receipt['feasible'])
        chosen,receipt=repair.solve({'1':'ab'},[],['ab'],1,5)
        self.assertTrue(receipt['feasible']);self.assertEqual(chosen,['ab'])

    def test_width_capacity_reserved_and_matched_freed_slots(self):
        observed=set('abc\n');reserved=set(ALPHABET)-observed
        cfg={'free_total':{'7':32,'8':48},'free_characters':8,'priority_characters':4,'top':2,'random':1}
        for w in (7,8):
            vocab=ALPHABET+['a'+str(i)+'b' for i in range(2**w-96)]
            for mode in ('fixed96','optional'):
                fixed,candidates,capacity,meta=engine.proposal(vocab,observed,reserved,['ab','bc'],['ab','bc'],random.Random(24),mode,cfg,{},w)
                self.assertEqual(len(fixed)+capacity,2**w)
                self.assertLessEqual(meta['freed_characters']+meta['freed_learned'],cfg['free_total'][str(w)])
                self.assertTrue(reserved<=set(fixed));self.assertFalse(set(fixed)&set(candidates))
                if mode=='fixed96':self.assertTrue(set(ALPHABET)<=set(fixed))
                else:self.assertEqual(meta['freed_characters'],len(observed))

    def test_python_body_excluded_and_newline_positions(self):
        text='class Solution:\n    def answer(self):\n        value = "\\v"\n        return value\n'
        ban=banned({'1':text},{'1':'answer'})
        self.assertIn(text,ban);self.assertIn('value = "\\v"\n        return value',ban)
        pool,_=engine.pool_rank({'1':text,'2':text},ban,100)
        self.assertFalse(set(pool)&ban)
        with self.assertRaises(AssertionError):banned({'1':text},{'1':'solve'})

    def test_qualification_rejects_wrong_hash_and_failed_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'q.json';source='class Solution: pass\n'
            q={'arms':[{'width':7,'arm':'scope_joint','qualification':{'1':{'passed':True}},'per_problem':{'1':{'source_sha256':sha(source.encode())}}}]}
            write(path,q);c={'qualification':{'file':str(path),'sha256':sha(path.read_bytes())}}
            authority(c,7,'scope_joint',{'1':source})
            with self.assertRaises(AssertionError):authority(c,7,'scope_joint',{'1':source+'\n'})
            q['arms'][0]['qualification']['1']['passed']=False;write(path,q);c['qualification']['sha256']=sha(path.read_bytes())
            with self.assertRaises(AssertionError):authority(c,7,'scope_joint',{'1':source})

    def test_fit_runner_seals_fixed_sources_and_retains_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);sources={'1':'class Solution:\n    def answer(self):\n        return 1\n','2':'class Solution:\n    def answer(self):\n        return 2\n'}
            def spec(name,obj):
                p=root/name;write(p,obj);return {'file':str(p),'sha256':sha(p.read_bytes())}
            q={'arms':[{'width':7,'arm':'scope_joint','qualification':{p:{'passed':True} for p in sources},
                       'per_problem':{p:{'source_sha256':sha(t.encode())} for p,t in sources.items()}}]}
            c={'limits':{'address_space_bytes':8*1024**3},'partition':{'dev_fit':[1,2]},'entries':{'1':'answer','2':'answer'},'qualification':spec('q.json',q),
               'inputs':{'7':{'fit':spec('fit.json',sources),'seed_dictionary':spec('seed.json',ALPHABET)}},
               'search':{'moves':1,'solver_seconds':2,'seconds':20,'checkpoint_reserve_seconds':1,'max_length':4,
                         'seed':24,'free_total':{'7':32},'free_characters':8,'priority_characters':4,'top':10,'random':2}}
            with patch.object(engine.os,'sched_setaffinity'), patch.object(common.resource,'setrlimit') as limits:
                result=engine.fit_arm((7,'optional',str(root/'good'),c,4))
                self.assertEqual(result['arm'],'optional')
                limits.assert_called_with(common.resource.RLIMIT_AS,(8*1024**3,8*1024**3))
                saved=root/'good/w7/optional';self.assertEqual(json.loads((saved/'fit-sources.json').read_text()),sources)
                self.assertFalse(json.loads((saved/'fit-seal.json').read_text())['validation_loaded'])
                with patch.object(engine,'pool_rank',side_effect=TimeoutError('synthetic phase failure')):
                    with self.assertRaises(TimeoutError):engine.fit_arm((7,'optional',str(root/'bad'),c,4))
                failed=root/'bad/w7/optional';self.assertTrue((failed/'dictionary.json').exists())
                self.assertEqual(json.loads((failed/'failure.json').read_text())['phase'],'pool')
                self.assertFalse((failed/'fit-seal.json').exists())

    def test_all_unencodable_keeps_denominator_and_blocks_gate(self):
        texts={str(i):'class Solution:\n    def answer(self):\n        return 1\n' for i in range(36)}
        c={'partition':{'dev_fit':list(range(27)),'dev_val':list(range(27,36))},'entries':{p:'answer' for p in texts}}
        a=evaluate(texts,['x'],7,c);b=evaluate(texts,ALPHABET,7,c)
        self.assertEqual(a['validation']['covered'],0);self.assertEqual(a['validation']['problems'],9)
        self.assertIsNone(a['validation']['actions'])
        checks,paired=report.predicates(a,b,c['partition']['dev_val'])
        self.assertFalse(all(checks.values()));self.assertEqual(paired['worse'],9)
        _,tied=report.predicates(a,a,c['partition']['dev_val'])
        self.assertEqual(tied,{'better':0,'same':9,'worse':0})

class ArtifactTests(unittest.TestCase):
    def fixture(self,root):
        out=root/'run';out.mkdir();inputs=root/'inputs';inputs.mkdir();here=root/'code';here.mkdir()
        texts={str(i):f'class Solution:\n    def answer(self):\n        return {i}\n' for i in range(36)}
        fit={str(i):texts[str(i)] for i in range(27)}
        c={'partition':{'dev_fit':list(range(27)),'dev_val':list(range(27,36))},'entries':{p:'answer' for p in texts},
           'inputs':{},'code_hashes':{},'decoder_source_files':{},'offline_encoder_bytes':1,'search':{'moves':8},
           'predictions':{'P1':'R reproduces','P2':'optional fit improves','P3':'no ready width','P4':'all decode/qualify'}}
        for rel in ('literals.py','pass2/working/bitpack.py'):
            raw=(common.LIT/rel).read_bytes();c['decoder_source_files'][rel]={'sha256':sha(raw),'bytes':len(raw)}
        c['decoder_source_bytes']=sum(x['bytes'] for x in c['decoder_source_files'].values())
        def spec(name,obj):
            path=inputs/name;write(path,obj);return {'file':str(path),'sha256':sha(path.read_bytes())}
        q={'arms':[],'baseline':{}}
        for w in (7,8):
            c['inputs'][str(w)]={'fit':spec(f'fit{w}.json',fit),'sources':spec(f'sources{w}.json',texts),
                'original_sources':spec(f'original{w}.json',texts),'seed_dictionary':spec(f'seed{w}.json',ALPHABET),
                'baseline_dictionary':spec(f'baseline{w}.json',ALPHABET)}
            for arm in ('control','scope_joint'):
                q['arms'].append({**evaluate(texts,ALPHABET,w,c),'arm':arm,'qualification':{p:{'passed':True} for p in texts}})
            q['baseline'][str(w)]=evaluate(texts,ALPHABET,w,c)
        c['qualification']=spec('qualification.json',q);write(here/'contract.json',c)
        arms=[];summaries=[]
        for w in (7,8):
            for name in ('R','seed31','fixed96','optional'):
                folder=out/f'w{w}'/name;folder.mkdir(parents=True);write(folder/'dictionary.json',ALPHABET);write(folder/'sources.json',texts)
                a=evaluate(texts,ALPHABET,w,c);a.update(arm=name,dictionary_sha256=sha((folder/'dictionary.json').read_bytes()),
                    sources_sha256=sha((folder/'sources.json').read_bytes()),qualification_receipt_sha256=c['qualification']['sha256'])
                (folder/'dictionary.bin').write_bytes(analyze.dictionary_bytes(ALPHABET));(folder/'packets').mkdir()
                for p,t in texts.items():(folder/'packets'/f'{p}.bin').write_bytes(analyze.encode(ALPHABET,analyze.shortest_encode(t,ALPHABET),w))
                if name in ('fixed96','optional'):
                    write(folder/'fit-sources.json',fit);write(folder/'pool.json',[])
                    write(folder/'fit-seal.json',{'validation_loaded':False,'dictionary_sha256':a['dictionary_sha256'],
                        'fit_source_sha256':sha((folder/'fit-sources.json').read_bytes()),'pool_sha256':sha((folder/'pool.json').read_bytes())})
                    s={'width':w,'arm':name,'moves':[],'fit_selections':a['fit']['selections']['total'],
                       'fit_seal_sha256':sha((folder/'fit-seal.json').read_bytes())}
                    write(folder/'fit-summary.json',s);summaries.append(s)
                arms.append(a)
        write(out/'results.json',{'contract_sha256':sha((here/'contract.json').read_bytes()),'arms':arms,'seconds':1})
        write(out/'all-fit-sealed.json',{'validation_loaded':False,'summaries':summaries})
        write(out/'status.json',{'complete':True});write(out/'supervisor-receipt.json',{'complete':True})
        return out,c,here

    def test_full_replay_rejects_cost_packet_seal_and_failure_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            out,c,here=self.fixture(Path(tmp))
            with patch.object(report,'HERE',here):
                r=report.replay(out,c);self.assertEqual(len(r['arms']),8)
                self.assertFalse(any(x['optional_successor'] for x in r['verdicts_by_width'].values()))
                result=out/'results.json';original=result.read_bytes();bad=json.loads(original)
                bad['arms'][0]['per_problem']['0']['actions']-=1;write(result,bad)
                with self.assertRaises(AssertionError):report.replay(out,c)
                result.write_bytes(original)
                packet=out/'w7/R/packets/0.bin';raw=packet.read_bytes();packet.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
                with self.assertRaises((AssertionError,ValueError)):report.replay(out,c)
                packet.write_bytes(raw)
                seal=out/'w7/optional/fit-seal.json';raw=seal.read_bytes();seal.write_bytes(raw+b' ')
                with self.assertRaises(AssertionError):report.replay(out,c)
                seal.write_bytes(raw);write(out/'failure.json',{'complete':False})
                with self.assertRaises(AssertionError):report.replay(out,c)
                with self.assertRaises(AssertionError):report.main(out)
                receipt=json.loads((out/'report-failure.json').read_text())
                self.assertFalse(receipt['complete']);self.assertIsNone(receipt['verdicts_by_width'])
                self.assertEqual(receipt,json.loads((here/'evidence/results.json').read_text()))

    def test_optimized_python_launch_fails_before_any_run(self):
        p=subprocess.run([sys.executable,'-O',str(common.HERE/'launch.py'),'--help'],capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0);self.assertIn('Optimized Python',p.stderr)

if __name__=='__main__':unittest.main()
