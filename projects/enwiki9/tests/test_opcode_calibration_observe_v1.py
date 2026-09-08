"""Pre-truth calibration attribution and unchanged exact parent replay."""
import math
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import opcode_calibration_observe_v1 as observer
import opcode_field_compact_observe_v1 as original


class CalibrationTests(unittest.TestCase):
    def events(self,bit=0,pf=1,pm=2,mode=0):
        a=observer.CalibrationAudit(4)
        a.transition((1,(0,()),mode,(1,1,1),3))
        a.probability((0,0,1,0,pf,('key',),(0,0,2,0),pm,(),()))
        a.transition((0,bit,((0,'key',(1,1)),),(0,0,2,0),(1,1),()))
        return a

    def test_known_ratio_sign_and_mode_partition(self):
        a=self.events();self.assertEqual(a.rows[(0,2)]['sse_excess_bits'],1)
        b=self.events(bit=1);self.assertAlmostEqual(b.rows[(0,2)]['sse_excess_bits'],math.log2(2/3))
        c=self.events(mode=1);self.assertNotIn((0,2),c.rows)
        d=self.events(pf=2,pm=2);self.assertEqual(d.rows[(0,2)]['changed_bits'],0)
        self.assertEqual(d.rows[(0,2)]['sse_excess_bits'],0)

    def test_unpaired_truth_and_duplicate_prediction_fail(self):
        a=observer.CalibrationAudit(4)
        with self.assertRaises(ValueError):a.transition((0,0,(),(),(),()))
        p=(0,0,1,0,1,('key',),(0,0,2,0),2,(),())
        a.probability(p)
        with self.assertRaises(ValueError):a.probability(p)

    def test_invalid_probability_rejected(self):
        with self.assertRaises(ValueError):self.events(pf=0)
        with self.assertRaises(ValueError):self.events(bit=2)

    def test_exact_parent_and_independent_witnesses(self):
        codec=original.load(ROOT/'programs/opcode_calibration_cost_v1/program.py')
        fixtures=[b'',bytes(range(256))*2,
            (b'<text xml:space="preserve">Oak is a tree. Oak is a tree.\n</text>')*16]
        copied=False;changed=False
        for raw in fixtures:
            ref,ref_audit=original.execute(codec,'encode',raw)
            arc,enc=observer.execute(codec,'encode',raw)
            inv,dec=observer.execute(codec,'decode',arc)
            rep,repeat=observer.execute(codec,'encode',inv)
            self.assertEqual(inv,raw);self.assertEqual(arc,ref);self.assertEqual(arc,rep)
            self.assertEqual(enc,dec);self.assertEqual(enc,repeat)
            self.assertEqual(enc['parent'],ref_audit)
            self.assertEqual(enc['observed_bits'],sum(r['bits'] for r in enc['rows']))
            copied|=any(r['mode']!=0 for r in enc['rows'])
            changed|=any(r['changed_bits'] for r in enc['rows'])
        self.assertTrue(copied);self.assertTrue(changed)


if __name__=='__main__':unittest.main(verbosity=2)
