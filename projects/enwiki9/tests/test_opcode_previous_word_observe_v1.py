"""Independent synthetic replay, causal history, and control witnesses."""
import copy
import hashlib
import json
import os
import re
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import opcode_previous_word_build_v1 as build
from tools import opcode_previous_word_observe_v1 as observe
from tools import opcode_field_compact_observe_v1 as parent
from tools import dualstream_grammar_gate_v1 as phase


class ObservationTests(unittest.TestCase):
    def setUp(self):
        retained = os.environ.get('GAMMA_PREVIOUS_WORD_UNIT_RESULTS')
        if retained:
            self.directory = Path(retained) / self._testMethodName
            self.directory.mkdir(parents=True, exist_ok=False)
        else:
            self.tmp = tempfile.TemporaryDirectory(dir=ROOT / 'results', prefix='previous_word_unit_')
            self.addCleanup(self.tmp.cleanup)
            self.directory = Path(self.tmp.name)
        self.bundle = self.directory / 'codec'
        self.inventory = build.write_bundle(self.bundle)
        self.module = parent.load(self.bundle / 'program.py')

    def test_exact_inverse_repeat_parent_projection_and_fixed_parse(self):
        fixtures = dict(empty=b'', no_letters=b'1234\t'*16,
                        arbitrary=bytes(range(256)) + b'<broken\0\xff',
                        words=b'Oakford town. Pinewell village. '*10,
                        overlap=b'alpha beta gamma delta\n'*12+b'alpha beta delta gamma\n'*8,
                        xml=b'<title>Oakford</title><text>Oakford is a town.</text>\r\n'*8)
        for name, raw in fixtures.items():
            with self.subTest(fixture=name):
                kept = self.directory / name
                kept.mkdir()
                (kept / 'input.raw').write_bytes(raw)
                rows = {}
                original, original_audit = parent.execute(
                    parent.load(ROOT / 'programs/opcode_field_compact_v1/program.py'), 'encode', raw)
                for arm in 'PKDS':
                    archive, audit = observe.execute(self.module, 'encode', raw, arm)
                    restored, inverse = observe.execute(self.module, 'decode', archive, arm)
                    repeat, repeated = observe.execute(self.module, 'encode', restored, arm)
                    unobserved, _ = observe.execute(self.module, 'encode', raw, arm, False)
                    self.assertEqual(raw, restored)
                    self.assertEqual(archive, repeat)
                    self.assertEqual(archive, unobserved)
                    observe.compare_audits(audit, inverse)
                    observe.compare_audits(audit, repeated)
                    self.assertEqual(sum(audit['updates_by_mode']), audit['parent']['predictor_bits'])
                    self.assertEqual(audit['parent']['predictor_bits'], 8*audit['parent']['modeled_bytes'])
                    for label, value in (('arc', archive), ('raw', restored),
                                         ('repeat.arc', repeat), ('plain.arc', unobserved)):
                        (kept / (arm + '.' + label)).write_bytes(value)
                    for label, value in (('encode', audit), ('decode', inverse), ('repeat', repeated)):
                        (kept / (arm + '-' + label + '.audit.json')).write_text(json.dumps(value, sort_keys=True, indent=2)+'\n')
                    rows[arm] = archive, audit
                self.assertEqual(rows['P'][0], original)
                self.assertEqual(rows['P'][1]['parent'], original_audit)
                self.assertEqual(rows['P'][0], rows['K'][0])
                self.assertEqual(rows['P'][1]['parent'], rows['K'][1]['parent'])
                for arm in 'KDS':
                    for key in ('parse_sha256', 'parse_events', 'updates_by_mode'):
                        self.assertEqual(rows['P'][1][key], rows[arm][1][key])
                    self.assertEqual(rows['K'][1]['word_history_sha256'], rows[arm][1]['word_history_sha256'])
                if name == 'overlap':
                    self.assertGreater(sum(rows['D'][1]['updates_by_mode'][1:]), 0)
                    self.assertNotEqual(rows['D'][1]['word_history_sha256'], rows['P'][1]['word_history_sha256'])
                    modeled = self.module.namespace('P')['oe'](raw)
                    completed = re.findall(rb'[A-Za-z]+(?=[^A-Za-z])', modeled)
                    expected_words = [w[-8:].hex() for w in completed[-2:][::-1]]
                    self.assertEqual(rows['D'][1]['completed_words_hex'], expected_words)
                if name in ('empty', 'no_letters'):
                    self.assertEqual(rows['D'], rows['S'])
                print(json.dumps(dict(fixture=name, raw_bytes=len(raw),
                    archives={a:dict(bytes=len(r[0]), sha256=hashlib.sha256(r[0]).hexdigest()) for a,r in rows.items()},
                    exact=True, repeat=True, parse_equal=True, parent_bookkeeping_equal=True)))

    def test_fresh_process_relocated_decoder(self):
        relocated = self.directory / 'relocated'
        inventory = build.write_bundle(relocated)
        self.assertEqual(self.inventory, inventory)
        raw = b'<title>Oakford</title><text>Oakford town. Oakford village.</text>\n'*4
        source = self.directory / 'fixture.raw'
        source.write_bytes(raw)
        limits = dict(phase_cpu_seconds=15, phase_wall_seconds=20,
                      phase_address_bytes=536870912)
        for arm in 'PKDS':
            outputs, audits = {}, {}
            for operation in ('encode', 'decode', 'repeat'):
                encode = operation != 'decode'
                output = self.directory / (arm + '-' + operation + '.bin')
                audit = self.directory / (arm + '-' + operation + '.json')
                src = source if operation == 'encode' else outputs['encode' if operation == 'decode' else 'decode']
                argv = [sys.executable, str(ROOT / 'tools/opcode_previous_word_observe_v1.py'),
                        'encode' if encode else 'decode', str(src), str(output), '--candidate-root',
                        str(self.bundle if operation == 'encode' else relocated), '--arm', arm,
                        '--audit', str(audit)]
                result = phase.run_phase(self.directory, arm+'-'+operation, argv, limits,
                                         self.directory / 'phases.jsonl')
                self.assertEqual(result['returncode'], 0,
                                 (self.directory / (arm+'-'+operation+'.stderr')).read_text())
                outputs[operation] = output
                audits[operation] = json.loads(audit.read_text())
            self.assertEqual(outputs['decode'].read_bytes(), raw)
            self.assertEqual(outputs['encode'].read_bytes(), outputs['repeat'].read_bytes())
            observe.compare_audits(audits['encode'], audits['decode'])
            observe.compare_audits(audits['encode'], audits['repeat'])
        print(json.dumps(dict(fresh_process_phases=12, relocated_package=self.inventory,
                              local_package_bytes=sum(r['bytes'] for r in self.inventory.values()))))

    def test_history_corruption_or_missing_evidence_fails(self):
        _, audit = observe.execute(self.module, 'encode', b'one two three ', 'D')
        for key in ('word_history_sha256', 'word_checkpoints', 'completed_words_hex',
                    'complete_state_sha256', 'modeled_field'):
            bad = copy.deepcopy(audit)
            del bad[key]
            with self.assertRaises(ValueError):
                observe.compare_audits(audit, bad)
            bad = copy.deepcopy(audit)
            bad[key] = None
            with self.assertRaises(ValueError):
                observe.compare_audits(audit, bad)

    def test_missing_treatment_history_fails(self):
        ns = self.module.namespace('P')
        state = ns['GST']()
        self.assertEqual(observe.history(state), (state.modeled_f, (b'', b'')))
        for arm in 'KDS':
            audit = observe.WordAudit(arm)
            with self.assertRaisesRegex(ValueError, 'missing completed-word'):
                audit.byte(state, 32)

if __name__ == '__main__':
    unittest.main()
