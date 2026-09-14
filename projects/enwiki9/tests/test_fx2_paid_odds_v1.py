import itertools
import struct
import unittest
from collections import Counter

from lib.fx2_paid_odds_v1 import (
    CONTEXTS, Q, context, corrected_count, empty_histograms, fit,
    pack_policy, select_context, truth_product, unpack_policy,
)


class PaidOddsTests(unittest.TestCase):
    def test_exact_selection_matches_joint_enumeration(self):
        # Independent literal multiplication over aligned events, all 343
        # joint policies, multiple heterogeneous synthetic populations.
        for bits in itertools.product((0, 1), repeat=4):
            populations = [[(4096 + 509 * i + r * 4096, b) for i, b in enumerate(bits)]
                           for r in range(3)]
            histories = [Counter(events) for events in populations]
            selected = tuple(select_context(h)[0] for h in histories)
            def score(policy):
                value = 1
                for events, choice in zip(populations, policy):
                    for p, bit in events:
                        q = corrected_count(p, choice)
                        value *= q if bit else Q - q
                return value
            best = max(itertools.product(range(7), repeat=3), key=score)
            self.assertEqual(selected, best)

    def test_explicit_policy_roundtrip(self):
        choices = [i % 7 for i in range(CONTEXTS)]
        data = pack_policy(choices)
        self.assertEqual(len(data), 48)
        self.assertEqual(unpack_policy(data), choices)
        for data in (b'', b'\0' * 47, b'\0' * 49, b'\xff' * 48):
            with self.assertRaises(ValueError):
                unpack_policy(data)

    def test_identity_and_extremes(self):
        for p in range(1, Q):
            self.assertEqual(corrected_count(p, 0), p)
        for p in (1, 2, 32768, 65534, 65535):
            for j in range(7):
                self.assertTrue(1 <= corrected_count(p, j) < Q)
        self.assertEqual(corrected_count(32768, 1), 21845)
        self.assertEqual(corrected_count(32768, 6), 43691)

    def test_bounds_are_exact_integer_inequalities(self):
        for bits in itertools.product((0, 1), repeat=6):
            h = Counter(zip((1, 8191, 16384, 32768, 49152, 65535), bits))
            j, row = select_context(h)
            n, d = truth_product(h, j), truth_product(h, 0)
            lo, hi = row['ideal_gain_lower_bits'], row['ideal_gain_upper_bits']
            self.assertGreaterEqual(n, d << lo)
            self.assertLessEqual(n, d << hi)
            self.assertLessEqual(hi - lo, 1)

    def test_fixed_cost_is_paid_even_for_empty_or_identity_contexts(self):
        data, result = fit(empty_histograms())
        self.assertEqual(data, bytes(48))
        self.assertEqual(result['paid_ideal_gain_lower_bits'], -384)
        self.assertEqual(result['paid_ideal_gain_upper_bits'], -384)

    def test_causal_partition_and_invalid_populations(self):
        self.assertEqual(context(1, 0), 0)
        self.assertEqual(context(65535, 7), 127)
        h = empty_histograms()
        h[0][(8192, 1)] = 1
        with self.assertRaises(ValueError):
            fit(h)
        for count, pos in ((0, 0), (65536, 0), (1, 8)):
            with self.assertRaises(ValueError):
                context(count, pos)
        for h in (Counter({(1, 2): 1}), Counter({(1, 0): -1})):
            with self.assertRaises(ValueError):
                select_context(h)

    def test_trace_alignment_and_fixed_cost(self):
        from tools.fx2_paid_odds_cost250k_v1 import analyze
        trace = b''.join(struct.pack('<7I', 0, 32768, 0, 0, 0, 0, b)
                         for b in (0, 1, 0, 1, 0, 1, 0, 1))
        policy, result = analyze(b'U', trace)
        self.assertEqual(len(policy), 48)
        self.assertEqual(result['events'], 8)
        self.assertFalse(result['paid_ideal_headroom_pass'])
        self.assertTrue(result['fixed_family_paid_ideal_reject'])
        for body, bad in ((b'T', trace), (b'U', trace[:-1])):
            with self.assertRaises(ValueError):
                analyze(body, bad)


if __name__ == '__main__':
    unittest.main()
