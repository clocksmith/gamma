"""Bounded synthetic transfer-runner checks; no retained corpus is opened."""
import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import opcode_previous_word_transfer_gate_v1 as gate
from tools import opcode_previous_word_compact_corpus_v1 as codec
from tools import opcode_previous_word_compact_build_v1 as compact
from tools import opcode_previous_word_release_build_v1 as release
from tools import opcode_previous_word_build_v1 as predecessor
from tools import opcode_previous_word_corpus_v1 as predecessor_codec


def reference(path):
    return dict(path=str(path.relative_to(ROOT)), bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


class TransferGateTests(unittest.TestCase):
    def setUp(self):
        retained = os.environ.get('GAMMA_PREVIOUS_WORD_TRANSFER_GATE_UNIT_OUTPUT')
        if retained:
            directory = Path(retained); directory.mkdir(parents=True, exist_ok=True)
            self.base = Path(tempfile.mkdtemp(prefix=self._testMethodName+'_', dir=directory)).resolve()
        else:
            temporary = tempfile.TemporaryDirectory(dir=ROOT / 'results', prefix='word_transfer_unit_')
            self.addCleanup(temporary.cleanup); self.base = Path(temporary.name)
        self.snapshot = self.base / 'snapshot'; compact.write_bundle(self.snapshot)
        release.write_bundle(self.snapshot / 'release')
        parent = self.base / 'predecessor'; predecessor.write_bundle(parent)
        self.raw = b'<title>Oak\x00</title>First Elm First Elm\xff\n' * 3
        self.assertEqual(len(self.raw), 120)
        archive, audit = predecessor_codec.execute(
            predecessor_codec.load(parent / 'program.py'), 'encode', self.raw, 'P')
        self.parent = audit['parent']
        self.plan = {}
        for key, name, data in (
                ('input', 'input.raw', self.raw), ('parent_archive', 'parent.arc', archive),
                ('parent_audit', 'parent.audit.json', json.dumps({'parent': self.parent}).encode())):
            path = self.base / name; path.write_bytes(data); self.plan[key] = reference(path)
        self.out = self.base / 'output'; self.out.mkdir()
        self.limits = dict(phase_cpu_seconds=10, phase_wall_seconds=15,
                           phase_address_bytes=536870912)

    def run_gate(self):
        result = gate.run_comparison(self.out, self.plan, self.snapshot,
                                    self.base / 'phases.jsonl', self.limits)
        (self.base / 'result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
        return result

    def test_seventeen_phases_and_fresh_release_dependency(self):
        actual = gate.release.run_comparison
        def released(directory, plan, snapshot, marker, limits):
            self.assertEqual(plan['parent_archive']['path'], reference(self.out / 'controls/D.arc')['path'])
            self.assertEqual(plan['parent_audit']['path'], reference(self.out / 'controls/D-encode.audit.json')['path'])
            self.assertEqual(plan['original_parent_archive'], self.plan['parent_archive'])
            self.assertEqual(snapshot, self.snapshot / 'release')
            return actual(directory, plan, snapshot, marker, limits)
        with patch.object(gate.release, 'run_comparison', side_effect=released):
            result = self.run_gate()
        labels = [arm+'-'+mode for arm in 'PKDS' for mode in ('encode','decode','repeat')]
        labels += ['D-plain', 'D-encode', 'D-decode', 'D-repeat', 'D-plain']
        self.assertEqual([r['phase'] for r in result['commands']], labels)
        self.assertTrue(all(r['returncode'] == 0 for r in result['commands']))
        controls = result['controls']
        for key in ('correctness_pass', 'controls_equivalent', 'same_arm_decoder_all_arms',
                    'all_arm_parse_and_updates_equal', 'KDS_history_equal'):
            self.assertTrue(controls[key])
        self.assertEqual(controls['arms']['P']['audit']['parent'], self.parent)
        self.assertEqual(controls['arms']['K']['audit']['parent'], self.parent)
        self.assertNotEqual(controls['arms']['P']['audit']['word_history_sha256'],
                            controls['arms']['K']['audit']['word_history_sha256'])
        for arm, row in controls['arms'].items():
            self.assertEqual((ROOT / row['artifacts']['restored']['path']).read_bytes(), self.raw)
            self.assertEqual(sum(row['audit']['updates_by_mode']), 8*row['audit']['parent']['modeled_bytes'])
            for ref in row['audits'].values():
                self.assertEqual(json.loads((ROOT / ref['path']).read_text()), row['audit'])
        for ref in result['release']['audits'].values():
            self.assertEqual(json.loads((ROOT / ref['path']).read_text()), controls['arms']['D']['audit'])
        self.assertTrue(result['release']['observed_unobserved_archive_equal'])
        self.assertFalse(result['release']['prediction_changed'])
        self.assertEqual(result['archive_minus_local_source_delta_bytes'], result['archive_saving_bytes']-110)
        self.assertEqual(result['archive_minus_two_local_source_copies_bytes'], result['archive_saving_bytes']-220)
        self.assertEqual(result['prediction_gate_pass'],
                         result['archive_saving_bytes'] > 0 and result['delayed_control_saving_bytes'] > 0)
        self.assertEqual(result['transfer_gate_pass'],
                         result['prediction_gate_pass'] and result['archive_saving_bytes'] > 110)

    def test_optional_telemetry_is_diagnostic(self):
        actual = gate.phase.run_phase
        def omit(directory, label, *args):
            record = actual(directory, label, *args)
            (directory / (label+'.stdout')).write_text('unavailable\n')
            return record
        with patch.object(gate.phase, 'run_phase', side_effect=omit):
            result = self.run_gate()
        self.assertTrue(result['correctness_pass'])
        self.assertEqual(len(result['commands']), 17)
        self.assertTrue(all(r['codec_resources'] is None and r['missing_diagnostics']
                            for r in result['commands']))

    def test_release_full_state_disagreement_is_retained(self):
        actual = gate.phase.run_phase
        def corrupt(directory, label, *args):
            record = actual(directory, label, *args)
            if directory.name == 'release' and label == 'D-encode':
                path = directory / (label+'.audit.json'); audit = json.loads(path.read_text())
                audit['word_history_sha256'] = '0'*64; path.write_text(json.dumps(audit))
            return record
        with patch.object(gate.phase, 'run_phase', side_effect=corrupt), self.assertRaises(ValueError):
            self.run_gate()
        self.assertTrue((self.out / 'release/D-encode-retained-state.divergence.json').is_file())

    def test_missing_mandatory_audit_fails_closed(self):
        actual = gate.phase.run_phase
        def omit(directory, label, *args):
            record = actual(directory, label, *args)
            if label == 'P-encode':
                (directory / (label+'.audit.json')).unlink()
            return record
        with patch.object(gate.phase, 'run_phase', side_effect=omit), self.assertRaises(gate.EvidenceFailure):
            self.run_gate()
        self.assertEqual(gate.base.failure_class(gate.EvidenceFailure('missing')), 'incomplete-evidence')
        self.assertEqual(gate.base.failure_class(MemoryError()), 'budget-exhausted')
        self.assertEqual(gate.base.failure_class(OSError()), 'infrastructure-failure')

    def test_malformed_bounds_fail_before_namespace(self):
        with patch.dict(codec.execute.__globals__, RAW_LIMIT=4):
            with self.assertRaises(ValueError): codec.execute(None, 'encode', b'12345', 'P')
        with patch.dict(codec.execute.__globals__, observe_execute=lambda *a: self.fail('codec invoked')):
            for data in (b'', struct.pack('>II',250001,0)+b'x', struct.pack('>II',1,3)+b'x'):
                with self.assertRaises(ValueError): codec.execute(None, 'decode', data, 'D')
            with patch.dict(codec.execute.__globals__, ARCHIVE_LIMIT=4):
                with self.assertRaises(ValueError): codec.execute(None, 'decode', b'12345', 'D')

    def test_population_package_and_materialization_identity(self):
        plan = dict(candidate_id=gate.CID, resources=dict(gate.CAPS), phase_resources=dict(gate.PHASES),
            source_files=[dict(path=p) for p in sorted(gate.SOURCES)],
            runtime_files=[dict(path=sys.executable)], evidence=[dict(path='receipt')],
            package_files=[dict(path=f'programs/{gate.CID}/{name}',bytes=size,sha256=digest)
                           for name,(size,digest) in gate.PACKAGE.items()],
            materialization=[dict(path='results/materialized/'+name,bytes=size,sha256=digest)
                             for name,(size,digest) in gate.PACKAGE.items()])
        plan.update({key:dict(bytes=size,sha256=digest) for key,(size,digest) in gate.EXPECTED.items()})
        gate.validate_plan(plan)
        for section,key,value in [('resources','wall_seconds',4201),('resources','cpus',[3]),
                ('phase_resources','phase_cpu_seconds',181),('input','sha256','0'*64),
                ('parent_archive','bytes',1),('parent_audit','sha256','0'*64)]:
            changed = copy.deepcopy(plan); changed[section][key] = value
            with self.assertRaises(ValueError): gate.validate_plan(changed)
        for section in ('source_files','runtime_files','evidence','package_files','materialization'):
            changed = copy.deepcopy(plan); changed[section] = []
            with self.assertRaises(ValueError): gate.validate_plan(changed)
        for section in ('package_files','materialization'):
            changed = copy.deepcopy(plan); changed[section][-1]['sha256'] = '0'*64
            with self.assertRaises(ValueError): gate.validate_plan(changed)
        self.assertEqual(gate._authenticate.__globals__['CAPS'], gate.CAPS)

    def test_frozen_plan_source_and_materialization_bindings(self):
        evidence = self.base / 'source'; evidence.write_bytes(b'source')
        material = self.base / 'material'; material.write_bytes(b'material')
        row, mat = reference(evidence), reference(material)
        plan = {key: row for key in gate.EXPECTED}
        plan.update(source_files=[row], evidence=[row], materialization=[mat])
        external = self.base / 'inputs.json'; external.write_text(json.dumps(plan))
        snapshot_plan = self.snapshot / 'gate-plan.json'; snapshot_plan.write_bytes(external.read_bytes())
        contract = dict(inputs=[reference(external), row, mat])
        with patch.dict(gate._bound.__globals__, INPUTS=reference(external)['path']):
            gate.verify_contract_bindings(contract, plan, self.snapshot)
            for rows in (contract['inputs'][:-1], contract['inputs']+[row], [row,mat]):
                with self.assertRaises(ValueError):
                    gate.verify_contract_bindings(dict(inputs=rows), plan, self.snapshot)
            snapshot_plan.write_text('{}')
            with self.assertRaises(ValueError): gate.verify_contract_bindings(contract, plan, self.snapshot)
            snapshot_plan.write_bytes(external.read_bytes())
            for path in (evidence, material, external):
                before = path.read_bytes(); path.write_bytes(before+b'changed')
                with self.assertRaises(ValueError): gate.verify_contract_bindings(contract, plan, self.snapshot)
                path.write_bytes(before)

    def test_empty_runtime_exact_authentication(self):
        path = self.base / 'empty.py'; path.write_bytes(b'')
        row = reference(path); row['path'] = str(path)
        self.assertEqual(gate.base.check_file(row, absolute=True), path)
        for changed in (dict(row, sha256='0'*64), dict(row, extra=True), dict(row, bytes=False)):
            with self.assertRaises(ValueError): gate.base.check_file(changed, absolute=True)
        path.write_bytes(b'x')
        with self.assertRaises(ValueError): gate.base.check_file(row, absolute=True)

    def test_post_run_authentication_failure_retains_recursive_manifest(self):
        fake_root = self.base / 'main'; output = fake_root / 'results' / gate.CID
        output.mkdir(parents=True)
        def completed(*args):
            nested = output / 'release'; nested.mkdir(); (nested / 'D.arc').write_bytes(b'evidence')
            return dict(correctness_pass=True, controls_equivalent=True,
                        prediction_gate_pass=True, local_subtotal_gate_pass=True,
                        transfer_gate_pass=True)
        plan = dict(self.plan, package_files=[])
        with patch.object(gate, 'ROOT', fake_root), patch.object(gate, 'authenticate',
                side_effect=[({},plan,self.snapshot),gate.EvidenceFailure('changed source')]), \
                patch.object(gate, 'run_comparison', side_effect=completed), \
                patch.dict(os.environ, GAMMA_RESOURCE_PHASE_MARKERS=str(self.base/'markers')), \
                patch.object(sys, 'argv', ['transfer-gate']):
            self.assertEqual(gate.main(), 1)
        stage = json.loads((output/'stage-decision.json').read_text())
        self.assertFalse(stage['correctness_pass'])
        for key in ('controls_equivalent', 'prediction_gate_pass',
                    'local_subtotal_gate_pass', 'transfer_gate_pass'):
            self.assertFalse(stage[key])
        self.assertEqual(stage['failure_class'], 'incomplete-evidence')
        manifest = json.loads((output/'artifacts.json').read_text())
        self.assertFalse(manifest['complete'])
        self.assertEqual(len(manifest['files']), 1)
        self.assertTrue(manifest['files'][0]['path'].endswith('release/D.arc'))


if __name__ == '__main__':
    unittest.main()
