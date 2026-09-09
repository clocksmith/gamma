"""Population isolation and antecedent checks without native execution."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('adaptive_transfer',ROOT/'tools/fx2_weight_adaptive_transfer250k_q0_v1.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)


def require(condition,message):
    if not condition:raise ValueError(message)


runner.require=require


class TransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=json.loads((ROOT/'operations/adaptive/experiments/fx2_weight_adaptive_transfer250k_q0_v1.json').read_text())
        cls.buffers={row['path']:(ROOT/row['path']).read_bytes() for row in cls.contract['inputs']}

    def gate(self):
        return type('Gate',(),{'contract':self.contract,'buffers':dict(self.buffers)})()

    def test_valid_transfer_antecedents(self):
        runner.validate(self.gate())

    def test_second_population_cannot_be_omitted(self):
        gate=self.gate();spec=json.loads(gate.buffers[runner.SPEC]);spec['populations'].pop()
        gate.buffers[runner.SPEC]=json.dumps(spec).encode()
        with self.assertRaisesRegex(ValueError,'wrong populations'):runner.validate(gate)

    def test_invalid_reference_transfer_is_rejected(self):
        gate=self.gate();spec=json.loads(gate.buffers[runner.SPEC]);path=spec['transfer_reflection']
        reflection=json.loads(gate.buffers[path]);reflection['validity']['valid']=False
        gate.buffers[path]=json.dumps(reflection).encode()
        with self.assertRaisesRegex(ValueError,'transfer is not valid'):runner.validate(gate)

    def test_population_prefix_and_raw_isolation(self):
        gate=type('Gate',(),{'buffers':{'opening':b'opening','distant':b'distant'}})()
        for name in ('opening','distant'):
            population={'name':name,'raw':{'path':name}}
            for arm in runner.ARMS:
                codec=runner.Codec(gate,Path('/unused'),arm,population)
                self.assertEqual(codec.prefix,name+'-'+arm)
                self.assertEqual(codec.model,'models/model.D' if arm=='D' else 'models/model.P')
                with self.assertRaisesRegex(ValueError,'wrong raw input'):codec.compress(b'other population')
                codec.count=2
                with self.assertRaisesRegex(ValueError,'unexpected encoder call'):codec.compress(name.encode())


if __name__=='__main__':unittest.main()
