"""Synthetic check: the exact repair equals brute force over additions to a fixed dictionary."""
import itertools, random, sys, unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent)]
import lns
import selection as sel


class Repair(unittest.TestCase):
    def test_repair_matches_brute_force(self):
        rng = random.Random(11); checked = 0
        for trial in range(12):
            texts = {p: ''.join(rng.choice('ab();=') for _ in range(rng.randint(10, 18))) for p in range(4)}
            pool = sel.build_pool(texts, set(texts.values()), 4)
            if len(pool) < 6: continue
            fixed = list(sel.ALPHABET) + pool[:2]; cand = pool[2:10]
            for k in (1, 2, 3):
                chosen, rec = lns.repair(texts, fixed, cand, k, 30)
                best = min(sel.exact_fit(texts, fixed + list(c)) for r in range(k + 1) for c in itertools.combinations(cand, r))
                self.assertEqual(rec['status'], 0)
                self.assertEqual(sel.exact_fit(texts, fixed + chosen), best, (trial, k))
                self.assertLessEqual(abs(rec['objective'] - best), 1e-6)
                checked += 1
        self.assertGreater(checked, 20)

    def test_sparse_incumbent_can_refill_all_free_capacity(self):
        texts = {0: 'abab;cdcd;efef', 1: 'abab;cdcd;efef!', 2: 'ab;cd;ef;'}
        pool = sel.build_pool(texts, set(texts.values()), 4)
        fixed = list(sel.ALPHABET)  # sparse incumbent: no learned entries
        chosen, rec = lns.repair(texts, fixed, pool, 3, 30)  # capacity 3 although nothing was freed
        self.assertEqual(rec['status'], 0)
        self.assertEqual(len(chosen), 3)


if __name__ == '__main__':
    unittest.main()
