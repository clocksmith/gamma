"""Synthetic checks: weighted and per-program-capped exact repairs equal brute force."""
import itertools, random, sys, unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent)]
import breadth
import selection as sel


def costs(texts, vocab):
    return {p: sel.exact_fit({p: t}, vocab) for p, t in texts.items()}


class Repair(unittest.TestCase):
    def test_weighted_and_capped_match_brute_force(self):
        rng = random.Random(5); checked = 0
        for trial in range(12):
            texts = {p: ''.join(rng.choice('ab();=') for _ in range(rng.randint(8, 16))) for p in range(4)}
            pool = sel.build_pool(texts, set(texts.values()), 4)
            if len(pool) < 6: continue
            fixed = list(sel.ALPHABET) + pool[:2]; cand = pool[2:9]
            base = costs(texts, fixed)
            weights = {p: rng.randint(1, 5) for p in texts}
            for k in (1, 2, 3):
                options = [fixed + list(c) for r in range(k + 1) for c in itertools.combinations(cand, r)]
                best_w = min(sum(weights[p] * v for p, v in costs(texts, o).items()) for o in options)
                chosen, rec = breadth.repair(texts, fixed, cand, k, 30, weights=weights)
                self.assertEqual(rec['status'], 0)
                self.assertEqual(sum(weights[p] * v for p, v in costs(texts, fixed + chosen).items()), best_w, (trial, k))
                feasible = [o for o in options if all(v <= base[p] for p, v in costs(texts, o).items())]
                best_c = min(sum(costs(texts, o).values()) for o in feasible)
                chosen, rec = breadth.repair(texts, fixed, cand, k, 30, caps=base)
                got = costs(texts, fixed + chosen)
                self.assertTrue(all(got[p] <= base[p] for p in texts))
                self.assertEqual(sum(got.values()), best_c, (trial, k))
                checked += 1
        self.assertGreater(checked, 20)


    def test_restrictive_caps_bind_and_can_be_infeasible(self):
        texts = {0: 'aaaa', 1: 'bbbb'}; fixed = list(sel.ALPHABET); cand = ['aa', 'bb']
        chosen, rec = breadth.repair(texts, fixed, cand, 1, 30, weights={0: 5, 1: 1})
        self.assertEqual((rec['status'], chosen), (0, ['aa']))  # uncapped: the heavier program wins
        chosen, rec = breadth.repair(texts, fixed, cand, 1, 30, weights={0: 5, 1: 1}, caps={0: 4, 1: 2})
        self.assertEqual((rec['status'], chosen), (0, ['bb']))  # the cap on program 1 forces bb
        chosen, rec = breadth.repair(texts, fixed, cand, 1, 30, caps={0: 2, 1: 2})
        self.assertFalse(rec['feasible'])  # one slot cannot satisfy both caps


if __name__ == '__main__':
    unittest.main()
