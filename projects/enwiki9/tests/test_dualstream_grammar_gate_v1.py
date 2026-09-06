"""Synthetic subprocess and bounded-selection checks; no corpus is opened."""
import copy
import json
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import dualstream_grammar_gate_v1 as gate


class GrammarGateTest(unittest.TestCase):
    def plan(self):
        return dict(schema=gate.SCHEMA, candidate_id='fixture', stage='development',
                    population={'bytes': 250000}, frame_size=65536,
                    arms=[dict(id=m, mode=m, config=gate.codec.Config().__dict__) for m in gate.codec.MODES],
                    resources=dict(cpus=[2], memory_bytes=2 * 1024**3, scratch_bytes=256 * 1024**2, swap_bytes=0, wall_seconds=900),
                    phase_wall_seconds=3, phase_cpu_seconds=2, phase_address_bytes=512 * 1024**2,
                    runtime_files=[{'path': '/declared-before-execution'}])

    def test_four_ablations_and_bounds_are_mandatory(self):
        plan = self.plan()
        gate.validate_plan(plan, 'fixture')
        for field, value in [('arms', plan['arms'][:-1]), ('frame_size', 0), ('phase_wall_seconds', 181)]:
            with self.subTest(field=field):
                changed = dict(plan, **{field: value})
                with self.assertRaises(gate.codec.CodecError):
                    gate.validate_plan(changed, 'fixture')

    def test_confirmation_cannot_select_multiple_configurations(self):
        plan = self.plan()
        plan['stage'] = 'confirmation'
        gate.validate_plan(plan, 'fixture')
        plan = copy.deepcopy(plan)
        plan['arms'][-1]['config']['grammar_budget'] = 8
        with self.assertRaisesRegex(gate.codec.CodecError, 'cannot tune'):
            gate.validate_plan(plan, 'fixture')

    def test_actual_synthetic_subprocess_closes_and_reports_exact_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            raw = b'<p>Oak\xff Oak</p>\r\n' * 3
            source, archive, restored = (directory / p for p in ('raw', 'archive', 'restored'))
            source.write_bytes(raw)
            marker = directory / 'phases.jsonl'
            for phase, inp, out in [('encode', source, archive), ('decode', archive, restored)]:
                command = [sys.executable, str(ROOT / gate.CODEC), phase, str(inp), str(out)]
                result = gate.run_phase(directory, phase, command, self.plan(), marker)
                self.assertEqual(result['returncode'], 0)
                self.assertFalse(result['timeout'])
                self.assertIsNone(result['error'])
                report = gate.read_json(directory / (phase + '.stdout'))
                self.assertEqual(report['result']['complete_archive_bytes'], archive.stat().st_size)
            self.assertEqual(restored.read_bytes(), raw)
            self.assertEqual([r['event'] for r in map(json.loads, marker.read_text().splitlines())], ['start', 'end', 'start', 'end'])

    def test_missing_executable_is_retained_as_launch_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            result = gate.run_phase(directory, 'missing', ['/no/such/grammar-codec'], self.plan(), directory / 'markers')
            self.assertIsNone(result['returncode'])
            self.assertIsNotNone(result['error'])
            self.assertTrue((directory / 'missing.execution.json').is_file())

    def test_timeout_and_unknown_kill_are_distinct(self):
        self.assertEqual(gate.classification(subprocess.TimeoutExpired('fixture', 1)), 'budget-exhausted')
        self.assertEqual(gate.classification(ValueError(), -signal.SIGXCPU), 'budget-exhausted')
        self.assertEqual(gate.classification(ValueError(), -signal.SIGKILL), 'infrastructure-failure')
        self.assertEqual(gate.classification(ValueError(), 1), 'implementation-failure')


if __name__ == '__main__':
    unittest.main()
