"""Synthetic safety and wire conformance; no corpus or native FX2 execution."""
import contextlib
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib


SOURCE = Path(__file__).resolve().parents[1] / "tools/wiki_schema_exact_codec_v1.py"
SPEC = importlib.util.spec_from_file_location("wiki_schema_exact_codec_v1", SOURCE)
codec = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = codec
SPEC.loader.exec_module(codec)


def word(value):
    return struct.pack("<I", value)


def counted(value):
    return word(len(value)) + value


def independent_archive(blocks, programs, *, block_size=64, arm="D"):
    """Independent wire writer, deliberately permits non-minimal grammar bodies."""
    raw = b"".join(blocks)
    header = struct.pack("<8sB3xIIIIQI32s", b"WGSC0001", "PLDC".index(arm),
                         block_size, 4096, 256, 1048576, len(raw), len(blocks),
                         hashlib.sha256(raw).digest())
    bitmap = bytearray((len(blocks)+7)//8)
    result = []
    for i, (block, program) in enumerate(zip(blocks, programs)):
        if program is not None:
            bitmap[i//8] |= 1 << (i%8)
        body = zlib.compress(block if program is None else program, 9)
        result.append(struct.pack("<II32s", len(block), len(body), hashlib.sha256(block).digest()) + body)
    return header + bytes(bitmap) + b"".join(result)


class SchemaCodecTests(unittest.TestCase):
    def assert_roundtrip(self, raw, **options):
        all_receipts = {}
        for arm in "PLDC":
            archive, encoded = codec.encode(raw, arm=arm, **options)
            again, second = codec.encode(raw, arm=arm, **options)
            restored, decoded = codec.decode_archive(archive)
            self.assertEqual(raw, restored)
            self.assertEqual(archive, again)
            self.assertEqual(encoded, second)
            self.assertEqual([x["dictionary_after"] for x in encoded["blocks"]],
                             [x["dictionary_after"] for x in decoded["blocks"]])
            self.assertEqual([x["dictionary_before"] for x in encoded["blocks"]],
                             [x["dictionary_before"] for x in decoded["blocks"]])
            all_receipts[arm] = encoded
            a = encoded["accounting"]
            self.assertEqual(8*len(archive), a["archive_bits"])
            self.assertEqual(a["mode_bits"], len(encoded["blocks"]))
            if arm != "P":
                self.assertTrue(a["bound_pass"])
                self.assertEqual(a["archive_bits"], a["sum_min_Bj_Gj_plus_N_plus_H_bits"])
        reference = all_receipts["P"]
        for arm, receipt in all_receipts.items():
            self.assertEqual([r["dictionary_after"] for r in reference["blocks"]],
                             [r["dictionary_after"] for r in receipt["blocks"]])
            self.assertEqual(reference["archive_bytes"], receipt["accounting"]["equivalent_framed_baseline_bytes"])
            self.assertLessEqual(receipt["archive_bytes"], reference["archive_bytes"])
        return all_receipts

    def test_empty_binary_malformed_xml_and_whitespace(self):
        fixtures = [b"", b"\0\xff\xfe\r\n\t&bogus;", b"unterminated",
            b" <row a = 'one' b=\"two\">A &amp; B</row> \r\n",
            b"<row a='unterminated>text</row>\n<row>mismatch</other>\n",
            b"<!DOCTYPE x [<!ENTITY x 'expansion'>]><x>&x;</x>\n",
            b"<parent><child>nested</child></parent>\n<?xml nope?>\n",
            b"{{Thing | name = A  | city=Rome}}\r\n{{bad|key=a|key=b}}\n",
            b"{{Thing|name=[[A|B]]|x={{other}}}}\n",
            "<x a='é'>λ\t&amp;\r\n</x>\n".encode()]
        for raw in fixtures:
            with self.subTest(raw=raw):
                self.assert_roundtrip(raw, block_size=64)
        for raw in fixtures[4:7]:
            self.assertIsNone(codec.parse_record(raw))

    def test_exact_scaffolds_and_holes_without_normalization(self):
        cases = [b"  <row x = 'A&amp;B' y=\" c \" >Text&#13;</row>\r\n",
                 b"\t<row x='>' /> \n", b"{{Infobox | name =  A | city= Paris }}\n"]
        for raw in cases:
            parsed = codec.parse_record(raw)
            self.assertIsNotNone(parsed)
            rule, args = parsed
            self.assertEqual(rule.expand(args, 4096), raw)
        self.assertIsNone(codec.parse_record(b"<row>unclosed\n"))

    def test_past_only_learning_cross_block_and_oversized_discard(self):
        dictionary = codec.Dictionary(128, 8, 4096)
        dictionary.update(b"<row a='first'>")
        self.assertFalse(dictionary.rules)
        dictionary.update(b"value</row>\n")
        self.assertEqual(len(dictionary.rules), 1)
        known = dictionary.digest()
        target = b"<row a='second'>value</row>\n"
        program, stats = codec.grammar(target, dictionary, "D")
        self.assertEqual(dictionary.digest(), known)
        self.assertEqual(codec.decode_grammar(program, dictionary, len(target)), target)
        dictionary.update(b"x" * 129)
        self.assertTrue(dictionary.discard)
        self.assertEqual(dictionary.pending, b"")
        dictionary.update(b"<new>never learn a suffix</new>\n<valid>yes</valid>\n")
        self.assertFalse(dictionary.discard)
        self.assertEqual({r.kind for r in dictionary.rules.values()}, {b"xml:row", b"xml:valid"})
        self.assert_roundtrip((b"<row a='long'>" + b"x"*64 + b"</row>\n")*12,
                              block_size=64, max_record=128)

    def test_dictionary_eviction_and_hard_limits(self):
        raw = b"".join(b"<r%d a='v'>text</r%d>\n" % (i, i) for i in range(20))
        receipts = self.assert_roundtrip(raw*3, block_size=64, max_rules=2, max_dictionary_bytes=256)
        self.assertGreater(receipts["D"]["blocks"][-1]["dictionary_evictions"], 0)
        for row in receipts["D"]["blocks"]:
            self.assertLessEqual(row["dictionary_rules"], 2)
            self.assertLessEqual(row["dictionary_serialized_bytes"], 256)
        for options in [{"block_size": 0}, {"max_record": 1}, {"max_rules": 0},
                        {"max_dictionary_bytes": 0}, {"arm": ""}, {"arm": None}]:
            with self.assertRaises(codec.CodecError):
                codec.encode(b"x", **options)

    def test_selected_grammar_blocks_reuse_paid_definitions(self):
        rng = random.Random(1776)
        attribute = bytes(rng.choice(b"abcdefghijklmnopqrstuvwxyz") for _ in range(180))
        blocks = []
        for i in range(12):
            line = b"<row " + attribute + b"='v%04d'>t%04d</row>" % (i, i)
            blocks.append(line + b" " * (511-len(line)) + b"\n")
        receipts = self.assert_roundtrip(b"".join(blocks), block_size=512)
        treatment = receipts["D"]["blocks"]
        self.assertEqual(treatment[0]["mode"], 0)
        self.assertEqual(treatment[0]["grammar_proposal"]["eligible_records"], 0)
        self.assertTrue(any(row["mode"] == 1 and row["grammar_proposal"]["references"]
                            for row in treatment[1:]))
        self.assertLess(receipts["D"]["archive_bytes"], receipts["P"]["archive_bytes"])

    def test_schema_association_control_and_exceptions(self):
        field = b"descriptive_attribute_" * 8
        first = b"<row " + field + b"='x'>text</row>\n"
        other = b"<row " + field + b" = \"x\">text</row>\n"
        dictionary = codec.Dictionary(4096, 8, 4096)
        dictionary.update(first + other)
        target = first.replace(b"'x'", b"'new'")
        d, ds = codec.grammar(target, dictionary, "D")
        c, cs = codec.grammar(target, dictionary, "C")
        l, ls = codec.grammar(target, dictionary, "L")
        self.assertEqual(ds["references"], 1)
        self.assertEqual(cs["shuffled_queries"], 1)
        self.assertGreater(cs["exceptions"], 0)
        self.assertNotEqual(d, c)
        self.assertEqual(ls["references"], 0)
        for program in (d, c, l):
            self.assertEqual(codec.decode_grammar(program, dictionary, len(target)), target)
        raw = (first+other)*4 + (target*8)
        self.assert_roundtrip(raw, block_size=512)

    def test_exact_insert_delete_substitute_and_invalid_edits(self):
        for base, target in [(b"abcdef", b"abXYef"), (b"abef", b"abCDef"),
                             (b"abCDef", b"abef"), (b"abcdef", b"abcdef"),
                             (b"", b"x"), (b"x", b"")]:
            self.assertEqual(codec.apply_exceptions(base, codec.exception_script(base, target), 128), target)
        self.assertEqual(codec.apply_exceptions(b"abcdef", ((1, 1, b"X"), (4, 1, b"YZ")), 128), b"aXcdYZf")
        for edits in [((7, 0, b"x"),), ((0, 7, b""),), ((1, 0, b""),),
                      ((3, 2, b"x"), (4, 0, b"y"))]:
            with self.assertRaises(codec.CodecError):
                codec.apply_exceptions(b"abcdef", edits, 128)

    def test_independent_wire_reference_and_missing_definition(self):
        original = b"<row a='x'>A</row>\n"
        first = original + b" " * (64-len(original)-1) + b"\n"
        target = b"<row a='y'>B</row>\n"
        program = (b"GSC1" + word(1) + b"\1" + struct.pack("<Q", 1) + word(2)
                   + counted(b"y") + counted(b"B") + word(0))
        archive = independent_archive([first, target], [None, program])
        self.assertEqual(codec.decode(archive), first+target)
        bad_id = program[:9] + struct.pack("<Q", 999) + program[17:]
        with self.assertRaisesRegex(codec.CodecError, "schema identifier"):
            codec.decode(independent_archive([first, target], [None, bad_id]))
        # The current record is not available as its own definition.
        with self.assertRaisesRegex(codec.CodecError, "schema identifier"):
            codec.decode(independent_archive([target], [program]))

    def test_malformed_grammar_operands(self):
        dictionary = codec.Dictionary(4096, 8, 4096)
        dictionary.update(b"<x>A</x>\n")
        prefix = b"GSC1" + word(1)
        malformed = [b"BAD!"+word(1)+b"\0"+counted(b"x"), b"GSC1"+word(0),
            prefix+b"\2", prefix+b"\0"+word(99)+b"x", prefix+b"\0"+word(0),
            prefix+b"\0"+counted(b"x")+b"trailing",
            prefix+b"\1"+struct.pack("<Q", 1)+word(17),
            prefix+b"\1"+struct.pack("<Q", 1)+word(1)+counted(b"B")+word(4097),
            prefix+b"\1"+struct.pack("<Q", 1)+word(1)+counted(b"B")+word(1)+word(999)+word(0)+counted(b"X")]
        for program in malformed:
            with self.subTest(program=program), self.assertRaises(codec.CodecError):
                codec.decode_grammar(program, dictionary, 1)

    def test_truncation_trailing_corruption_padding_and_expansion(self):
        archive, _ = codec.encode(b"<row>x</row>\n"*8, block_size=64)
        for end in range(len(archive)):
            with self.subTest(end=end), self.assertRaises(codec.CodecError):
                codec.decode(archive[:end])
        damaged = [archive+b"extra", b"badmagic"+archive[8:]]
        reserved = bytearray(archive); reserved[9] = 1; damaged.append(bytes(reserved))
        padding = bytearray(archive); padding[codec.HEADER.size] |= 128; damaged.append(bytes(padding))
        corruption = bytearray(archive); corruption[-1] ^= 1; damaged.append(bytes(corruption))
        for value in damaged:
            with self.assertRaises(codec.CodecError):
                codec.decode(value)
        body = zlib.compress(b"x"*4096)
        with self.assertRaisesRegex(codec.CodecError, "exceeds limit"):
            codec.inflate(body, 64)
        for body in (zlib.compress(b"x")+b"junk", zlib.compress(b"x")[:-1],
                     zlib.compress(b"x")+zlib.compress(b"y")):
            with self.assertRaises(codec.CodecError):
                codec.inflate(body, 64)

    def test_seeded_mixed_byte_records(self):
        rng = random.Random(49021)
        records = []
        for i in range(120):
            value = bytes(rng.randrange(256) for _ in range(rng.randrange(32)))
            records.extend([b"<row id='%d'>value_%d</row>\r\n" % (i, i % 9),
                            b"{{Infobox|name=value_%d|city=city_%d}}\n" % (i, i % 7),
                            value+b"\n"])
        self.assert_roundtrip(b"".join(records), block_size=256, max_rules=8)

    def test_cli_exclusive_publication_and_no_output_on_bad_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, archive, restored, receipt = (root / name for name in ("raw", "archive", "restored", "receipt"))
            source.write_bytes(b"<x>A</x>\n" * 32)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(codec.main(["encode", str(source), str(archive), "--receipt", str(receipt)]), 0)
                original = archive.read_bytes()
                self.assertEqual(codec.main(["encode", str(source), str(archive)]), 1)
                self.assertEqual(archive.read_bytes(), original)
                self.assertEqual(codec.main(["decode", str(archive), str(restored)]), 0)
                self.assertEqual(restored.read_bytes(), source.read_bytes())
                bad, absent = root / "bad", root / "absent"
                bad.write_bytes(original[:-1])
                self.assertEqual(codec.main(["decode", str(bad), str(absent)]), 1)
                self.assertFalse(absent.exists())
                alias, victim = root / "alias", root / "victim"
                victim.write_bytes(b"preserve")
                alias.symlink_to(victim)
                self.assertEqual(codec.main(["decode", str(archive), str(alias)]), 1)
                self.assertEqual(victim.read_bytes(), b"preserve")
            self.assertFalse(any(p.name.startswith(".") for p in root.iterdir()))

    def test_cli_rejects_fifo_device_directory_and_input_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fifo, source, alias = (root / name for name in ("fifo", "raw", "alias"))
            os.mkfifo(fifo)
            source.write_bytes(b"<x>A</x>\n")
            alias.symlink_to(source)
            # The FIFO deliberately has no writer. A bounded subprocess makes
            # this a failing regression, rather than a hung suite, if reopened
            # with a blocking read. Neither command may publish an output.
            for command in ("encode", "decode"):
                for index, input_path in enumerate((fifo, Path("/dev/null"), root, alias)):
                    output = root / (command + str(index))
                    with self.subTest(command=command, input=input_path):
                        result = subprocess.run(
                            [sys.executable, "-B", str(SOURCE), command, str(input_path), str(output)],
                            capture_output=True, timeout=5, check=False)
                        self.assertEqual(result.returncode, 1, result.stderr)
                        self.assertIn(b"input must be a regular file", result.stderr)
                        self.assertFalse(output.exists())
            self.assertEqual(source.read_bytes(), b"<x>A</x>\n")

    def test_regular_input_exact_limit_and_oversize(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "raw"
            path.write_bytes(b"four")
            self.assertEqual(codec.read_bounded(path, 4), b"four")
            with self.assertRaisesRegex(codec.CodecError, "exceeds bounded gate"):
                codec.read_bounded(path, 3)


if __name__ == "__main__":
    unittest.main()
