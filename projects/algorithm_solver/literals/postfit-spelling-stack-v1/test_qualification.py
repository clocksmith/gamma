"""Deduplication/failure preservation with invented receipt data; no sandbox run."""
import concurrent.futures as futures
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import common as c
import qualification as q

class InlinePool:
    def __init__(self,**kwargs):pass
    def submit(self,fn,args):
        future=futures.Future()
        try:future.set_result(fn(args))
        except BaseException as error:future.set_exception(error)
        return future
    def shutdown(self,**kwargs):pass
    def terminate_workers(self):pass

class QualificationTests(unittest.TestCase):
    def test_duplicate_hash_runs_once_and_failed_hash_stays_failed(self):
        for passed in (True,False):
            with self.subTest(passed=passed),tempfile.TemporaryDirectory() as folder:
                root=Path(folder);out=root/'out';work=root/'work';calls=[]
                text='function solve(a){return a}';digest=c.sha(text.encode())
                c.write(out/'all-validation-sealed.json',{'qualification_started':False})
                c.write(out/'global-ledger.json',{'legal':True})
                c.write(work/'population500/manifest.json',{'rows':[{'id':0}]})
                arms=[]
                for name in ('24-S','43N-S'):
                    c.write(out/'artifacts'/name/'sources.json',{'0':text})
                    arms.append({'arm':name,'dictionary_bytes':5,'per_problem':{'0':{
                        'source_sha256':digest,'source_bytes':len(text),'encodable':True,'selections':3,
                        'actions':4,'single_characters':1,'packet_bytes':44}}})
                config={'active':True,'source_bound':True,'work':str(work),
                    'manifest_sha256':c.hashfile(work/'population500/manifest.json'),'qualification':[{'id':0,'files':{}}],
                    'known_receipts':{},'all_cores':[0,1,2,3],'partition':{'dev_fit':[0],'dev_val':[]},'decoder_dependency_bytes':13010}
                def run(args):calls.append(args);return (passed,2 if passed else 1,2,{} if passed else {'mismatch':1},'raw-digest')
                with patch.object(q.futures,'ProcessPoolExecutor',InlinePool),patch.object(q,'job',side_effect=run):
                    got=q.qualify(out,config,arms)
                self.assertEqual(len(calls),1);self.assertEqual(got['distinct_new_sources'],1)
                self.assertEqual(got['failed_sources'],0 if passed else 1)
                self.assertTrue(c.read(out/'qualification-private.json')['complete'])
                for arm in arms:self.assertEqual(arm['per_problem']['0']['qualified_source'],passed)

if __name__=='__main__':unittest.main()
