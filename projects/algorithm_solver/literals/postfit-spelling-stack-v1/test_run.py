"""Invented six-view pipeline; tests access barriers without private corpus reads."""
import copy
import os
from pathlib import Path
import platform
import tempfile
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
    return work,out,config


class RunTests(unittest.TestCase):
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
