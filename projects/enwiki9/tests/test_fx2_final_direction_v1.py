"""Independent high-precision derivatives and malformed trace rejection."""
from decimal import Decimal, localcontext
from pathlib import Path
import struct
import tempfile
import unittest
from projects.enwiki9.tools import fx2_final_direction_v1 as direction


class DirectionTests(unittest.TestCase):
    def calculate(self, events):
        coefficients, rows, changed = direction.histogram(events)
        logs = {n: direction.log_bounds(n) for n, value in enumerate(coefficients) if value}
        return direction.certificate(coefficients, logs)

    def test_identical_endpoints_have_exact_zero_direction(self):
        result = self.calculate([(1, 1, 0), (65535, 65535, 1), (123, 123, 1)])
        self.assertEqual(result['certified_sign'], 'zero')
        self.assertEqual(result['derivative_nats_lower_numerator'], '0')
        self.assertEqual(result['derivative_nats_upper_numerator'], '0')

    def test_known_positive_and_negative_directions(self):
        self.assertEqual(self.calculate([(32768, 49152, 1)])['certified_sign'], 'positive')
        self.assertEqual(self.calculate([(32768, 49152, 0)])['certified_sign'], 'negative')

    def test_integer_aggregation_encloses_independent_direct_derivative(self):
        events = [(1, 2, 1), (65535, 64535, 0), (32768, 49152, 1), (1234, 1200, 0)]
        result = self.calculate(events)
        with localcontext() as context:
            context.prec = 140
            q = Decimal(65536)
            direct = sum((Decimal(y) - Decimal(p) / q) *
                         ((Decimal(t) / (q - t)).ln() - (Decimal(p) / (q - p)).ln())
                         for p, t, y in events)
            denominator = Decimal(result['derivative_denominator'])
            self.assertLess(Decimal(result['derivative_nats_lower_numerator']) / denominator, direct)
            self.assertGreater(Decimal(result['derivative_nats_upper_numerator']) / denominator, direct)

    def test_logarithm_enclosures_at_domain_edges(self):
        self.assertEqual(direction.log_bounds(1), (0, 0))
        for n in (2, 3, 32768, 65535):
            lo, hi = direction.log_bounds(n)
            with localcontext() as context:
                context.prec = 140
                value = Decimal(n).ln() * direction.SCALE
                self.assertLess(Decimal(lo), value)
                self.assertGreater(Decimal(hi), value)
        for n in (0, 65536):
            with self.assertRaises(ValueError):
                direction.log_bounds(n)

    def test_invalid_counts_and_truth_are_rejected(self):
        for event in ((0, 1, 0), (1, 65536, 0), (1, 2, 2)):
            with self.assertRaises(ValueError):
                direction.histogram([event])

    def test_trace_alignment_and_truncation_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p, q = Path(directory) / 'p', Path(directory) / 'q'
            payload = struct.pack('<7I', 123, 32768, 0, 0, 0, 0, 1)
            p.write_bytes(payload)
            q.write_bytes(payload[:-1])
            with self.assertRaisesRegex(ValueError, 'length'):
                list(direction.trace_events(p, q, 1))
            q.write_bytes(struct.pack('<7I', 124, 49152, 0, 0, 0, 0, 1))
            with self.assertRaisesRegex(ValueError, 'prediction or truth'):
                list(direction.trace_events(p, q, 1))


if __name__ == '__main__':
    unittest.main()
