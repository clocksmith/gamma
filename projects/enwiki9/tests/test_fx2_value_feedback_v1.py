from fractions import Fraction as F
from pathlib import Path
import random
import struct
import subprocess
import tempfile
import unittest

from lib import fx2_value_feedback_v1 as ref

ROOT = Path(__file__).resolve().parents[1]
PROBE = r'''
#include "lib/fx2_value_feedback_v1.h"
#include <cstring>
#include <iostream>
using namespace gamma_value_feedback_v1;
int main() {
  char kind; long long a, b;
  while (std::cin >> kind >> a >> b) {
    if (kind == 's') {
      auto r = step(int32_t(a), int32_t(b));
      std::cout << r.valid << ' ' << r.value << ' ' << r.residual << '\n';
    } else if (kind == 'n') {
      uint32_t bits = uint32_t(a); float f;
      std::memcpy(&f, &bits, sizeof(f));
      int32_t result = 0; bool ok = normalized_q16(f, result);
      std::cout << ok << ' ' << result << '\n';
    } else return 2;
  }
}
'''


class FeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(dir='/run/user/1000')
        p = Path(cls.tmp.name)
        (p / 'probe.cpp').write_text(PROBE)
        cls.binary = p / 'probe'
        subprocess.run(['/usr/bin/g++', '-std=c++17', '-O2', '-fno-fast-math',
                        '-ffp-contract=off', '-I', str(ROOT), str(p / 'probe.cpp'),
                        '-o', str(cls.binary)], check=True, capture_output=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def native(self, lines):
        run = subprocess.run([str(self.binary)], input='\n'.join(lines) + '\n',
                             text=True, capture_output=True, check=True)
        return [tuple(map(int, s.split())) for s in run.stdout.splitlines()]

    def test_native_integer_domain_edges_and_independent_reference(self):
        rng = random.Random(20260916)
        fixed = [(n, r) for n in [ref.MINIMUM, ref.MINIMUM + 1, -ref.Q,
                                  -ref.HALF, -1, 0, 1, ref.HALF, ref.Q,
                                  ref.MAXIMUM - 1, ref.MAXIMUM]
                 for r in [-ref.HALF, -ref.HALF + 1, -1, 0, 1,
                           ref.HALF - 1, ref.HALF]]
        pairs = fixed + [(rng.randint(ref.MINIMUM, ref.MAXIMUM),
                          rng.randint(-ref.HALF, ref.HALF)) for _ in range(20000)]
        actual = self.native([f's {n} {r}' for n, r in pairs])
        expected = [(1, *ref.step(n, r)) for n, r in pairs]
        self.assertEqual(actual, expected)
        for (n, r0), (_, q, r1) in zip(pairs, actual):
            self.assertLessEqual(abs(r1), ref.HALF)
            self.assertEqual(n + r0, q * ref.Q + r1)
            self.assertTrue(-128 <= q <= 127)

    def test_every_residual_state_at_clipped_endpoints(self):
        pairs = [(n, r) for n in (ref.MINIMUM, ref.MAXIMUM)
                 for r in range(-ref.HALF, ref.HALF + 1)]
        actual = self.native([f's {n} {r}' for n, r in pairs])
        for (n, r0), row in zip(pairs, actual):
            q = 126 if n == ref.MAXIMUM and r0 == -ref.HALF else n // ref.Q
            self.assertEqual(row, (1, q, n + r0 - q * ref.Q))
            self.assertLessEqual(abs(row[2]), ref.HALF)

    def test_fp32_to_q16_against_exact_rationals(self):
        rng = random.Random(91261)
        bits = [rng.getrandbits(32) for _ in range(20000)]
        values = [-129., -128., -127.5, -0.5, 0., 0.5, 126.5, 127., 128.,
                  1 / (2 * ref.Q), 3 / (2 * ref.Q), -3 / (2 * ref.Q)]
        bits += [struct.unpack('<I', struct.pack('<f', v))[0] for v in values]
        bits += [0x00000001, 0x80000001, 0x7f800000, 0xff800000,
                 0x7fc00000, 0xffc00000]
        actual = self.native([f'n {b} 0' for b in bits])
        expected = []
        for b in bits:
            try:
                expected.append((1, ref.normalized_q16(b)))
            except ValueError:
                expected.append((0, 0))
        self.assertEqual(actual, expected)

    def test_invalid_integer_states_fail_closed(self):
        pairs = [(ref.MINIMUM - 1, 0), (ref.MAXIMUM + 1, 0),
                 (0, -ref.HALF - 1), (0, ref.HALF + 1)]
        self.assertEqual(self.native([f's {n} {r}' for n, r in pairs]),
                         [(0, 0, 0)] * len(pairs))
        for n, r in pairs + [(1.5, 0), (0, True)]:
            with self.assertRaises(ValueError): ref.step(n, r)

    def test_uniform_means_and_ring_subranges(self):
        rng = random.Random(667)
        values = [rng.randint(ref.MINIMUM, ref.MAXIMUM) for _ in range(64)]
        qs, rs = ref.sequence(values)
        for left in range(64):
            for right in range(left + 1, 65):
                n = right - left
                c = ref.weighted_certificate(values[left:right], qs[left:right],
                    rs[left:right + 1], [F(1, n)] * n)
                ceiling = F(1, 2 * n) if left == 0 else F(1, n)
                self.assertLessEqual(c['bound'], ceiling)

    def test_arbitrary_attention_weights_and_identity(self):
        rng = random.Random(193)
        for _ in range(100):
            n = rng.randint(1, 128)
            values = [rng.randint(ref.MINIMUM, ref.MAXIMUM) for _ in range(n)]
            qs, rs = ref.sequence(values, initial=rng.randint(-ref.HALF, ref.HALF))
            weights = [rng.randrange(1000) for _ in values]
            total = sum(weights) or 1
            c = ref.weighted_certificate(values, qs, rs, [F(w, total) for w in weights])
            self.assertLessEqual(abs(c['error']), c['bound'])

    def test_no_universal_attention_improvement(self):
        values = [32113, 32113]
        qs, rs = ref.sequence(values)
        self.assertEqual(qs, [0, 1])
        uniform = ref.weighted_certificate(values, qs, rs, [F(1, 2)] * 2)
        peaky = ref.weighted_certificate(values, qs, rs, [0, 1])
        parent_error = F(32113, ref.Q)
        self.assertLess(abs(uniform['error']), parent_error)
        self.assertGreater(abs(peaky['error']), parent_error)

    def test_misaligned_feedback_is_not_a_label_renaming(self):
        first = [32113, -32113]
        states = [ref.step(v, 0)[1] for v in first]
        aligned = [ref.step(v, r)[0] for v, r in zip(first, states)]
        shifted = [ref.step(v, r)[0] for v, r in zip(first, states[::-1])]
        self.assertEqual(aligned, [1, -1])
        self.assertEqual(shifted, [0, 0])

    def test_prefix_causality_reset_and_rejected_false_certificate(self):
        a = [3, 17, 64000, 5]
        self.assertEqual(ref.sequence(a)[0], ref.sequence(a + [-70000])[0][:4])
        qs, rs = ref.sequence(a)
        self.assertNotEqual(ref.step(a[0], rs[-1]), ref.step(a[0], 0))
        self.assertEqual(self.native([f's {a[0]} 0'])[0], (1, 0, 3))
        qs[1] += 1
        with self.assertRaises(ValueError):
            ref.weighted_certificate(a, qs, rs, [F(1, 4)] * 4)


if __name__ == '__main__': unittest.main()
