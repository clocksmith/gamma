"""Fresh-population runner tests; no reserved corpus bytes are evaluated."""
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
from tools import opcode_event_parse_validation_gate_v1 as gate


class ValidationTests(unittest.TestCase):
    def setUp(self):
        fixtures.GateTests.setUp(self)
        self.plan = {'input': self.plan['input'], 'package_files': []}

    def test_actual_main_ten_phases_without_retained_parent(self):
        out = self.base / 'results' / gate.CID
        out.mkdir(parents=True)
        run = gate.run_comparison
        with patch.object(gate, 'ROOT', self.base), \
             patch.object(gate, 'authenticate', return_value=({}, self.plan, self.snapshot)), \
             patch.object(gate, 'run_comparison', side_effect=lambda *a: run(*a, limits=self.limits)), \
             patch.dict(os.environ, GAMMA_RESOURCE_PHASE_MARKERS=str(self.base / 'phases.jsonl')), \
             patch.object(sys, 'argv', ['gate']):
            status = gate.main()
        result = json.loads((out / 'stage-decision.json').read_text())
        self.assertEqual(status, 0, result)
        self.assertEqual(result['selection_stage'], 'validation')
        self.assertEqual(len(result['commands']), 10)
        self.assertTrue(result['correctness_pass'] and result['original_decoder_all_arms'])
        self.assertEqual(result['arms']['P']['audit'], result['arms']['K']['audit'])
        for row in result['arms'].values():
            self.assertEqual((ROOT / row['artifacts']['restored']['path']).read_bytes(), self.raw)

    def test_missing_mandatory_witness_blocks(self):
        original = gate.phase.run_phase
        def remove(directory, label, *args):
            record = original(directory, label, *args)
            if label == 'D-decode':
                (directory / 'D-decode.audit.json').unlink()
            return record
        with patch.object(gate.phase, 'run_phase', side_effect=remove), self.assertRaises(FileNotFoundError):
            gate.run_comparison(self.out, self.plan, self.snapshot, self.base / 'phases.jsonl', self.limits)

    def test_frozen_population_package_limits_and_shared_modules(self):
        plan = dict(candidate_id=gate.CID, resources=gate.CAPS, phase_resources=gate.PHASES,
                    input=dict(bytes=250000, sha256='ffb6c9e73f59dc3ee7109441aa05881d1980ff440f47db63120bf36822b765bf'),
                    source_files=[dict(path=p) for p in gate.SOURCES], runtime_files=[{}], evidence=[{}],
                    package_files=[dict(path=f'programs/{gate.CID}/{n}',bytes=v[0],sha256=v[1])
                                   for n,v in gate.PACKAGE.items()])
        gate.validate_plan(plan)
        for section, key, value in [('input','bytes',1000000),('resources','cpus',[3])]:
            changed = copy.deepcopy(plan)
            changed[section][key] = value
            with self.assertRaises(ValueError):
                gate.validate_plan(changed)
        changed = copy.deepcopy(plan)
        changed['package_files'][0]['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            gate.validate_plan(changed)
        self.assertEqual(gate.engine.CID, 'opcode_event_parse250k_q0_v1')
        self.assertEqual(gate.engine.authority.CID, 'opcode_wiki_slot_v1')
        self.assertIs(gate.authenticate.__globals__['validate_plan'], gate.validate_plan)
        self.assertIs(gate.run_comparison.__globals__['compare'], gate.engine.compare)
        with self.assertRaises(ValueError):
            gate.reuse(gate.engine.run_comparison, [('nonexistent exact source fragment','')], vars(gate.engine))


if __name__ == '__main__':
    unittest.main()
