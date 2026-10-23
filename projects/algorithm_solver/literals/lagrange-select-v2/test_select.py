"""Synthetic checks: the Lagrangian bound never exceeds the exact optimum (brute force on tiny instances)."""
import itertools, random, sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import selection as sel


def brute(texts, pool, b):
    best = None
    for k in range(b + 1):
        for chosen in itertools.combinations(pool, k):
            cost = sel.exact_fit(texts, sel.ALPHABET + list(chosen))
            best = cost if best is None else min(best, cost)
    return best


class Bound(unittest.TestCase):
    def test_bound_below_optimum_and_primal_feasible(self):
        rng = random.Random(0)
        for trial in range(12):
            texts = {p: ''.join(rng.choice('ab(){};') for _ in range(rng.randint(8, 18))) for p in range(4)}
            pool = sel.build_pool(texts, set(texts.values()), 4)[:12]
            if not pool: continue
            graph = sel.Graph(texts, pool, 4)
            for b in (1, 2, 3):
                cfg = {'iterations': 200, 'seconds': 30, 'theta': 1.0, 'halve_after': 10, 'primal_every': 1}
                lb, lam, vocab, cost = sel.lagrange(texts, pool, graph, b, list(sel.ALPHABET), cfg, [])
                opt = brute(texts, pool, b)
                cert = sel.certify(graph, lam, b, 10**6)
                self.assertLessEqual(lb, opt + 1e-6, (trial, b))
                self.assertLessEqual(cert['integer_lower_bound'], opt, (trial, b))
                self.assertLessEqual(cert['numerator'], opt * cert['denominator'])
                self.assertGreaterEqual(cost, opt)
                self.assertLessEqual(len(set(vocab) - set(sel.ALPHABET)), b)
                self.assertEqual(cost, sel.exact_fit(texts, vocab))

    def test_zero_multipliers_give_unlimited_pool_paths(self):
        texts = {0: 'abcabc', 1: 'abcxyz'}
        pool = sel.build_pool(texts, set(texts.values()), 3)
        graph = sel.Graph(texts, pool, 3)
        total, y = graph.shortest(np.zeros(len(graph.occ_entry)))
        self.assertEqual(total, sel.exact_fit(texts, sel.ALPHABET + pool))


    def test_generated_primal_is_not_the_incumbent(self):
        texts = {0: 'abcabcxx', 1: 'abcyyabc', 2: 'zzabczz'}
        pool = sel.build_pool(texts, set(texts.values()), 3)
        graph = sel.Graph(texts, pool, 3)
        incumbent = sel.ALPHABET + ['abc']  # already optimal for b=1
        cfg = {'iterations': 5, 'seconds': 30, 'theta': 1.0, 'halve_after': 10, 'primal_every': 1}
        _, _, vocab, cost = sel.lagrange(texts, pool, graph, 1, incumbent, cfg, [])
        self.assertIsNotNone(vocab)
        self.assertEqual(cost, sel.exact_fit(texts, vocab))


if __name__ == '__main__':
    unittest.main()
