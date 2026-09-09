import math
import struct
import unittest
from tools.context_edit_fx2_audit_v1 import evaluate
from tools.context_edit_fx2_attribution_v1 import attribute, reset_ideal_gain


class AttributionTest(unittest.TestCase):
    def test_episode_and_original_trajectory(self):
        donor = b'0123456789abcdefghijklmnopqrstuv'
        raw = b'ABCDEFGH' + donor + bytes(range(128, 168)) + b'ABCDEFGH!' + donor[:-1]
        trace = b''.join(struct.pack('<7I', 0, 32768, 0, 0, 0, 0, (v >> b) & 1)
                         for v in raw for b in range(7, -1, -1))
        original = evaluate(raw, trace)
        result = attribute(raw, trace, original)
        self.assertTrue(result['original_trajectory_verified'])
        self.assertEqual(result['episode_count'], 1)
        episode = result['episodes'][0]
        self.assertEqual((episode['start_byte'], episode['donor_start_byte'], episode['bits']), (88, 8, 256))
        self.assertGreater(episode['pure_saved_bits']['D'], episode['pure_saved_bits']['L'])
        self.assertGreater(episode['pure_saved_bits']['D'], episode['pure_saved_bits']['S'])
        original['probability_sha256']['D'] = 'corrupt'
        with self.assertRaises(ValueError): attribute(raw, trace, original)

    def test_ideal_reset_formula_and_limits(self):
        for gain in (-12.0, -1.0, 0.0, 1.0, 12.0):
            self.assertAlmostEqual(reset_ideal_gain(gain), math.log2((1 + 2 ** gain) / 2))
        self.assertEqual(reset_ideal_gain(-10000), -1)
        self.assertEqual(reset_ideal_gain(10000), 9999)


if __name__ == '__main__':
    unittest.main()
