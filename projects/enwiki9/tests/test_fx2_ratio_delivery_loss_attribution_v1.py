"""Independent synthetic loss expectations and closed-trace alignment failures."""
import math
from pathlib import Path
import struct
import tempfile
import unittest

from projects.enwiki9.tools import fx2_ratio_delivery_loss_attribution_v1 as audit
from test_fx2_residual_ratio_native_v1 import Reference


class AttributionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.library = audit.ROOT / 'results/fx2_residual_ratio_native_v1/attempt01/ratio.so'
        self.raw = b'\x01' * 4
        self.vocabulary = list(range(205))
        self.parent = self.root / 'parent.coder'
        self.target = self.root / 'target.coder'
        self.state = self.root / 'state.ratio'
        native = audit.Native(audit.load_library(self.library), 205, 'D')
        self.addCleanup(native.close)
        reference = Reference(205, 'D')
        cached = [(v, 0, 0) for v in self.vocabulary]
        records = []

        def record(kind):
            inner = native.serialize()
            payload = b'GRD2' + struct.pack('<HBBH', 205, ord('D'), int(kind != 'I'), len(inner)) + inner
            payload += b''.join(struct.pack('<BQQ', *row) for row in cached)
            records.append(kind.encode() + struct.pack('<I', len(payload)) + payload)

        record('I')
        previous = None
        expected = []
        for byte in self.raw:
            if previous is not None:
                p, q = previous
                expected.append(math.log2(float((q[byte] / sum(q)) / (p[byte] / sum(p)))))
                native.observe(byte)
                reference.observe(byte)
                record('O')
            base = [audit.bits(1 / 205)] * 205
            corrected = native.predict(base)
            exact = reference.predict(base)
            self.assertEqual(corrected, exact)
            previous = ([audit.value(x) for x in base], [audit.value(x) for x in exact])
            cached = [(v, int(audit.value(p) * audit.UNIT), int(audit.value(q) * audit.UNIT))
                      for v, p, q in zip(self.vocabulary, base, corrected)]
            record('P')
        self.expected = math.fsum(expected)
        self.state.write_bytes(b''.join(records))
        coder = b''.join(struct.pack('<7I', audit.bits(.5), 32768, 0, 0, 0, 0, (v >> b) & 1)
                         for v in self.raw for b in range(7, -1, -1))
        self.parent.write_bytes(coder)
        self.target.write_bytes(coder)

    def replay(self):
        return audit.replay(self.parent, self.target, self.state, self.vocabulary,
                            self.library, len(self.raw), 'D')

    def test_causal_expert_loss_and_full_state_replay(self):
        raw, result = self.replay()
        self.assertEqual(raw, self.raw)
        self.assertEqual(result['scored_symbols'], 3)
        self.assertEqual(result['matched_calibration_states'], 8)
        self.assertAlmostEqual(result['expert_ideal_bits_saved'], self.expected, places=12)
        self.assertGreater(result['expert_ideal_bits_saved'], 0)
        self.assertEqual(result['final_coder_ideal_bits_saved'], 0)
        self.assertEqual(result, self.replay()[1])

    def test_changed_original_prediction_is_rejected(self):
        payload = bytearray(self.target.read_bytes())
        payload[0] ^= 1
        self.target.write_bytes(payload)
        with self.assertRaisesRegex(ValueError, 'original prediction'):
            self.replay()

    def test_changed_cached_correction_is_rejected(self):
        payload = bytearray(self.state.read_bytes())
        payload[5976 + 5 + 2486 + 9] ^= 1
        self.state.write_bytes(payload)
        with self.assertRaisesRegex(ValueError, 'corrected mass'):
            self.replay()

    def test_changed_ratio_state_is_rejected(self):
        payload = bytearray(self.state.read_bytes())
        payload[5 + 10 + 16] ^= 1
        self.state.write_bytes(payload)
        with self.assertRaisesRegex(ValueError, 'ratio-state divergence'):
            self.replay()

    def test_truncated_trace_is_rejected(self):
        self.state.write_bytes(self.state.read_bytes()[:-1])
        with self.assertRaisesRegex(Exception, 'incomplete delivery'):
            self.replay()


if __name__ == '__main__':
    unittest.main()
