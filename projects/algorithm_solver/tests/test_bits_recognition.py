import hashlib
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

import numpy as np

from algsolve.bits_recognition import BitsRecognizer
from algsolve.bits_server import create_server


class Runtime:
    def __init__(self):self.calls=[]; self.last_receipt={'embedding_rows':[{'truncated':False}]}
    def encode(self, texts, **kwargs):
        self.calls.append(('embedding', texts));return np.array([[1.,0.]])
    def rerank_evidence(self, query, documents):
        self.calls.append(('rerank',query,documents))
        return [{'trueLogit':10.,'falseLogit':20.},{'trueLogit':9.,'falseLogit':0.}]


class RecognitionTests(unittest.TestCase):
    def setUp(self):
        self.recognizer=BitsRecognizer.__new__(BitsRecognizer)
        self.recognizer.keys=['lc:first','lc:second']
        self.recognizer.metadata={k:{'key':k,'slug':slug,'title':title,'problem_id':f'leetcode:{i}'}
            for i,(k,slug,title) in enumerate([('lc:first','first','First Problem'),('lc:second','second','Second Problem')],1)}
        self.recognizer.vectors=np.array([[1.,0.],[.8,.6]])
        self.recognizer.identity_sha256='frozen-index'
        self.recognizer.lock=threading.Lock(); self.recognizer.runtime=Runtime()
        self.recognizer.runtime_factory=None
        self.recognizer.document=lambda key:(self.recognizer.metadata[key]['title'],'title-only')

    def test_exact_metadata_does_not_execute_models_or_open_statements(self):
        result=self.recognizer.recognize('First Problem')
        self.assertEqual(result['method'],'exact-metadata')
        self.assertEqual(result['candidates'][0]['key'],'lc:first')
        self.assertEqual(self.recognizer.runtime.calls,[])
        self.assertFalse(result['recognition_qualified'])

    def test_semantic_discovery_preserves_identity_and_uses_yes_minus_no(self):
        text='A description without an exact title.'
        result=self.recognizer.recognize(text)
        self.assertEqual(result['candidates'][0]['key'],'lc:second')
        self.assertEqual(result['query_sha256'],hashlib.sha256(text.encode()).hexdigest())
        self.assertNotIn('source',json.dumps(result))
        self.assertNotIn('tests',json.dumps(result))

    def test_truncated_query_abstains_and_busy_requests_do_not_queue(self):
        self.recognizer.runtime.last_receipt['embedding_rows'][0]['truncated']=True
        self.assertEqual(self.recognizer.recognize('description')['status'],'abstain')
        self.assertEqual(len(self.recognizer.runtime.calls),1)
        self.recognizer.lock.acquire()
        with self.assertRaises(RuntimeError):self.recognizer.recognize('description')
        self.recognizer.lock.release()

    def test_protected_statement_is_not_opened(self):
        self.recognizer.gate={'artifact_paths':{},'trusted_hashes':{}}
        with patch('projects.algorithm_solver.catalogue.boundary_policy.authorize_before_open',side_effect=PermissionError):
            self.assertEqual(BitsRecognizer.document(self.recognizer,'lc:first'),('First Problem','title-only'))


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);(self.root/'index.html').write_text('BITS')
        class Recognizer:
            def recognize(self,text):return {'status':'candidates','candidates':[]}
        self.server=create_server(self.root,Recognizer(),0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.close)
    def close(self):
        self.server.shutdown();self.server.server_close();self.thread.join(timeout=2)
    def request(self,method,path,body=None,headers=None):
        connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=3)
        connection.request(method,path,body=body,headers=headers or {})
        response=connection.getresponse();result=response.status,response.read();connection.close();return result
    def test_same_origin_api_binds_request_and_rejects_cross_origin(self):
        body=json.dumps({'text':'description','request_id':'r1'})
        headers={'Origin':f'http://127.0.0.1:{self.server.server_port}',
                 'Content-Type':'application/json','X-Bits-Request':'recognize'}
        status,raw=self.request('POST','/api/bits/recognize',body,headers)
        self.assertEqual(status,200);self.assertEqual(json.loads(raw)['request_id'],'r1')
        self.assertEqual(self.request('POST','/api/bits/recognize',body,dict(headers,Origin='https://attacker.example'))[0],403)
        self.assertEqual(self.request('POST','/api/bits/recognize',body,{'Content-Type':'application/json'})[0],403)
    def test_static_root_cannot_expose_private_files_or_symlink_targets(self):
        (self.root/'.private').write_text('hidden')
        (self.root/'outside').symlink_to('/etc/passwd')
        self.assertEqual(self.request('GET','/')[0],200)
        self.assertEqual(self.request('GET','/.private')[0],403)
        self.assertEqual(self.request('GET','/outside')[0],403)
        self.assertEqual(self.request('GET','/','',{'Host':'attacker.example'})[0],403)


if __name__=='__main__':unittest.main()
