"""Exercise the real gate and relocated package before corpus admission."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import opcode_event_parse_gate_v1 as gate
from tools import opcode_event_parse_build_v1 as build
from tools import opcode_event_parse_corpus_v1 as codec
from tools import opcode_field_compact_observe_v1 as parent


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / 'results', prefix='event_parse_gate_test_')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.snapshot = self.base / 'codec'
        build.write_bundle(self.snapshot)
        self.raw = b'<title>Oak\0</title><id>12</id><title>Oak\0</title>\xff\r\n<broken'
        source, arc, audit = [self.base / name for name in ('input.raw', 'parent.arc', 'parent.json')]
        source.write_bytes(self.raw)
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

    def test_ten_fresh_phases_original_decoder_and_controls(self):
        result = self.run_gate()
        self.assertEqual(len(result['commands']), 10)
        self.assertTrue(result['correctness_pass'] and result['original_decoder_all_arms'])
        self.assertEqual(set(result['arms']), set('PKD'))
        self.assertEqual(result['arms']['P']['audit'], result['arms']['K']['audit'])
        self.assertEqual(result['archive_saving_bytes'],
                         result['arms']['P']['archive_bytes'] - result['arms']['D']['archive_bytes'])
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

    def test_mandatory_state_divergence_retained(self):
        original = gate.phase.run_phase
        def corrupt(directory, label, *args):
            record = original(directory, label, *args)
            if label == 'D-decode':
                path = directory / 'D-decode.audit.json'
                data = json.loads(path.read_text())
                data['parent']['terminal_common_state_sha256'] = '0' * 64
                path.write_text(json.dumps(data))
            return record
        with patch.object(gate.phase, 'run_phase', side_effect=corrupt), self.assertRaises(ValueError):
            self.run_gate()
        self.assertTrue((self.out / 'D-decode-state.divergence.json').exists())

    def test_retained_parent_divergence_blocks(self):
        Path(self.plan['parent_archive']['path']).write_bytes(b'wrong')
        with self.assertRaises(ValueError):
            self.run_gate()

    def test_relocated_bundle_repeat_authentication_and_original_decode(self):
        other = self.base / 'relocated'
        build.write_bundle(other)
        for name, data in build.bundle().items():
            self.assertEqual((other / name).read_bytes(), data)
        module = parent.load(other / 'program.py')
        for arm in 'PKD':
            arc, enc = codec.execute(module, 'encode', self.raw, arm)
            restored, dec = codec.execute(module, 'decode', arc, arm)
            self.assertEqual(restored, self.raw)
            self.assertEqual(enc, dec)
        (other / 'v').write_bytes(b'bad')
        with self.assertRaises(ValueError):
            parent.load(other / 'program.py')

    def test_population_source_resources_and_authentication_reuse(self):
        plan = dict(candidate_id=gate.CID, resources=gate.CAPS, phase_resources=gate.PHASES,
                    input=dict(bytes=250000, sha256='665fc689441b68462d88f82dc33212abe9c4824be095d03a556c9b55a2829fd3'),
                    source_files=[dict(path=p) for p in sorted(gate.SOURCES)],
                    package_files=[dict(path=f'programs/{gate.CID}/{n}', bytes=len(b)) for n,b in build.bundle().items()],
                    runtime_files=[dict(path='/usr/bin/python3')], evidence=[dict(path='receipt')])
        gate.validate_plan(plan)
        for section, key, value in [('input','bytes',1000000), ('resources','cpus',[3]),
                                    ('phase_resources','phase_cpu_seconds',10000)]:
            changed = copy.deepcopy(plan)
            changed[section][key] = value
            with self.assertRaises(ValueError):
                gate.validate_plan(changed)
        for section in ('source_files','package_files','runtime_files','evidence'):
            changed = copy.deepcopy(plan)
            changed[section] = []
            with self.assertRaises(ValueError):
                gate.validate_plan(changed)
        self.assertIs(gate.authenticate.__code__, gate.authority.authenticate.__code__)
        self.assertEqual(gate.authenticate.__globals__['CID'], gate.CID)
        self.assertEqual(gate.authority.CID, 'opcode_wiki_slot_v1')
        with self.assertRaises(gate.BudgetStop):
            gate.require_phase(dict(timeout=True, returncode=124, error=None))


if __name__ == '__main__':
    unittest.main()
