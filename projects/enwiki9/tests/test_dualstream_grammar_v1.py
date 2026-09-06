"""Exact bytes and hostile program fixtures; these are not enwik9 measurements."""
from dataclasses import replace
import hashlib
import io
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import dualstream_grammar_v1 as codec


class DualStreamGrammarTest(unittest.TestCase):
    def check_all(self, raw, **kwargs):
        for mode in (*codec.MODES, "auto"):
            with self.subTest(mode=mode, bytes=len(raw)):
                archive, report = codec.encode(raw, mode=mode, **kwargs)
                self.assertEqual(codec.decode(archive), raw)
                self.assertEqual(codec.encode(raw, mode=mode, **kwargs)[0], archive)
                self.assertEqual(report["complete_archive_bytes"], len(archive))
                self.assertEqual(sum(report[k] for k in ("literal_definition_bytes", "structure_bytes", "content_bytes",
                    "argument_reference_bytes", "exception_bytes", "framing_bytes")), len(archive))

    def test_empty_and_arbitrary_bytes(self):
        self.check_all(b"")
        self.check_all(bytes(range(256)) * 2, config=codec.Config(grammar_budget=3))
        raw = b"".join(hashlib.sha256(i.to_bytes(4, "little")).digest() for i in range(12))
        self.check_all(raw, config=codec.Config(grammar_budget=3))

    def test_no_normalization_of_markup_whitespace_or_unicode(self):
        raw = b'<x b="2" a="1">New York\r\nNEW YORK\nNew  York&amp;\xff\x00</x>\n<bad x="\'not closed\n'
        self.check_all(raw, config=codec.Config(grammar_budget=3))

    def test_exact_records_span_separate_bounded_frames(self):
        raw = (b'<page><title>Oakford</title><text>Oakford is a town.</text></page>\r\n' * 5) + b'final'
        self.check_all(raw, frame_size=71, config=codec.Config(grammar_budget=3))

    def test_repeated_argument_discovery_and_interpreter(self):
        raw = b''.join(b'<page><title>' + n + b'</title><text>' + n + b' is a town.</text></page>\n'
                       for n in (b'Oakford', b'Pinewell', b'Ashbury'))
        chunks = codec.records(raw)
        proposals = codec.template_proposals(chunks)
        self.assertTrue(proposals)
        template, uses = next((t, u) for t, u in proposals if t[0] == 1 and sum(isinstance(x, codec.Arg) for x in t[1]) == 2)
        self.assertEqual(len(uses), 3)
        self.assertEqual([args for _, args in uses], [(b'Oakford',), (b'Pinewell',), (b'Ashbury',)])
        model = codec.model_for(chunks, [(i, (0, args)) for i, args in uses], [template])
        sections = codec.packed_sections(model)
        self.assertEqual(codec.interpret(sections, len(raw)), raw)

    def test_backward_recursive_phrases_and_templates(self):
        model = codec.Model(structure=(("call", 0),), arguments=(b'X',),
                            phrases=((b'a', b'b'), (codec.Ref(0), b'c')),
                            templates=((1, (codec.Ref(1), codec.Arg(0), codec.Arg(0))),))
        self.assertEqual(codec.interpret(codec.packed_sections(model), 5), b'abcXX')

    def test_cyclic_and_forward_phrase_rules_are_rejected(self):
        for reference in (0, 1):
            model = codec.Model(structure=(("content", 2),), content=(codec.Ref(0),), phrases=((codec.Ref(reference), b'a'),))
            with self.assertRaisesRegex(codec.CodecError, 'forward or invalid phrase'):
                codec.interpret(codec.packed_sections(model), 2)

    def test_cyclic_structure_rules_are_rejected(self):
        model = codec.Model(structure=(codec.Ref(0),), structure_rules=((codec.Ref(0), ("literal", b'x')),))
        with self.assertRaisesRegex(codec.CodecError, 'forward or cyclic'):
            codec.interpret(codec.packed_sections(model), 2)

    def test_acyclic_empty_expansion_still_has_a_global_work_limit(self):
        rules = ((("literal", b''), ("literal", b'')),) + tuple((codec.Ref(i - 1), codec.Ref(i - 1)) for i in range(1, 20))
        model = codec.Model(structure=(codec.Ref(19),), structure_rules=rules)
        with self.assertRaisesRegex(codec.CodecError, 'work limit'):
            codec.interpret(codec.packed_sections(model), 1)

    def test_missing_extra_and_invalid_arguments_are_rejected(self):
        good = codec.Model(structure=(("call", 0),), arguments=(b'X',), templates=((1, (codec.Arg(0), codec.Arg(0))),))
        for changed in (replace(good, arguments=()), replace(good, arguments=(b'X', b'Y')),
                        replace(good, templates=((1, (codec.Arg(1),)),))):
            with self.assertRaises(codec.CodecError):
                codec.interpret(codec.packed_sections(changed), 2)

    def test_truncation_checksum_trailing_data_and_output_limits(self):
        archive, _ = codec.encode(b'not normalized\r\n', mode='split')
        for end in (0, 3, codec.HEADER.size, len(archive) - 1):
            with self.assertRaises(codec.CodecError):
                codec.decode(archive[:end])
        changed = bytearray(archive)
        changed[codec.HEADER.size + codec.FRAME.size - 1] ^= 1
        with self.assertRaisesRegex(codec.CodecError, 'checksum'):
            codec.decode(changed)
        with self.assertRaises(codec.CodecError):
            codec.decode(archive + b'extra')
        with self.assertRaises(codec.CodecError):
            codec.decode(archive, max_output=1)

    def test_bounded_deflate_and_integer_reader(self):
        bomb = zlib.compress(b'x' * (codec.MAX_SECTION + 1))
        with self.assertRaises(codec.CodecError):
            codec.inflate(bomb)
        with self.assertRaises(codec.CodecError):
            codec.inflate(zlib.compress(b'ok') + b'extra')
        with self.assertRaises(codec.CodecError):
            codec.Reader(b'\x80\x00').number()

    def test_auto_fallback_and_every_selected_change_pays(self):
        raw = b''.join(b'<x>' + str(i).encode() + b':' + str(i).encode() + b'</x>\n' for i in range(40))
        auto, report = codec.encode(raw, mode='auto', config=codec.Config(grammar_budget=4))
        plain, _ = codec.encode(raw, mode='plain')
        self.assertLessEqual(len(auto), len(plain))
        for frame in report['frames']:
            for decision in frame['decisions']:
                if decision['accepted']:
                    self.assertGreaterEqual(decision['before'] - decision['best'], 1)

    def test_streaming_file_reconstruction_and_existing_output_refusal(self):
        raw = b'<x>one\n\xff\x00</x>\r\n' * 17
        encoded, decoded = io.BytesIO(), io.BytesIO()
        codec.encode_stream(io.BytesIO(raw), encoded, len(raw), 'parameter', 97, codec.Config(grammar_budget=3))
        codec.decode_stream(io.BytesIO(encoded.getvalue()), decoded)
        self.assertEqual(decoded.getvalue(), raw)
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'result'
            codec.new_file(p, lambda f: f.write(raw))
            with self.assertRaises(codec.CodecError):
                codec.new_file(p, lambda f: f.write(b'changed'))
            self.assertEqual(p.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
