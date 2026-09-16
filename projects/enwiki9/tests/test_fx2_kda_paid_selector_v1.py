"""Independent exhaustive policy checks and exact serialization boundaries."""
from collections import Counter
from fractions import Fraction
import itertools
import unittest

from lib.fx2_kda_paid_selector_v1 import (
    Q, context, corrected, empty_histograms, fit, pack_policy, ratio_bounds,
    select_context, truth_product, unpack_policy)


class Tests(unittest.TestCase):
    def test_count_domain_identity_endpoints(self):
        for p in range(1, Q):
            for d in (1, Q - p, Q - 1):
                values = [corrected(p, d, j) for j in range(5)]
                self.assertEqual((values[0], values[4]), (p, d))
                self.assertTrue(all(min(p, d) <= x <= max(p, d) for x in values))
                for j, got in enumerate(values):
                    exact = Fraction((4 - j) * p + j * d, 4)
                    self.assertEqual(got, (exact + Fraction(1, 2)).numerator // (exact + Fraction(1, 2)).denominator)

    def test_complete_policy_serialization(self):
        xs = [i % 5 for i in range(64)]
        self.assertEqual(unpack_policy(pack_policy(xs)), xs)
        self.assertEqual(len(pack_policy(xs)), 25)
        for data in (b'', bytes(25), b'\x01' + bytes([255]) * 24):
            with self.assertRaises(ValueError): unpack_policy(data)

    def test_separable_exact_optimum_vs_exhaustive(self):
        histories = [Counter({(10000, 50000, 1): 3, (10000, 50000, 0): 2}),
                     Counter({(40000, 35000, 1): 4, (40000, 35000, 0): 7}),
                     Counter({(12000, 2000, 0): 5, (12000, 2000, 1): 1})]
        chosen = tuple(select_context(h)[0] for h in histories)
        def score(js):
            n = 1
            for h, j in zip(histories, js): n *= truth_product(h, j)
            return n
        policies = list(itertools.product(range(5), repeat=3))
        expected = max(policies, key=score)
        self.assertEqual(chosen, expected)
        self.assertEqual(score(chosen), max(map(score, policies)))

    def test_fit_prices_unused_entries_and_identity(self):
        hs = empty_histograms()
        hs[context(32768, 32768, 3)][32768, 32768, 1] = 9
        table, r, n, d = fit(hs)
        self.assertEqual(unpack_policy(table), [0] * 64)
        self.assertEqual(n, d)
        self.assertEqual(r['paid_ideal_gain_upper_bits'], -200)
        hs[0][32768, 32768, 1] = 1
        with self.assertRaises(ValueError): fit(hs)

    def test_pretruth_contexts_and_rounding(self):
        for bit in range(8):
            for p in (1, 16383, 16384, 32767, 32768, 49151, 49152, 65535):
                for d in (1, 32768, 65535):
                    self.assertEqual(context(p, d, bit), bit * 8 + (p // 16384) * 2 + int(d > p))
        self.assertEqual(corrected(1, 3, 1), 2)

    def test_ratio_certificate_without_logs(self):
        for n in range(1, 80):
            for d in range(1, 80):
                b = ratio_bounds(n, d)
                self.assertLessEqual(Fraction(2) ** b['lower_bits'], Fraction(n, d))
                self.assertLessEqual(Fraction(n, d), Fraction(2) ** b['upper_bits'])
                self.assertLessEqual(b['upper_bits'] - b['lower_bits'], 1)


if __name__ == '__main__': unittest.main()
