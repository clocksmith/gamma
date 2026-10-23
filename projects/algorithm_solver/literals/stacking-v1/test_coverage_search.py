import itertools
import random
import unittest
import coverage_search as s


class CoverageSearchTests(unittest.TestCase):
    def test_order_preserves_exact_set(self):
        self.assertEqual(s.order(['ab', 'b', 'ab']), ['b', 'ab'])
        self.assertNotIn('a', s.order(['ab', 'b']))

    def test_missing_character_is_not_restored(self):
        budget = s.Budget({'trials': 100, 'seconds': 10})
        state = s.evaluate({'p': 'ab'}, ['ab'], 1, budget)
        self.assertEqual(state['vocab'], ['ab'])
        self.assertEqual(state['characters'], 0)
        self.assertIsNone(s.evaluate({'p': 'ac'}, ['ab'], 1, budget))
        self.assertEqual(budget.coverage_failures, 1)

    def test_weighted_path_matches_exhaustive(self):
        rng = random.Random(29)
        words = ['a', 'b', 'aa', 'ab', 'ba', 'bb', 'aba']
        for _ in range(80):
            text = ''.join(rng.choice('ab') for _ in range(rng.randrange(1, 7)))
            vocab = s.order(rng.sample(words, rng.randrange(1, len(words)+1)))
            weight = rng.choice([0, 1, 4, 16])
            def paths(i):
                if i == len(text):
                    yield ()
                for j, word in enumerate(vocab):
                    if text.startswith(word, i):
                        for suffix in paths(i+len(word)):
                            yield (j,) + suffix
            paths_found = list(paths(0))
            def cost(seq):
                n = len(seq)
                c = sum(len(vocab[i]) == 1 for i in seq)
                return 4*n+weight*c, n, c, seq
            state = s.evaluate({'p': text}, vocab, weight,
                               s.Budget({'trials': 100, 'seconds': 10}))
            if paths_found:
                expected = min(paths_found, key=cost)
                self.assertEqual(state['parsed']['p'], tuple(vocab[i] for i in expected))
            else:
                self.assertIsNone(state)

    def test_reserved_and_optional_coverage(self):
        texts = {'a': 'abab', 'b': 'abab'}
        neighborhood = dict(additions=20, swaps=200, pair_additions=5, pair_removals=5, pairs=200)
        for reserved in (set(), {'a', 'b'}):
            state, receipt = s.optimize(texts, ['a', 'b'], 1, reserved, set(), neighborhood,
                                        {'trials': 2000, 'seconds': 10})
            self.assertTrue(reserved <= set(state['vocab']))
            self.assertEqual(''.join(state['parsed']['a']), 'abab')
            self.assertLess(state['selections'], 8)
            self.assertNotIn('c', state['vocab'])
            self.assertGreater(receipt['coverage_failures'], 0 if not reserved else -1)

    def test_illegal_start_fails_closed(self):
        for vocab, reserved, banned in [(['ab'], {'a'}, set()), (['ab'], set(), {'ab'})]:
            with self.assertRaises(ValueError):
                s.optimize({'p': 'ab'}, vocab, 0, reserved, banned, {}, {'trials': 5, 'seconds': 1})


if __name__ == '__main__':
    unittest.main()
