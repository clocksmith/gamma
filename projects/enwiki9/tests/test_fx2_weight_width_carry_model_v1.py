"""The trained-model runner is exercised only on synthetic tensors here."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import fx2_weight_width_carry_model_v1 as runner
import fx2_weight_marginal_fixtures_v1 as reference


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=os.environ['FX2_CARRY_TMP'])
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        original=self.root/'original'
        original.write_bytes(reference.encode_reference([
            reference.tensor('a',0,[2,3],1,[-7,0,7]*2),
            reference.tensor('b',0,[2,3],1,[-7,0,7]*2)]))
        parent=self.root/'parent.model'
        subprocess.run([os.environ['FX2_CARRY_PARENT'],'D',str(original),str(parent)],
                       check=True,capture_output=True,timeout=10)
        self.plan=dict(models=dict(original=runner.binding(original),parent=runner.binding(parent)),
                       executables={k:runner.binding(os.environ[e]) for k,e in
                                    [('parent','FX2_CARRY_PARENT'),('treatment','FX2_CARRY_PROBE')]},
                       bounds=dict(elapsed_seconds=30,phase_elapsed_seconds=10,cpu_seconds_per_phase=10,
                                   address_space_bytes=536870912,per_file_bytes=33554432,scratch_bytes=67108864))

    def test_exact_comparison_and_accounting(self):
        result=runner.run(self.plan,self.root/'output')
        self.assertTrue(result['all_exact_inverses'])
        self.assertTrue(result['all_deterministic_repeats'])
        self.assertTrue(result['selected_parent_identity'])
        self.assertEqual(result['phase_count'],10)
        self.assertEqual(result['model_plus_comparison_executable_bytes_saved'],
                         result['model_bytes_saved']-result['comparison_executable_added_bytes'])
        self.assertIsNone(result['full_corpus_score_bytes'])

    def test_changed_reference_rejected_before_execution(self):
        self.plan['models']['parent']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'changed input'):
            runner.run(self.plan,self.root/'output')
        self.assertFalse((self.root/'output').exists())

    def test_existing_output_preserved(self):
        output=self.root/'output';output.mkdir();sentinel=output/'owned';sentinel.write_bytes(b'existing')
        with self.assertRaises(FileExistsError):
            runner.run(self.plan,output)
        self.assertEqual(sentinel.read_bytes(),b'existing')


if __name__=='__main__':
    unittest.main()
