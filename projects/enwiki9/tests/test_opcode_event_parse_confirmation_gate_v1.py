"""Synthetic confirmation execution and wrapper resource-boundary tests."""
import copy
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
import test_opcode_event_parse_gate_v1 as fixtures
from tools import opcode_event_parse_confirmation_gate_v1 as gate
from tools import opcode_event_parse_corpus1m_v1 as cli


class ConfirmationTests(unittest.TestCase):
    def setUp(self):
        fixtures.GateTests.setUp(self)
        self.plan = {'input': self.plan['input'], 'package_files': []}

    def test_actual_main_ten_phases_and_component_cost(self):
        out = self.base / 'results' / gate.CID
        out.mkdir(parents=True)
        with patch.dict(gate.main.__globals__, ROOT=self.base,
                        authenticate=lambda *a: ({}, self.plan, self.snapshot),
                        run_comparison=lambda *a: gate.run_comparison(*a, limits=self.limits)), \
             patch.dict(os.environ, GAMMA_RESOURCE_PHASE_MARKERS=str(self.base / 'phases.jsonl')), \
             patch.object(sys, 'argv', ['gate']):
            self.assertEqual(gate.main(), 0)
        result = json.loads((out / 'stage-decision.json').read_text())
        self.assertEqual(result['selection_stage'], 'confirmation')
        self.assertEqual(len(result['commands']), 10)
        self.assertTrue(result['correctness_pass'] and result['original_decoder_all_arms'])
        self.assertEqual(result['arms']['P']['audit'], result['arms']['K']['audit'])
        self.assertEqual(result['archive_minus_one_source_zip_delta_bytes'],
                         result['archive_saving_bytes'] - 1895)
        self.assertEqual(result['source_component_gate_pass'], result['archive_saving_bytes'] > 1895)

    def test_one_million_wrapper_boundary_without_codec_run(self):
        source, out = self.base / 'synthetic.raw', self.base / 'encoded'
        args = ['codec','encode',str(source),str(out),'--candidate-root',str(self.snapshot),'--arm','D']
        source.write_bytes(b'x' * 1000000)
        def fake_execute(module, operation, data, arm, observed):
            self.assertEqual(len(data), 1000000)
            return b'fixture', None
        with patch.dict(cli.main.__globals__, execute=fake_execute), patch.object(sys,'argv',args):
            cli.main()
        self.assertEqual(out.read_bytes(), b'fixture')
        out.unlink()
        source.write_bytes(b'x' * 1000001)
        with patch.object(sys,'argv',args), self.assertRaisesRegex(ValueError,'input exceeds frozen bound'):
            cli.main()
        self.assertFalse(out.exists())
        source.write_bytes(b'fixture')
        args[1] = 'decode'
        with patch.dict(cli.main.__globals__, execute=lambda *a: (b'x'*1000001,None)), \
             patch.object(sys,'argv',args), self.assertRaisesRegex(ValueError,'reconstructed output exceeds'):
            cli.main()
        self.assertFalse(out.exists())

    def test_frozen_scope_package_resources_and_reuse(self):
        plan = dict(candidate_id=gate.CID, resources=gate.CAPS, phase_resources=gate.PHASES,
                    input=dict(bytes=1000000,sha256='851329174ac0763701a0364fed26b58ba7c6847a3c0b8a737d2c5b88a24785d4'),
                    source_files=[dict(path=p) for p in gate.SOURCES],runtime_files=[{}],
                    evidence=[dict(path='results/opcode_event_parse_source_zip_v1/attempt01/cost.json')],
                    package_files=[dict(path=f'programs/{gate.CID}/{n}',bytes=v[0],sha256=v[1])
                                   for n,v in gate.PACKAGE.items()])
        gate.validate_plan(plan)
        for section,key,value in [('input','bytes',1000001),('resources','cpus',[3]),
                                  ('phase_resources','phase_cpu_seconds',601)]:
            changed = copy.deepcopy(plan)
            changed[section][key] = value
            with self.assertRaises(ValueError):
                gate.validate_plan(changed)
        changed = copy.deepcopy(plan)
        changed['evidence'] = [{}]
        with self.assertRaises((ValueError,KeyError)):
            gate.validate_plan(changed)
        self.assertEqual(gate.base.CID, 'opcode_event_parse_validation250k_q0_v1')
        self.assertIs(gate.authenticate.__code__,gate.base.authenticate.__code__)
        self.assertIs(gate.comparison.__code__,gate.base.run_comparison.__code__)
        self.assertEqual(gate.comparison.__defaults__, (gate.PHASES,))
        self.assertIs(cli.main.__globals__['execute'],cli.original.execute)


if __name__ == '__main__':
    unittest.main()
