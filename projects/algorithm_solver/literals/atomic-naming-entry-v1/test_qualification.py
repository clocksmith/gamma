"""Invented strict-observation fixtures; sandbox results are injected, not executed."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import core as c
import qualification


def fixture(root):
    source='function solve(a){return a+1;}'
    record={'result':2,'result_type':'number','args_before':[1],'args_after':[1],'alias_edges':[],'error':None}
    c.write(root/'population500/1-tests.json',[{'args':[1],'expected':2}])
    c.write(root/'population500-baseline/qualification/baselines/1.json',[record])
    return source,record,{'id':1,'transport':'standard'}


class QualificationTests(unittest.TestCase):
    def test_raw_batch_preserves_strict_success_and_mismatch(self):
        c.module('atomic_test_minify',c.LIT/'minify-control-v1/minify.py')
        from algsolve.judge import sandbox
        for mismatch in (False,True):
            with self.subTest(mismatch=mismatch),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);source,record,spec=fixture(root);record['args_after']=[9] if mismatch else [1]
                stdout=(json.dumps(record)+'\n'+json.dumps({'done':1})+'\n').encode()
                injected=sandbox.SandboxResult(0,None,stdout,b'invented stderr',.001)
                raw=root/'raw'
                with patch.object(sandbox,'run',return_value=injected) as execute:
                    passed,ok,total,bad,digest=qualification.execute(root,1,source,spec,raw)
                self.assertEqual(execute.call_count,1);self.assertEqual(passed,not mismatch)
                self.assertEqual((ok,total),(0 if mismatch else 1,1));self.assertEqual(bool(bad),mismatch)
                receipt=c.read(raw/'receipt.json');self.assertTrue(receipt['complete']);self.assertEqual(digest,c.sha((raw/'receipt.json').read_bytes()))
                batch=receipt['batches'][0];self.assertEqual((batch['offset'],batch['count']),(0,1))
                self.assertEqual(batch['input_files']['program.js'],c.sha(source.encode()))
                self.assertEqual((raw/batch['stdout']).read_bytes(),stdout);self.assertEqual(batch['stdout_sha256'],c.sha(stdout))
                self.assertEqual(batch['stderr_sha256'],c.sha(b'invented stderr'));self.assertFalse(batch['output_limit_exceeded'])

    def test_raw_timeout_and_exception_remain_failed(self):
        c.module('atomic_test_minify_failure',c.LIT/'minify-control-v1/minify.py')
        from algsolve.judge import sandbox
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source,_,spec=fixture(root)
            injected=sandbox.SandboxResult(None,None,b'',b'timeout',1.0,timed_out=True)
            with patch.object(sandbox,'run',return_value=injected):
                passed,ok,total,bad,_=qualification.execute(root,1,source,spec,root/'timeout')
            self.assertFalse(passed);self.assertEqual(ok,0);self.assertTrue(bad)
            receipt=c.read(root/'timeout/receipt.json');self.assertTrue(receipt['batches'][0]['timed_out'])
            with patch.object(sandbox,'run',side_effect=RuntimeError('invented unavailable')):
                with self.assertRaises(RuntimeError):qualification.execute(root,1,source,spec,root/'exception')
            receipt=c.read(root/'exception/receipt.json');self.assertFalse(receipt['complete']);self.assertFalse(receipt['batches'][0]['complete'])
            self.assertEqual(receipt['batches'][0]['error_type'],'RuntimeError')

if __name__=='__main__':unittest.main()
