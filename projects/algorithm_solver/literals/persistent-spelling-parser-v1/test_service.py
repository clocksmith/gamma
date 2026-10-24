"""Invented inputs only. No corpus loaders, benchmark or scientific execution."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
import client

LIT = Path(__file__).resolve().parents[1]


def load46():
    saved_path = list(sys.path); old = sys.modules.get('common')
    try:
        spec = importlib.util.spec_from_file_location('persistent_test_common46', LIT/'postfit-spelling-stack-v1/common.py')
        c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
        sys.modules['common'] = c
        spec = importlib.util.spec_from_file_location('persistent_test_engine46', LIT/'postfit-spelling-stack-v1/engine.py')
        e = importlib.util.module_from_spec(spec); spec.loader.exec_module(e)
        return c,e
    finally:
        sys.path[:] = saved_path
        if old is None: sys.modules.pop('common',None)
        else: sys.modules['common'] = old


c,e = load46()
TEXT = 'function solve(a){return a+a}'
MENU = {'names':['aa','ab'], 'contexts':[
    {'pattern':['return ',None,'+',None,'']},
    {'pattern':['return ',None,'+',None,'']}]}


def untimed(value):
    value = copy.deepcopy(value); value.pop('seconds',None); return value


class ServiceTests(unittest.TestCase):
    def test_scalar_parity_multiple_requests_and_original_key_shapes(self):
        inputs = [
            {'10':TEXT,'2':'const solve = (a) => a+1;'},
            {'2:'+('a'*64):'let solve = function(x){ /* c */ return "x"+x; };'},
            {'0':'const solve = (x)=>{return `a${x}`};'},
            {'0':'function solve(){return /x/.test("x");}'},
            {'0':TEXT,'1':TEXT}, {}, {'__proto__':TEXT},
        ]
        with client.Client() as service:
            pid = service.process.pid
            for texts in inputs:
                self.assertEqual(service.banned(texts),c.p.banned(texts))
                self.assertEqual(service.process.pid,pid)
                self.assertIsNone(service.process.poll())
            self.assertEqual(service.ident,len(inputs)-1)  # empty banned() calls no helper
        self.assertIsNotNone(service.process.returncode)

    def test_original_512_chunking(self):
        texts={str(i):TEXT for i in range(513)}
        with client.Client() as service:
            self.assertEqual(service.banned(texts),c.p.banned(texts))
            self.assertEqual(service.ident,2)

    def test_response_larger_than_pipe_chunk_is_complete(self):
        texts={'0':'function solve(a){/*'+('x'*100000)+'*/return a}'}
        with client.Client() as service:
            self.assertEqual(service.banned(texts),c.p.banned(texts))

    def test_parse_unicode_and_empty_body_caller_class_and_close(self):
        for text in ['function solve(',TEXT+'/*é*/','function solve(){}','function other(){return 1}',
                     'const solve=()=>{};']:
            with self.subTest(text=text):
                with self.assertRaises(subprocess.CalledProcessError): c.p.banned({'0':text})
                service=client.Client()
                with self.assertRaises(subprocess.CalledProcessError): service.banned({'0':text})
                self.assertTrue(service.closed);self.assertIsNotNone(service.process.returncode)
                with self.assertRaises(RuntimeError):service.banned({'0':TEXT})

    def test_lexical_serialization_and_byte_guard_boundary(self):
        texts={'0':TEXT+'/*comment*/','1':'const solve=(x)=>"a"+x;'}
        old=subprocess.run(['/usr/bin/node',str(LIT/'cost-decomposition-v1/lexical.cjs')],input=json.dumps(texts),
                           text=True,capture_output=True,check=True).stdout
        script='const m=require("./logic.cjs");const fs=require("fs");process.stdout.write(JSON.stringify(m.lexical(JSON.parse(fs.readFileSync(0,"utf8")))));'
        new=subprocess.run(['/usr/bin/node','-e',script],cwd=client.HERE,input=json.dumps(texts),
                           text=True,capture_output=True,check=True).stdout
        self.assertEqual(old,new)
        script='''const m=require('./logic.cjs');
if(m.LEXICAL_STDOUT_LIMIT!==33554432)throw Error('limit');
m.lexicalByteGuard('abc',3);m.lexicalByteGuard('é',2);
let caught=0;for(const [s,n] of [['abcd',3],['é',1]])try{m.lexicalByteGuard(s,n)}catch(e){if(e.code==='LEXICAL_STDOUT_LIMIT')caught++}
if(caught!==2)throw Error('boundary');'''
        subprocess.run(['/usr/bin/node','-e',script],cwd=client.HERE,check=True)

    def test_full_untimed_engine_menu_order_duplicate_trace_and_ledger(self):
        texts={'10':TEXT,'2':TEXT.replace('(a)','(b)').replace('a+a','b+b')}
        vocab=list(reversed(c.p.ALPHABET))+['aa','ab']
        before_menu=e.menu(texts,vocab)
        old=e.apply(texts,vocab,MENU)
        with client.Client() as service,patch.object(c.p,'banned',service.banned):
            self.assertEqual(before_menu,e.menu(texts,vocab))
            new=e.apply(texts,vocab,MENU)
        self.assertEqual(untimed(old),untimed(new))
        self.assertEqual(new['trace'][0]['pid'],'2')
        self.assertGreater(new['proposals'],len(new['ledger']['variants'])-len(texts))
        self.assertEqual(new['vocab'],vocab)
        self.assertTrue(new['complete'])

    def test_unchanged_failure_prefixes_parse_and_global_collision(self):
        renamed=TEXT.replace('(a)','(aa)').replace('a+a','aa+aa')
        cases=[({'0':TEXT},{'own':c.p.ALPHABET,'other':c.p.ALPHABET+[renamed]},c.LegalityFailure),
               ({'0':'function solve('},None,subprocess.CalledProcessError),
               ({'0':TEXT+'/*é*/'},None,subprocess.CalledProcessError)]
        for texts,dictionaries,error in cases:
            baseline=[];actual=[]
            with self.assertRaises(error):e.apply(texts,c.p.ALPHABET,MENU,checkpoint=baseline.append,dictionaries=dictionaries)
            with client.Client() as service,patch.object(c.p,'banned',service.banned):
                with self.assertRaises(error):e.apply(texts,c.p.ALPHABET,MENU,checkpoint=actual.append,dictionaries=dictionaries)
            self.assertEqual([untimed(x) for x in baseline],[untimed(x) for x in actual])
            self.assertFalse(actual[-1]['complete'])

    def test_request_limit_is_new_explicit_failure_envelope(self):
        service=client.Client()
        with patch.object(client,'REQUEST_LIMIT',16):
            with self.assertRaises(subprocess.CalledProcessError) as caught:service.banned({'0':TEXT})
        self.assertEqual(caught.exception.stderr,'REQUEST_LIMIT');self.assertTrue(service.closed)

    def fake_client(self,code,timeout=1):
        spawn=subprocess.Popen
        def fake(*args,**kwargs):return spawn([sys.executable,'-c',code],**kwargs)
        with patch.object(client.subprocess,'Popen',side_effect=fake):return client.Client(timeout=timeout)

    def test_wrong_id_missing_body_extra_output_and_exit_close(self):
        responses=[{'id':9,'ok':True,'bodies':{'0':['x']}},
                   {'id':1,'ok':True,'bodies':{}},
                   {'id':1,'ok':False,'error':'not_a_fixed_enum'}]
        for response in responses:
            code='import sys;sys.stdin.readline();print('+repr(json.dumps(response))+',flush=True);sys.stdin.read()'
            service=self.fake_client(code)
            with self.assertRaises(subprocess.CalledProcessError):service.banned({'0':TEXT})
            self.assertTrue(service.closed);self.assertIsNotNone(service.process.returncode)
        service=self.fake_client('pass')
        with self.assertRaises(subprocess.CalledProcessError):service.banned({'0':TEXT})
        self.assertTrue(service.closed)

    def test_timeout_and_outer_baseexception_close(self):
        service=self.fake_client('import time;time.sleep(5)',timeout=.05)
        with self.assertRaises(subprocess.TimeoutExpired):service.banned({'0':TEXT})
        self.assertTrue(service.closed);self.assertIsNotNone(service.process.returncode)
        class OuterDeadline(BaseException):pass
        service=client.Client()
        with patch.object(client.selectors.DefaultSelector,'select',side_effect=OuterDeadline):
            with self.assertRaises(OuterDeadline):service.banned({'0':TEXT})
        self.assertTrue(service.closed);self.assertIsNotNone(service.process.returncode)

    def test_concurrent_request_rejected_and_primary_exception_not_masked(self):
        service=client.Client();service._request_lock.acquire()
        try:
            with self.assertRaises(subprocess.CalledProcessError):service.request({'0':TEXT})
        finally:service._request_lock.release()
        self.assertTrue(service.closed);self.assertIsNotNone(service.process.returncode)
        service=client.Client();close=service.close
        def failed_close():close();raise RuntimeError('invented cleanup failure')
        with patch.object(service,'close',side_effect=failed_close):
            with self.assertRaises(subprocess.CalledProcessError) as caught:service.request({'0':'bad syntax @'})
        self.assertIn('Parser cleanup failed',caught.exception.__notes__[0])
        self.assertIsNotNone(service.process.returncode)

    def test_response_limit_and_group_affinity_inheritance(self):
        service=client.Client()
        self.assertEqual(os.getpgid(service.process.pid),os.getpgrp())
        self.assertEqual(os.sched_getaffinity(service.process.pid),os.sched_getaffinity(0))
        with patch.object(client,'RESPONSE_LIMIT',16):
            with self.assertRaises(subprocess.CalledProcessError):service.banned({'0':TEXT})
        self.assertTrue(service.closed)


if __name__=='__main__':unittest.main()
