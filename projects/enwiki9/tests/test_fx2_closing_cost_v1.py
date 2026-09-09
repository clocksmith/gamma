import importlib.util
from pathlib import Path
import struct
import unittest

spec=importlib.util.spec_from_file_location('closing_cost',Path(__file__).resolve().parents[1]/'lib/fx2_closing_cost_v1.py')
cost=importlib.util.module_from_spec(spec);spec.loader.exec_module(cost)


def coder(body,p=32768):
    return b''.join(struct.pack('<7I',0,p,0,0,0,0,(v>>(7-b))&1) for v in body for b in range(8))


class Tests(unittest.TestCase):
    def test_no_activation_is_parent_identity(self):
        r=cost.analyze(b'ab',coder(b'ab'),[(0,0,0)]*2)
        self.assertEqual(r['perfect_probability_ideal_ceiling_bits'],0)
        self.assertTrue(all(a['changed_probabilities']==0 for a in r['arms'].values()))

    def test_first_wrong_donor_is_charged(self):
        r=cost.analyze(b'\x00',coder(b'\x00'),[(1,255,0)])
        self.assertLess(r['arms']['D']['ideal_bits_saved'],0)
        self.assertEqual(r['active_bits'],8)
        self.assertEqual(r['arms']['D']['correct_donors'],0)

    def test_right_donor_and_wrong_control_separate(self):
        r=cost.analyze(b'ab',coder(b'ab'),[(1,97,0),(1,98,0)])
        self.assertGreater(r['arms']['D']['ideal_bits_saved'],0)
        self.assertGreater(r['arms']['D']['ideal_bits_saved'],r['arms']['S']['ideal_bits_saved'])
        self.assertEqual(r['arms']['K']['changed_probabilities'],0)

    def test_ceiling_rounding_and_invalid_coordinates(self):
        for n,d,expected in [(1,1,0),(1,2,-1),(3,2,1),(1,3,-1),(9,1,4)]:
            self.assertEqual(cost.ceiling_ratio(n,d),expected)
        with self.assertRaises(ValueError):cost.analyze(b'a',coder(b'b'),[(1,97,0)])
        with self.assertRaises(ValueError):cost.analyze(b'a',coder(b'a',0),[(1,97,0)])

    def test_donor_trace_framing(self):
        terminal=bytearray(b'CLR1'+bytes(1120));struct.pack_into('<Q',terminal,12,1)
        data=b'CLT1'+struct.pack('<Q',1)+struct.pack('<BBQ',1,97,0)+terminal
        self.assertEqual(cost.trace_rows(data,1),[(1,97,0)])
        with self.assertRaises(ValueError):cost.trace_rows(data[:-1],1)


if __name__=='__main__':unittest.main()
