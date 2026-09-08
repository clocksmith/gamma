import itertools
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.fx2_compact_complement_bound_v1 import analyze, aligned_counts, ceil_log2_ratio, product


class BoundTests(unittest.TestCase):
    def test_integer_ceiling_exhaustive(self):
        for n, d in itertools.product(range(1, 65), repeat=2):
            k = ceil_log2_ratio(n, d)
            self.assertTrue(n <= d * 2**k if k >= 0 else n * 2**-k <= d)
            lower = k - 1
            self.assertTrue(n > d * 2**lower if lower >= 0 else n * 2**-lower > d)
        self.assertEqual(product([]), 1)
        self.assertEqual(product(range(1, 11)), 3628800)
        for x in [(0, 1), (1, 0), (-1, 2)]:
            with self.assertRaises(ValueError): ceil_log2_ratio(*x)

    def test_equal_and_worse(self):
        for d in [32768, 16384]:
            x = analyze([32768] * 16, [d] * 16, (1,))
            self.assertEqual(x['clairvoyant_ideal_gain_ceiling_bits'], 0)
            self.assertEqual(x['fixed_block_oracles'][0]['after_selector_ideal_gain_ceiling_bits'], -2)

    def test_complementary_segments_and_paid_labels(self):
        p = [16384] * 16
        d = [8192] * 8 + [32768] * 8
        x = analyze(p, d, (1, 2))
        self.assertEqual(x['all_treatment_ideal_gain_bits_approx'], 0)
        self.assertEqual(x['clairvoyant_ideal_gain_ceiling_bits'], 8)
        self.assertEqual(x['fixed_block_oracles'][0]['after_selector_ideal_gain_ceiling_bits'], 6)
        self.assertEqual(x['fixed_block_oracles'][1]['after_selector_ideal_gain_ceiling_bits'], -1)

    def test_mixture_bound_on_all_small_arm_assignments(self):
        p = [2, 3, 4, 5, 6, 7, 8, 9]
        d = list(reversed(p))
        upper = product(max(a, b) for a, b in zip(p, d))
        for choices in itertools.product((0, 1), repeat=8):
            self.assertLessEqual(product((d if c else p)[i] for i, c in enumerate(choices)), upper)
        # Midpoint convex probabilities: multiply by two to stay integral.
        self.assertLessEqual(product(a + b for a, b in zip(p, d)), upper * 2**8)

    def test_trace_alignment_and_corruption(self):
        body = b'\x81'
        rows = [struct.pack('<7I', 0, 16384, 0, 0, 0, 0, (body[0] >> (7-i)) & 1) for i in range(8)]
        trace = b''.join(rows)
        p, d = aligned_counts(trace, trace, body)
        self.assertEqual(p, d)
        self.assertEqual(p, [16384] + [49152] * 6 + [16384])
        for left, right, raw in [(trace[:-1], trace, body), (trace, trace, b'\x80')]:
            with self.assertRaises(ValueError): aligned_counts(left, right, raw)
        for p, d in [([], []), ([1], [1]), ([1] * 8, [0] * 8)]:
            with self.assertRaises(ValueError): analyze(p, d)


if __name__ == '__main__':
    unittest.main()
