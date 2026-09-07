"""Exact selected-graph and event-interpreter fixtures; no corpus search."""
import unittest
import json
import resource
import time

from tools import dualstream_grammar_v1 as old
from tools import dualstream_event_codec_v1 as codec
from tools import dualstream_grammar_reserialize_v1 as rep


def selected(raw, model):
    frame, _ = old.frame_bytes(raw, "parameter", model)
    return old.HEADER.pack(old.MAGIC, old.MAX_FRAME, 1, len(raw)) + frame


class EventCodecTests(unittest.TestCase):
    def assert_model(self, raw, model):
        source = selected(raw, model)
        self.assertEqual(old.decode(source), raw)
        encoded = {}
        for mode in ("G", "X"):
            archive, report = codec.encode(source, mode)
            inverse, inverse_report = codec.decode(archive)
            self.assertEqual(inverse, raw)
            self.assertEqual(report, inverse_report)
            self.assertEqual(codec.encode(source, mode), (archive, report))
            self.assertEqual(report["frames"][0]["model_sha256"], rep.fingerprint(model))
            self.assertEqual(sum(report["costs"].values()), len(archive))
            encoded[mode] = report
        self.assertEqual(encoded["G"]["frames"][0]["stored_nodes"], encoded["X"]["frames"][0]["stored_nodes"])
        self.assertEqual(encoded["G"]["frames"][0]["interpreter_sha256"], encoded["X"]["frames"][0]["interpreter_sha256"])
        return encoded

    def test_shared_nonmonotonic_and_empty_arguments(self):
        model = old.Model(structure=(("call", 0), ("call", 0)), arguments=(b"", b"Oak", b"!", b"Pine"),
            templates=((2, (b"<x>", old.Arg(1), old.Arg(0), b"|", old.Arg(1), b"</x>")),))
        report = self.assert_model(b"<x>Oak|Oak</x><x>Pine!|Pine</x>", model)
        self.assertEqual(report["G"]["frames"][0]["repeated_argument_references"], 2)

    def test_phrase_crosses_content_spans(self):
        model = old.Model(structure=(("content", 1), ("literal", b"<gap>"), ("content", 2)),
                          content=(old.Ref(1),), phrases=((b"A", b"B"), (old.Ref(0), b"C")))
        self.assert_model(b"A<gap>BC", model)

    def test_backward_structure_and_phrase_rules(self):
        model = old.Model(structure=(old.Ref(1),), content=(old.Ref(0), old.Ref(0)),
            phrases=((b"x", b"y"),), structure_rules=((("literal", b"<a>"), ("content", 2)),
                                                     (old.Ref(0), old.Ref(0))))
        self.assert_model(b"<a>xy<a>xy", model)

    def test_raw_arbitrary_and_partial_frames(self):
        raw = bytes(range(256)) + b"\xff\x00\r\n<bad & broken"
        archive, report = codec.encode(raw, "R", 97)
        inverse, inverse_report = codec.decode(archive)
        self.assertEqual(inverse, raw)
        self.assertEqual(inverse_report, report)
        self.assertEqual(codec.encode(raw, "R", 97)[0], archive)
        self.assertEqual(report["frames"][-1]["raw_bytes"], len(raw) % 97)

    def test_empty(self):
        archive, report = codec.encode(b"", "R")
        self.assertEqual(codec.decode(archive), (b"", report))

    def test_truncation_corruption_and_trailing(self):
        archive, _ = codec.encode(b"arbitrary bytes", "R")
        for bad in (archive[:-1], archive + b"\0", archive[:25], archive[:5]):
            with self.assertRaises((ValueError, codec.struct.error)):
                codec.decode(bad)
        corrupt = bytearray(archive)
        corrupt[-1] ^= 1
        with self.assertRaises(ValueError):
            codec.decode(bytes(corrupt))

    def test_input_frontend_rejected(self):
        with self.assertRaises(ValueError):
            codec.encode(b"D2GRAM02" + b"\0" * 32, "G")

    def test_invalid_selected_graph(self):
        # Exercise encoder rejection independently of old archive validation.
        for model in (old.Model(structure=(old.Ref(0),), structure_rules=((old.Ref(0), ("literal", b"a")),)),
                      old.Model(structure=(("call", 0),), templates=((1, (b"a",)),))):
            with self.assertRaises((ValueError, IndexError)):
                codec.Interpreter(codec.EventChannel("G"), 1, model).run()

    def test_bounded_synthetic_kernel(self):
        raw = (b"<page><title>Oak 17</title><text>Oak 17 is a town.\r\n</text></page>\n" * 150)[:8192]
        args = tuple((b"name %04d, exact \xff bytes" % i) for i in range(64))
        model = old.Model(structure=tuple(("call", 0) for _ in args), arguments=args,
            templates=((1, (b"<title>", old.Arg(0), b"</title><text>", old.Arg(0), b"</text>\n")),))
        grammar_raw = b"".join(b"<title>" + a + b"</title><text>" + a + b"</text>\n" for a in args)
        source = selected(grammar_raw, model)
        for mode, data, expected in (("R", raw, raw), ("G", source, grammar_raw), ("X", source, grammar_raw)):
            cpu, wall = time.process_time(), time.monotonic()
            archive, report = codec.encode(data, mode)
            encode_cpu, encode_wall = time.process_time() - cpu, time.monotonic() - wall
            cpu, wall = time.process_time(), time.monotonic()
            inverse, decoded = codec.decode(archive)
            decode_cpu, decode_wall = time.process_time() - cpu, time.monotonic() - wall
            self.assertEqual((inverse, decoded), (expected, report))
            self.assertEqual(codec.encode(data, mode), (archive, report))
            print(json.dumps(dict(synthetic_kernel=mode, raw_bytes=len(expected), raw_sha256=rep.sha(expected),
                archive_bytes=len(archive), archive_sha256=rep.sha(archive), exact_inverse=True, repeat=True,
                encode_cpu_seconds=encode_cpu, decode_cpu_seconds=decode_cpu,
                encode_elapsed_seconds=encode_wall, decode_elapsed_seconds=decode_wall,
                peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                frame_synchronization=[r["synchronization"] for r in report["frames"]]), sort_keys=True))


if __name__ == "__main__":
    unittest.main()
