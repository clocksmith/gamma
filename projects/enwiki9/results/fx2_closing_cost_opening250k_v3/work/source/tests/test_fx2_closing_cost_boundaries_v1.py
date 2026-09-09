import importlib.util
from pathlib import Path
import math
import struct
import unittest

spec=importlib.util.spec_from_file_location('closing_cost',Path(__file__).resolve().parents[1]/'lib/fx2_closing_cost_v1.py')
cost=importlib.util.module_from_spec(spec);spec.loader.exec_module(cost)


def coder(body):
    return b''.join(struct.pack('<7I',0,32768,0,0,0,0,(v>>(7-b))&1) for v in body for b in range(8))


class Boundaries(unittest.TestCase):
    def test_last_bit_error_is_charged(self):
        r=cost.analyze(bytes([0]),coder(bytes([0])),[(1,1,0)])
        self.assertLess(r['arms']['D']['ideal_bits_saved'],0)
        self.assertEqual(r['arms']['D']['changed_probabilities'],8)

    def test_oracle_rollover(self):
        for n,chunks in [(512,1),(513,2)]:
            r=cost.analyze(bytes(n),coder(bytes(n)),[(1,0,0)]*n)
            exact_diagnostic=n*8*math.log2(65535/32768)
            self.assertEqual(r['ceiling_chunks'],chunks)
            self.assertGreaterEqual(r['perfect_probability_ideal_ceiling_bits'],exact_diagnostic)
            self.assertLess(r['perfect_probability_ideal_ceiling_bits'],exact_diagnostic+chunks)

    def test_invalid_terminal_and_activation(self):
        terminal=bytearray(b'CLR1'+bytes(1120));struct.pack_into('<Q',terminal,12,1)
        for active,donor in [(2,0),(0,1)]:
            data=b'CLT1'+struct.pack('<Q',1)+struct.pack('<BBQ',active,donor,0)+terminal
            with self.assertRaises(ValueError):cost.trace_rows(data,1)
        struct.pack_into('<Q',terminal,12,2)
        data=b'CLT1'+struct.pack('<Q',1)+struct.pack('<BBQ',1,0,0)+terminal
        with self.assertRaises(ValueError):cost.trace_rows(data,1)


if __name__=='__main__':unittest.main()
