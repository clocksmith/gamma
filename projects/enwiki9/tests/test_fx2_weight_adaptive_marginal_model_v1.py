"""Exercise the complete-model runner on synthetic inputs before publication."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import fx2_weight_adaptive_marginal_model_v1 as runner
import fx2_weight_marginal_fixtures_v1 as reference


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=os.environ['FX2_CONTAINER_TMP'])
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        tensors=[reference.tensor('w',0,[3,3],1,[-7,0,7]*3)]
        original=self.root/'original';original.write_bytes(reference.encode_reference(tensors))
        parent=self.root/'parent';parent.write_bytes(reference.encode_reference(tensors,'D'))
        self.plan=dict(model=runner.binding(original),selected_parent=runner.binding(parent),
                       bounds=dict(elapsed_seconds=60,phase_elapsed_seconds=10,cpu_seconds_per_phase=10,
                                   address_space_bytes=536870912,per_file_bytes=33554432,scratch_bytes=33554432))

    def execute(self):
        return runner.run(self.plan,self.root/'result',os.environ['FX2_CONTAINER_PROBE'],os.environ['FX2_CONTAINER_FIXED'])

    def test_exact_comparison_and_inventory(self):
        result=self.execute()
        self.assertEqual(result['phase_count'],10)
        self.assertTrue(result['independently_restored'])
        self.assertTrue(result['selected_parent_identity'])
        inv=result['executable_inventory']
        self.assertEqual(result['model_plus_comparison_executable_bytes_saved'],
                         result['model_bytes_saved']-(inv['adaptive']['bytes']-inv['fixed']['bytes']))
        self.assertIsNone(result['complete_package_bytes'])

    def test_wrong_parent_blocks_receipt(self):
        self.plan['selected_parent']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'selected fixed parent differs'):
            self.execute()
        self.assertFalse((self.root/'result/receipt.json').exists())


if __name__=='__main__':
    unittest.main()
