"""Synthetic sandbox checks for the independent Python qualification path."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('python_name_qualification',HERE/'run.py')
run=importlib.util.module_from_spec(spec);spec.loader.exec_module(run)


class QualificationTests(unittest.TestCase):
    def check_candidate(self, candidate):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);tests=[{'args':[3],'expected':4},{'args':[6],'expected':7}]
            original='class Solution:\n def solve(self,a):return a+1\n'
            res=run.sandbox.run(['/usr/bin/python3','harness.py'],files={'harness.py':(HERE/'harness.py').read_bytes(),
                'candidate.py':original,'inputs.json':json.dumps({'entry':'solve','calls':[{'args':t['args']} for t in tests]})})
            self.assertTrue(res.ok,res.stderr)
            (p/'tests.json').write_text(json.dumps(tests));(p/'baseline').write_bytes(res.stdout)
            item={'entry':'solve','cases':2,'tests_file':str(p/'tests.json'),
                  'baseline_calls':[{'file':str(p/'baseline'),'sha256':run.analyze.sha(res.stdout),'cases':2}]}
            return run.qualify_one({'spec':item,'source':candidate,'folder':str(p/'receipt')})

    def test_renamed_source_passes(self):
        q=self.check_candidate('class Solution:\n def solve(self,b):return b+1\n')
        self.assertTrue(q['passed']);self.assertEqual(q['checks_passed'],2)

    def test_same_numeric_value_wrong_type_fails_parity(self):
        q=self.check_candidate('class Solution:\n def solve(self,b):return float(b+1)\n')
        self.assertFalse(q['passed']);self.assertTrue(q['failures'])

    def test_bad_protocol_rejected(self):
        with self.assertRaises((AssertionError,ValueError)):run.parse(b'{"done":1}\n',1)
        with self.assertRaises(ValueError):run.parse(b'{"i":0,"i":0}\n{"done":1}\n',1)


if __name__=='__main__':unittest.main()
