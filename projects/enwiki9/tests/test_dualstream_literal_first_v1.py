"""Synthetic correctness and complete-cost admission; no corpus selection."""
import hashlib
import importlib.util
from pathlib import Path
import random
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import dualstream_literal_first_v1 as codec


def parent(raw, frame_size=65536):
    core = codec.legacy
    parts = [raw[i:i + frame_size] for i in range(0, len(raw), frame_size)]
    return core.HEADER.pack(codec.PLAIN_MAGIC, frame_size, len(parts), len(raw)) + b"".join(
        core.frame_bytes(part, "plain")[0] for part in parts)


def fixture(count=96, width=180):
    rng = random.Random(712)
    records = []
    for index in range(count):
        value = bytes(rng.choice(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789") for _ in range(width))
        records.append(b"<page><title>" + value + b"</title><text>" + value
                       + b" is an exact repeated field.</text></page>\n")
    return b"".join(records)


class LiteralFirstTests(unittest.TestCase):
    def check_roundtrip(self, raw, frame_size=65536):
        for mode in ("K", "D"):
            first, report = codec.encode(raw, mode, frame_size)
            inverse, decoded = codec.decode(first)
            second, repeated = codec.encode(raw, mode, frame_size)
            self.assertEqual(raw, inverse)
            self.assertEqual(first, second)
            self.assertEqual(report, repeated)
            common = {key: value for key, value in report.items()
                      if key not in ("mode", "search_spec", "repeat_scope", "raw_encoder_repeat_proved")}
            common["frames"] = [{key: value for key, value in f.items() if key != "search"} for f in report["frames"]]
            self.assertEqual(common, decoded)
            self.assertEqual(sum(report["costs"].values()), len(first))
            self.assertLessEqual(len(first), len(parent(raw, frame_size)))
            if mode == "K":
                self.assertEqual(first, parent(raw, frame_size))

    def test_arbitrary_bytes_empty_and_partial_frames(self):
        for raw in (b"", b"x", bytes(range(256)), b"\xff<bad\x00\r\n  &amp;\n" * 9):
            with self.subTest(raw=len(raw)):
                self.check_roundtrip(raw, 97)

    def test_all_plain_fallback_is_exact(self):
        raw = random.Random(491).randbytes(2048)
        self.check_roundtrip(raw)
        archive, report = codec.encode(raw)
        self.assertEqual(parent(raw), archive)
        self.assertTrue(all(f["selected_rules"] == 0 for f in report["frames"]))

    def test_shared_argument_program(self):
        program = codec.Program(((1, (b"<title>", codec.Arg(0), b"</title><text>", codec.Arg(0), b"</text>")),),
                                (codec.Call(0, (b"Oakford",)), codec.Call(0, (b"Pinewell",))))
        raw = b"<title>Oakford</title><text>Oakford</text><title>Pinewell</title><text>Pinewell</text>"
        payload, costs = codec.pack(program)
        self.assertEqual(sum(costs.values()), len(payload))
        recovered, stats = codec.execute(codec.unpack(payload), len(raw))
        self.assertEqual(raw, recovered)
        self.assertEqual(stats["repeated_argument_references"], 2)
        frame, report = codec.frame_from_program(raw, program)
        archive = codec.HEADER.pack(codec.MAGIC, 65536, 1, len(raw)) + frame
        self.assertEqual(codec.decode(archive)[0], raw)

    def test_backward_template_and_empty_argument(self):
        program = codec.Program(((1, (b"[", codec.Arg(0), b"]")),
                                 (1, (codec.Call(0, (codec.Arg(0),)), b"=", codec.Arg(0)))),
                                (codec.Call(1, (b"",)), codec.Call(1, (b"abc",))))
        data, _ = codec.pack(program)
        inverse, stats = codec.execute(codec.unpack(data), len(b"[]=[abc]=abc"))
        self.assertEqual(inverse, b"[]=[abc]=abc")
        self.assertEqual(stats["calls"], 4)

    def test_reject_forward_unused_and_unconsumed_definitions(self):
        bad = [codec.Program(((0, (codec.Call(0, ()),)),), (codec.Call(0, ()),)),
               codec.Program(((1, (b"literal",)),), (codec.Call(0, (b"extra",)),)),
               codec.Program(((0, (b"unused",)),), (b"x",))]
        for program in bad:
            with self.subTest(program=program), self.assertRaises(codec.CodecError):
                payload, _ = codec.pack(program)
                codec.execute(codec.unpack(payload), 1)

    def test_selected_spans_cannot_overlap(self):
        with self.assertRaises(codec.CodecError):
            codec.build_program(b"abcd", (), [(0, 3, codec.Call(0, ())), (2, 4, codec.Call(0, ()))])

    def test_measured_admission_and_repeated_discovery(self):
        raw = fixture()
        with patch.object(codec, "discover", wraps=codec.discover) as discovery:
            archive, report = codec.encode(raw)
            repeat, repeat_report = codec.encode(raw)
            self.assertEqual(discovery.call_count, 2)
        self.assertEqual(archive, repeat)
        self.assertEqual(report, repeat_report)
        self.assertEqual(codec.decode(archive)[0], raw)
        self.assertLess(len(archive), len(parent(raw)))
        self.assertGreater(sum(f["repeated_argument_references"] for f in report["frames"]), 0)
        for frame in report["frames"]:
            accepted = [e for e in frame["search"]["evaluations"] if e["accepted"]]
            self.assertEqual(len(accepted), frame["selected_rules"])
            for decision in accepted:
                self.assertGreater(decision["delta"], 0)
                self.assertEqual(decision["delta"], decision["before"] - decision["candidate"])
            if accepted:
                self.assertEqual(accepted[-1]["candidate"], frame["complete_frame_bytes"])
        self.check_roundtrip(raw)

    def test_truncation_corruption_and_output_limits(self):
        archive, _ = codec.encode(b"raw exact\xff\n" * 5)
        for position in (0, 7, 23, len(archive) - 1):
            with self.subTest(position=position), self.assertRaises(codec.CodecError):
                codec.decode(archive[:position])
        for malformed in (archive + b"extra", archive[:-1] + bytes([archive[-1] ^ 1])):
            with self.assertRaises((codec.CodecError, codec.zlib.error)):
                codec.decode(malformed)
        with self.assertRaises(codec.CodecError):
            codec.decode(archive, max_output=4)


if __name__ == "__main__":
    unittest.main()
