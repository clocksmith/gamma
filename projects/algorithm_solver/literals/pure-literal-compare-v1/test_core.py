import itertools
from pathlib import Path
import struct
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent), str(HERE.parent / 'pass2/working')]
import core
import literals
import bitpack


class PureLiteralTests(unittest.TestCase):
    def test_full_alphabet_coverage(self):
        selected, _ = core.alphabet({'a': 'ab', 'b': 'bc'}, 4)
        self.assertEqual(selected, ['a', 'b', 'c'])

    def test_complete_coverage_over_frequent_outlier(self):
        sources = {'a': 'ab', 'b': 'ac', 'c': 'ad', 'd': 'x' * 100 + 'yzw'}
        selected, frequency = core.alphabet(sources, 4)
        covered = lambda chars: sum(set(s) <= set(chars) for s in sources.values())
        self.assertGreater(covered(selected), covered(frequency))
        self.assertEqual(len(selected), 4)

    def test_duplicate_hash_does_not_add_support(self):
        d, trace = core.pair_fit({'a': 'abab', 'b': 'abab'}, ['a', 'b'], 3, set())
        self.assertEqual(d, ['a', 'b'])
        self.assertFalse(trace)

    def test_pairs_are_flat_exact_strings(self):
        d, trace = core.pair_fit({'a': 'ababx', 'b': 'ababy'}, list('abxy'), 7, set())
        self.assertIn('abab', d)
        self.assertTrue(trace)
        for s in ['ababx', 'ababy']:
            seq = literals.shortest_encode(s, d)
            self.assertEqual(''.join(d[i] for i in seq), s)

    def test_body_exclusions_are_global_and_containment_based(self):
        d, trace = core.pair_fit({'a': 'ababx', 'b': 'ababy'}, list('abxy'), 8, {b'ab'})
        self.assertFalse(any('ab' in s for s in d))

    def test_nonoverlapping_pair_counts(self):
        d, trace = core.pair_fit({'a': 'aaaax', 'b': 'aaaay'}, list('axy'), 4, set())
        self.assertEqual(trace[0]['pair_count'], 4)
        self.assertEqual(d[-1], 'aa')

    def test_rare_symbols_stay_uncovered(self):
        d, _ = core.pair_fit({'a': 'aax', 'b': 'aay'}, ['a', 'x'], 4, set())
        with self.assertRaises(ValueError):
            literals.shortest_encode('aay', d)

    def test_unicode_is_exact_not_normalized(self):
        d = ['é', 'e', '\u0301', '\U00020000']
        for s in ['é\U00020000', 'e\u0301\U00020000']:
            seq = literals.shortest_encode(s, d)
            self.assertEqual(bitpack.decode(literals.dictionary_bytes(d), bitpack.encode(d, seq, 6)), s)

    def test_exhaustive_shortest_oracle(self):
        pool = ['a', 'b', 'aa', 'ab', 'ba', 'bb', 'aba']
        for mask in range(1, 1 << len(pool)):
            d = [v for i, v in enumerate(pool) if mask >> i & 1]
            for n in range(5):
                for chars in itertools.product('ab', repeat=n):
                    s = ''.join(chars)
                    costs = [0] + [999] * len(s)
                    for end in range(1, len(s) + 1):
                        for v in d:
                            start = end - len(v)
                            if start >= 0 and s[start:end] == v:
                                costs[end] = min(costs[end], costs[start] + 1)
                    if costs[-1] == 999:
                        with self.assertRaises(ValueError):
                            literals.shortest_encode(s, d)
                    else:
                        seq = literals.shortest_encode(s, d)
                        self.assertEqual(len(seq), costs[-1])
                        self.assertEqual(literals.reconstruct(d, seq), s)

    def test_packet_costs_and_widths(self):
        for width in [6, 7, 8]:
            d, seq = ['foo', 'bar'], [0, 1, 0]
            p = bitpack.encode(d, seq, width)
            self.assertEqual(len(p), 41 + (3 * width + 7) // 8)
            self.assertEqual(bitpack.decode(literals.dictionary_bytes(d), p), 'foobarfoo')

    def test_packet_corruption_fails_closed(self):
        d = ['foo', 'bar']
        db = literals.dictionary_bytes(d)
        p = bitpack.encode(d, [0], 6)
        for corrupt in [p[:-1], p + b'\0', p[:-1] + bytes([p[-1] | 1]), p[:5] + b'X' * 32 + p[37:],
                        p[:37] + struct.pack('>I', 100) + p[41:]]:
            with self.assertRaises(ValueError):
                bitpack.decode(db, corrupt)
        with self.assertRaises(ValueError):
            bitpack.encode([str(i) for i in range(65)], [0], 6)


if __name__ == '__main__':
    unittest.main()
