"""Independent byte inverse and finite literal-first admission checks."""
import hashlib
from pathlib import Path
import random
import sys
import unittest
from unittest.mock import patch
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import dualstream_literal_first_v1 as codec
from tools import dualstream_grammar_argtokens_v2 as published_parent


def archive_for_payload(payload, raw, level=9):
    compressed = zlib.compress(payload, level)
    return (codec.HEADER.pack(codec.MAGIC, codec.MAX_FRAME, 1, len(raw)) +
            codec.FRAME.pack(len(raw), 4, 0, 0, 0, len(compressed), 0, hashlib.sha256(raw).digest()) + compressed)


class IndependentLiteralFirstTests(unittest.TestCase):
    def test_nested_forwarding_empty_and_arbitrary_arguments(self):
        Arg, Call, Program = codec.Arg, codec.Call, codec.Program
        program = Program(((2, (b"<", Arg(0), b"|", Arg(1), b">")),
                           (1, (Call(0, (Arg(0), Arg(0))), b"/", Arg(0))),
                           (1, (b"[", Call(1, (Arg(0),)), b"]"))),
                          (Call(2, (b"",)), b"\xff\r\n", Call(2, (b"A\0\xff",))))
        expected = b"[<|>/]\xff\r\n[<A\0\xff|A\0\xff>/A\0\xff]"
        payload, costs = codec.pack(program)
        parsed = codec.unpack(payload)
        self.assertEqual(parsed, program)
        self.assertEqual(sum(costs.values()), len(payload))
        output, report = codec.execute(parsed, len(expected))
        self.assertEqual(output, expected)
        self.assertEqual(report["calls"], 6)
        self.assertEqual(report["repeated_argument_references"], 4)
        archive = archive_for_payload(payload, expected)
        self.assertEqual(codec.decode(archive)[0], expected)
        self.assertEqual(codec.decode(archive)[1]["frames"][0]["boundary_sha256"], report["boundary_sha256"])

    def test_malformed_rules_calls_and_argument_use_rejected(self):
        Arg, Call, Program = codec.Arg, codec.Call, codec.Program
        bad = [Program(((0, (Call(0, ()),)),), (Call(0, ()),)),
               Program(((0, (Call(1, ()),)), (0, (Call(0, ()),))), (Call(1, ()),)),
               Program(((2, (Arg(0),)),), (Call(0, (b"x", b"y")),)),
               Program(((1, (Arg(1),)),), (Call(0, (b"x",)),)),
               Program(((1, (Arg(0),)),), (Call(0, ()),)),
               Program(((0, (b"unused",)),), (b"x",)),
               Program(((0, (b"a", b"b")),), (Call(0, ()),))]
        for program in bad:
            with self.subTest(program=program), self.assertRaises(codec.CodecError):
                payload, _ = codec.pack(program)
                codec.decode(archive_for_payload(payload, b"x"))
        for payload in (b"\0\1\1\0", b"\0\1\0\0", b"\x80\0\0", b"\0\0\0"):
            with self.subTest(payload=payload), self.assertRaises(codec.CodecError):
                codec.unpack(payload)

    def test_nested_empty_expansion_has_a_finite_work_bound(self):
        Arg, Call, Program = codec.Arg, codec.Call, codec.Program
        rules = [(1, (Arg(0),))]
        for i in range(1, 8):
            rules.append((1, (Call(i - 1, (Arg(0),)), Call(i - 1, (Arg(0),)))))
        program = Program(tuple(rules), (b"x", Call(7, (b"",))))
        payload, _ = codec.pack(program)
        checked = codec.unpack(payload)
        with patch.object(codec, "MAX_STEPS", 32), self.assertRaisesRegex(codec.CodecError, "work bound"):
            codec.execute(checked, 1)
        self.assertEqual(codec.execute(checked, 1)[0], b"x")

    def test_published_plain_parent_equals_bookkeeping_on_all_frames(self):
        rng = random.Random(8702)
        values = (b"", bytes(range(256)), rng.randbytes(1777), b"bad\xff<xml\0\r\n  &amp;\r" * 40)
        for raw in values:
            frame_size = 131
            parent = published_parent.encode(raw, mode="plain", frame_size=frame_size)[0]
            with patch.object(codec, "discover", wraps=codec.discover) as discovery:
                kept, report = codec.encode(raw, "K", frame_size)
                repeated, repeat_report = codec.encode(raw, "K", frame_size)
            self.assertEqual(kept[:8], b"D2GRAM02")
            self.assertEqual(kept, parent)
            self.assertEqual((kept, report), (repeated, repeat_report))
            self.assertEqual(discovery.call_count, 2 * ((len(raw) + frame_size - 1) // frame_size))
            self.assertEqual(codec.decode(kept)[0], raw)
            self.assertEqual(sum(report["costs"].values()), len(kept))

    def test_complete_cost_selects_best_reversible_proposal(self):
        rng = random.Random(52308)
        values = [rng.randbytes(48) for _ in range(16)]
        records = [(value + b"|") * 40 + b"\n" for value in values]
        raw = b"".join(records)
        spans, start = [], 0
        for record, value in zip(records, values):
            spans.append((start, start + len(record), (value,)))
            start += len(record)
        body = codec.coalesce(tuple(x for _ in range(40) for x in (codec.Arg(0), b"|")) + (b"\n",))
        useful = ((1, body), tuple(spans))
        identity = ((1, (codec.Arg(0),)), tuple((a, b, (raw[a:b],)) for a, b, _ in spans))
        proposals = [identity, useful]
        candidates = []
        for rule, uses in proposals:
            selected = [(a, b, codec.Call(0, args)) for a, b, args in uses]
            program = codec.build_program(raw, [rule], selected)
            candidates.append(codec.frame_from_program(raw, program)[0])
        parent = codec.plain_frame(raw)[0]
        self.assertLess(len(candidates[1]), len(parent))
        with patch.object(codec, "discover", return_value=(proposals, dict(spans=16, proposals=2))):
            encoded, report = codec.encode_frame(raw, "D")
            bookkeeping, _ = codec.encode_frame(raw, "K")
        self.assertEqual(encoded, min(candidates + [parent], key=len))
        self.assertEqual(bookkeeping, parent)
        accepted = [r for r in report["search"]["evaluations"] if r["accepted"]]
        self.assertEqual(len(accepted), 1)
        self.assertEqual(accepted[0]["proposal"], 1)
        self.assertEqual(accepted[0]["delta"], len(parent) - len(encoded))
        self.assertEqual(sum(report["costs"].values()), len(encoded))
        self.assertEqual(codec.decode(codec.HEADER.pack(codec.MAGIC, codec.MAX_FRAME, 1, len(raw)) + encoded)[0], raw)

    def test_unprofitable_proposal_falls_back_exactly(self):
        raw = b"x" * 2048
        rule = (1, (codec.Arg(0),))
        uses = ((0, 1024, (raw[:1024],)), (1024, 2048, (raw[1024:],)))
        with patch.object(codec, "discover", return_value=([(rule, uses)], dict(spans=2, proposals=1))):
            frame, report = codec.encode_frame(raw, "D")
        self.assertEqual(frame, codec.plain_frame(raw)[0])
        self.assertEqual(report["search"]["admitted"], 0)
        self.assertTrue(all(r["delta"] <= 0 and not r["accepted"] for r in report["search"]["evaluations"]))

    def test_archive_bounds_modes_checksums_and_noncanonical_deflate(self):
        program = codec.Program(((1, (b"<", codec.Arg(0), b">")),), (codec.Call(0, (b"x",)),))
        payload, _ = codec.pack(program)
        raw = b"<x>"
        archive = archive_for_payload(payload, raw)
        for cut in range(len(archive)):
            with self.subTest(cut=cut), self.assertRaises(codec.CodecError):
                codec.decode(archive[:cut])
        for invalid in (archive + b"x", archive_for_payload(payload, raw, level=1),
                        codec.PLAIN_MAGIC + archive[8:], archive_for_payload(payload, b"<y>")):
            with self.assertRaises(codec.CodecError):
                codec.decode(invalid)
        with self.assertRaises(codec.CodecError):
            codec.decode(archive, max_output=2)
        plain, _ = codec.encode(b"plain bytes", "K")
        with self.assertRaises(codec.CodecError):
            codec.decode(codec.MAGIC + plain[8:])
        with self.assertRaises(codec.CodecError):
            codec.encode(b"x" * (codec.MAX_RAW + 1))

    def test_lf_span_policy_and_capped_coverage_are_explicit(self):
        _, report = codec.discover(b"one\rtwo\rthree\nlast")
        self.assertEqual(report["total_spans"], 2)
        self.assertFalse(report["spans_truncated"])
        raw = b"".join(str(i).encode() + b"\n" for i in range(codec.SEARCH_SPEC["max_spans"] + 3))
        _, capped = codec.discover(raw)
        self.assertEqual(capped["total_spans"], codec.SEARCH_SPEC["max_spans"] + 3)
        self.assertEqual(capped["spans"], codec.SEARCH_SPEC["max_spans"])
        self.assertTrue(capped["spans_truncated"])
        self.assertGreaterEqual(capped["total_proposals"], capped["proposals"])


if __name__ == "__main__":
    unittest.main()
