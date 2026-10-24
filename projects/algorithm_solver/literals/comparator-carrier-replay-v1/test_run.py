"""Invented end-to-end adapter/decision/publication fixtures, no corpus reads."""
import copy
import json
from pathlib import Path
import signal
import tempfile
import time
import types
import unittest
from unittest.mock import patch
import common as c
import decisions
import run
from test_adapter import Fixture

class BanStub:
    def __init__(self,*args):pass
    def extend(self,values):self.values=values
    def banned(self,values):return set()
    def receipt(self):return {'parsed_variants':len(self.values),'persistent_parser_used':False}

class RunTests(unittest.TestCase):
    def tearDown(self):signal.setitimer(signal.ITIMER_REAL,0)
    def test_invented_full_adapter_decisions_and_safe_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Fixture(Path(tmp));r=c.shared('report');parent=f.f.config;arms=[]
            base=f.f.index['43N-U','canonical'];db=base['dictionary_bytes']
            for anchor in ('24','43N','43W'):
                for suffix in ('U','S'):
                    for policy in r.POLICIES:
                        a=copy.deepcopy(base);a.update(arm=anchor+'-'+suffix,policy=policy,width=8,illegal_entry_sha256=[])
                        for row in a['per_problem'].values():
                            row.update(source_byte_delta=0,packet_sha256='a'*64,one_program_package_bytes=db+row['packet_bytes'],one_program_package_with_decoder_dependencies=db+row['packet_bytes']+17)
                        a['qualification']={pid:{'passed':True} for pid in a['per_problem']}
                        for split,key in (('fit','dev_fit'),('validation','dev_val')):a[split]=r.aggregate(a['per_problem'],parent['partition'][key],db,17)
                        arms.append(a)
            references={(name,p):next(a for a in arms if a['arm']=='43N-U' and a['policy']==p) for name in ('R','seed13','best24','N','NCP') for p in r.POLICIES}
            best={p:references['R',p] for p in r.POLICIES}
            outcome=decisions.decisions(arms,references,parent,best,{'resolved':True},r.aggregate)
            e={'arms':arms,**outcome};e['predictions']['P4']=None
            class Reader:
                def __init__(self,*args):self.private_reads=[]
                def __call__(self,base,path,h):
                    value=f.reader(base,path,h)
                    if Path(base)==f.f.work:self.private_reads.append({'path':path,'sha256':h,'bytes':(Path(base)/path).stat().st_size})
                    return value
            config={'comparator_binding':f.f.binding,'private_inputs':{p:'unused' for p in f.allowed},'recorded54_commit':'invented54','fixed51_commit':'invented51','authorities':{},'offline_implementation_bytes':123}
            actual_shared=c.shared
            def shared(name):return types.SimpleNamespace(BanReplay=BanStub) if name=='ban_replay' else actual_shared(name)
            with patch.object(r.c,'LIT',f.f.public),patch.object(c,'verify'),patch.object(run.binding,'public_inputs',return_value=(parent,e,references)),patch.object(c,'Reader',Reader),patch.object(c,'shared',side_effect=shared),patch.object(c,'hashfile',return_value='b'*64):
                result=run.execute(config,time.monotonic()+10)
            signal.setitimer(signal.ITIMER_REAL,0)
            result.update(worker_seconds=.1,peak_rss_kib=100);run.validate_output(result)
            bad=copy.deepcopy(result);bad['private_debug']='must reject'
            with self.assertRaises(AssertionError):run.validate_output(bad)
            self.assertTrue(result['complete']);self.assertEqual(result['decoded_comparator_packets'],800)
            self.assertEqual(result['candidate_packets_replayed_here'],0);self.assertTrue(result['historical_only']);self.assertFalse(result['current_best_claim'])
            self.assertEqual(len(result['candidates']),12);self.assertEqual(result['comparator']['shortest_min_char']['validation']['single_character_codes'],0)
            self.assertEqual(result['comparator']['canonical']['validation']['single_character_codes'],100)
            self.assertFalse('"abcd"' in json.dumps(result));self.assertEqual(result['parent54_P4_preserved'],None)
    def test_failure_publication_and_shared_deadline(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);(out/'results.json').write_text('{"complete":true}');(out/'REPORT.md').write_text('stale')
            signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(run.Deadline()))
            error=ValueError('private detail excluded');run.withdraw(out,error,time.monotonic()+10)
            self.assertFalse(c.read(out/'results.json')['complete']);self.assertNotIn('private detail',(out/'failure.json').read_text())
            first=error._carrier58_failure_deadline;self.assertLessEqual(run.failure_bound(error,time.monotonic()+100),first)
    def test_slow_first_failure_write_has_no_later_operations(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);calls=[]
            signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(run.Deadline()))
            def slow(path,value):calls.append(Path(path).name);time.sleep(2)
            error=ValueError();error._carrier58_failure_deadline=time.monotonic()+.05
            started=time.monotonic()
            with patch.object(c,'write',side_effect=slow):
                with self.assertRaises(run.Deadline):run.withdraw(out,error,time.monotonic()+10)
            self.assertEqual(calls,['failure.json']);self.assertLess(time.monotonic()-started,.5)
    def test_real_old_parser_supplied_sources(self):
        texts={'1':'function solve(x){ return x+1; }','2':'function solve(x){ return x+2; }'}
        prior=c.shared('report');variants={f'{pid}:{c.sha(t.encode())}':t for pid,t in texts.items()}
        proof=c.shared('ban_replay').BanReplay(c.LIT/'tail-search-v1/structure.cjs',time.monotonic()+10,run.Deadline)
        proof.extend(variants);self.assertEqual(proof.banned(variants),prior.p.banned(variants));self.assertEqual(proof.parsed_variants,2)
if __name__=='__main__':unittest.main()
