"""Focused development-harness controls; these do not qualify the 66 candidates."""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('bounded_development_runner',HERE/'run.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)


class HarnessControls(unittest.TestCase):
    def test_exact_comparison_preserves_json_types(self):
        self.assertFalse(runner.equal(True,1));self.assertFalse(runner.equal(False,0));self.assertFalse(runner.equal('1',1));self.assertFalse(runner.equal([1],[1,2]));self.assertFalse(runner.equal(float('nan'),float('nan')));self.assertFalse(runner.equal(float('inf'),float('inf')))
        self.assertTrue(runner.equal({'x':[1,False,None]},{'x':[1.0,False,None]}))

    def invoke(self,language,code,args,timeout=3):
        with tempfile.TemporaryDirectory(prefix='dev66-control-') as td:
            source=Path(td)/('candidate.py' if language=='python' else 'candidate.js');source.write_text(code)
            command=[sys.executable,str(HERE/'run-case.py'),str(source)] if language=='python' else ['node','--jitless','--max-old-space-size=512',str(HERE/'run-case.cjs'),str(source)]
            process=subprocess.run(command,input=json.dumps(args),capture_output=True,text=True,timeout=timeout,check=True)
            response=json.loads(process.stdout);self.assertEqual(response['sourceSha256'],hashlib.sha256(source.read_bytes()).hexdigest());return response

    def test_wrong_answer_and_input_mutation_are_observable(self):
        for language,code in [('python','def solve(a):\n a.append(99)\n return -1\n'),('javascript','module.exports=function(a){a.push(99);return -1;};')]:
            result=self.invoke(language,code,[[1]]);self.assertFalse(runner.equal(result['result'],1));self.assertFalse(runner.equal(result['argumentsAfter'],[[1]]));self.assertIsNone(result['exception'])

    def test_exceptions_are_not_successful_null_results(self):
        for language,code in [('python','def solve():\n raise ValueError("control")\n'),('javascript','module.exports=function(){throw new Error("control");};')]:
            result=self.invoke(language,code,[]);self.assertIsNotNone(result['exception']);self.assertIn('control',result['exception']['message'])

    def test_stalled_calls_have_a_process_timeout(self):
        for language,code in [('python','def solve():\n while True: pass\n'),('javascript','module.exports=function(){while(true){}};')]:
            with self.assertRaises(subprocess.TimeoutExpired):self.invoke(language,code,[],timeout=.25)

    def test_existing_receipts_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            sentinel=Path(td)/'results.json';sentinel.write_text('immutable receipt')
            process=subprocess.run([sys.executable,str(HERE/'run.py'),'--output',td],capture_output=True,text=True,timeout=3)
            self.assertNotEqual(process.returncode,0);self.assertEqual(sentinel.read_text(),'immutable receipt')

    def test_unknown_selection_cannot_pass_as_an_empty_run(self):
        with tempfile.TemporaryDirectory() as td:
            process=subprocess.run([sys.executable,str(HERE/'run.py'),'--output',str(Path(td)/'new'),'--only','999999'],capture_output=True,text=True,timeout=3)
            self.assertNotEqual(process.returncode,0);self.assertIn('Unknown requested development IDs',process.stderr);self.assertFalse((Path(td)/'new/results.json').exists())


if __name__=='__main__':unittest.main()
