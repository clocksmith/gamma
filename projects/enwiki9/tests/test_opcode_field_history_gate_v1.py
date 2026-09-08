"""Synthetic execution and failure injection for the actual corpus runner."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import opcode_field_history_gate_v1 as gate
from tools import opcode_field_history_build_v1 as build
from tools import opcode_field_compact_observe_v1 as parent


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / 'results', prefix='history_gate_test_')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.snapshot = self.base / 'codec'
        build.write_bundle(self.snapshot)
        self.raw = b'<title>Oak\0</title><id>12</id><title>Ash</title>\xff\r\n<broken'
        source = self.base / 'input.raw'
        source.write_bytes(self.raw)
        arc = self.base / 'parent.arc'
        audit = self.base / 'parent.json'
        encoded, observed = parent.execute(parent.load(ROOT / 'programs/opcode_field_compact_v1/program.py'),
                                           'encode', self.raw)
        arc.write_bytes(encoded)
        audit.write_text(json.dumps(observed))
        self.plan = dict(input=dict(path=str(source)), parent_archive=dict(path=str(arc)),
                         parent_audit=dict(path=str(audit)))
        self.out = self.base / 'output'
        self.out.mkdir()
        self.limits = dict(phase_cpu_seconds=10, phase_wall_seconds=15, phase_address_bytes=536870912)

    def run_gate(self):
        return gate.run_comparison(self.out, self.plan, self.snapshot, self.base / 'phases.jsonl', self.limits)

    def test_sixteen_fresh_phases_and_five_arm_controls(self):
        result = self.run_gate()
        self.assertEqual(len(result['commands']), 16)
        self.assertTrue(result['correctness_pass'])
        self.assertEqual(set(result['arms']), set('PKDGS'))
        self.assertEqual(result['arms']['P']['audit']['parent'], result['arms']['K']['audit']['parent'])
        for key, arm in [('archive_saving_bytes', 'P'), ('aligned_vs_global_bytes', 'G'),
                         ('aligned_vs_randomized_bytes', 'S')]:
            self.assertEqual(result[key], result['arms'][arm]['archive_bytes'] - result['arms']['D']['archive_bytes'])
        self.assertEqual(result['prediction_gate_pass'], all(result[k] > 0 for k in
                         ('archive_saving_bytes', 'aligned_vs_global_bytes', 'aligned_vs_randomized_bytes')))
        for row in result['arms'].values():
            self.assertEqual((ROOT / row['artifacts']['restored']['path']).read_bytes(), self.raw)

    def test_optional_telemetry_stays_missing(self):
        original = gate.phase.run_phase
        def missing(directory, label, *args):
            record = original(directory, label, *args)
            (directory / (label + '.stdout')).write_text('missing\n')
            return record
        with patch.object(gate.phase, 'run_phase', side_effect=missing):
            result = self.run_gate()
        self.assertTrue(result['correctness_pass'])
        self.assertTrue(all(c['codec_resources'] is None and c['missing_diagnostics'] for c in result['commands']))

    def test_missing_mandatory_audit_blocks(self):
        original = gate.phase.run_phase
        def missing(directory, label, *args):
            record = original(directory, label, *args)
            if label == 'P-decode':
                (directory / 'P-decode.audit.json').unlink()
            return record
        with patch.object(gate.phase, 'run_phase', side_effect=missing), self.assertRaises(FileNotFoundError):
            self.run_gate()

    def test_introduced_state_divergence_is_retained(self):
        original = gate.phase.run_phase
        def corrupt(directory, label, *args):
            record = original(directory, label, *args)
            if label == 'G-decode':
                path = directory / 'G-decode.audit.json'
                data = json.loads(path.read_text())
                data['side_state_sha256'] = '0' * 64
                path.write_text(json.dumps(data))
            return record
        with patch.object(gate.phase, 'run_phase', side_effect=corrupt), self.assertRaises(ValueError):
            self.run_gate()
        detail = json.loads((self.out / 'G-decode-state.divergence.json').read_text())
        self.assertEqual(detail['path'], '$.side_state_sha256')

    def test_retained_parent_divergence_blocks(self):
        Path(self.plan['parent_archive']['path']).write_bytes(b'wrong')
        with self.assertRaises(ValueError):
            self.run_gate()
        self.assertTrue((self.out / 'retained-parent-archive.divergence.json').exists())

    def test_budget_stop_and_authentication_reuse(self):
        with self.assertRaises(gate.BudgetStop):
            gate.require_phase(dict(timeout=True, returncode=124, error=None))
        self.assertIs(gate.authenticate.__code__, gate.authority.authenticate.__code__)
        self.assertEqual(gate.authenticate.__globals__['CID'], gate.CID)
        self.assertEqual(gate.authority.CID, 'opcode_wiki_slot_v1')
        self.assertIs(gate.authenticate.__globals__['validate_plan'], gate.validate_plan)

    def test_population_resource_source_and_package_bounds(self):
        plan = dict(candidate_id=gate.CID, resources=gate.CAPS, phase_resources=gate.PHASES,
                    input=dict(bytes=250000, sha256='665fc689441b68462d88f82dc33212abe9c4824be095d03a556c9b55a2829fd3'),
                    source_files=[dict(path=p) for p in sorted(gate.SOURCES)],
                    package_files=[dict(path=f'programs/{gate.CID}/p', bytes=6075),
                                   dict(path=f'programs/{gate.CID}/program.py', bytes=531)],
                    runtime_files=[dict(path='/usr/bin/python3')], evidence=[dict(path='receipt')])
        gate.validate_plan(plan)
        for section, key, value in [('input', 'bytes', 1000000), ('resources', 'cpus', [3]),
                                    ('phase_resources', 'phase_cpu_seconds', 10000)]:
            changed = copy.deepcopy(plan)
            changed[section][key] = value
            with self.assertRaises(ValueError):
                gate.validate_plan(changed)
        for section in ('source_files', 'package_files', 'runtime_files', 'evidence'):
            changed = copy.deepcopy(plan)
            changed[section] = []
            with self.assertRaises(ValueError):
                gate.validate_plan(changed)


if __name__ == '__main__':
    unittest.main()
