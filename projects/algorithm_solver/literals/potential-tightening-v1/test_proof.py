"""Invented exhaustive small dictionaries check the stated dominance theorem."""
import itertools
import random
import unittest

import proof


def paths(text, vocab):
    distance = [None] * len(text) + [0]
    for i in range(len(text) - 1, -1, -1):
        options = [(9 if len(word) == 1 else -1) + distance[i + len(word)]
                   for word in vocab if text.startswith(word, i)
                   and distance[i + len(word)] is not None]
        distance[i] = min(options) if options else None
    return distance[0]


class TighteningTests(unittest.TestCase):
    def test_random_full_paths_weights_and_exhaustive_weak_duality(self):
        rng = random.Random(53)
        strict = 0
        for _ in range(32):
            texts = [''.join(rng.choice('abc') for _ in range(4)) for _ in range(2)]
            banned = set(texts)
            owners = {}
            for pid, text in enumerate(texts):
                for i in range(len(text)):
                    for j in range(i + 1, len(text) + 1):
                        word = text[i:j]
                        if word not in banned:
                            owners.setdefault(word, set()).add(pid)
            old_pool = {word for word in owners if len(word) == 1 or rng.random() < .3}
            charges = [{word: 0 for word in owners} for _ in range(2)]
            total = 0
            for text in texts:
                full = [(i, j) for i in range(len(text)) for j in range(i + 1, len(text) + 1)
                        if text[i:j] not in banned]
                old = [(i, j, rng.randrange(60)) for i, j in full if text[i:j] in old_pool]
                d0, lifted = proof.lift(len(text), old, full, 7, tighten_old=False)
                d1, tightened = proof.lift(len(text), old, full, 7, tighten_old=True)
                self.assertEqual(d0, d1)
                total += d0[0]
                for a, b in zip(lifted, tightened):
                    self.assertEqual(a[:2], b[:2]); self.assertLessEqual(b[2], a[2])
                    charges[0][text[a[0]:a[1]]] += a[2]
                    charges[1][text[b[0]:b[1]]] += b[2]
            words = sorted(owners); capacity = 4
            subsets = [choice for n in range(capacity + 1) for choice in itertools.combinations(words, n)]
            last = [None, None]
            for k in range(capacity + 1):
                feasible = [choice for choice in subsets if sum(len(owners[w]) == 1 for w in choice) <= k]
                charge = [max(sum(weights[w] for w in choice) for choice in feasible) for weights in charges]
                self.assertLessEqual(charge[1], charge[0]); strict += charge[1] < charge[0]
                for arm in range(2):
                    if last[arm] is not None: self.assertGreaterEqual(charge[arm], last[arm])
                    last[arm] = charge[arm]
                bound = -(-(total - charge[1]) // 7)
                for choice in feasible:
                    values = [paths(text, choice) for text in texts]
                    if all(value is not None for value in values):
                        self.assertLessEqual(bound, sum(values))
        self.assertGreater(strict, 0)

    def test_lower_slack_can_leave_top_charge_unchanged(self):
        old = [(0, 1, 100), (1, 2, 100), (0, 2, 0)]
        full = [(0, 1), (0, 2), (1, 2)]
        d0, a = proof.lift(2, old, full, 1, tighten_old=False)
        d1, b = proof.lift(2, old, full, 1, tighten_old=True)
        self.assertEqual(d0, d1)
        self.assertLess(sum(row[2] for row in b), sum(row[2] for row in a))
        self.assertEqual(max(row[2] for row in a), max(row[2] for row in b))

    def test_larger_penalties_can_raise_actual_path_term(self):
        # Fixed-L dominance is not an optimum over freshly recomputed distances.
        self.assertGreater(proof.suffix(1, [(0, 1, 10)], 1)[0],
                           proof.suffix(1, [(0, 1, 0)], 1)[0])


if __name__ == '__main__':
    unittest.main()
