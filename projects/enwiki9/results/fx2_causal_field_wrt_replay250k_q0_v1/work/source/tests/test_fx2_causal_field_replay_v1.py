"""Synthetic integration checks; these tests never open a corpus or model."""
import hashlib
import importlib.util
from pathlib import Path
import struct
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
import fx2_causal_field_replay_v1 as codec
from causal_field_parent_coder_v1 import Encoder
from wrt_exact import wrt_byte_transform, parse_store_bytes


def fixture(raw):
    modeled = bytearray([7])
    for byte in raw:
        if byte >= 128 or byte in (6, 7, 12, 64):
            modeled.append(wrt_byte_transform(12))
        modeled.append(wrt_byte_transform(byte))
    modeled = bytes(modeled)
    prefix = b"GFV1\x07" + len(raw).to_bytes(4, "big") + ((1 << 39) + len(modeled)).to_bytes(5, "big") + b"\xff" * 32
    q16 = b"".join(struct.pack("<H", 16000 + (i * 19) % 30000) for i in range(len(modeled) * 8))
    return modeled, prefix, q16


def native_trace(modeled, q16):
    coder = Encoder(max_bits=len(modeled) * 8)
    trace = bytearray()
    for index, (q,) in enumerate(struct.iter_unpack("<H", q16)):
        before = (coder.low, coder.high)
        bit = (modeled[index // 8] >> (7 - index % 8)) & 1
        coder.encode(bit, q)
        fp = struct.unpack("<I", struct.pack("<f", (q - 1) / 65534))[0]
        trace.extend(struct.pack("<7I", fp, q, *before, coder.low, coder.high, bit))
    return bytes(trace), coder.finish()


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.raw = b"{{t|a=a|b=" + b"x" * 53 + b"}}\n{{t|a=b|b=" + b"y" * 53 + b"}}\n{{t|a=a|b=" + b"x" * 53 + b"}}"
        self.modeled, self.prefix, self.q16 = fixture(self.raw)
        self.words = [b"unused"]
        self.digest = hashlib.sha256(self.raw).hexdigest()

    def run_arm(self, operation, body, arm="T", **changes):
        options = dict(operation=operation, body=body, q16=self.q16, prefix=self.prefix,
                       words=self.words, arm=arm, raw_bytes=len(self.raw), raw_sha256=self.digest)
        options.update(changes)
        return codec.replay(**options)

    def test_five_arm_independent_inverse_repeat_and_every_byte_state(self):
        outputs = {}
        for arm in codec.ARMS:
            archive, sync, result = self.run_arm("encode", self.modeled, arm)
            restored, decoded_sync, decoded = self.run_arm("decode", archive, arm)
            repeat, repeated_sync, repeated = self.run_arm("repeat", self.modeled, arm)
            self.assertEqual(restored, self.raw)
            self.assertEqual(archive, repeat)
            self.assertEqual(sync, decoded_sync)
            self.assertEqual(sync, repeated_sync)
            self.assertEqual(result, decoded)
            self.assertEqual(result, repeated)
            self.assertEqual(len(sync), len(self.modeled) * 32)
            self.assertFalse(result["standalone_decoder"])
            outputs[arm] = (archive, result)
        self.assertEqual(outputs["P"][0], outputs["K"][0])
        self.assertEqual(outputs["P"][1]["probability_digest"], outputs["K"][1]["probability_digest"])
        self.assertGreater(outputs["T"][1]["changed_probability_bits"], 0)

    def test_reference_wrt_inverse_and_header_mode_byte(self):
        stored = b"\x80\0\0\0\0\x07" + len(self.raw).to_bytes(4, "big") + self.modeled
        self.assertEqual(parse_store_bytes(stored, self.words).decoded, self.raw)
        archive, _, result = self.run_arm("encode", self.modeled, "P")
        self.assertEqual(archive[:46], self.prefix)
        self.assertEqual(result["prefix_bytes"], 46)

    def test_native_parent_trace_projection_reproduces_complete_archive(self):
        trace, payload = native_trace(self.modeled, self.q16)
        projected, report = codec.project_trace(trace, self.modeled, self.prefix + payload, len(self.raw))
        self.assertEqual(projected, self.q16)
        self.assertEqual(len(projected), len(self.modeled) * 16)
        self.assertTrue(report["native_intervals_and_payload_exact"])
        self.assertFalse(report["decoder_receives_truth_trace"])
        archive, _, _ = self.run_arm("encode", self.modeled, "P")
        self.assertEqual(archive, self.prefix + payload)

    def test_trace_truth_interval_probability_and_length_tampering_rejected(self):
        trace, payload = native_trace(self.modeled, self.q16)
        for word, value in ((0, 0x7FC00000), (1, 0), (2, 12), (4, 12), (6, 2)):
            changed = bytearray(trace)
            struct.pack_into("<I", changed, word * 4, value)
            with self.subTest(word=word), self.assertRaises(ValueError):
                codec.project_trace(bytes(changed), self.modeled, self.prefix + payload, len(self.raw))
        with self.assertRaises(ValueError):
            codec.project_trace(trace[:-1], self.modeled, self.prefix + payload, len(self.raw))
        with self.assertRaises(ValueError):
            codec.project_trace(trace, self.modeled, self.prefix + payload + b"\0", len(self.raw))

    def test_truncated_trailing_or_changed_archive_fails(self):
        archive, _, _ = self.run_arm("encode", self.modeled)
        for value in (archive[:-1], archive + b"\0", archive[:46] + bytes([archive[46] ^ 128]) + archive[47:]):
            with self.subTest(length=len(value)), self.assertRaises(ValueError):
                self.run_arm("decode", value)

    def test_declared_population_probability_and_work_bounds(self):
        for changes in ({"raw_sha256": "0" * 64}, {"raw_bytes": len(self.raw) + 1},
                        {"q16": self.q16[:-2]}, {"q16": b"\0\0" + self.q16[2:]},
                        {"raw_bytes": 250001}, {"arm": "TR"},
                        {"prefix": self.prefix[:14] + b"\0" * 32}):
            with self.subTest(changes=tuple(changes)), self.assertRaises(ValueError):
                self.run_arm("encode", self.modeled, **changes)

    def test_arbitrary_raw_bytes_preserve_spelling(self):
        raw = bytes(range(256)) + b"\r\n\t{{broken|A=A\xff"
        modeled, prefix, q16 = fixture(raw)
        options = dict(q16=q16, prefix=prefix, words=self.words, arm="T", raw_bytes=len(raw), raw_sha256=hashlib.sha256(raw).hexdigest())
        archive, sync, report = codec.replay("encode", modeled, **options)
        restored, sync2, report2 = codec.replay("decode", archive, **options)
        self.assertEqual((restored, sync2, report2), (raw, sync, report))


if __name__ == "__main__":
    unittest.main()
