import importlib.util
from functools import lru_cache
from pathlib import Path
import random
import sys
import unittest

spec = importlib.util.spec_from_file_location('fragment_spelling_codec', Path(__file__).with_name('codec.py'))
codec = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = codec
spec.loader.exec_module(codec)


def dictionary(width, entries=()):
    result = list(entries)
    result.extend(f'~unused-{i}~' for i in range((1 << width) - 1 - len(result)))
    return result


def independent_cost(source, fragments, width):
    raw = source.encode('utf-8')
    words = [fragment.encode('utf-8') for fragment in fragments]

    @lru_cache(None)
    def cost(offset):
        if offset == len(raw):
            return 0
        candidates = [width + 9 * size + 1 + cost(offset + size)
                      for size in range(1, len(raw) - offset + 1)]
        candidates.extend(width + cost(offset + len(word)) for word in words if raw.startswith(word, offset))
        return min(candidates)
    return cost(0)


class CodecTest(unittest.TestCase):
    def test_all_widths_roundtrip_unicode_nul_whitespace_and_unknown_identifiers(self):
        source = 'const variable42 = "café🙂\\n";\n\t\x00'
        for width in (6, 7, 8):
            words = dictionary(width, ['const ', ' = ', ';\n'])
            packet = codec.encode(source, words, width)
            self.assertEqual(codec.decode(packet.bits, words, width), source)
            self.assertEqual(packet.source_bytes, len(source.encode()))
            self.assertGreater(packet.spelling_bytes, 0)
            self.assertEqual(packet.input_presses, packet.fragment_bits + packet.spelling_bits + packet.mode_switch_bits)
            self.assertEqual(packet.spelling_bits, packet.spelling_bytes * 9)

    def test_every_mode_switch_and_byte_is_charged(self):
        words = dictionary(6, ['ab'])
        for source, expected in [('ab', 6), ('z', 16), ('zz', 25), ('zabz', 38), ('', 0)]:
            self.assertEqual(codec.encode(source, words, 6).input_presses, expected)
        self.assertEqual(codec.encode('🙂', words, 6).spelling_bytes, 4)
        self.assertEqual(codec.encode('🙂', words, 6).input_presses, 6 + 4 * 9 + 1)

    def test_dynamic_program_matches_independent_exhaustive_segment_oracle(self):
        rng = random.Random(421)
        for width in (6, 7, 8):
            words = dictionary(width, ['ab', 'ba', 'aa', 'abc', 'bc'])
            for _ in range(30):
                source = ''.join(rng.choice('abcx') for _ in range(rng.randrange(1, 10)))
                self.assertEqual(codec.encode(source, words, width).input_presses,
                                 independent_cost(source, words, width))

    def test_partial_codewords_invalid_utf8_and_unclosed_modes_refuse(self):
        words = dictionary(6, ['ab'])
        for bits in ['x', '1', '000000', '0000001', '0000001' + '11111111' + '0']:
            with self.assertRaises(ValueError):
                codec.decode(bits, words, 6)

    def test_width_slot_duplicates_and_single_character_dictionaries_refuse(self):
        for words, width in [(dictionary(6), 5), (dictionary(6)[:-1], 6), (['aa'] * 63, 6), (dictionary(6, ['a']), 6)]:
            with self.assertRaises(ValueError):
                codec.encode('aa', words, width)

    def test_binary_packets_preserve_exact_length_and_reject_hidden_padding(self):
        words = dictionary(6, ['ab'])
        packet = codec.encode('zab🙂', words, 6)
        stored = codec.packet_bytes(packet)
        self.assertEqual(codec.decode_packet(stored, words, 6), 'zab🙂')
        self.assertEqual(len(stored), 9 + (packet.input_presses + 7) // 8)
        self.assertEqual(codec.dictionary_bytes(words, 6)[:5], b'FSD1\x06')
        with self.assertRaises(ValueError):
            codec.decode_packet(stored + b'\x00', words, 6)
        padded = codec.packet_bytes(codec.encode('ab', words, 6))
        with self.assertRaises(ValueError):
            codec.decode_packet(padded[:-1] + bytes([padded[-1] | 1]), words, 6)

    def test_source_and_input_bounds_are_enforced(self):
        words = dictionary(6, ['aa'])
        with self.assertRaises(ValueError):
            codec.encode('a' * (codec.MAX_SOURCE_BYTES + 1), words, 6)
        with self.assertRaises(ValueError):
            codec.decode('0' * (codec.MAX_BITS + 1), words, 6)


if __name__ == '__main__':
    unittest.main()
