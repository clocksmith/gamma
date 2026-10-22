"""Focused synthetic checks for the matched runner; no corpus search or source execution."""
import json
import tempfile
import unittest
from pathlib import Path

import run

TEXTS = {'1': 'abcabc\nxyz\n', '2': 'abc xyz\nabc\n', '3': 'xyz\nxyzabc\n'}
DESIGNED = ['abc', 'xyz\n', 'never-present']
LIMITS = {'search_seconds_per_arm': 30, 'shortlist': 6, 'max_trials_per_arm': 200}


class CandidatePools(unittest.TestCase):
    def setUp(self):
        self.vocab = list(run.base.ALPHABET)
        self.current = run.base.sequences(TEXTS, self.vocab)

    def candidates(self, pool):
        return run.fixed_candidates(pool, DESIGNED)(TEXTS, self.vocab, self.current, set())

    def test_each_pool_returns_only_its_own_candidates(self):
        designed, mined, combined = (set(self.candidates(p)) for p in run.POOLS)
        self.assertEqual(designed, {'abc', 'xyz\n'})
        self.assertEqual(mined, set(run.base.proposals(TEXTS, self.vocab, self.current)))
        self.assertEqual(combined, designed | mined)

    def test_ranking_ignores_candidate_origin(self):
        pool = sorted(set(self.candidates('combined')))
        joined = '\x00'.join(TEXTS.values())
        self.assertEqual(run.rank(pool, joined, self.vocab), run.rank(list(reversed(pool)), joined, self.vocab))

    def test_retired_and_present_entries_are_not_proposed(self):
        propose = run.fixed_candidates('designed', DESIGNED)
        self.assertNotIn('abc', propose(TEXTS, self.vocab + ['abc'], self.current, set()))
        self.assertNotIn('xyz\n', propose(TEXTS, self.vocab, self.current, {'xyz\n'}))


class Search(unittest.TestCase):
    def test_designed_arm_admits_only_designed_pieces(self):
        snapshots, trace = run.learn(TEXTS, LIMITS, run.fixed_candidates('designed', DESIGNED))
        for vocab, _ in snapshots.values():
            self.assertLessEqual(set(vocab) - set(run.base.ALPHABET), set(DESIGNED))
        self.assertGreater(len(trace['steps']), 0)

    def test_joint_improvement_never_ends_worse(self):
        sources = {int(k): {'canonical': v, 'compact': v.replace('\n', '')} for k, v in TEXTS.items()}
        start = run.joint.evaluate(sources, list(run.base.ALPHABET), 7)
        limits = {'rounds_per_start': 2, 'trials_per_start': 60, 'seconds_per_start': 30, 'addition_shortlist': 4,
                  'removal_shortlist': 2, 'pair_addition_shortlist': 3, 'pair_removal_sets': 2}
        final, _ = run.improve(sources, start, 7, 'input', limits, run.joint_candidates('combined', DESIGNED))
        self.assertLessEqual(run.joint.cost(final, 'input'), run.joint.cost(start, 'input'))


class Integrity(unittest.TestCase):
    def test_changed_frozen_input_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'frozen input changed'):
            run.load_inputs({'inputs': {'run.py': '0' * 64}, 'qualification_receipts': {}})

    def test_packet_that_does_not_decode_to_its_source_fails(self):
        vocab = list(run.base.ALPHABET) + ['abc']
        seqs = run.base.sequences(TEXTS, vocab)
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / 'arm'
            run.base.save(folder, TEXTS, vocab, seqs, 7, 'synthetic', 'test')
            run.verify_and_extend(folder, TEXTS, vocab, lambda s: 'x')
            tampered = dict(TEXTS, **{'1': TEXTS['1'].replace('xyz', 'xyy')})
            with self.assertRaises(AssertionError):
                run.verify_and_extend(folder, tampered, vocab, lambda s: 'x')


if __name__ == '__main__':
    unittest.main()
