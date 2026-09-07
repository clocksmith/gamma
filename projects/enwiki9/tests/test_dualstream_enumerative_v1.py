from collections import Counter
from itertools import permutations
import random
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import dualstream_enumerative_v1 as e
from tools import dualstream_grammar_v1 as old
from tools import dualstream_grammar_argtokens_v2 as new


class EnumerativeTests(unittest.TestCase):
    def test_rank_matches_exhaustive_lexicographic_order(self):
        for sample in (b"", b"a", b"aaab", b"aabc", b"abbccd"):
            strings = sorted(set(permutations(sample)))
            counts = [sample.count(s) for s in range(256)]
            self.assertEqual(e.ways(counts), len(strings))
            for index, string in enumerate(strings):
                packed = index.to_bytes(e.width(len(strings)), "big")
                self.assertEqual(e.rank_bytes(bytes(string)), packed)
                self.assertEqual(e.unrank(counts, packed), bytes(string))

    def test_exact_width_boundaries(self):
        for value, expected in ((1, 0), (2, 1), (255, 1), (256, 1), (257, 2), (65536, 2)):
            self.assertEqual(e.width(value), expected)
        self.assertEqual(e.rank_bytes(b"b" + b"a" * 255), b"\xff")

    def test_sections_arbitrary_bytes_and_chunks(self):
        rng = random.Random(3007)
        for sample in (b"", b"a" * 4097, bytes(range(256)) * 17, rng.randbytes(8193)):
            packed, costs = e.encode_section(sample)
            self.assertEqual(e.decode_section(packed), sample)
            self.assertEqual(packed, e.encode_section(sample)[0])
            self.assertEqual(len(packed), sum(costs[k] for k in ("rank_bytes", "count_table_bytes", "stream_header_bytes")))

    def test_invalid_counts_and_ranks(self):
        counts = [0] * 256
        counts[0], counts[1] = 2, 1
        for rank in (b"\x03", b"", b"\x00\x00"):
            with self.assertRaises(ValueError):
                e.unrank(counts, rank)
        counts[0] = 4097
        with self.assertRaises(ValueError):
            e.ways(counts)

    def test_bad_tables(self):
        for packed in (b"\x02\x02a\x01a\x01", b"\x02\x02b\x01a\x01",
                       b"\x01\x01a\x00", b"\x01\x01a\x02", b"\x81\x00", b"\x00\x00"):
            with self.assertRaises(ValueError):
                e.decode_section(packed)

    def test_truncated_sections(self):
        packed, _ = e.encode_section(b"abcabc")
        for end in range(len(packed)):
            with self.assertRaises(ValueError):
                e.decode_section(packed[:end])

    def test_modes_versions_and_identity(self):
        raw = b"<page><title>Oak</title><text>Oak is a town.</text></page>\n" * 4 + b"\xff\x00\r\nbad<"
        for codec in (old, new):
            for mode in old.MODES:
                selected = codec.encode(raw, mode=mode, config=codec.Config(grammar_budget=4))[0]
                for storage in ("old", "new"):
                    archive, result = e.encode(selected, storage)
                    restored, decoded = e.decode(archive)
                    self.assertEqual(restored, raw)
                    self.assertEqual(result["section_hashes"], decoded["section_hashes"])
                    self.assertEqual(sum(result["costs"].values()), len(archive))
                    self.assertEqual(e.encode(selected, storage)[0], archive)
                    self.assertFalse(result["raw_encoder_repeat_proved"])

    def test_shared_arguments_manual_graph(self):
        model = old.Model(structure=(("call", 0),), arguments=(b"Oak\x00\xff",),
                          phrases=((b" is", b" a town."),),
                          templates=((1, (b"<title>", old.Arg(0), b"</title>", old.Arg(0), old.Ref(0))),))
        raw = b"<title>Oak\x00\xff</title>Oak\x00\xff is a town."
        selected = old.HEADER.pack(old.MAGIC, old.MAX_FRAME, 1, len(raw)) + old.frame_bytes(raw, "parameter", model)[0]
        for storage in ("old", "new"):
            archive, report = e.encode(selected, storage)
            self.assertEqual(e.decode(archive)[0], raw)
            self.assertEqual(report["frames"][0]["repeated_argument_references"], 1)

    def test_empty_frames_corruption_and_output_bounds(self):
        for raw in (b"", b"abcd\xff" * 30):
            selected = old.encode(raw, mode="plain", frame_size=37)[0]
            archive, _ = e.encode(selected)
            self.assertEqual(e.decode(archive)[0], raw)
            for bad in (archive[:-1], archive + b"x", b"x" + archive[1:]):
                with self.assertRaises(ValueError):
                    e.decode(bad)
            if raw:
                with self.assertRaises(ValueError):
                    e.decode(archive, len(raw) - 1)
                broken = bytearray(archive)
                broken[e.HEADER.size + old.FRAME.size - 1] ^= 1
                with self.assertRaises(ValueError):
                    e.decode(bytes(broken))

    def test_base_import_not_mutated(self):
        sample = b"unchanged zlib boundary"
        self.assertEqual(old.inflate(old.zlib.compress(sample)), sample)


if __name__ == "__main__":
    unittest.main()
