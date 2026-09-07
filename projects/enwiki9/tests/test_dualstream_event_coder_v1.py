"""Synthetic categorical arithmetic inverses and complete state checks."""
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.dualstream_event_coder_v1 import EventChannel, EventCodecError, MODEL_SPEC


class EventChannelTests(unittest.TestCase):
    def roundtrip(self, mode, events, emits=None):
        encoder = EventChannel(mode)
        checkpoints = {}
        for index, (kind, alphabet, value, context, category) in enumerate(events):
            self.assertEqual(encoder.event(kind, alphabet, value, context, category), value)
            if emits is not None:
                encoder.emit(emits[index])
            if index in (0, 1, 31, len(events) - 1):
                checkpoints[index] = encoder.state_digest()
        payload, first = encoder.finish()
        decoder = EventChannel(mode, payload)
        for index, (kind, alphabet, value, context, category) in enumerate(events):
            self.assertEqual(decoder.event(kind, alphabet, None, context, category), value)
            if emits is not None:
                # Different call grouping must not change output history/trace.
                for byte in emits[index]:
                    decoder.emit(bytes([byte]))
            if index in checkpoints:
                self.assertEqual(decoder.state_digest(), checkpoints[index])
        absent, second = decoder.finish()
        self.assertIsNone(absent)
        self.assertEqual(first, second)
        self.assertEqual(sum(first["actual_bytes_by_category"].values()), len(payload))
        self.assertEqual(first["payload_bytes"], len(payload))
        self.assertEqual(first["state_digest"], decoder.state_digest())
        return payload, first

    def test_empty_stream_and_singleton_events(self):
        for mode in ("R", "G", "X"):
            payload, report = self.roundtrip(mode, [])
            self.assertEqual(report["binary_events"], 0)
            self.assertEqual(report["actual_bytes_by_category"], {"framing": len(payload)})
            events = [(3, 1, 0, (i,), "program") for i in range(6)]
            payload2, report2 = self.roundtrip(mode, events, [b"" for _ in events])
            self.assertEqual(report2["binary_events"], 0)
            self.assertNotEqual(payload, payload2)

    def test_balanced_nonpower_and_maximal_alphabets(self):
        rng = random.Random(61671)
        events = []
        alphabets = [2, 3, 5, 255, 256, 257, 65535, 65536, 65537, 1048576]
        for index in range(180):
            alphabet = alphabets[index % len(alphabets)]
            value = (0, alphabet - 1, rng.randrange(alphabet))[index % 3]
            events.append((index % 11, alphabet, value, (index % 7, -1), "literal" if index % 2 else "program"))
        for mode in ("R", "G", "X"):
            payload, report = self.roundtrip(mode, events, [rng.randbytes(i % 8) for i in range(len(events))])
            self.assertGreater(report["binary_events"], len(events))
            self.assertLessEqual(report["binary_events"], 20 * len(events))

    def test_repeat_and_context_isolation(self):
        sequence = [0, 1, 0, 0, 1, 1] * 40
        fixed = [(4, 2, value, (), "content") for value in sequence]
        contextual = [(4, 2, value, (i % 7,), "content") for i, value in enumerate(sequence)]
        gp, gr = self.roundtrip("G", fixed)
        gp_repeat, gr_repeat = self.roundtrip("G", fixed)
        self.assertEqual((gp, gr), (gp_repeat, gr_repeat))
        context_gp, context_gr = self.roundtrip("G", contextual)
        self.assertEqual(gp[:-32], context_gp[:-32])
        self.assertEqual(gr["probability_trace_sha256"], context_gr["probability_trace_sha256"])
        self.assertEqual(gr["model_state_digest"], context_gr["model_state_digest"])
        self.assertNotEqual(gr["sync_trace_sha256"], context_gr["sync_trace_sha256"])
        _, xr = self.roundtrip("X", contextual)
        self.assertNotEqual(context_gr["probability_trace_sha256"], xr["probability_trace_sha256"])
        self.assertNotEqual(context_gr["model_state_digest"], xr["model_state_digest"])
        rp, rr = self.roundtrip("R", fixed)
        self.assertEqual(rp, gp)
        self.assertEqual(rr["probability_trace_sha256"], gr["probability_trace_sha256"])

    def test_count_rescaling_and_rare_outcome(self):
        events = [(0, 2, 0, (), "content")] * 33000 + [(0, 2, 1, (), "content")]
        _, report = self.roundtrip("G", events)
        self.assertEqual(report["binary_events"], 33001)
        channel = EventChannel("G")
        for kind, alphabet, value, context, category in events:
            channel.event(kind, alphabet, value, context, category)
        occupied = [i for i, value in enumerate(channel.base.tags) if value]
        self.assertEqual(len(occupied), 1)
        index = occupied[0]
        self.assertLess(channel.base.zero[index] + channel.base.one[index], 32768)
        self.assertGreater(channel.base.zero[index], 16000)
        self.assertGreater(channel.base.one[index], 0)

    def test_truncation_trailing_and_corruption_rejected(self):
        events = [(1, 257, (i * 37) % 257, (i % 3,), "arguments") for i in range(40)]
        payload, _ = self.roundtrip("X", events)
        malformed = [payload[:cut] for cut in range(len(payload))]
        malformed += [payload + b"\0", payload + payload]
        for location in (0, len(payload) // 2, len(payload) - 33, len(payload) - 1):
            changed = bytearray(payload)
            changed[location] ^= 1
            malformed.append(bytes(changed))
        for bad in malformed:
            with self.subTest(length=len(bad)), self.assertRaises(EventCodecError):
                decoder = EventChannel("X", bad)
                for kind, alphabet, _, context, category in events:
                    decoder.event(kind, alphabet, None, context, category)
                decoder.finish()

    def test_output_truth_and_event_schedule_bound_to_checksum(self):
        encoder = EventChannel("G")
        encoder.event(0, 1, 0)
        encoder.emit(b"exact\0\xff")
        payload, _ = encoder.finish()
        for variant in ("output", "event", "kind"):
            with self.subTest(variant=variant), self.assertRaises(EventCodecError):
                decoder = EventChannel("G", payload)
                if variant != "event":
                    decoder.event(1 if variant == "kind" else 0, 1)
                decoder.emit(b"wrong\0\xff" if variant == "output" else b"exact\0\xff")
                decoder.finish()

    def test_invalid_parameters_and_finite_budgets(self):
        for mode in ("", "P", None):
            with self.assertRaises(EventCodecError):
                EventChannel(mode)
        invalid = [dict(kind=-1, alphabet=2, value=0), dict(kind=True, alphabet=2, value=0),
                   dict(kind=0, alphabet=0, value=0), dict(kind=0, alphabet=1048577, value=0),
                   dict(kind=0, alphabet=2, value=2), dict(kind=0, alphabet=2, value=None),
                   dict(kind=0, alphabet=2, value=0, context=[1]),
                   dict(kind=0, alphabet=2, value=0, context=(1 << 63,)),
                   dict(kind=0, alphabet=2, value=0, category="framing")]
        for kwargs in invalid:
            with self.subTest(kwargs=kwargs), self.assertRaises(EventCodecError):
                EventChannel("G").event(**kwargs)
        channel = EventChannel("G")
        channel.events = MODEL_SPEC["max_events"]
        with self.assertRaises(EventCodecError):
            channel.event(0, 1, 0)
        channel = EventChannel("G")
        channel.bits = MODEL_SPEC["max_binary_events"]
        with self.assertRaises(EventCodecError):
            channel.event(0, 2, 0)
        channel = EventChannel("G")
        with self.assertRaises(EventCodecError):
            channel.emit(b"x" * (MODEL_SPEC["max_output_bytes"] + 1))

    def test_finish_closes_and_decoder_cannot_receive_truth(self):
        encoder = EventChannel("G")
        payload, _ = encoder.finish()
        for action in (lambda: encoder.finish(), lambda: encoder.event(0, 1, 0), lambda: encoder.emit(b"")):
            with self.assertRaises(EventCodecError):
                action()
        decoder = EventChannel("G", payload)
        with self.assertRaises(EventCodecError):
            decoder.event(0, 1, 0)


if __name__ == "__main__":
    unittest.main()
