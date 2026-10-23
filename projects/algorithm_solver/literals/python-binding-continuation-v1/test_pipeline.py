"""Synthetic exact-search, packet and qualification checks; no corpus imports."""
import json
from pathlib import Path
import tempfile
from unittest import mock
import sys
import unittest
from backend import analyze,body,polish,LIT,HERE,module
from qualification import parse,qualify_one,sandbox

class PipelineTests(unittest.TestCase):
    def test_capped_search_preserves_feasible_incumbent(self):
        text='class Solution:\n def solve(self,n):\n  answer=n+1\n  return answer\n'
        variants={1:{'original':text},2:{'original':text.replace('n+1','n+2')}}
        alphabet=[chr(i) for i in range(32,127)]+['\n']
        cfg={'search':{'trials':1,'seconds':60},'neighborhood':{'additions':96,'swaps':500,'pairs':150,'pair_additions':16,'pair_removals':8,'designed_fraction':.25}}
        state,info=polish(variants,alphabet,7,{1:'solve',2:'solve'},cfg,True)
        self.assertEqual(info['trials'],1)
        self.assertEqual(state['vocab'],alphabet)
        for pid,v in variants.items():
            selected=v[state['chosen'][pid]];packet=analyze.encode(state['vocab'],analyze.shortest_encode(selected,state['vocab']),7)
            self.assertEqual(analyze.decode(analyze.dictionary_bytes(state['vocab']),packet),selected)

    def qualification(self,candidate):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);tests=[{'args':[3],'expected':4},{'args':[6],'expected':7}]
            source='class Solution:\n def solve(self,n):return n+1\n'
            result=sandbox.run(['/usr/bin/python3','harness.py'],files={'harness.py':(LIT/'python-name-v1/harness.py').read_bytes(),
                'candidate.py':source,'inputs.json':json.dumps({'entry':'solve','calls':[{'args':t['args']} for t in tests]})})
            self.assertTrue(result.ok,result.stderr);(p/'tests.json').write_text(json.dumps(tests));(p/'baseline').write_bytes(result.stdout)
            spec={'entry':'solve','cases':2,'tests_file':str(p/'tests.json'),'tests_sha256':analyze.sha((p/'tests.json').read_bytes()),
                  'baseline_calls':[{'file':str(p/'baseline'),'sha256':analyze.sha(result.stdout),'cases':2}]}
            return qualify_one({'spec':spec,'source':candidate,'folder':str(p/'receipt')})

    def test_changed_local_passes_strict_qualification(self):
        q=self.qualification('class Solution:\n def solve(self,n):\n  result=n+1\n  return result\n')
        self.assertTrue(q['passed']);self.assertEqual(q['checks_passed'],2)

    def test_equal_numeric_wrong_type_fails(self):
        q=self.qualification('class Solution:\n def solve(self,n):return float(n+1)\n')
        self.assertFalse(q['passed'])

    def test_strict_protocol(self):
        with self.assertRaises(ValueError):parse(b'{"i":0,"i":0}\n{"done":1}\n',1)
        with self.assertRaises((ValueError,AssertionError)):parse(b'{"done":1}\n',1)

    def test_python_body_forbidden(self):
        source='class Solution:\n def solve(self,n):return n+1\n'
        self.assertIn('return n+1',body.forbidden(source,'solve'))
        self.assertIn(source,body.forbidden(source,'solve'))

    def test_preflight_failure_has_durable_receipt(self):
        runner=module('python_continuation_failure_test',HERE/'run.py')
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'run'
            with mock.patch.object(runner,'contract',return_value={'limits':{'overall_seconds':60}}), \
                 mock.patch.object(runner,'verify',side_effect=RuntimeError('synthetic preflight failure')), \
                 mock.patch.object(sys,'argv',['run.py','--output',str(output)]):
                with self.assertRaises(RuntimeError):runner.main()
            receipt=json.loads((output/'failure.json').read_text())
            self.assertEqual(receipt['phase'],'preflight')
            self.assertFalse(receipt['promotion_allowed'])
            self.assertFalse((output/'results.json').exists())

if __name__=='__main__':unittest.main()
