"""Compile only the public trusted scorer; candidates remain inert synthetic text."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import frontier as f


class MinimalKernelDependencyControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler=shutil.which('cc')
        if compiler is None:raise unittest.SkipTest('C compiler unavailable; no native scorer check claimed')
        cls.temp=tempfile.TemporaryDirectory()
        cls.library=Path(cls.temp.name)/'scorer.so'
        subprocess.run([compiler,'-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',
            str(f.LIT/'explicit-basis-v2/score_kernel.c'),'-o',str(cls.library)],check=True,timeout=15,capture_output=True)
        cls.a=f.load('minimal_public_scorer_dependency',f.LIT/'explicit-basis-v2/accelerator.py')
        cls.a.configure(hashlib.sha256(cls.library.read_bytes()).hexdigest(),cls.library)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def test_public_synthetic_exact_cost_and_unreachable_controls(self):
        for text,dictionary in [('abcde',['a','bcde','ab','cde']),('éé🙂é',['éé','🙂','é']),
                                ('aba',['ab','ba']),('', ['a']),('ababab',['a','b','ab'])]:
            expected=f.exact_path(text,dictionary)
            actual=self.a.Graph({'synthetic':text}).score(dictionary,materialize=True)['synthetic']
            if expected is None:self.assertIsNone(actual)
            else:
                self.assertEqual((actual['selections'],actual['characters']),expected[:2])
                self.assertEqual(actual['used'],[dictionary[i] for i in expected[2]])

    def test_native_kernel_hash_binding_fails_closed(self):
        with self.assertRaises(ValueError):self.a.configure('0'*64,self.library)

if __name__=='__main__':unittest.main()
