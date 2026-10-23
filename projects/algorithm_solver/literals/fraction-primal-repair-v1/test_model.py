"""Exhaustive invented populations only; never accesses corpus or result files."""
import itertools
import random
import unittest

import numpy as np
import model
import pool


def brute_paths(text, words):
    if not text:
        return [(0, 0, 0)]
    return [(f + model.word_cost(w), c + (len(w) == 1), n + 1)
            for w in words if text.startswith(w)
            for f, c, n in brute_paths(text[len(w):], words)]


def brute_dictionary(texts, words, capacity):
    best = None
    for size in range(capacity + 1):
        for subset in itertools.combinations(words, size):
            paths = [brute_paths(text, subset) for text in texts.values()]
            if any(not p for p in paths):
                continue
            value = sum(min(p)[0] for p in paths)
            best = value if best is None else min(best, value)
    return best


class ModelTests(unittest.TestCase):
    def test_negative_cost_dag_exhaustive_warm_cold(self):
        rng = random.Random(400)
        for trial in range(24):
            texts = {i: ''.join(rng.choices('ab', k=5)) for i in range(2)}
            words = ['a', 'b'] + rng.sample(['aa', 'ab', 'ba', 'bb', 'aaa', 'aba'], 3)
            cap = rng.randrange(2, 5)
            m = model.build(texts, words, cap, ['a', 'b'])
            initial = sum(min(brute_paths(t, ['a', 'b']))[0] for t in texts.values())
            self.assertEqual(initial, m['initial'])
            expected = brute_dictionary(texts, words, cap)
            for warm in (False, True):
                with self.subTest(trial=trial, warm=warm):
                    chosen, receipt, replay = model.solve(m, texts, words, warm, 10)
                    self.assertTrue(receipt['optimal']); self.assertTrue(receipt['feasible'])
                    self.assertEqual(receipt['objective'], expected)
                    self.assertEqual(replay['F'], expected)
                    self.assertEqual(replay['F'], 10 * replay['C'] - replay['N'])
                    self.assertLessEqual(len(chosen), cap)

    def test_optional_characters_can_all_disappear(self):
        texts = {0: 'ababab', 1: 'bababa'}; words = ['a', 'b', 'ab', 'ba']
        m = model.build(texts, words, 2, ['a', 'b'])
        chosen, receipt, replay = model.solve(m, texts, words, True, 10)
        self.assertEqual(set(chosen), {'ab', 'ba'})
        self.assertEqual((replay['F'], replay['C'], replay['N']), (-6, 0, 6))
        self.assertEqual(receipt['objective'], -6)

    def test_min_f_seed_differs_from_min_selection_seed(self):
        texts = {0: 'aaaaaa'}; words = ['a', 'aa', 'aaaa']
        m = model.build(texts, words, 3, words)
        row = m['initial_exact']['per_program'][0]
        self.assertEqual((row['F'], row['N']), (-3, 3))
        self.assertEqual([words[i] for i in row['sequence']], ['aa', 'aa', 'aa'])

    def test_all_incumbent_rows_and_objective_are_checked(self):
        texts = {0: 'abab'}; words = ['a', 'b', 'ab']; m = model.build(texts, words, 2, ['a', 'b'])
        def reject(point, objective=None):
            with self.assertRaises(AssertionError):
                model.check_point(m, point, objective)
        point = m['start'].copy(); point[0] = -.1; reject(point)
        point = m['start'].copy(); point[0] = .5; reject(point)  # activation integrality/link
        point = m['start'].copy(); point[2] = 1; reject(point)  # capacity
        point = m['start'].copy(); point[0] = 0; reject(point)  # every used arc links to y
        point = m['start'].copy(); point[3:] = 0; reject(point)  # conservation
        point = m['start'].copy(); point[0] = np.nan; reject(point)
        reject(m['start'], m['initial'] - 1)
        bad = dict(m); bad['upper'] = m['upper'].copy(); bad['upper'][-1] = 1
        with self.assertRaises(AssertionError):model.check_point(bad, m['start'])

    def test_zero_solver_budget_preserves_warm_feasibility(self):
        texts = {0: 'abab' * 10}; words = ['a', 'b', 'ab', 'ba']; m = model.build(texts, words, 2, ['a', 'b'])
        _, receipt, replay = model.solve(m, texts, words, True, 0)
        self.assertTrue(receipt['feasible']); self.assertLessEqual(replay['F'], m['initial'])

    def test_missing_coverage_bans_and_finite_construction_caps(self):
        with self.assertRaises(ValueError):model.build({0: 'ab'}, ['a', 'b'], 2, ['a'])
        with self.assertRaises(AssertionError):model.build({0: 'ab'}, ['a', 'b'], 2, ['a', 'b'], banned=['b'])
        with self.assertRaises(ValueError):model.build({0: 'abab'}, ['a', 'b', 'ab'], 2, ['a', 'b'], max_arcs=1)
        with self.assertRaises(ValueError):model.build({0: 'abab'}, ['a', 'b', 'ab'], 2, ['a', 'b'], max_transitions=1)
        with self.assertRaises(AssertionError):model.build({0: 'abab'}, ['a', 'b', 'ab'], 2, ['a', 'b'], max_pool_characters=1)

    def test_pool_seed_selected_paths_bans_determinism(self):
        texts = {0: 'abababa', 1: 'bababab'}; banned = set(texts.values()) | {'aba'}
        index = pool.implicit.Index(texts, banned)
        q = {pid: [[(i + b) % 3 for b in range(len(pool.implicit.BINS))] for i in range(len(t))] for pid, t in texts.items()}
        words, info = pool.build(index, q, ['a', 'b'], denominator=10, capacity=2, pool_cap=8)
        self.assertTrue({'a', 'b'} <= set(words)); self.assertFalse(set(words) & banned)
        self.assertLessEqual(len(words), 8); self.assertEqual(words, sorted(words))
        self.assertEqual((words, info), pool.build(index, q, ['a', 'b'], denominator=10, capacity=2, pool_cap=8))
        self.assertEqual(set(info['provenance']), set(words))
        with self.assertRaises(AssertionError):pool.build(index, q, ['a', 'b'], capacity=2, pool_cap=1)
        with self.assertRaises(AssertionError):pool.build(index, q, ['a', 'z'], capacity=2)
        with self.assertRaises(AssertionError):pool.build(index, q, ['a', 'aba'], capacity=2)

    def test_exact_dp_ties_against_all_paths(self):
        words = ['a', 'aa', 'aaa', 'b', 'ab', 'ba']
        for size in range(1, 7):
            for letters in itertools.product('ab', repeat=size):
                text = ''.join(letters); r = model.exact({0: text}, words)
                self.assertEqual(r['F'], min(brute_paths(text, words))[0])


if __name__ == '__main__':
    unittest.main()
