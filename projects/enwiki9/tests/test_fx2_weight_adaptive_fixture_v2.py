"""Reuse routing checks and reject missing production-repair antecedents."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


previous=load('fixture_tests_v1','tests/test_fx2_weight_adaptive_fixture_v1.py')
runner=load('fixture_runner_v2','tools/fx2_weight_adaptive_fixture50051_q0_v2.py')
runner.require=previous.require
previous.runner=runner


class RoutingTests(previous.RoutingTests):
    pass


class AntecedentTests(unittest.TestCase):
    def gate(self):
        contract=json.loads((ROOT/'operations/adaptive/experiments/fx2_weight_adaptive_fixture50051_q0_v2.json').read_text())
        buffers={row['path']:(ROOT/row['path']).read_bytes() for row in contract['inputs']}
        return type('Gate',(),{'contract':contract,'buffers':buffers})()

    def test_matching_repair_and_retry_are_accepted(self):
        runner.validate(self.gate())

    def test_missing_production_comparison_is_rejected(self):
        gate=self.gate();spec=json.loads(gate.buffers[runner.SPEC]);path=spec['native_terminal']
        proof=json.loads(gate.buffers[path]);proof['result']['all_production_outputs_exact']=False
        gate.buffers[path]=json.dumps(proof).encode()
        with self.assertRaisesRegex(ValueError,'entrypoint controls'):runner.validate(gate)

    def test_unapproved_parent_transition_is_rejected(self):
        gate=self.gate();spec=json.loads(gate.buffers[runner.SPEC]);path=spec['parent_reflection']
        reflection=json.loads(gate.buffers[path]);reflection['decision']['verdict']='retire'
        gate.buffers[path]=json.dumps(reflection).encode()
        with self.assertRaisesRegex(ValueError,'implementation retry'):runner.validate(gate)


if __name__=='__main__':unittest.main()
