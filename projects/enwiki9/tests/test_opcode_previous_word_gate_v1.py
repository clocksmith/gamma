"""Bounded synthetic runner checks; never open a retained corpus population."""
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
from tools import opcode_previous_word_gate_v1 as gate
from tools import opcode_previous_word_corpus_v1 as codec
from tools import opcode_previous_word_build_v1 as build


def reference(path, root=None):
    return dict(path=str(path.relative_to(root)) if root else str(path),
                bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())


class GateTests(unittest.TestCase):
    def setUp(self):
        retained = os.environ.get('GAMMA_PREVIOUS_WORD_UNIT_OUTPUT')
        if retained:
            root = Path(retained); root.mkdir(parents=True, exist_ok=True)
            self.base = Path(tempfile.mkdtemp(prefix=self._testMethodName+'_', dir=root))
        else:
            tmp = tempfile.TemporaryDirectory(dir=ROOT / 'results', prefix='previous_word_gate_unit_')
            self.addCleanup(tmp.cleanup); self.base = Path(tmp.name)
        self.snapshot = self.base / 'codec'; build.write_bundle(self.snapshot)
        self.raw = (b'<title>Oak\x00</title>First Elm First Elm\xff\n' * 3)
        self.assertLessEqual(len(self.raw), 4096)
        raw, archive, audit = [self.base / n for n in ('input.raw', 'parent.arc', 'parent.audit.json')]
        raw.write_bytes(self.raw)
        encoded, observed = codec.execute(codec.load(self.snapshot / 'program.py'), 'encode', self.raw, 'P')
        archive.write_bytes(encoded); audit.write_text(json.dumps(dict(parent=observed['parent'])))
        self.plan = dict(input=reference(raw), parent_archive=reference(archive), parent_audit=reference(audit))
        self.out = self.base / 'output'; self.out.mkdir()
        self.limits = dict(phase_cpu_seconds=10, phase_wall_seconds=15, phase_address_bytes=536870912)

    def run_gate(self):
        return gate.run_comparison(self.out, self.plan, self.snapshot, self.base / 'phases.jsonl', self.limits)

    def test_thirteen_same_arm_phases_and_projection_controls(self):
        result = self.run_gate()
        self.assertEqual(len(result['commands']), 13)
        self.assertTrue(result['correctness_pass'] and result['same_arm_decoder_all_arms'])
        self.assertTrue(result['all_arm_parse_and_updates_equal'] and result['KDS_history_equal'])
        rows = result['arms']
        self.assertEqual(rows['P']['audit']['parent'], rows['K']['audit']['parent'])
        self.assertNotEqual(rows['P']['audit']['word_history_sha256'], rows['K']['audit']['word_history_sha256'])
        for arm, row in rows.items():
            self.assertEqual((ROOT / row['artifacts']['restored']['path']).read_bytes(), self.raw)
            self.assertEqual(sum(row['audit']['updates_by_mode']), 8*row['audit']['parent']['modeled_bytes'])
            for command in row['commands']:
                argv = command['argv']; self.assertEqual(argv[argv.index('--arm')+1], arm)
        self.assertTrue(sum(rows['D']['audit']['updates_by_mode'][1:]) > 0)
        self.assertEqual(result['prediction_gate_pass'], rows['D']['archive_bytes'] < rows['P']['archive_bytes']
                         and rows['D']['archive_bytes'] < rows['S']['archive_bytes'])

    def test_optional_telemetry_is_not_mandatory_evidence(self):
        original = gate.phase.run_phase
        def omit(directory, label, *args):
            row = original(directory, label, *args)
            (directory / (label+'.stdout')).write_text('unavailable\n')
            return row
        with patch.object(gate.phase, 'run_phase', side_effect=omit): result = self.run_gate()
        self.assertTrue(result['correctness_pass'])
        self.assertTrue(all(c['codec_resources'] is None and c['missing_diagnostics'] for c in result['commands']))

    def test_complete_history_divergence_retained(self):
        original = gate.phase.run_phase
        def corrupt(directory, label, *args):
            row = original(directory, label, *args)
            if label == 'D-decode':
                p = directory / 'D-decode.audit.json'; data = json.loads(p.read_text())
                data['word_history_sha256'] = '0'*64; p.write_text(json.dumps(data))
            return row
        with patch.object(gate.phase, 'run_phase', side_effect=corrupt), self.assertRaises(ValueError):
            self.run_gate()
        self.assertTrue((self.out / 'D-decode-state.divergence.json').is_file())

    def test_missing_evidence_and_resource_classification(self):
        with self.assertRaises(gate.EvidenceFailure): gate.read_audit(self.base / 'missing.json')
        with self.assertRaises(gate.EvidenceFailure): gate.read_audit(self.base / 'parent.audit.json')
        self.assertEqual(gate.failure_class(gate.EvidenceFailure('missing')), 'incomplete-evidence')
        self.assertEqual(gate.failure_class(MemoryError()), 'budget-exhausted')
        self.assertEqual(gate.failure_class(OSError()), 'infrastructure-failure')
        with self.assertRaises(gate.BudgetStop):
            gate.require_phase(dict(timeout=True, returncode=124, error=None))

    def test_cross_arm_parse_disagreement_retained(self):
        original = gate.phase.run_phase
        def corrupt(directory, label, *args):
            row = original(directory, label, *args)
            if label.startswith('D-'):
                path = directory / (label+'.audit.json')
                data = json.loads(path.read_text()); data['parse_sha256'] = '0'*64
                path.write_text(json.dumps(data))
            return row
        with patch.object(gate.phase, 'run_phase', side_effect=corrupt), self.assertRaises(ValueError):
            self.run_gate()
        self.assertTrue((self.out / 'D-parse_sha256.divergence.json').is_file())

    def test_codec_declared_bounds_fail_before_decoder(self):
        with patch.object(codec, 'observe_execute') as execute:
            for archive in (b'', struct.pack('>II',250001,0)+b'x', struct.pack('>II',1,3)+b'x'):
                with self.assertRaises(ValueError): codec.execute(None, 'decode', archive, 'D')
            execute.assert_not_called()
            with patch.object(codec, 'RAW_LIMIT', 4), self.assertRaises(ValueError):
                codec.execute(None, 'encode', b'12345', 'D')
            execute.assert_not_called()

    def test_exact_empty_runtime_and_nonempty_checks(self):
        empty = self.base / 'empty.py'; empty.touch(); row = reference(empty)
        self.assertEqual(gate.check_file(row, absolute=True), empty)
        for mutation in ({'sha256':'0'*64}, {'bytes':False}, {'extra':0}, {'path':str(empty)+'/../empty.py'}):
            bad = dict(row, **mutation)
            with self.assertRaises(ValueError): gate.check_file(bad, absolute=True)
        empty.write_bytes(b'x')
        with self.assertRaises(ValueError): gate.check_file(row, absolute=True)
        nonempty = reference(empty); self.assertEqual(gate.check_file(nonempty, absolute=True), empty)
        empty.write_bytes(b'y')
        with self.assertRaises(ValueError): gate.check_file(nonempty, absolute=True)

    def test_external_plan_binding_without_future_program_inputs(self):
        root = self.base / 'binding'; root.mkdir()
        evidence = root / 'evidence.json'; evidence.write_text('{}')
        evidence_ref = reference(evidence, root)
        plan = {k: evidence_ref for k in ('input', 'parent_archive', 'parent_audit')}
        plan.update(source_files=[evidence_ref], evidence=[evidence_ref],
                    runtime_files=[], package_files=[dict(path=f'programs/{gate.CID}/p',bytes=1,sha256='0'*64)])
        plan_path = root / gate.INPUTS; plan_path.parent.mkdir(parents=True)
        plan_path.write_text(json.dumps(plan))
        snapshot = root / 'snapshot'; snapshot.mkdir(); (snapshot / 'gate-plan.json').write_bytes(plan_path.read_bytes())
        contract = dict(inputs=[reference(plan_path, root), evidence_ref])
        with patch.object(gate, 'ROOT', root):
            gate.verify_contract_bindings(contract, plan, snapshot)
            for entries in ([evidence_ref], contract['inputs']+[evidence_ref], [reference(plan_path,root)]):
                with self.assertRaises(ValueError):
                    gate.verify_contract_bindings(dict(inputs=entries), plan, snapshot)
            (snapshot / 'gate-plan.json').write_text('{}')
            with self.assertRaises(ValueError): gate.verify_contract_bindings(contract, plan, snapshot)
            (snapshot / 'gate-plan.json').write_bytes(plan_path.read_bytes()); evidence.write_text('{"changed":true}')
            with self.assertRaises(ValueError): gate.verify_contract_bindings(contract, plan, snapshot)

    def test_fixed_population_source_package_and_resources(self):
        plan = dict(candidate_id=gate.CID, resources=dict(gate.CAPS), phase_resources=dict(gate.PHASES),
            input=dict(bytes=250000,sha256='665fc689441b68462d88f82dc33212abe9c4824be095d03a556c9b55a2829fd3'),
            parent_archive=dict(bytes=67658,sha256='bda617eab7628f7cec6724ca3d82bf505efee9c2be4813dd404dcfa715140e6f'),
            parent_audit=dict(bytes=24889,sha256='7aa2091cc61cf1bc838062df300aff0719d23eec0cfc734508f56d5633356315'),
            source_files=[dict(path=p,sha256=gate.PUBLISHED.get(p,'0'*64)) for p in sorted(gate.SOURCES)],
            package_files=[dict(path=f'programs/{gate.CID}/{n}',bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
                           for n,b in build.bundle().items()],
            runtime_files=[dict(path=sys.executable)],evidence=[dict(path='receipt')])
        gate.validate_plan(plan)
        for section,key,value in [('resources','cpus',[3]),('resources','wall_seconds',3121),
                                  ('phase_resources','phase_cpu_seconds',181),('input','bytes',1000000)]:
            bad=copy.deepcopy(plan);bad[section][key]=value
            with self.assertRaises(ValueError): gate.validate_plan(bad)
        for field in ('source_files','runtime_files','package_files','evidence'):
            bad=copy.deepcopy(plan);bad[field]=[]
            with self.assertRaises(ValueError): gate.validate_plan(bad)
        self.assertIs(gate._authenticate.__code__, gate.authority.authenticate.__code__)
        self.assertEqual(gate._authenticate.__globals__['CAPS'],gate.CAPS)


if __name__ == '__main__':
    unittest.main()
