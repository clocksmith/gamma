"""Test adaptive fixture routing without launching native inference."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('adaptive_fixture',ROOT/'tools/fx2_weight_adaptive_fixture50051_q0_v1.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
def require(condition,message):
    if not condition:raise ValueError(message)
runner.require=require


class RoutingTests(unittest.TestCase):
    def test_exact_loader_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            gate=type('Gate',(),{'result':Path(directory)})()
            for arm,selected,side in [('P','D','7169'),('K','D','7169'),('D','A','0')]:
                text=f'Gamma weight loader selected={selected} tensors=434 histogram_tensors=111 histogram_symbols=5868864 side_information_bytes={side} canonical=1\n'
                (gate.result/'phase.stderr').write_text(text)
                runner.activation(gate,'phase',arm)
                (gate.result/'phase.stderr').write_text(text+text)
                with self.assertRaisesRegex(ValueError,'loader activation'):runner.activation(gate,'phase',arm)

    def test_model_selection_and_input_guard(self):
        gate=type('Gate',(),{'spec':{'population':{'raw':{'path':'raw'}}},'buffers':{'raw':b'expected'}})()
        for arm in runner.ARMS:
            codec=runner.Codec(gate,Path('/unused'),arm)
            self.assertEqual(codec.model,'models/model.D' if arm=='D' else 'models/model.P')
            with self.assertRaisesRegex(ValueError,'wrong raw input'):codec.compress(b'wrong')
            codec.count=2
            with self.assertRaisesRegex(ValueError,'unexpected encoder call'):codec.compress(b'expected')


if __name__=='__main__':unittest.main()
