"""Independent rank-order and malformed-input checks; no corpus population."""
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import dualstream_enumerative_v1 as enum
from tools import dualstream_grammar_reserialize_v1 as rep


def counts_for(data):
    frequency = Counter(data)
    return [frequency[i] for i in range(256)]


class IndependentEnumerativeTests(unittest.TestCase):
    def test_exhaustive_rank_matches_independent_lexicographic_order(self):
        # Enumerate strings independently; grouping yields the exact type class.
        for size in range(8):
            classes = defaultdict(list)
            for symbols in product((0, 1, 255), repeat=size):
                data = bytes(symbols)
                classes[tuple(data.count(c) for c in (0, 1, 255))].append(data)
            for sequences in classes.values():
                ordered = sorted(sequences)
                counts = counts_for(ordered[0])
                self.assertEqual(enum.ways(counts), len(ordered))
                for index, sequence in enumerate(ordered):
                    encoded = enum.rank_bytes(sequence)
                    self.assertEqual(int.from_bytes(encoded, "big"), index)
                    self.assertEqual(enum.unrank(counts, encoded), sequence)

    def test_exact_power_widths_and_actual_256_ordering_type(self):
        for possibilities, expected in ((1, 0), (2, 1), (255, 1), (256, 1),
                                        (257, 2), (65536, 2), (65537, 3)):
            self.assertEqual(enum.width(possibilities), expected)
        counts = [255, 1] + [0] * 254
        self.assertEqual(enum.ways(counts), 256)
        for location in range(256):
            data = bytes(location) + b"\1" + bytes(255 - location)
            encoded = enum.rank_bytes(data)
            self.assertEqual(len(encoded), 1)
            self.assertEqual(encoded[0], 255 - location)
            self.assertEqual(enum.unrank(counts, encoded), data)

    def test_chunk_edges_and_complete_section_cost(self):
        rng = random.Random(93581)
        populations = (b"", b"x" * enum.CHUNK, bytes(range(256)) * 17,
                       rng.randbytes(enum.CHUNK - 1), rng.randbytes(enum.CHUNK + 1))
        for data in populations:
            encoded, report = enum.encode_section(data)
            self.assertEqual(enum.decode_section(encoded), data)
            self.assertEqual(enum.encode_section(data), (encoded, report))
            self.assertEqual(len(encoded), report["rank_bytes"] + report["count_table_bytes"]
                             + report["stream_header_bytes"])

    def test_invalid_counts_rank_and_width_rejected(self):
        for counts in ([1], [True] + [0] * 255, [-1] + [0] * 255,
                       [enum.CHUNK + 1] + [0] * 255):
            with self.assertRaises(ValueError):
                enum.ways(counts)
        counts = [2, 1] + [0] * 254
        for encoded in (b"", b"\0\0", b"\3", b"\xff"):
            with self.assertRaises(ValueError):
                enum.unrank(counts, encoded)
        for encoded in (b"\0", b"\0\0"):
            with self.assertRaises(ValueError):
                enum.unrank([0] * 256, encoded)

    def test_malformed_count_tables_and_lengths_rejected(self):
        # Section size, alphabet length, ordered (symbol, count), then rank.
        malformed = (b"\1\0", b"\2\2\0\1\0\1\0",  # empty, duplicate
                     b"\2\2\1\1\0\1\0",             # unordered
                     b"\1\1\0\0", b"\2\1\0\1",  # zero, short total
                     b"\1\1\0\2", b"\x80\0",       # excess, noncanonical
                     b"\0\0", b"\3\2\0\2\1\1\3") # trailing, rank=M
        for encoded in malformed:
            with self.subTest(encoded=encoded.hex()), self.assertRaises(ValueError):
                enum.decode_section(encoded)
        valid, _ = enum.encode_section(b"\0\1\2")
        for cut in range(len(valid)):
            with self.assertRaises(ValueError):
                enum.decode_section(valid[:cut])

    def test_shared_binding_program_inverse_and_module_isolation(self):
        old = rep.old
        original_inflate = old.inflate
        model = old.Model(structure=(old.Ref(0),), content=(old.Ref(0),),
                          arguments=(b"name\0 \xff",), phrases=((b"a", b"b"),),
                          templates=((1, (old.Arg(0), b"/", old.Arg(0))),),
                          structure_rules=((("content", 2), ("call", 0)),))
        raw = b"abname\0 \xff/name\0 \xff"
        body, _ = old.frame_bytes(raw, "parameter", model)
        parent = old.HEADER.pack(old.MAGIC, old.MAX_FRAME, 1, len(raw)) + body
        for storage in ("old", "new"):
            encoded, report = enum.encode(parent, storage)
            decoded, inverse = enum.decode(encoded)
            self.assertEqual(decoded, raw)
            self.assertEqual(inverse["section_hashes"], report["section_hashes"])
            self.assertEqual(sum(report["costs"].values()), len(encoded))
            self.assertEqual(report["frames"][0]["model_sha256"], rep.fingerprint(model))
            self.assertEqual(report["frames"][0]["repeated_argument_references"], 1)
            self.assertEqual(enum.encode(parent, storage), (encoded, report))
        self.assertIs(old.inflate, original_inflate)
        self.assertEqual(old.decode(parent), raw)

    def test_archive_corruption_and_output_limit(self):
        parent, _ = rep.old.encode(b"exact\0\xff\n", mode="split")
        encoded, _ = enum.encode(parent)
        for bad in (encoded[:-1], encoded + b"x", b"invalid!" + encoded[8:]):
            with self.assertRaises(ValueError):
                enum.decode(bad)
        with self.assertRaises(ValueError):
            enum.decode(encoded, max_output=1)
        changed_hash = bytearray(encoded)
        changed_hash[enum.HEADER.size + enum.core.FRAME.size - 1] ^= 1
        with self.assertRaisesRegex(ValueError, "hash"):
            enum.decode(bytes(changed_hash))
        fields = list(enum.HEADER.unpack(encoded[:enum.HEADER.size]))
        fields[2] += 1
        with self.assertRaises(ValueError):
            enum.decode(enum.HEADER.pack(*fields) + encoded[enum.HEADER.size:])


if __name__ == "__main__":
    unittest.main()
