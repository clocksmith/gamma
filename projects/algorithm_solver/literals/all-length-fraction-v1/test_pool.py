import random
import unittest
from collections import defaultdict
import pool


def brute(texts, banned):
    owners = defaultdict(set)
    for pid, text in texts.items():
        for i in range(len(text)):
            for j in range(i + 2, len(text) + 1):
                owners[text[i:j]].add(pid)
    return sorted(word for word, pids in owners.items() if len(pids) >= 2 and word not in banned)


class PoolTests(unittest.TestCase):
    def test_suffix_array_and_lcp_against_brute(self):
        rng = random.Random(280)
        for _ in range(300):
            values = rng.choices(range(-2, 4), k=rng.randrange(35))
            sa = pool.suffix_array(values)
            self.assertEqual(sa, sorted(range(len(values)), key=lambda i: values[i:]))
            expected = [0] * len(sa)
            for k in range(1, len(sa)):
                a, b = sa[k - 1], sa[k]
                while a + expected[k] < len(values) and b + expected[k] < len(values) and values[a + expected[k]] == values[b + expected[k]]:
                    expected[k] += 1
            self.assertEqual(pool.lcp_array(values, sa), expected)

    def test_random_pool_against_exhaustive(self):
        rng = random.Random(281)
        for _ in range(500):
            texts = {str(i): ''.join(rng.choices('aab\n\x00Ω', k=rng.randrange(13))) for i in range(rng.randrange(7))}
            possible = brute(texts, set())
            banned = set(rng.sample(possible, rng.randrange(len(possible) + 1)))
            self.assertEqual(pool.build_pool(texts, banned), brute(texts, banned))

    def test_repeated_owner_does_not_count_twice(self):
        self.assertEqual(pool.build_pool({'only': 'abababababab', 'other': 'xyz'}, set()), [])
        texts = {'a': 'aaaaaaaaab', 'b': 'aaa', 'c': 'aaaaac', 'd': 'aaaa'}
        self.assertEqual(pool.build_pool(texts, set()), brute(texts, set()))

    def test_identical_documents_and_banned_prefixes(self):
        texts = {'a': 'abababa', 'b': 'abababa', 'c': 'ab'}
        banned = {'ab', 'aba', 'abababa'}
        actual = pool.build_pool(texts, banned)
        self.assertEqual(actual, brute(texts, banned))
        self.assertIn('ababab', actual)
        self.assertNotIn('ab', actual)

    def test_long_entries_and_no_boundary_crossing(self):
        texts = {'a': 'a' * 80 + 'x', 'b': 'a' * 80 + 'y', 'c': 'z'}
        actual = pool.build_pool(texts, {'aa', 'a' * 79})
        self.assertEqual(actual, brute(texts, {'aa', 'a' * 79}))
        self.assertIn('a' * 80, actual)
        self.assertFalse(any('x' in s or 'y' in s or 'z' in s for s in actual))

    def test_empty_and_one_character_documents(self):
        for texts in ({}, {'a': ''}, {'a': 'a', 'b': 'a'}, {'a': 'abc'}):
            self.assertEqual(pool.build_pool(texts, set()), [])


if __name__ == '__main__':
    unittest.main()
