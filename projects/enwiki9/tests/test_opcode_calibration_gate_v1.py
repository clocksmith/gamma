"""Real synthetic phase execution, parity and evidence-failure checks."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import opcode_calibration_gate_v1 as runner
import opcode_field_compact_observe_v1 as old


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.out=Path(self.tmp.name)
        self.raw=(b'<text xml:space="preserve">Oak. Oak. Oak.</text>\n')*6
        (self.out/'input').write_bytes(self.raw)
        self.codec=ROOT/'programs/opcode_calibration_cost_v1'
        arc,audit=old.execute(old.load(self.codec/'program.py'),'encode',self.raw)
        (self.out/'parent').write_bytes(arc);(self.out/'audit').write_text(json.dumps(audit))
        self.plan=dict(input=dict(path=str(self.out/'input')),parent_archive=dict(path=str(self.out/'parent')),
                       parent_audit=dict(path=str(self.out/'audit')))

    def tearDown(self):self.tmp.cleanup()

    def run_gate(self):
        return runner.run_comparison(self.out,self.plan,self.codec,self.out/'markers',
            dict(phase_address_bytes=536870912,phase_cpu_seconds=10,phase_wall_seconds=15))

    def test_three_independent_phases(self):
        r=self.run_gate();self.assertTrue(r['correctness_pass']);self.assertEqual(len(r['commands']),3)
        self.assertEqual(r['archive_saving_bytes'],0)
        self.assertEqual((self.out/'K.raw').read_bytes(),self.raw)

    def test_wrong_parent_fails(self):
        (self.out/'parent').write_bytes(b'wrong')
        with self.assertRaises(ValueError):self.run_gate()
        self.assertTrue((self.out/'parent-archive.divergence.json').exists())

    def test_missing_audit_fails(self):
        original=runner.gate.phase.run_phase
        def missing(directory,label,*args):
            r=original(directory,label,*args)
            if label=='decode':(directory/'decode.audit.json').unlink()
            return r
        with patch.object(runner.gate.phase,'run_phase',side_effect=missing),self.assertRaises(FileNotFoundError):self.run_gate()

    def test_optional_telemetry_missing_is_not_codec_failure(self):
        original=runner.gate.phase.run_phase
        def missing(directory,label,*args):
            r=original(directory,label,*args);(directory/(label+'.stdout')).write_text('missing');return r
        with patch.object(runner.gate.phase,'run_phase',side_effect=missing):r=self.run_gate()
        self.assertTrue(r['correctness_pass']);self.assertTrue(all(x['missing_diagnostics'] for x in r['commands']))


if __name__=='__main__':unittest.main(verbosity=2)
