"""Exact synthetic tests for the separately identified argument representation."""
import hashlib
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import dualstream_grammar_v1 as legacy
from tools import dualstream_grammar_argtokens_v2 as codec


class ArgumentTokenTests(unittest.TestCase):
    def test_exact_arbitrary_bytes_and_deterministic_ablations(self):
        rng = random.Random(731)
        populations = [b"", bytes(range(256)), rng.randbytes(1024),
                       b"<bad &amp;\xff>New  York\r\nNEW YORK\n" * 3]
        for raw in populations:
            for mode in codec.MODES:
                with self.subTest(size=len(raw), mode=mode):
                    archive, report = codec.encode(raw, mode=mode, config=codec.Config(4, 4, 1, 4))
                    self.assertEqual(codec.decode(archive), raw)
                    repeated, again = codec.encode(raw, mode=mode, config=codec.Config(4, 4, 1, 4))
                    self.assertEqual((archive, report), (repeated, again))
                    self.assertEqual(report["complete_archive_bytes"], len(archive))

    def model(self):
        first = b"New  York &amp; \xff"
        second = b"New York &amp; \xff"
        model = codec.Model(structure=(("call", 0), ("call", 0)), arguments=(first, second),
                            templates=((1, (b"<title>", codec.Arg(0), b"</title><text>", codec.Arg(0), b"</text>\r\n")),))
        raw = b"".join(b"<title>" + value + b"</title><text>" + value + b"</text>\r\n" for value in (first, second))
        return model, raw

    def test_shared_bindings_reconstruct_and_whole_arguments_are_not_pool_literals(self):
        model, raw = self.model()
        sections = codec.pack_arguments(model)
        self.assertEqual(codec.interpret_arguments(sections, len(raw)), raw)
        reader = codec.Reader(codec.inflate(sections[0]))
        pool = [reader.take(reader.number()) for _ in range(reader.number())]
        reader.end()
        self.assertNotIn(model.arguments[0], pool)
        self.assertNotIn(model.arguments[1], pool)
        self.assertIn(b"New", pool)
        self.assertIn(b"  ", pool)

    def test_no_argument_sections_and_plain_payload_remain_identical(self):
        raw = b"alpha beta alpha gamma\n" * 4
        # Representation adaptation cannot change sections without arguments.
        model = codec.model_for(codec.records(raw))
        self.assertEqual(codec.pack_arguments(model), codec.original_pack(model))
        old, _ = legacy.encode(raw, mode="plain")
        new, _ = codec.encode(raw, mode="plain")
        self.assertEqual(old[8:], new[8:])
        self.assertEqual(legacy.MAGIC, b"D2GRAM01")
        self.assertEqual(codec.MAGIC, b"D2GRAM02")
        with self.assertRaises(legacy.CodecError):
            legacy.decode(new)
        with self.assertRaises(codec.CodecError):
            codec.decode(old)

    def test_invalid_reference_trailing_argument_and_expansion_limit_rejected(self):
        model, raw = self.model()
        sections = codec.pack_arguments(model)
        for invalid in (b"\x01\x01\x01", b"\x01\x01" + codec.uint(999999),
                        codec.inflate(sections[4]) + b"\x00"):
            changed = list(sections)
            changed[4] = codec.zlib.compress(invalid, 9)
            with self.assertRaises(codec.CodecError):
                codec.interpret_arguments(changed, len(raw))
        with self.assertRaises(codec.CodecError):
            codec.interpret_arguments(sections, 1)

    def test_truncation_checksum_and_output_bounds(self):
        raw = b"<page><title>A</title><text>A town</text></page>\n" * 4
        archive, _ = codec.encode(raw, mode="parameter", frame_size=80)
        self.assertEqual(codec.decode(archive), raw)
        for bad in (archive[:-1], archive + b"x", archive[:50] + bytes([archive[50] ^ 1]) + archive[51:]):
            with self.assertRaises(codec.CodecError):
                codec.decode(bad)
        with self.assertRaises(codec.CodecError):
            codec.decode(archive, max_output=len(raw) - 1)


if __name__ == "__main__":
    unittest.main()
