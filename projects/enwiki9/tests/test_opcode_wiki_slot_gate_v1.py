"""Exercise the actual bounded comparison runner on synthetic inputs only."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import opcode_wiki_slot_gate_v1 as gate
import opcode_field_compact_observe_v1 as old


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='wiki-slot-runner-')
        self.base = Path(self.tmp.name)
        self.raw = b'<title>Oak</title>{{cite|title=Oak}} [[Category:Trees]]\0'
        self.input = self.base/'input.raw';self.input.write_bytes(self.raw)
        self.arc = self.base/'parent.arc';self.audit = self.base/'parent.audit.json'
        archive,audit=old.execute(old.load(ROOT/'programs/opcode_field_compact_v1/program.py'),'encode',self.raw)
        self.arc.write_bytes(archive);self.audit.write_text(json.dumps(audit))
        self.plan=dict(input=dict(path=str(self.input)),parent_archive=dict(path=str(self.arc)),parent_audit=dict(path=str(self.audit)))
        self.out=self.base/'out';self.out.mkdir()
        self.snapshot=ROOT/'programs/opcode_wiki_slot_v1'
        self.limits=dict(phase_cpu_seconds=10,phase_wall_seconds=15,phase_address_bytes=536870912)

    def tearDown(self):self.tmp.cleanup()

    def run_gate(self):
        return gate.run_comparison(self.out,self.plan,self.snapshot,self.base/'phases.jsonl',self.limits)

    def test_ten_fresh_phases_and_complete_controls(self):
        result=self.run_gate()
        self.assertEqual(len(result['commands']),10)
        self.assertTrue(result['correctness_pass'])
        self.assertEqual(result['arms']['P']['audit']['parent'],result['arms']['K']['audit']['parent'])
        self.assertGreater(result['arms']['D']['audit']['changed_slot_bytes'],0)
        self.assertEqual(result['archive_saving_bytes'],result['arms']['P']['archive_bytes']-result['arms']['D']['archive_bytes'])
        for row in result['arms'].values():
            self.assertEqual((ROOT/row['artifacts']['restored']['path']).read_bytes(),self.raw)

    def test_optional_telemetry_is_explicitly_missing(self):
        original=gate.phase.run_phase
        def missing(directory,label,*args):
            record=original(directory,label,*args)
            (directory/(label+'.stdout')).write_text('unavailable\n')
            return record
        with patch.object(gate.phase,'run_phase',side_effect=missing):result=self.run_gate()
        self.assertTrue(result['correctness_pass'])
        self.assertTrue(all(c['codec_resources'] is None and c['missing_diagnostics'] for c in result['commands']))

    def test_missing_mandatory_audit_blocks(self):
        original=gate.phase.run_phase
        def missing(directory,label,*args):
            record=original(directory,label,*args)
            if label=='P-decode':(directory/'P-decode.audit.json').unlink()
            return record
        with patch.object(gate.phase,'run_phase',side_effect=missing),self.assertRaises(FileNotFoundError):self.run_gate()

    def test_side_state_divergence_is_retained(self):
        original=gate.phase.run_phase
        def corrupt(directory,label,*args):
            record=original(directory,label,*args)
            if label=='K-decode':
                path=directory/'K-decode.audit.json';audit=json.loads(path.read_text())
                audit['complete_terminal_sha256']='0'*64;path.write_text(json.dumps(audit))
            return record
        with patch.object(gate.phase,'run_phase',side_effect=corrupt),self.assertRaises(ValueError):self.run_gate()
        self.assertTrue((self.out/'K-decode-state.divergence.json').exists())

    def test_wrong_retained_parent_fails(self):
        self.arc.write_bytes(b'wrong')
        with self.assertRaises(ValueError):self.run_gate()
        self.assertTrue((self.out/'retained-parent-archive.divergence.json').exists())

    def test_budget_stop_is_distinct(self):
        with self.assertRaises(gate.BudgetStop):
            gate.require_phase(dict(timeout=True,returncode=124,error=None))


if __name__=='__main__':unittest.main(verbosity=2)
