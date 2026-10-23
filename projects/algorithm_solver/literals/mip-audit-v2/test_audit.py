"""Synthetic exhaustive checks: the MILP optimum equals brute force on tiny instances."""
import itertools, random, sys, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE)]
import audit
import selection as sel  # put on sys.path by audit


def brute(texts, pool, b):
    return min(sel.exact_fit(texts, sel.ALPHABET + list(ch)) for k in range(b + 1) for ch in itertools.combinations(pool, k))


class Exact(unittest.TestCase):
    def test_milp_matches_brute_force(self):
        from scipy.optimize import milp, Bounds
        rng = random.Random(7); checked = 0
        for trial in range(15):
            texts = {p: ''.join(rng.choice('ab();=') for _ in range(rng.randint(8, 16))) for p in range(4)}
            pool = sel.build_pool(texts, set(texts.values()), 4)[:11]
            if not pool: continue
            for b in (1, 2, 3):
                cost, cons, integ, _ = audit.model(texts, pool, 4, b)
                res = milp(cost, constraints=cons, integrality=integ, bounds=Bounds(0, 1), options={'mip_rel_gap': 0.0})
                chosen = [pool[k] for k in range(len(pool)) if res.x[k] > 0.5]
                self.assertEqual(res.status, 0)
                self.assertLessEqual(len(chosen), b)
                self.assertEqual(round(res.fun), brute(texts, pool, b), (trial, b))
                self.assertEqual(sel.exact_fit(texts, sel.ALPHABET + chosen), round(res.fun))
                checked += 1
        self.assertGreater(checked, 30)


if __name__ == '__main__':
    unittest.main()
