"""Independent small oracle for minimum-press segmentation."""
import itertools
import unittest
from algsolve.input_vocabulary import codes, encode, fit


class InputVocabularyTests(unittest.TestCase):
    def test_segmentation_matches_exhaustive_oracle(self):
        book = codes({'a': 9, 'b': 4, 'ab': 8, 'ba': 3})
        def brute(text):
            if not text:
                return 0
            return min(len(bits) + brute(text[len(token):]) for token, bits in book.items() if text.startswith(token))
        for length in range(8):
            for chars in itertools.product('ab', repeat=length):
                text = ''.join(chars)
                self.assertEqual(encode(text, book)[0], brute(text))

    def test_fitting_keeps_all_ascii_representable(self):
        weights = fit(['def solve(x):\n    return x + 1\n'] * 4)
        book = codes(weights)
        for code in range(128):
            self.assertGreater(encode(chr(code), book)[0], 0)
        with self.assertRaises(ValueError):
            encode('\u0100', book)


if __name__ == '__main__':
    unittest.main()
