import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent), str(HERE.parent / 'pass2/working')]
import verify
import literals
import bitpack


class IndependentVerifierTests(unittest.TestCase):
    def test_missing_languages_fail_closed(self):
        for data in [{}, {'schema': 'gamma.pure-literal-development.v1', 'languages': {}},
                     {'schema': 'gamma.pure-literal-development.v1', 'languages': {'javascript': {}}}]:
            with tempfile.TemporaryDirectory() as td:
                path = Path(td)
                (path / 'results.json').write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    verify.verify(path)

    def test_equal_length_packet_does_not_hide_different_width(self):
        dictionary = ['x', 'y']
        data = literals.dictionary_bytes(dictionary)
        packet6 = bitpack.encode(dictionary, [0], 6)
        packet8 = bitpack.encode(dictionary, [0], 8)
        self.assertEqual(len(packet6), len(packet8))
        self.assertEqual(verify.decode(data, packet6, 6)[2], 'x')
        with self.assertRaises(ValueError):
            verify.decode(data, packet6, 8)

    def test_forward_shortest_path_and_uncovered(self):
        self.assertEqual(verify.minimum('ababa', ['a', 'b', 'aba']), 3)
        self.assertEqual(verify.minimum('abc', ['a', 'b']), float('inf'))

    def test_decoder_rejects_padding_trailing_and_hash(self):
        data = literals.dictionary_bytes(['a'])
        packet = bitpack.encode(['a'], [0], 7)
        for corrupt in [packet + b'\0', packet[:-1] + b'\1', packet[:5] + b'x'*32 + packet[37:]]:
            with self.assertRaises(ValueError):
                verify.decode(data, corrupt, 7)


if __name__ == '__main__':
    unittest.main()
