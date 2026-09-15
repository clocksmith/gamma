import copy
from fractions import Fraction
import hashlib
import math
import struct
import unittest

from lib.fx2_causal_residual_v1 import Controller, AMPLITUDES, corrected, headroom
from tools.causal_field_parent_coder_v1 import Encoder, Decoder


def fixture(n=64):
    body = bytes(0xaa if i % 2 == 0 else 0x55 for i in range(n))
    features = bytearray(); coder = bytearray()
    for i, byte in enumerate(body):
        packed = sum((1 if i % 2 == 0 else 2) << (2 * j) for j in range(32))
        for r in range(8):
            y = byte >> (7-r) & 1
            features.extend(struct.pack('<QHBB', packed, 32768, r | 8, y))
            coder.extend(struct.pack('<7I', 0, 32768, 0, 0, 0, 0, y))
    return body, bytes(features), bytes(coder)


class Tests(unittest.TestCase):
    def test_alignment_and_certified_slope(self):
        body, f, c = fixture()
        report, vectors = headroom(f, body, c)
        self.assertEqual(report['arms'][0]['slope_diagnostic'], 128)
        self.assertEqual(report['arms'][1]['slope_diagnostic'], -128)
        self.assertEqual(report['distinct_control_probabilities'], 256)
        self.assertEqual(list(vectors[0][0][:256]), [0]*256)
        for j, sign in enumerate((1, -1)):
            x = [Fraction(sign, 2)] * 256
            for k in AMPLITUDES:
                gain = sum(math.log1p(float(v * k / 32768)) for v in x)
                b = report['arms'][j]['rounded_upper_bits_diagnostic'] * math.log(2)
                self.assertLessEqual(gain, b + 1e-10)

    def test_exact_count_reference_and_zero(self):
        for c in range(1, 65536):
            self.assertEqual(corrected(c, 0, 123, 456), c)
        for c in (1, 2, 32768, 65534, 65535):
            for k in AMPLITUDES:
                for a, m in ((0, 0), (1, 3), (-1, 3), (67107840, 67107840), (-67107840, 67107840)):
                    q = Fraction(c) if not m else Fraction(c) + Fraction(c * (65536-c)*k*a, 65536*32768*m)
                    expected = max(1, min(65535, (q + Fraction(1, 2)).numerator // (q + Fraction(1, 2)).denominator))
                    self.assertEqual(corrected(c, k, a, m), expected)

    def test_native_style_inverse_and_complete_state(self):
        body, f, c = fixture(97)
        for shifted in (False, True):
            model = Controller(shifted); enc = Encoder(); states = hashlib.sha256()
            for packed, count, flags, y in struct.iter_unpack('<QHBB', f):
                a, m = model.predict(count, packed)
                enc.encode(y, corrected(count, 4096, a, m)); model.observe(y)
                states.update(model.state())
            dec = Decoder(enc.finish()); other = Controller(shifted); check = hashlib.sha256()
            for packed, count, flags, y in struct.iter_unpack('<QHBB', f):
                a, m = other.predict(count, packed)
                truth = dec.decode(corrected(count, 4096, a, m))
                self.assertEqual(truth, y); other.observe(truth); check.update(other.state())
            self.assertEqual(states.digest(), check.digest())

    def test_no_second_half_truth_learning(self):
        body, f, c = fixture()
        model = Controller()
        rows = list(struct.iter_unpack('<QHBB', f))
        for packed, count, flags, y in rows[:256]:
            self.assertEqual(model.predict(count, packed), (0, 0)); model.observe(y)
        other = copy.deepcopy(model)
        for packed, count, flags, y in rows[256:]:
            self.assertEqual(model.predict(count, packed), other.predict(count, packed))
            model.observe(y); other.observe(1-y)
        self.assertEqual(model.memory, [[0]*32 for _ in range(8)])
        self.assertEqual(model.state(), other.state())

    def test_tails_and_repeat(self):
        for n in (1, 31, 32, 33, 63, 64, 65):
            body, f, c = fixture(n)
            a, v = headroom(f, body, c); b, w = headroom(f, body, c)
            self.assertEqual(a, b); self.assertEqual(v, w)
            self.assertEqual(a['aligned_nonzero_events'], max(0, min(n, 64)-32)*8)

    def test_missing_features_and_invalid_order(self):
        model = Controller()
        with self.assertRaises(ValueError): model.observe(0)
        self.assertEqual(model.predict(32768, 0), (0, 0))
        with self.assertRaises(ValueError): model.predict(32768, 0)
        with self.assertRaises(ValueError): model.state()
        model.observe(1)
        with self.assertRaises(ValueError): corrected(0, 0, 0, 0)
        with self.assertRaises(ValueError): corrected(32768, 4096, 2, 1)
        with self.assertRaises(ValueError): model.predict(32768, 3)

    def test_record_corruption(self):
        body, f, c = fixture()
        for offset in (10, 11):
            broken = bytearray(f); broken[offset] ^= 1
            with self.assertRaises(ValueError): headroom(bytes(broken), body, c)


if __name__ == '__main__': unittest.main()
