"""Synthetic release gate evidence; no retained corpus is read by these tests."""
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
from tools import opcode_previous_word_release_gate_v1 as gate
from tools import opcode_previous_word_release_corpus_v1 as codec
from tools import opcode_previous_word_release_build_v1 as release
from tools import opcode_previous_word_build_v1 as parent
from tools import opcode_previous_word_corpus_v1 as parent_codec


def reference(path):
    return dict(path=str(path.relative_to(ROOT)), bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


class ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        retained = os.environ.get('GAMMA_PREVIOUS_WORD_RELEASE_GATE_UNIT_OUTPUT')
        if retained:
            directory = Path(retained); directory.mkdir(parents=True, exist_ok=True)
            self.base = Path(tempfile.mkdtemp(prefix=self._testMethodName+'_', dir=directory)).resolve()
        else:
            temporary = tempfile.TemporaryDirectory(dir=ROOT / 'results', prefix='word_release_gate_unit_')
            self.addCleanup(temporary.cleanup); self.base = Path(temporary.name)
        self.snapshot = self.base / 'release'; release.write_bundle(self.snapshot)
        development = self.base / 'development'; parent.write_bundle(development)
        module = parent_codec.load(development / 'program.py')
        self.raw = b'<title>Oak\x00</title>First Elm First Elm\xff\n' * 3
        self.assertLessEqual(len(self.raw), 256)
        archive, audit = parent_codec.execute(module, 'encode', self.raw, 'D')
        original, _ = parent_codec.execute(module, 'encode', self.raw, 'P')
        self.plan = {}
        for key, name, data in (('input','input.raw',self.raw), ('parent_archive','parent.arc',archive),
                ('parent_audit','parent.audit.json',json.dumps(audit).encode()),
                ('original_parent_archive','original.arc',original)):
            path = self.base / name; path.write_bytes(data); self.plan[key] = reference(path)
        self.out = self.base / 'output'; self.out.mkdir()
        self.limits = dict(phase_cpu_seconds=10, phase_wall_seconds=15, phase_address_bytes=536870912)

    def run_gate(self):
        return gate.run_comparison(self.out, self.plan, self.snapshot, self.base / 'phases.jsonl', self.limits)

    def test_four_phases_exact_treatment_state_and_plain_release(self):
        result = self.run_gate()
        self.assertEqual(len(result['commands']), 4)
        for name in ('correctness_pass', 'retained_treatment_archive_and_state_equal',
                     'exact_inverse', 'deterministic_repeat', 'observed_unobserved_archive_equal'):
            self.assertTrue(result[name])
        self.assertFalse(result['prediction_changed'])
        self.assertEqual(result['source_delta_bytes'], 110)
        self.assertEqual(result['adapter_source_saving'], 1167)
        self.assertEqual(result['archive_minus_local_source_delta_bytes'], result['archive_saving_bytes']-110)
        self.assertEqual(result['archive_minus_two_local_source_copies_bytes'], result['archive_saving_bytes']-220)
        for index, command in enumerate(result['commands']):
            self.assertNotIn('--arm', command['argv'])
            self.assertEqual('--audit' in command['argv'], index != 3)
        self.assertEqual((ROOT / result['artifacts']['restored']['path']).read_bytes(), self.raw)
        self.assertEqual(len(result['audits']), 3)

    def test_optional_telemetry_does_not_replace_mandatory_audit(self):
        original = gate.phase.run_phase
        def omit(directory, label, *args):
            record = original(directory, label, *args)
            (directory / (label+'.stdout')).write_text('unavailable\n')
            return record
        with patch.object(gate.phase, 'run_phase', side_effect=omit):
            result = self.run_gate()
        self.assertTrue(result['correctness_pass'])
        self.assertTrue(all(row['codec_resources'] is None and row['missing_diagnostics']
                            for row in result['commands']))

    def test_decoder_history_divergence_is_retained(self):
        original = gate.phase.run_phase
        def corrupt(directory, label, *args):
            record = original(directory, label, *args)
            if label == 'D-decode':
                path = directory / (label+'.audit.json'); audit = json.loads(path.read_text())
                audit['word_history_sha256'] = '0'*64; path.write_text(json.dumps(audit))
            return record
        with patch.object(gate.phase, 'run_phase', side_effect=corrupt), self.assertRaises(ValueError):
            self.run_gate()
        self.assertTrue((self.out / 'D-decode-retained-state.divergence.json').is_file())

    def test_missing_audit_and_phase_failure_classification(self):
        original = gate.phase.run_phase
        def omit(directory, label, *args):
            record = original(directory, label, *args)
            (directory / (label+'.audit.json')).unlink()
            return record
        with patch.object(gate.phase, 'run_phase', side_effect=omit), self.assertRaises(gate.EvidenceFailure):
            self.run_gate()
        self.assertEqual(gate.failure_class(gate.EvidenceFailure('missing')), 'incomplete-evidence')
        self.assertEqual(gate.failure_class(MemoryError()), 'budget-exhausted')
        self.assertEqual(gate.failure_class(OSError()), 'infrastructure-failure')
        with self.assertRaises(gate.base.BudgetStop):
            gate.require_phase(dict(timeout=True, returncode=124, error=None))

    def test_declared_bounds_fail_before_namespace(self):
        with patch.dict(codec._bounded_execute.__globals__, RAW_LIMIT=4):
            with self.assertRaises(ValueError): codec.execute(None, 'encode', b'12345')
        with patch.dict(codec._bounded_execute.__globals__, observe_execute=lambda *args: self.fail('decoder invoked')):
            for data in (b'', struct.pack('>II',250001,0)+b'x', struct.pack('>II',1,3)+b'x'):
                with self.assertRaises(ValueError): codec.execute(None, 'decode', data)

    def test_observer_arm_is_external_and_plain_namespace_is_unconfigured(self):
        namespaces = []
        class Module:
            def namespace(self):
                namespace = {'compress': lambda data: data}; namespaces.append(namespace)
                return namespace
        def observed(module, operation, data, arm, enabled):
            self.assertEqual(module.namespace(arm)['_arm'], 'D')
            return data, {'external': True}
        with patch.object(codec, 'compact_execute', side_effect=observed):
            self.assertEqual(codec.release_execute(Module(), 'encode', b'x', 'D'), (b'x', {'external': True}))
        self.assertEqual(codec.release_execute(Module(), 'encode', b'x', 'D', False), (b'x', None))
        self.assertNotIn('_arm', namespaces[-1])
        with self.assertRaises(ValueError): codec.release_execute(Module(), 'encode', b'x', 'P')

    def test_external_plan_original_parent_and_materialization_are_frozen(self):
        evidence = self.base / 'evidence.json'; evidence.write_text('{}')
        row = reference(evidence)
        plan = {key: row for key in gate.EXPECTED}
        plan.update(source_files=[row], evidence=[row], materialization=[row])
        external = self.base / 'inputs.json'; external.write_text(json.dumps(plan))
        (self.snapshot / 'gate-plan.json').write_bytes(external.read_bytes())
        contract = dict(inputs=[reference(external), row])
        with patch.dict(gate._bound.__globals__, INPUTS=reference(external)['path']):
            gate.verify_contract_bindings(contract, plan, self.snapshot)
            for rows in ([row], contract['inputs']+[row], [reference(external)]):
                with self.assertRaises(ValueError):
                    gate.verify_contract_bindings(dict(inputs=rows), plan, self.snapshot)
            (self.snapshot / 'gate-plan.json').write_text('{}')
            with self.assertRaises(ValueError): gate.verify_contract_bindings(contract, plan, self.snapshot)
            (self.snapshot / 'gate-plan.json').write_bytes(external.read_bytes())
            extra = self.base / 'extra'; extra.write_bytes(b'x')
            for key in ('original_parent_archive', 'materialization'):
                changed = copy.deepcopy(plan)
                changed[key] = [reference(extra)] if key == 'materialization' else reference(extra)
                with self.assertRaises(ValueError): gate.verify_contract_bindings(contract, changed, self.snapshot)
            evidence.write_text('{"changed":true}')
            with self.assertRaises(ValueError): gate.verify_contract_bindings(contract, plan, self.snapshot)

    def test_canonical_caps_parent_and_delivered_package(self):
        plan = dict(candidate_id=gate.CID, resources=dict(gate.CAPS), phase_resources=dict(gate.PHASES),
            source_files=[dict(path=p) for p in sorted(gate.SOURCES)], runtime_files=[dict(path=sys.executable)],
            evidence=[dict(path='receipt')],
            package_files=[dict(path=f'programs/{gate.CID}/{name}', bytes=size, sha256=digest)
                           for name,(size,digest) in gate.PACKAGE.items()],
            materialization=[dict(path='results/materialized/'+name, bytes=size, sha256=digest)
                             for name,(size,digest) in gate.PACKAGE.items()])
        plan.update({key:dict(bytes=size,sha256=digest) for key,(size,digest) in gate.EXPECTED.items()})
        gate.validate_plan(plan)
        for section,key,value in [('resources','wall_seconds',1081),('resources','cpus',[3]),
                ('phase_resources','phase_cpu_seconds',181),('parent_audit','bytes',1),
                ('original_parent_archive','sha256','0'*64)]:
            changed = copy.deepcopy(plan); changed[section][key] = value
            with self.assertRaises(ValueError): gate.validate_plan(changed)
        for section in ('source_files','runtime_files','evidence','package_files','materialization'):
            changed = copy.deepcopy(plan); changed[section] = []
            with self.assertRaises(ValueError): gate.validate_plan(changed)
        self.assertIs(gate._authenticate.__code__, gate.base.authority.authenticate.__code__)
        self.assertEqual(gate._authenticate.__globals__['CAPS'], gate.CAPS)


if __name__ == '__main__':
    unittest.main()
