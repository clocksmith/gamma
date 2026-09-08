"""Exercise the validation wrapper with synthetic data and immutable bundle checks."""
import copy
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import opcode_field_history_validation_gate_v1 as gate
from tests.test_opcode_field_history_gate_v1 import GateTests as Fixture


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = Fixture('test_sixteen_fresh_phases_and_five_arm_controls')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def test_actual_main_closes_all_synthetic_phases(self):
        f = self.fixture
        directory = f.base / 'results' / gate.CID
        directory.mkdir(parents=True)
        plan = dict(f.plan, package_files=[dict(path='codec/'+name, bytes=size, sha256=sha)
                    for name, (size, sha) in gate.PACKAGE.items()])
        with patch.object(gate, 'ROOT', f.base), patch.object(gate, 'authenticate', return_value=({}, plan, f.snapshot)), \
             patch.object(sys, 'argv', ['validation-gate']), \
             patch.dict(os.environ, {'GAMMA_RESOURCE_PHASE_MARKERS': str(f.base / 'phases.jsonl')}):
            self.assertEqual(gate.main(), 0)
        stage = json.loads((directory / 'stage-decision.json').read_text())
        self.assertEqual(stage['candidate_id'], gate.CID)
        self.assertEqual(stage['selection_stage'], 'validation')
        self.assertEqual(len(stage['commands']), 16)
        self.assertTrue(stage['correctness_pass'])
        self.assertEqual(set(stage['arms']), set('PKDGS'))
        self.assertIsNone(stage['complete_package_bytes'])
        self.assertTrue(json.loads((directory / 'artifacts.json').read_text())['complete'])

    def plan(self):
        return dict(candidate_id=gate.CID, resources=gate.CAPS, phase_resources=gate.PHASES,
                    input=dict(bytes=250000, sha256='4c6b839c77999f9da19c0f856c40cceb1262aefb536ecc7e7f54e37f694c9b8b'),
                    source_files=[dict(path=p) for p in sorted(gate.SOURCES)],
                    package_files=[dict(path=f'programs/{gate.CID}/{name}', bytes=size, sha256=sha)
                                   for name, (size, sha) in gate.PACKAGE.items()],
                    runtime_files=[dict(path='/usr/bin/python3')], evidence=[dict(path='receipt')])

    def test_reject_development_population_and_mutated_bundle(self):
        plan = self.plan()
        gate.validate_plan(plan)
        bad = copy.deepcopy(plan)
        bad['input']['sha256'] = '665fc689441b68462d88f82dc33212abe9c4824be095d03a556c9b55a2829fd3'
        with self.assertRaises(ValueError):
            gate.validate_plan(bad)
        bad = copy.deepcopy(plan)
        bad['package_files'][0]['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            gate.validate_plan(bad)
        bad = copy.deepcopy(plan)
        bad['resources']['cpus'] = [3]
        with self.assertRaises(ValueError):
            gate.validate_plan(bad)

    def test_reuses_measured_comparison_without_global_mutation(self):
        self.assertIs(gate.run_comparison, gate.engine.run_comparison)
        self.assertIs(gate.authenticate.__code__, gate.engine.authenticate.__code__)
        self.assertEqual(gate.authenticate.__globals__['CID'], gate.CID)
        self.assertEqual(gate.engine.authenticate.__globals__['CID'], 'opcode_field_history250k_q0_v1')


if __name__ == '__main__':
    unittest.main()
