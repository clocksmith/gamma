import itertools
import unittest

from literals import (decode_bytes, decode4_bytes, dictionary_bytes, encode_corpus, merged_dictionary,
                      program_bytes, program4_bytes, reconstruct, shortest_encode)


class LiteralTests(unittest.TestCase):
    def test_shortest_path_beats_longest_match(self):
        literals = ["ab", "abcd", "cdef", "e", "f"]
        self.assertEqual(shortest_encode("abcdef", literals), [0, 2])

    def test_small_exhaustive_against_independent_recursion(self):
        literals = ["a", "b", "aa", "ab", "ba", "aba"]
        def optimum(text):
            if not text:
                return 0
            return 1 + min(optimum(text[len(s):]) for s in literals if text.startswith(s))
        for size in range(7):
            for letters in itertools.product("ab", repeat=size):
                text = "".join(letters)
                seq = shortest_encode(text, literals)
                self.assertEqual(len(seq), optimum(text))
                self.assertEqual(reconstruct(literals, seq), text)

    def test_exact_unicode_whitespace_and_binary_roundtrip(self):
        text = "const value = 'é';\n  // λ\n"
        literals = sorted(set(text))
        seq = shortest_encode(text, literals)
        dictionary = dictionary_bytes(literals)
        program = program_bytes(literals, seq)
        self.assertEqual(decode_bytes(dictionary, program), text)
        self.assertEqual(len(dictionary), 8 + 4 * len(literals) + sum(len(s.encode()) for s in literals))
        self.assertEqual(len(program), 40 + 4 * len(seq))

    def test_invalid_streams(self):
        for literals in ([], [""], ["a", "a"]):
            with self.assertRaises(ValueError):
                reconstruct(literals, [])
        for sequence in ([True], [-1], [1], [0.0]):
            with self.assertRaises(ValueError):
                reconstruct(["a"], sequence)
        with self.assertRaises(ValueError):
            shortest_encode("b", ["a"])
        d, p = dictionary_bytes(["a"]), program_bytes(["a"], [0])
        for bad_d, bad_p in ((d[:-1], p), (d + b"x", p), (d, p[:-1]), (d, p + b"x"),
                             (dictionary_bytes(["b"]), p)):
            with self.assertRaises(ValueError):
                decode_bytes(bad_d, bad_p)

    def test_merging_flattens_and_prunes_without_loss(self):
        sources = {"one": "const counts = new Map();\n", "two": "const values = new Set();\n"}
        for shared in (False, True):
            vocab = merged_dictionary(list(sources.values()), "lexical", 16, shared)
            result = encode_corpus(sources, vocab)
            for key, row in result["programs"].items():
                self.assertEqual(reconstruct(result["literals"], row["sequence"]), sources[key])
            self.assertEqual(result["metrics"]["exact_reconstructions"], 2)

    def test_four_bit_cap_lengths_padding_and_missing_ids(self):
        literals = [chr(65 + i) for i in range(16)]
        for sequence in ([], [15], [15, 0], [0, 1, 15]):
            packed = program4_bytes(literals, sequence)
            self.assertEqual(len(packed), 40 + (len(sequence) + 1) // 2)
            self.assertEqual(decode4_bytes(dictionary_bytes(literals), packed),
                             reconstruct(literals, sequence))
        with self.assertRaises(ValueError):
            program4_bytes(literals + ["Q"], [0])
        packed = program4_bytes(["a"], [0])
        with self.assertRaises(ValueError):
            decode4_bytes(dictionary_bytes(["a"]), packed[:-1] + b"\x01")
        with self.assertRaises(ValueError):
            decode4_bytes(dictionary_bytes(["a"]), packed[:-1] + b"\x10")


if __name__ == "__main__":
    unittest.main()
