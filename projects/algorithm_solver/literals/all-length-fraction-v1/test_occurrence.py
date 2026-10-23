import itertools
import random
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'fraction-capacity-v1'))
import dual
import occurrence


class OccurrenceTests(unittest.TestCase):
    def compare(self, texts, pool, mandatory, rng):
        old = occurrence.BaseGraph(texts, pool, mandatory)
        new = occurrence.Graph(texts, pool, mandatory)
        self.assertEqual(old.at, new.at)
        self.assertEqual(old.order, new.order)
        self.assertEqual(old.lengths, new.lengths)
        self.assertTrue(np.array_equal(old.occ_entry, new.occ_entry))
        lam = np.array([rng.random() * 12 for _ in old.occ_entry])
        a, y = old.shortest(lam)
        b, z = new.shortest(lam)
        self.assertEqual(a, b)
        self.assertTrue(np.array_equal(y, z))
        for capacity in (0, 1, 3, len(pool) + 1):
            cert, q = old.certificate(lam, capacity, 1000)
            cert2, q2 = new.certificate(lam, capacity, 1000)
            self.assertEqual((cert, q), (cert2, q2))
            expected = dual.independent_certificate(texts, pool, mandatory, q, capacity, 1000)
            self.assertEqual(expected, occurrence.independent_certificate(texts, pool, mandatory, q, capacity, 1000))
            self.assertEqual(expected, cert['numerator'])

    def test_random_exact_graph_order_paths_and_certificates(self):
        rng = random.Random(282)
        words = [''.join(x) for n in range(2, 6) for x in itertools.product('ab', repeat=n)]
        for _ in range(150):
            texts = {str(i): ''.join(rng.choices('ab', k=rng.randrange(1, 16))) for i in range(3)}
            mandatory = ['a', 'b'] if rng.randrange(2) else []
            pool = ([] if mandatory else ['a', 'b']) + rng.sample(words, 12)
            rng.shuffle(pool)
            self.compare(texts, pool, mandatory, rng)

    def test_long_prefix_failure_links_and_mandatory_multichar(self):
        self.compare({'a': 'a' * 180 + 'b', 'b': 'b' + 'a' * 150},
                     ['a', 'b'] + ['a' * n for n in range(2, 160)], [], random.Random(283))
        self.compare({'a': 'abababab', 'b': 'babaabab'}, ['a', 'b', 'aba', 'bab'], ['ab'], random.Random(284))

    def test_match_set_against_exhaustive_and_boundaries(self):
        rng = random.Random(285)
        for _ in range(100):
            text = ''.join(rng.choices('ab\x00Ω', k=25))
            words = sorted({text[i:j] for i in range(25) for j in range(i + 1, min(26, i + 7))})
            pool = rng.sample(words, min(20, len(words)))
            actual = sorted(occurrence.Automaton(pool, []).matches(text))
            expected = sorted((i, i + len(word), entry) for entry, word in enumerate(pool)
                              for i in range(len(text)) if text.startswith(word, i))
            self.assertEqual(actual, expected)

    def test_integer_penalties_and_unreachable_fail_closed(self):
        texts = {'a': 'ab', 'b': 'ba'}
        pool = ['a', 'b', 'ab', 'ba']
        graph = occurrence.BaseGraph(texts, pool, [])
        q = [10**30 + i for i in range(len(graph.occ_entry))]
        self.assertEqual(dual.independent_certificate(texts, pool, [], q, 2, 10**20),
                         occurrence.independent_certificate(texts, pool, [], q, 2, 10**20))
        with self.assertRaises(AssertionError):
            occurrence.independent_certificate({'a': 'ab'}, ['a'], [], [0], 1, 1000)
        with self.assertRaises(AssertionError):
            occurrence.independent_certificate(texts, pool, [], q[:-1], 2, 1000)


if __name__ == '__main__':
    unittest.main()
