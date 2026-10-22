"""Focused checks for iteration 3: readable units, move search and seeded kicks; synthetic, no corpus search."""
import unittest

import run
import units

TEXTS = {1: 'function solve(a){let b=0;for(const c of a){b+=c;}return b;}',
         2: 'function solve(a){let b=1;for(const c of a){b*=c;}return b;}',
         3: 'function solve(a){const b=[];for(const c of a){b.push(c);}return b;}'}
CANONICAL = 'function solve(values) {\n  let total = 0;\n  for (const value of values) {\n    total += value;\n  }\n  return total;\n}\n'
BOUNDS = {'additions': 12, 'designed_fraction': 0.25, 'swaps': 40, 'pair_additions': 4, 'pair_removals': 3, 'pairs': 10,
          'refill_shortlist': 6}


def sources():
    return {pid: {'compact': text} for pid, text in TEXTS.items()}


class Units(unittest.TestCase):
    def test_tokens_cover_source_exactly(self):
        self.assertEqual(''.join(t for _, t, _ in units.tokens(CANONICAL)), CANONICAL)

    def test_units_follow_the_frozen_classes(self):
        found = set(units.units_of(CANONICAL))
        for item in [('name', 'total'), ('head', 'return '), ('head', 'for ('), ('tail', ') {\n'), ('tail', ';\n'),
                     ('tail', '}\n'), ('indent', '    '), ('operator', ' += '), ('operator', ' = ')]:
            self.assertIn(item, found)
        self.assertNotIn(('name', 'tota'), found)

    def test_extract_requires_two_witnesses_and_one_class(self):
        found = units.extract({k: v for k, v in TEXTS.items()})
        self.assertIn('return ', found)
        self.assertNotIn('push', found)  # one witness only
        self.assertEqual(found['b'], 'name')

    def test_alignment_counts_split_names(self):
        self.assertEqual(units.aligned_fraction('let ab', ['let ', 'ab']), 1)
        self.assertEqual(units.aligned_fraction('let ab', ['let a', 'b']), 0)


class Search(unittest.TestCase):
    def setUp(self):
        self.budget = run.Budget({'trials': 10**6, 'seconds': 600})
        self.start = run.joint.evaluate(sources(), list(run.base.ALPHABET), 7)

    def test_local_search_never_loses_and_respects_capacity(self):
        log = []
        final, stop = run.local_search(sources(), self.start, 7, run.hybrid_proposer(['for(const c of a){'], sources()),
                                       BOUNDS, self.budget, log)
        self.assertLess(final['selections'], self.start['selections'])
        self.assertLessEqual(len(final['vocab']), 128)
        self.assertEqual(stop, 'local_optimum')
        self.assertEqual([r['after']['selections'] for r in log], sorted((r['after']['selections'] for r in log), reverse=True))

    def test_hybrid_reserves_designed_slots(self):
        listed = run.hybrid_proposer(['for(const c of a){', 'never'], sources())(sources(), self.start, 8, 0.25)
        self.assertIn('for(const c of a){', listed)
        self.assertNotIn('never', listed)
        self.assertEqual(len(listed), len(set(listed)))

    def test_trial_cap_binds(self):
        budget = run.Budget({'trials': 25, 'seconds': 600})
        run.local_search(sources(), self.start, 7, run.readable_proposer(sorted(units.extract(TEXTS))), BOUNDS, budget, [])
        self.assertLessEqual(budget.trials, 26)  # one prune may follow the last counted trial
        self.assertEqual(budget.reason(), 'trial_limit')

    def test_seeded_kicks_are_reproducible_and_never_lose(self):
        propose = run.hybrid_proposer([], sources())
        start, _ = run.local_search(sources(), self.start, 7, propose, BOUNDS, run.Budget({'trials': 10**6, 'seconds': 600}), [])
        results = []
        for _ in range(2):
            final, kicks = run.iterated(sources(), start, 7, propose, BOUNDS, 2, 3, run.Budget({'trials': 4000, 'seconds': 600}))
            results.append((final['vocab'], [k['removed'] for k in kicks]))
            self.assertLessEqual(run.cost(final), run.cost(start))
        self.assertEqual(results[0], results[1])


if __name__ == '__main__':
    unittest.main()
