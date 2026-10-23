"""Invented300-source artifact bundle: replay/cost/q/failure checks only."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import implicit
import optimize
import backend
# Named loading avoids the unrelated report.py modules imported by old utilities.
report=backend.module('length_sensitive_synthetic_report',backend.HERE/'report.py')

class ReportTests(unittest.TestCase):
    def fixture(self,root):
        here=root/'code';lit=root/'lit';work=root/'work';out=root/'out'
        for p in (here,lit,work,out):p.mkdir()
        texts={str(i):'function solve(x){return x+1}' for i in range(300)};seed=sorted(set(next(iter(texts.values()))))
        banned=backend.dual.sel.forbidden_strings(texts);index=implicit.Index(texts,banned)
        oldq={p:[0]*len(t) for p,t in texts.items()};oldcert=index.base.certificate(oldq,256,1000)
        c={'fit_ids':list(range(300)),'cohorts':{'R':'R','naming':'naming'},'private_files':{},'code_hashes':{},'runtime_files':{},
           'decoder_source_files':{},'decoder_dependency_bytes':13010,'offline_encoder_bytes':1,'offline_encoder_scope':'synthetic',
           'pool':{'capacity':256,'scope':'synthetic full substring'},'parent_evidence':'parent.json','parent_private_results':'parent-private.json',
           'limits':{'overall_seconds':2400},
           'parent_q':{},'search':{'iterations':1,'seconds':10,'denominator':1000,'halve_after':30,'primal_every':25}}
        for rel in ('literals.py','pass2/working/bitpack.py'):
            path=lit/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((backend.LIT/rel).read_bytes())
            c['decoder_source_files'][rel]={'sha256':backend.sha(path),'bytes':path.stat().st_size}
        proof={'arms':[]};parent_public={'complete':True,'validation_loaded':False,'arms':[]};parent_private={'complete':True,'validation_loaded':False,'arms':[]}
        for cohort in ('R','naming'):
            folder=work/cohort;folder.mkdir()
            for name,value in [('fit-sources.json',texts),('dictionary.json',seed),('parent-q.json',oldq)]:
                backend.write(folder/name,value);c['private_files'][f'{cohort}/{name}']=backend.sha(folder/name)
            c['parent_q'][cohort]=f'{cohort}/parent-q.json'
            cert={k:oldcert[k] for k in optimize.CERT_KEYS};cert['q_sha256']=backend.sha(folder/'parent-q.json')
            counts={'pool_entries':index.distinct_allowed_entries,'implicit_groups':len(index.base.groups),'source_characters':len(index.base.positions),
                    'exact_ban_occurrences':sum(len(s) for rows in index.base.banned_ends.values() for s in rows)}
            a={'cohort':cohort,'complete':True,'validation_loaded':False,'fit_source_sha256':backend.sha(folder/'fit-sources.json'),
               **counts,'optimization':{'certificate':cert}}
            parent_public['arms'].append(a);parent_private['arms'].append(copy.deepcopy(a))
            proof['arms'].append({'arm':'control' if cohort=='R' else 'scope_joint','width':8,
                'per_problem':{p:{'source_sha256':backend.analyze.sha(t.encode())} for p,t in texts.items()},'qualification':{p:{'passed':True} for p in texts}})
        backend.write(work/'parent-private.json',parent_private);parent_public['private_results_sha256']=backend.sha(work/'parent-private.json')
        c['private_files']['parent-private.json']=parent_public['private_results_sha256']
        backend.write(lit/'parent.json',parent_public);(lit/'binding-descent-v1/evidence').mkdir(parents=True)
        backend.write(lit/'binding-descent-v1/evidence/results.json',proof)
        for rel in ('parent.json','binding-descent-v1/evidence/results.json'):c['code_hashes'][rel]=backend.sha(lit/rel)
        backend.write(here/'contract.json',c);chash=backend.sha(here/'contract.json');arms=[]
        for cohort in ('R','naming'):
            folder=out/f'{cohort}-flex256';folder.mkdir();traces=[]
            info,q,clean_seed,best,generated=optimize.optimize(index,seed,oldq,oldcert,256,c['search'],traces.append)
            for row in traces:row['validation_loaded']=False
            (folder/'trace.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in traces))
            backend.write(folder/'certificate-q.json',q);info['certificate']['q_sha256']=backend.sha(folder/'certificate-q.json')
            witnesses={}
            for name,vocab in [('seed',clean_seed),('best',best),('generated',generated)]:
                if vocab is not None:witnesses[name]=backend.measure(texts,vocab,folder/name,13010)
            raw={'cohort':cohort,'mode':'flex256','complete':True,'validation_loaded':False,'contract_sha256':chash,
                 'fit_problems':300,'fit_source_sha256':c['private_files'][f'{cohort}/fit-sources.json'],
                 'parent_q_sha256':backend.sha(work/c['parent_q'][cohort]),**counts,'length_pieces':len(index.pieces),
                 'capacity':256,'mandatory_entries':0,'pool_scope':c['pool']['scope'],'pool_seconds':0.,'seconds':1.,
                 'optimization':info,'witnesses':witnesses,'ignored_private_payload':'MUST_NOT_PUBLISH'}
            backend.write(folder/'results.json',raw);backend.write(folder/'status.json',{'phase':'complete','complete':True});arms.append(raw)
        aggregate={'arms':arms,'complete':True,'validation_loaded':False,'contract_sha256':chash,'seconds':2.}
        backend.write(out/'results.json',aggregate)
        return here,lit,work,out,c,aggregate

    def test_complete_artifact_replay_corruptions_and_failure_without_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            here,lit,work,out,c,aggregate=self.fixture(Path(tmp))
            result=report.build_report(out,work,here,lit);report.write_report(result,here)
            self.assertTrue(result['complete']);self.assertGreaterEqual(result['decoded_packets'],1200)
            self.assertNotIn('MUST_NOT_PUBLISH',(here/'evidence/results.json').read_text())
            self.assertNotIn('function solve',(here/'evidence/results.json').read_text())
            def corrupt(change):
                altered=copy.deepcopy(aggregate);change(altered['arms'][0])
                backend.write(out/'results.json',altered);backend.write(out/'R-flex256/results.json',altered['arms'][0])
                with self.assertRaises((AssertionError,ValueError)):report.build_report(out,work,here,lit)
                backend.write(out/'results.json',aggregate);backend.write(out/'R-flex256/results.json',aggregate['arms'][0])
            corrupt(lambda a:a.__setitem__('length_pieces',a['length_pieces']+1))
            corrupt(lambda a:a['witnesses']['seed']['per_problem']['0'].__setitem__('characters',999))
            corrupt(lambda a:a['optimization'].__setitem__('finite_numerator_gain',999))
            corrupt(lambda a:a.__setitem__('seconds',aggregate['seconds']+1))
            outside=copy.deepcopy(aggregate);outside['seconds']=c['limits']['overall_seconds']+.1
            backend.write(out/'results.json',outside)
            with self.assertRaises(AssertionError):report.build_report(out,work,here,lit)
            backend.write(out/'results.json',aggregate)
            tracepath=out/'R-flex256/trace.jsonl';saved_trace=tracepath.read_text()
            for key,payload in (('exact_numerator','MUST_NOT_PUBLISH'),('improved','MUST_NOT_PUBLISH'),('duplicate_of',['MUST_NOT_PUBLISH'])):
                traces=[json.loads(line) for line in saved_trace.splitlines()]
                self.assertEqual(traces[1]['status'],'duplicate_baseline')
                traces[1][key]=payload
                tracepath.write_text(''.join(json.dumps(row)+'\n' for row in traces))
                corrupt(lambda a:a['optimization']['bin_release'][0].__setitem__(key,payload))
                tracepath.write_text(saved_trace)
            qpath=out/'R-flex256/certificate-q.json';original=qpath.read_bytes();q=json.loads(original);q['0'][0][0]+=123456789;backend.write(qpath,q)
            corrupt(lambda a:a['optimization']['certificate'].__setitem__('q_sha256',backend.sha(qpath)));qpath.write_bytes(original)
            packet=out/'R-flex256/seed/packets/0.bin';original=packet.read_bytes();packet.write_bytes(original[:-1]+b'\xff')
            with self.assertRaises((AssertionError,ValueError)):report.build_report(out,work,here,lit)
            packet.write_bytes(original)
            failure={'complete':False,'partial_certificates_promoted':False,'contract_sha256':aggregate['contract_sha256'],
                     'exception':'TimeoutError','seconds':2400.1,'validation_loaded':False}
            backend.write(out/'failure.json',failure)
            incomplete=report.build_report(out,Path(tmp)/'nonexistent-inputs',here,lit)
            self.assertFalse(incomplete['complete']);self.assertNotIn('arms',incomplete)
            report.write_report(incomplete,here);self.assertIn('no whole-job certificate',(here/'README.md').read_text())
            failure['validation_loaded']=True;backend.write(out/'failure.json',failure)
            with self.assertRaises(AssertionError):report.build_report(out,Path(tmp)/'nonexistent-inputs',here,lit)

if __name__=='__main__':unittest.main()
