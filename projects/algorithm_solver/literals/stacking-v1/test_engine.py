"""Generic synthetic integration cases only; no population loading."""
import unittest
import engine as e


class StackEngineTests(unittest.TestCase):
    def test_source_factorial_parses_and_retains_anchors(self):
        original = {'p': 'function solve(a){let total=0;for(let i=0;i<a.length;i++){total+=a[i];}return total;}'}
        seed = dict(original)
        vocab = e.slots.ALPHABET + ['function solve(', 'return ', 'total', 'a.length']
        cfg = dict(sweeps=1, trials=30, rounds=1, proposal_limit=8, state_limit=100)
        for arm in e.SOURCE_ARMS:
            variants, stats = e.propose_sources(original, seed, seed, {'p': []}, vocab, arm, cfg)
            self.assertIn(original['p'], variants['p'].values())
            self.assertLessEqual(len(variants['p']), 12)
            self.assertEqual(list(variants['p'].values()), sorted(set(variants['p'].values())))
            self.assertIn('rewrite', stats)
            records = e.base.rewrite.records({str(i):t for i,t in enumerate(variants['p'].values())})
            self.assertEqual(len(records), len(variants['p']))

    def test_selection_tie_is_source_text(self):
        groups = {'p': ['a', 'b']}
        variants = e.normalized(groups)
        # Character-only candidates are illegal whole-program literals in the
        # inherited selection API, so inspect the explicit order separately.
        self.assertEqual(list(variants['p'].values()), ['a', 'b'])

    def test_optional_weighted_replacement_can_restore_coverage(self):
        # At capacity, deleting either character alone is infeasible. A paid
        # 'ab' entry can replace one and still cover every source.
        texts = {'p': 'abab', 'q': 'abab'}
        reserved = {f'UNUSED_{i:03d}' for i in range(254)}
        vocab = e.weighted.order(reserved | {'a', 'b'})
        limits = {'trials': 1000, 'seconds': 10}
        nb = dict(additions=4, swaps=20, pair_additions=4, pair_removals=2, pairs=20)
        budget = e.weighted.Budget(limits)
        state = e.weighted.evaluate(texts, vocab, 0, budget)
        candidate, move = e.weighted.best_move(texts, state, reserved, {'abab'}, nb, budget)
        self.assertIsNotNone(candidate)
        self.assertLess(candidate['selections'], state['selections'])
        self.assertEqual(len(candidate['vocab']), 256)
        self.assertTrue(set(move['remove']) <= {'a', 'b'})
        self.assertIn('ab', move['add'])
        self.assertGreater(budget.coverage_failures, 0)


if __name__ == '__main__':
    unittest.main()
